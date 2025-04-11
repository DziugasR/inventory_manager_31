# test_main_window.py
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open

from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QWidget, QCheckBox, QHBoxLayout, QAbstractItemView
from PyQt5.QtCore import Qt, QUrl, QObject
from PyQt5.QtTest import QTest, QSignalSpy

from frontend.ui.main_window import InventoryUI
from frontend.ui.add_component_dialog import AddComponentDialog
from pathlib import Path


class MockComponent(QObject):
    def __init__(self, part_number="PN", name="Name", component_type="RES", value="1k", quantity=10, purchase_link=None, datasheet_link=None):
        super().__init__()
        self.part_number = part_number
        self.name = name
        self.component_type = component_type
        self.value = value
        self.quantity = quantity
        self.purchase_link = purchase_link
        self.datasheet_link = datasheet_link

app = QApplication(sys.argv)

class TestInventoryUI(unittest.TestCase):

    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)

    def setUp(self):
        self.patcher_setup_toolbar = patch('frontend.ui.main_window.setup_toolbar', return_value=None)
        self.patcher_path = patch('frontend.ui.main_window.Path', autospec=True)
        self.MockPathClass = self.patcher_path.start()
        self.mock_path_instance = self.MockPathClass.return_value
        self.mock_parent = MagicMock()
        self.mock_path_instance.parent = self.mock_parent
        self.mock_final_path = MagicMock(name="FinalPathObject")
        self.mock_parent.__truediv__.return_value = self.mock_final_path
        self.patcher_open = patch('builtins.open', new_callable=mock_open, read_data="QPushButton { color: red; }")
        self.patcher_adjust_width = patch.object(InventoryUI, '_adjust_window_width', return_value=None)

        self.mock_setup_toolbar = self.patcher_setup_toolbar.start()
        self.mock_file_open = self.patcher_open.start()
        self.mock_adjust_width = self.patcher_adjust_width.start()

        self.patcher_add_dialog = patch('frontend.ui.main_window.AddComponentDialog')
        self.MockAddComponentDialog = self.patcher_add_dialog.start()
        mock_dialog_instance = self.MockAddComponentDialog.return_value
        mock_dialog_instance.ui_to_backend_name_mapping = {"Resistor": "RES", "Capacitor": "CAP", "IC": "IC", "TypeAUI": "TYPEA"}

        self.window = InventoryUI()

    def tearDown(self):
        self.patcher_setup_toolbar.stop()
        self.patcher_path.stop()
        self.patcher_open.stop()
        self.patcher_adjust_width.stop()
        self.patcher_add_dialog.stop()

        self.window.close()
        del self.window

    def test_initialization(self):
        self.assertEqual(self.window.windowTitle(), "Electronics Inventory Manager")
        self.assertIsNotNone(self.window.central_widget)
        self.assertIsNotNone(self.window.table)
        self.assertIsNotNone(self.window.add_button)
        self.assertIsNotNone(self.window.remove_button)
        self.assertIsNotNone(self.window.generate_ideas_button)
        self.mock_setup_toolbar.assert_called_once_with(self.window)
        self.assertEqual(self.window.table.columnCount(), 8)
        self.assertEqual(self.window.table.horizontalHeaderItem(self.window.PART_NUMBER_COL).text(), "Part Number")
        self.assertEqual(self.window.table.horizontalHeaderItem(self.window.CHECKBOX_COL).text(), "Select")
        self.assertTrue(self.window.table.isSortingEnabled())
        self.assertEqual(self.window.table.editTriggers(), QAbstractItemView.NoEditTriggers)
        self.assertTrue(self.window.add_button.isEnabled())
        self.assertFalse(self.window.remove_button.isEnabled())
        self.assertFalse(self.window.generate_ideas_button.isEnabled())
        self.mock_file_open.assert_called_once_with(self.mock_final_path, "r", encoding="utf-8")
        self.mock_adjust_width.assert_called()

    def test_display_data_empty(self):
        self.mock_adjust_width.reset_mock()
        self.window.display_data([])
        self.assertEqual(self.window.table.rowCount(), 0)
        self.assertEqual(len(self.window._checkboxes), 0)
        self.assertFalse(self.window.remove_button.isEnabled())
        self.assertFalse(self.window.generate_ideas_button.isEnabled())
        self.mock_adjust_width.assert_not_called()

    def test_display_data_with_items(self):
        self.mock_adjust_width.reset_mock()
        components = [
            MockComponent(part_number="R101", name="R 1k", component_type="RES", value="1k", quantity=5, purchase_link="http://example.com/r1"),
            MockComponent(part_number="C202", name="C 100n", component_type="CAP", value="100nF", quantity=0, datasheet_link="example.com/c2"),
            MockComponent(part_number="U303", name="IC", component_type="IC", value=None, quantity="Many", purchase_link=None),
        ]
        self.window.display_data(components)
        self.assertEqual(self.window.table.rowCount(), 3)
        self.assertEqual(len(self.window._checkboxes), 3)
        self.assertEqual(self.window.table.item(0, self.window.PART_NUMBER_COL).text(), "C202")
        url_c2 = self.window.table.item(0, self.window.DATASHEET_COL).data(Qt.UserRole)
        self.assertEqual(url_c2.toString(), "http:example.com/c2")
        self.assertEqual(self.window.table.item(1, self.window.PART_NUMBER_COL).text(), "R101")
        self.assertEqual(self.window.table.item(2, self.window.PART_NUMBER_COL).text(), "U303")
        self.mock_adjust_width.assert_called_once()


    def test_display_data_missing_dialog_for_mapping(self):
        self.patcher_add_dialog.stop()
        with patch('frontend.ui.main_window.AddComponentDialog', side_effect=NameError("Dialog not found")):
            self.mock_adjust_width.reset_mock()
            components = [MockComponent(part_number="R101", component_type="RES")]
            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                self.window.display_data(components)
            self.assertEqual(self.window.table.item(0, self.window.TYPE_COL).text(), "RES")
        self.patcher_add_dialog.start()


    def test_add_button_emits_signal(self):
        spy = QSignalSpy(self.window.add_component_requested)
        self.assertEqual(len(spy), 0)
        QTest.mouseClick(self.window.add_button, Qt.LeftButton)
        self.assertEqual(len(spy), 1)

    def test_remove_button_emits_signal_when_checked(self):
        self.mock_adjust_width.reset_mock()
        components = [MockComponent(part_number="R1"), MockComponent(part_number="C2")]
        self.window.display_data(components)
        checkbox_widget_r1 = self.window.table.cellWidget(1, self.window.CHECKBOX_COL)
        checkbox_r1 = checkbox_widget_r1.findChild(QCheckBox)
        checkbox_r1.setChecked(True)
        QTest.qWait(50)
        self.assertTrue(self.window.remove_button.isEnabled())
        spy = QSignalSpy(self.window.remove_components_requested)
        self.assertEqual(len(spy), 0)
        QTest.mouseClick(self.window.remove_button, Qt.LeftButton)
        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0], [["R1"]])


    def test_generate_ideas_button_emits_signal_when_checked(self):
        self.mock_adjust_width.reset_mock()
        components = [MockComponent(part_number="PNA"), MockComponent(part_number="PNB")]
        self.window.display_data(components)
        checkbox_widget_a = self.window.table.cellWidget(0, self.window.CHECKBOX_COL)
        checkbox_a = checkbox_widget_a.findChild(QCheckBox)
        checkbox_a.setChecked(True)
        checkbox_widget_b = self.window.table.cellWidget(1, self.window.CHECKBOX_COL)
        checkbox_b = checkbox_widget_b.findChild(QCheckBox)
        checkbox_b.setChecked(True)
        QTest.qWait(50)
        self.assertTrue(self.window.generate_ideas_button.isEnabled())
        spy = QSignalSpy(self.window.generate_ideas_requested)
        self.assertEqual(len(spy), 0)
        QTest.mouseClick(self.window.generate_ideas_button, Qt.LeftButton)
        self.assertEqual(len(spy), 1)
        self.assertCountEqual(spy[0][0], ["PNA", "PNB"])


    def test_checkbox_state_updates_buttons(self):
        self.mock_adjust_width.reset_mock()
        components = [MockComponent(part_number="T1")]
        self.window.display_data(components)
        self.assertFalse(self.window.remove_button.isEnabled())
        self.assertFalse(self.window.generate_ideas_button.isEnabled())
        checkbox_widget = self.window.table.cellWidget(0, self.window.CHECKBOX_COL)
        checkbox = checkbox_widget.findChild(QCheckBox)
        checkbox.setChecked(True)
        QTest.qWait(50)
        self.assertTrue(self.window.remove_button.isEnabled())
        self.assertTrue(self.window.generate_ideas_button.isEnabled())
        checkbox.setChecked(False)
        QTest.qWait(50)
        self.assertFalse(self.window.remove_button.isEnabled())
        self.assertFalse(self.window.generate_ideas_button.isEnabled())

    def test_link_click_emits_signal(self):
        self.mock_adjust_width.reset_mock()
        link = "http://datasheet.com/ds1"
        components = [MockComponent(part_number="LNK1", datasheet_link=link)]
        self.window.display_data(components)
        spy = QSignalSpy(self.window.link_clicked)
        self.assertEqual(len(spy), 0)
        self.window.table.cellClicked.emit(0, self.window.DATASHEET_COL)
        self.assertEqual(len(spy), 1)
        expected_url = QUrl(link)
        self.assertEqual(spy[0], [expected_url])

    def test_link_click_no_link_no_signal(self):
        self.mock_adjust_width.reset_mock()
        components = [MockComponent(part_number="NL1", purchase_link=None)]
        self.window.display_data(components)
        spy = QSignalSpy(self.window.link_clicked)
        self.assertEqual(len(spy), 0)
        self.window.table.cellClicked.emit(0, self.window.PURCHASE_LINK_COL)
        self.assertEqual(len(spy), 0)
        self.window.table.cellClicked.emit(0, self.window.NAME_COL)
        self.assertEqual(len(spy), 0)

    def test_get_checked_part_numbers(self):
        self.mock_adjust_width.reset_mock()
        components = [
            MockComponent(part_number="CHK1"),
            MockComponent(part_number="CHK2"),
            MockComponent(part_number="CHK3"),
        ]
        self.window.display_data(components)
        self.assertEqual(self.window.get_checked_part_numbers(), [])
        cb0 = self.window.table.cellWidget(0, self.window.CHECKBOX_COL).findChild(QCheckBox)
        cb2 = self.window.table.cellWidget(2, self.window.CHECKBOX_COL).findChild(QCheckBox)
        cb0.setChecked(True)
        cb2.setChecked(True)
        checked = self.window.get_checked_part_numbers()
        self.assertCountEqual(checked, ["CHK1", "CHK3"])

    def test_get_selected_part_number(self):
        self.mock_adjust_width.reset_mock()
        components = [MockComponent(part_number="SEL1"), MockComponent(part_number="SEL2")]
        self.window.display_data(components)
        self.assertIsNone(self.window.get_selected_part_number())
        self.window.table.setCurrentCell(1, 0)
        self.assertEqual(self.window.get_selected_part_number(), "SEL2")
        self.window.table.setCurrentCell(0, 0)
        self.assertEqual(self.window.get_selected_part_number(), "SEL1")
        self.window.table.clearSelection()
        self.window.table.setCurrentCell(-1,-1)
        self.assertIsNone(self.window.get_selected_part_number())

    def test_get_selected_row_data(self):
        self.mock_adjust_width.reset_mock()
        link_p = "http://pur.chase/p1"
        link_d = "http://data.sheet/d1"
        components = [MockComponent(part_number="ROW1", name="Comp A", component_type="TYPEA", value="ValA", quantity=1, purchase_link=link_p, datasheet_link=link_d)]
        self.window.display_data(components)
        self.assertIsNone(self.window.get_selected_row_data())
        self.window.table.setCurrentCell(0, 0)
        data = self.window.get_selected_row_data()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("Part Number"), "ROW1")
        self.assertEqual(data.get("Type"), "TypeAUI")
        self.assertEqual(data.get("Purchase Link_url"), link_p)
        self.assertEqual(data.get("Datasheet_url"), link_d)

    def test_stylesheet_load_not_found(self):
        self.patcher_path.stop()
        self.patcher_open.stop()

        with patch('frontend.ui.main_window.Path', autospec=True) as MockPathLocal, \
                patch('builtins.open', side_effect=FileNotFoundError) as mock_open_local:

            mock_path_inst_local = MockPathLocal.return_value
            mock_parent_local = MagicMock()
            mock_path_inst_local.parent = mock_parent_local
            mock_final_path_local = MagicMock(name="FinalPathLocalForNotFoundCall")
            mock_parent_local.__truediv__.return_value = mock_final_path_local

            with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
                style_content = self.window._load_stylesheet()

        self.assertEqual(style_content, "")
        mock_open_local.assert_called_once_with(mock_final_path_local, "r", encoding="utf-8")

        found_warning = False
        for call_args in mock_stdout.write.call_args_list:
            if call_args and call_args.args:
                printed_string = call_args.args[0]
                if isinstance(printed_string, str) and "Warning: Stylesheet not found at" in printed_string:
                    found_warning = True
                    break
        self.assertTrue(found_warning, "Expected 'Stylesheet not found' warning was not printed.")

        self.patcher_path.start()
        self.patcher_open.start()


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)