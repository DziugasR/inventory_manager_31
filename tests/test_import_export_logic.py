import unittest
import pandas as pd
import uuid
from unittest.mock import patch, MagicMock

from backend import import_export_logic
from backend.models import Component
from backend.exceptions import DatabaseError, InvalidInputError, ComponentError


class MockDbComponent:
    def __init__(self, part_number, component_type, value, quantity, purchase_link=None, datasheet_link=None):
        self.id = uuid.uuid4()
        self.part_number = part_number
        self.component_type = component_type
        self.value = value
        self.quantity = quantity
        self.purchase_link = purchase_link
        self.datasheet_link = datasheet_link


class MockCreatedComponent:
    def __init__(self, **kwargs):
        self.id = uuid.uuid4()
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestImportExportLogic(unittest.TestCase):

    @patch('backend.import_export_logic.ExcelWriter', MagicMock())
    @patch('backend.import_export_logic.pd.DataFrame')
    @patch('backend.import_export_logic.get_session')
    def test_export_to_excel_success(self, mock_get_session, mock_pd_dataframe):
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_ordered_query = MagicMock()

        mock_comp1 = MockDbComponent("R101", "resistor", "10k", 5, "link1", "link2")
        mock_comp2 = MockDbComponent("C202", "capacitor", "1uF", 10)
        mock_db_data = [mock_comp1, mock_comp2]

        mock_ordered_query.all.return_value = mock_db_data
        mock_query.order_by.return_value = mock_ordered_query
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        mock_df_instance = MagicMock()
        mock_pd_dataframe.return_value = mock_df_instance

        mock_excel_writer_instance = MagicMock()
        mock_excel_writer_context = MagicMock()
        mock_excel_writer_context.__enter__.return_value = mock_excel_writer_instance
        import_export_logic.ExcelWriter.return_value = mock_excel_writer_context

        filename = "test_export.xlsx"
        result = import_export_logic.export_to_excel(filename)

        self.assertTrue(result)
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.order_by.assert_called_once_with(Component.part_number)
        mock_ordered_query.all.assert_called_once()

        expected_df_data = [
            {"Part Number": "R101", "Type": "resistor", "Value": "10k", "Quantity": 5, "Purchase Link": "link1",
             "Datasheet Link": "link2"},
            {"Part Number": "C202", "Type": "capacitor", "Value": "1uF", "Quantity": 10, "Purchase Link": None,
             "Datasheet Link": None},
        ]
        mock_pd_dataframe.assert_called_once_with(expected_df_data, columns=import_export_logic.EXCEL_COLUMNS)

        import_export_logic.ExcelWriter.assert_called_once_with(filename, engine='openpyxl')
        mock_df_instance.to_excel.assert_called_once_with(mock_excel_writer_instance, sheet_name='Inventory',
                                                          index=False, header=True)
        mock_session.close.assert_called_once()

    @patch('backend.import_export_logic.get_session')
    def test_export_to_excel_db_error(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("DB connection failed")
        mock_get_session.return_value = mock_session

        filename = "test_export_fail.xlsx"
        with self.assertRaisesRegex(DatabaseError, "Failed to fetch components for export"):
            import_export_logic.export_to_excel(filename)

        mock_session.close.assert_called_once()

    @patch('backend.import_export_logic.ExcelWriter')
    @patch('backend.import_export_logic.pd.DataFrame')
    @patch('backend.import_export_logic.get_session')
    def test_export_to_excel_io_error(self, mock_get_session, mock_pd_dataframe, mock_excel_writer):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_ordered_query = MagicMock()
        mock_ordered_query.all.return_value = [MockDbComponent("T1", "transistor", "2N2222", 1)]
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_ordered_query
        mock_session.query.return_value = mock_query
        mock_pd_dataframe.return_value = MagicMock()

        mock_excel_writer.side_effect = IOError("Permission denied")

        filename = "test_export_io_fail.xlsx"
        with self.assertRaisesRegex(IOError, "Failed to write Excel file"):
            import_export_logic.export_to_excel(filename)

        mock_session.close.assert_called_once()

    @patch('backend.import_export_logic.ComponentFactory.create_component')
    @patch('backend.import_export_logic.get_session')
    @patch('backend.import_export_logic.pd.read_excel')
    def test_import_from_excel_success(self, mock_read_excel, mock_get_session, mock_create_component):
        mock_data = {
            "Part Number": ["PN101", "PN102", " PN103 "],
            "Type": ["Resistor", " capacitor ", "LED"],
            "Value": ["1k", "10uF", " 5mm Red "],
            "Quantity": [50, 10, 100],
            "Purchase Link": ["link1", None, " "],
            "Datasheet Link": [None, "link_ds_2", "link_ds_3"]
        }
        mock_df = pd.DataFrame(mock_data)
        mock_read_excel.return_value = mock_df

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_create_component.side_effect = lambda **kwargs: MockCreatedComponent(**kwargs)

        filename = "test_import.xlsx"
        result = import_export_logic.import_from_excel(filename)

        self.assertTrue(result)
        mock_read_excel.assert_called_once_with(filename, engine='openpyxl')
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_session.query(Component).delete.assert_called_once()

        self.assertEqual(mock_create_component.call_count, 3)
        mock_create_component.assert_any_call(component_type='resistor', part_number='PN101', value='1k', quantity=50,
                                              purchase_link='link1', datasheet_link=None)
        mock_create_component.assert_any_call(component_type='capacitor', part_number='PN102', value='10uF',
                                              quantity=10, purchase_link=None, datasheet_link='link_ds_2')
        mock_create_component.assert_any_call(component_type='led', part_number='PN103', value='5mm Red', quantity=100,
                                              purchase_link=None, datasheet_link='link_ds_3')

        self.assertEqual(mock_session.add.call_count, 3)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()

    @patch('backend.import_export_logic.pd.read_excel')
    def test_import_from_excel_file_not_found(self, mock_read_excel):
        mock_read_excel.side_effect = FileNotFoundError("File missing")
        filename = "non_existent.xlsx"
        with self.assertRaisesRegex(FileNotFoundError, "Import file not found"):
            import_export_logic.import_from_excel(filename)

    @patch('backend.import_export_logic.pd.read_excel')
    def test_import_from_excel_read_error(self, mock_read_excel):
        mock_read_excel.side_effect = Exception("Cannot parse file")
        filename = "corrupted.xlsx"
        with self.assertRaisesRegex(InvalidInputError, "Failed to read or parse Excel file"):
            import_export_logic.import_from_excel(filename)

    @patch('backend.import_export_logic.pd.read_excel')
    def test_import_from_excel_missing_column(self, mock_read_excel):
        mock_data = {
            "Part Number": ["PN101"],
            "Type": ["Resistor"],
            "Quantity": [50]
        }
        mock_df = pd.DataFrame(mock_data)
        mock_read_excel.return_value = mock_df
        filename = "missing_col.xlsx"
        with self.assertRaisesRegex(InvalidInputError, "missing required columns: Value"):
            import_export_logic.import_from_excel(filename)

    @patch('backend.import_export_logic.pd.read_excel')
    def test_import_from_excel_invalid_row_data(self, mock_read_excel):
        mock_data = {
            "Part Number": ["PN101"], "Type": ["Resistor"], "Value": ["1k"], "Quantity": [-5]
        }
        mock_df = pd.DataFrame(mock_data)
        mock_read_excel.return_value = mock_df
        filename = "invalid_row.xlsx"
        with self.assertRaisesRegex(InvalidInputError, "Invalid data found in row 2.*Quantity cannot be negative"):
            import_export_logic.import_from_excel(filename)

    @patch('backend.import_export_logic.ComponentFactory.create_component')
    @patch('backend.import_export_logic.get_session')
    @patch('backend.import_export_logic.pd.read_excel')
    def test_import_from_excel_component_creation_error(self, mock_read_excel, mock_get_session, mock_create_component):
        mock_data = {
            "Part Number": ["PN101"], "Type": ["UnknownType"], "Value": ["1"], "Quantity": [1]
        }
        mock_df = pd.DataFrame(mock_data)
        mock_read_excel.return_value = mock_df
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_create_component.side_effect = ValueError("Invalid type")

        filename = "invalid_comp_type.xlsx"
        with self.assertRaisesRegex(ComponentError, "Failed to create component for Part Number 'PN101'"):
            import_export_logic.import_from_excel(filename)

        mock_session.query(Component).delete.assert_called_once()
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.import_export_logic.ComponentFactory.create_component')
    @patch('backend.import_export_logic.get_session')
    @patch('backend.import_export_logic.pd.read_excel')
    def test_import_from_excel_db_commit_error(self, mock_read_excel, mock_get_session, mock_create_component):
        mock_data = {
            "Part Number": ["PN101"], "Type": ["Resistor"], "Value": ["1k"], "Quantity": [50]
        }
        mock_df = pd.DataFrame(mock_data)
        mock_read_excel.return_value = mock_df

        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("DB commit failed")
        mock_get_session.return_value = mock_session
        mock_create_component.return_value = MockCreatedComponent()

        filename = "db_commit_fail.xlsx"
        with self.assertRaisesRegex(DatabaseError, "Database error during import"):
            import_export_logic.import_from_excel(filename)

        mock_session.query(Component).delete.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
