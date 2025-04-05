import sys
import unittest
from unittest.mock import patch, Mock, ANY # ANY can be useful for complex args

# Required for QApplication
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtTest import QTest # May be needed for more complex interactions
from PyQt5.QtCore import Qt

# The class we are testing
from frontend.ui.add_component_dialog import AddComponentDialog

# --- Global QApplication instance ---
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# --- Mock QMessageBox ---
# We need to patch it where it's *looked up* inside add_component_dialog.py
MODULE_PATH_PREFIX = 'frontend.ui.add_component_dialog'

# --- The Test Class ---
class TestAddComponentDialog(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up resources shared by all tests in this class."""
        # Patch QMessageBox for all tests in this class
        cls.mock_msgbox_patcher = patch(f'{MODULE_PATH_PREFIX}.QMessageBox', autospec=True)
        cls.MockQMessageBox = cls.mock_msgbox_patcher.start()

    @classmethod
    def tearDownClass(cls):
        """Clean up resources shared by all tests in this class."""
        cls.mock_msgbox_patcher.stop()

    def setUp(self):
        """Set up resources before each test."""
        # Create a new instance of the UI for each test
        self.dialog = AddComponentDialog()
        # Reset the mock message box calls before each test
        self.MockQMessageBox.reset_mock()

    def tearDown(self):
        """Clean up resources after each test."""
        # Close the dialog window after each test
        # self.dialog.close() # Or self.dialog.deleteLater() - often not strictly needed if instance is local
        del self.dialog


    # --- Test Cases ---

    def test_initialization(self):
        """Test dialog initialization and default values."""
        self.assertEqual(self.dialog.windowTitle(), "Add New Component")
        self.assertIsNotNone(self.dialog.type_input)
        self.assertIsNotNone(self.dialog.part_number_input)
        self.assertIsNotNone(self.dialog.name_input)
        self.assertIsNotNone(self.dialog.quantity_input)
        self.assertIsNotNone(self.dialog.purchase_link_input)
        self.assertIsNotNone(self.dialog.datasheet_link_input)
        self.assertIsNotNone(self.dialog.button_box)

        # Check default type and quantity
        self.assertEqual(self.dialog.type_input.currentText(), "Resistor")
        self.assertEqual(self.dialog.quantity_input.value(), 1)

        # Check initial dynamic fields for Resistor
        self.assertIn("Resistance (Ω)", self.dialog.dynamic_fields)
        self.assertIn("Tolerance (%)", self.dialog.dynamic_fields)
        self.assertEqual(len(self.dialog.dynamic_fields), 2)

    def test_dynamic_field_update(self):
        """Test if dynamic fields change when the type is changed."""
        # Initial state (Resistor)
        self.assertIn("Resistance (Ω)", self.dialog.dynamic_fields)
        self.assertIn("Tolerance (%)", self.dialog.dynamic_fields)
        self.assertNotIn("Capacitance (µF)", self.dialog.dynamic_fields) # Ensure others aren't present

        # Change type to Capacitor
        self.dialog.type_input.setCurrentText("Capacitor")
        # Note: In a real app, the signal would trigger update_fields.
        # In unittest, we might need to call it manually if signal processing isn't tested directly
        # However, setCurrentText often triggers the signal synchronously in tests. Let's assume it does.
        # If not, uncomment the line below:
        # self.dialog.update_fields() # Call manually if needed

        # Verify new state
        self.assertNotIn("Resistance (Ω)", self.dialog.dynamic_fields, "Old Resistor field should be removed")
        self.assertNotIn("Tolerance (%)", self.dialog.dynamic_fields, "Old Resistor field should be removed")
        self.assertIn("Capacitance (µF)", self.dialog.dynamic_fields, "Capacitor field should be added")
        self.assertIn("Voltage (V)", self.dialog.dynamic_fields, "Capacitor field should be added")
        self.assertEqual(len(self.dialog.dynamic_fields), 2) # Should only have the 2 capacitor fields

        # Change type to IC
        self.dialog.type_input.setCurrentText("IC")
        # self.dialog.update_fields() # If needed

        self.assertNotIn("Capacitance (µF)", self.dialog.dynamic_fields)
        self.assertIn("Number of Pins", self.dialog.dynamic_fields)
        self.assertIn("Function", self.dialog.dynamic_fields)
        self.assertEqual(len(self.dialog.dynamic_fields), 2)

    def test_validation_success(self):
        """Test validation passes when all required fields are filled."""
        # Select type (e.g., Resistor)
        self.dialog.type_input.setCurrentText("Resistor")
        # Fill required fields
        self.dialog.part_number_input.setText("PN123")
        self.dialog.name_input.setText("My Resistor")
        # Fill dynamic fields (Resistor needs Resistance and Tolerance)
        resistance_input = self.dialog.dynamic_fields["Resistance (Ω)"][1]
        tolerance_input = self.dialog.dynamic_fields["Tolerance (%)"][1]
        resistance_input.setText("10k")
        tolerance_input.setText("5")

        # Validate
        is_valid = self.dialog.validate_inputs()

        # Assertions
        self.assertTrue(is_valid)
        self.MockQMessageBox.warning.assert_not_called() # No warning should appear

    def test_validation_fail_missing_part_number(self):
        """Test validation fails when part number is missing."""
        self.dialog.name_input.setText("My Resistor")
        # Fill dynamic fields
        resistance_input = self.dialog.dynamic_fields["Resistance (Ω)"][1]
        tolerance_input = self.dialog.dynamic_fields["Tolerance (%)"][1]
        resistance_input.setText("10k")
        tolerance_input.setText("5")

        is_valid = self.dialog.validate_inputs()

        self.assertFalse(is_valid)
        self.MockQMessageBox.warning.assert_called_once_with(
            self.dialog, "Input Error", "Part number is required."
        )

    def test_validation_fail_missing_name(self):
        """Test validation fails when name is missing."""
        self.dialog.part_number_input.setText("PN123")
        # Fill dynamic fields
        resistance_input = self.dialog.dynamic_fields["Resistance (Ω)"][1]
        tolerance_input = self.dialog.dynamic_fields["Tolerance (%)"][1]
        resistance_input.setText("10k")
        tolerance_input.setText("5")

        is_valid = self.dialog.validate_inputs()

        self.assertFalse(is_valid)
        self.MockQMessageBox.warning.assert_called_once_with(
            self.dialog, "Input Error", "Name is required."
        )

    def test_validation_fail_missing_dynamic_field(self):
        """Test validation fails when a dynamic field is missing."""
        self.dialog.part_number_input.setText("PN123")
        self.dialog.name_input.setText("My Resistor")
        # Fill only ONE dynamic field
        resistance_input = self.dialog.dynamic_fields["Resistance (Ω)"][1]
        resistance_input.setText("10k")
        # Leave Tolerance empty

        is_valid = self.dialog.validate_inputs()

        self.assertFalse(is_valid)
        self.MockQMessageBox.warning.assert_called_once_with(
            self.dialog, "Input Error", "'Tolerance (%)' is required."
        )

    def test_get_component_data(self):
        """Test data collection from all fields."""
        # Setup
        self.dialog.type_input.setCurrentText("Capacitor")
        self.dialog.part_number_input.setText(" CPN456 ") # Add whitespace
        self.dialog.name_input.setText(" Big Cap")
        self.dialog.quantity_input.setValue(25)
        self.dialog.purchase_link_input.setText("http://buy.co ")
        self.dialog.datasheet_link_input.setText("http://data.co")
        # Dynamic fields for Capacitor
        cap_input = self.dialog.dynamic_fields["Capacitance (µF)"][1]
        volt_input = self.dialog.dynamic_fields["Voltage (V)"][1]
        cap_input.setText(" 100 ")
        volt_input.setText(" 16")

        # Get data
        data = self.dialog.get_component_data()

        # Expected data
        expected = {
            'part_number': 'CPN456',
            'name': 'Big Cap',
            'component_type': 'capacitor', # Check backend name
            'value': 'Capacitance (µF): 100, Voltage (V): 16', # Check combined/formatted value
            'quantity': 25,
            'purchase_link': 'http://buy.co',
            'datasheet_link': 'http://data.co'
        }

        # Assert
        self.assertDictEqual(data, expected)

    def test_accept_success_emits_signal(self):
        """Test clicking OK with valid data emits the signal and accepts."""
        # Setup valid data (similar to test_validation_success)
        self.dialog.part_number_input.setText("PN123")
        self.dialog.name_input.setText("My Resistor")
        resistance_input = self.dialog.dynamic_fields["Resistance (Ω)"][1]
        tolerance_input = self.dialog.dynamic_fields["Tolerance (%)"][1]
        resistance_input.setText("10k")
        tolerance_input.setText("5")
        self.dialog.quantity_input.setValue(50) # Add quantity etc.
        self.dialog.purchase_link_input.setText("link1")
        self.dialog.datasheet_link_input.setText("link2")


        # Mock the accept method to check if it's called
        self.dialog.accept = Mock()
        # Create a mock slot to connect to the signal
        mock_slot = Mock()
        self.dialog.component_data_collected.connect(mock_slot)

        # Simulate OK button click (by emitting the accepted signal)
        self.dialog.button_box.accepted.emit()

        # Assertions
        self.MockQMessageBox.warning.assert_not_called() # Validation should pass

        # Check signal emission
        expected_data = {
            'part_number': 'PN123',
            'name': 'My Resistor',
            'component_type': 'resistor',
            'value': 'Resistance (Ω): 10k, Tolerance (%): 5',
            'quantity': 50,
            'purchase_link': 'link1',
            'datasheet_link': 'link2'
        }
        mock_slot.assert_called_once_with(expected_data)

        # Check if dialog was accepted
        self.dialog.accept.assert_called_once()

    def test_accept_fail_validation_no_signal(self):
        """Test clicking OK with invalid data shows warning and does not emit/accept."""
        # Setup invalid data (missing name)
        self.dialog.part_number_input.setText("PN123")
        resistance_input = self.dialog.dynamic_fields["Resistance (Ω)"][1]
        tolerance_input = self.dialog.dynamic_fields["Tolerance (%)"][1]
        resistance_input.setText("10k")
        tolerance_input.setText("5")

        # Mock accept method and signal slot
        self.dialog.accept = Mock()
        mock_slot = Mock()
        self.dialog.component_data_collected.connect(mock_slot)

        # Simulate OK button click
        self.dialog.button_box.accepted.emit()

        # Assertions
        # Check warning was shown
        self.MockQMessageBox.warning.assert_called_once_with(
            self.dialog, "Input Error", "Name is required."
        )
        # Check signal was NOT emitted
        mock_slot.assert_not_called()
        # Check dialog was NOT accepted
        self.dialog.accept.assert_not_called()

    def test_reject_cancels_dialog(self):
        """Test clicking Cancel rejects the dialog."""
         # Mock the reject method to check if it's called
        self.dialog.reject = Mock()
        mock_slot = Mock() # To ensure data signal is not emitted
        self.dialog.component_data_collected.connect(mock_slot)

        # Simulate Cancel button click
        self.dialog.button_box.rejected.emit()

        # Assertions
        mock_slot.assert_not_called()
        self.dialog.reject.assert_called_once()


if __name__ == '__main__':
    unittest.main()