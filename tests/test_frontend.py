import unittest
from PyQt5.QtWidgets import QApplication
from frontend.main import InventoryApp
from unittest.mock import patch


class TestInventoryApp(unittest.TestCase):

    def setUp(self):
        """ Set up the QApplication instance. """
        self.app = QApplication([])  # Initialize QApplication
        self.window = InventoryApp()  # Initialize the main window

    def test_add_component_button(self):
        """ Test if the 'Add Component' button is present. """
        button = self.window.add_button
        self.assertEqual(button.text(), "Add Component")
        self.assertTrue(button.isEnabled())

    def test_input_fields(self):
        """ Test if the input fields are present and enabled. """
        self.assertTrue(self.window.part_number_input.isEnabled())
        self.assertTrue(self.window.name_input.isEnabled())
        self.assertTrue(self.window.type_input.isEnabled())
        self.assertTrue(self.window.value_input.isEnabled())
        self.assertTrue(self.window.quantity_input.isEnabled())

    @patch("frontend.main.add_component")
    def test_add_component_function(self, mock_add_component):
        """ Test if the 'Add Component' button calls the add_component function. """
        # Simulate user input
        self.window.part_number_input.setText("ABC123")
        self.window.name_input.setText("Resistor")
        self.window.type_input.setCurrentIndex(0)  # Resistor
        self.window.value_input.setText("10kΩ")
        self.window.quantity_input.setText("100")

        # Trigger the 'Add Component' button click
        self.window.add_button.click()

        # Check if the add_component function was called with correct arguments
        mock_add_component.assert_called_once_with("ABC123", "Resistor", "Resistor", "10kΩ", 100)

    def tearDown(self):
        """ Clean up after tests. """
        self.window.close()


if __name__ == '__main__':
    unittest.main()
