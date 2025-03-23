import unittest
from PyQt5.QtWidgets import QApplication
from frontend.ui import InventoryUI

app = QApplication([])  # Required for testing PyQt

class TestUI(unittest.TestCase):
    def setUp(self):
        """ Initialize UI before each test """
        self.ui = InventoryUI()

    def test_window_title(self):
        """ Test if the window title is correct """
        self.assertEqual(self.ui.windowTitle(), "Electronics Inventory Manager")

    def test_table_headers(self):
        """ Test if table has correct headers """
        headers = [self.ui.table.horizontalHeaderItem(i).text() for i in range(self.ui.table.columnCount())]
        expected_headers = ["Part Number", "Name", "Type", "Value", "Quantity", "Purchase Link", "Datasheet"]
        self.assertEqual(headers, expected_headers)

    def test_add_component_button(self):
        """ Test if the 'Add Component' button exists """
        self.assertEqual(self.ui.add_button.text(), "Add Component")

if __name__ == "__main__":
    unittest.main()