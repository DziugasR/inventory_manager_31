import sys
import unittest
from unittest.mock import Mock, patch

# Ensure QApplication exists for widget testing
from PyQt5.QtWidgets import QApplication, QDialog
# Import the class to be tested
from frontend.ui.add_component_dialog import AddComponentDialog

# Initialize QApplication if it doesn't exist
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

class TestAddComponentDialog(unittest.TestCase):

    def setUp(self):
        self.dialog = AddComponentDialog()

    def tearDown(self):
        self.dialog.deleteLater() # Ensure cleanup

    def test_initialization(self):
        self.assertIsInstance(self.dialog, AddComponentDialog)
        self.assertEqual(self.dialog.windowTitle(), "Add New Component")
        self.assertEqual(self.dialog.type_input.currentText(), "Resistor")
        self.assertIn("Resistance (Ω)", self.dialog.dynamic_fields)
        self.assertIn("Tolerance (%)", self.dialog.dynamic_fields)
        self.assertEqual(self.dialog.quantity_input.value(), 1)

    def test_update_fields_on_type_change(self):
        initial_fields = list(self.dialog.dynamic_fields.keys())
        self.assertIn("Resistance (Ω)", initial_fields)

        self.dialog.type_input.setCurrentText("Capacitor")
        # Simulate signal emission if setCurrentText doesn't trigger it in test env
        # self.dialog.update_fields() # Direct call for robustness in test

        new_fields = list(self.dialog.dynamic_fields.keys())
        self.assertNotIn("Resistance (Ω)", new_fields)
        self.assertIn("Capacitance (µF)", new_fields)
        self.assertIn("Voltage (V)", new_fields)

    def test_get_component_data(self):
        self.dialog.type_input.setCurrentText("LED")
        self.dialog.part_number_input.setText(" PN123 ")
        self.dialog.dynamic_fields["Wavelength (nm)"][1].setText(" 650 ")
        self.dialog.dynamic_fields["Luminous Intensity (mcd)"][1].setText(" 1500 ")
        self.dialog.quantity_input.setValue(50)
        self.dialog.purchase_link_input.setText(" http://buy.com/led ")
        self.dialog.datasheet_link_input.setText(" http://data.com/led ")

        expected_data = {
            'part_number': 'PN123',
            'component_type': 'led',
            'value': "Wavelength (nm): 650, Luminous Intensity (mcd): 1500",
            'quantity': 50,
            'purchase_link': 'http://buy.com/led',
            'datasheet_link': 'http://data.com/led'
        }
        actual_data = self.dialog.get_component_data()
        self.assertDictEqual(actual_data, expected_data)

    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_validate_inputs_fail_no_part_number(self, mock_warning):
        self.dialog.part_number_input.setText("")
        self.dialog.dynamic_fields["Resistance (Ω)"][1].setText("1k")
        self.assertFalse(self.dialog.validate_inputs())
        mock_warning.assert_called_once_with(self.dialog, "Input Error", "Part number is required.")

    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_validate_inputs_fail_no_primary_value(self, mock_warning):
        self.dialog.type_input.setCurrentText("Capacitor")
        self.dialog.part_number_input.setText("C1")
        # Leave "Capacitance (µF)" empty
        self.dialog.dynamic_fields["Voltage (V)"][1].setText("16")
        self.assertFalse(self.dialog.validate_inputs())
        mock_warning.assert_called_once_with(self.dialog, "Input Error", "Primary value 'Capacitance (µF)' is required.")

    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_validate_inputs_success(self, mock_warning):
        self.dialog.part_number_input.setText("R1")
        self.dialog.dynamic_fields["Resistance (Ω)"][1].setText("10k")
        self.assertTrue(self.dialog.validate_inputs())
        mock_warning.assert_not_called()

    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_handle_accept_success(self, mock_warning):
        mock_slot = Mock()
        self.dialog.component_data_collected.connect(mock_slot)
        self.dialog.accept = Mock() # Mock the accept method

        self.dialog.part_number_input.setText("R1")
        self.dialog.dynamic_fields["Resistance (Ω)"][1].setText("10k")
        self.dialog.quantity_input.setValue(5)

        expected_data = {
            'part_number': 'R1',
            'component_type': 'resistor',
            'value': "Resistance (Ω): 10k, Tolerance (%): ", # Tolerance is empty but collected
            'quantity': 5,
            'purchase_link': '',
            'datasheet_link': ''
        }

        self.dialog.handle_accept()

        mock_warning.assert_not_called()
        mock_slot.assert_called_once_with(expected_data)
        self.dialog.accept.assert_called_once()


    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_handle_accept_fail_validation(self, mock_warning):
        mock_slot = Mock()
        self.dialog.component_data_collected.connect(mock_slot)
        self.dialog.accept = Mock() # Mock the accept method

        # Fail validation (no part number)
        self.dialog.part_number_input.setText("")
        self.dialog.dynamic_fields["Resistance (Ω)"][1].setText("10k")

        self.dialog.handle_accept()

        mock_warning.assert_called_once()
        mock_slot.assert_not_called()
        self.dialog.accept.assert_not_called()

    def test_reject_button_connection(self):
         # Test the reject functionality via the button box signal
        self.dialog.reject = Mock() # Mock the dialog's reject slot
        self.dialog.button_box.rejected.emit() # Simulate signal from button box
        self.dialog.reject.assert_called_once()


if __name__ == '__main__':
    unittest.main()