import sys
import unittest
from unittest.mock import patch, MagicMock, Mock # Use Mock for simple signal slots

# Required for QApplication
# Make sure PyQt5 is installed: pip install PyQt5
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtTest import QTest # Often useful, but we'll try without explicit QTest simulation first

# The class we are testing
from frontend.ui.main_window import InventoryUI
# We need to mock AddComponentDialog where it's *looked up* inside main_window.py
MODULE_PATH_PREFIX = 'frontend.ui.main_window'

# --- Global QApplication instance ---
# Create one instance for all tests in this module
# Prevents issues with multiple QApplications
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# --- Mock Component Data Structure ---
# Helper to create objects mimicking the structure expected by display_data
class MockComponent:
    def __init__(self, part_number, name, component_type, value, quantity, purchase_link=None, datasheet_link=None):
        self.part_number = part_number
        self.name = name
        self.component_type = component_type # This should be the BACKEND name
        self.value = value
        self.quantity = quantity
        self.purchase_link = purchase_link
        self.datasheet_link = datasheet_link

# --- The Test Class ---
class TestInventoryUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up resources shared by all tests in this class (if any)."""
        # QApplication is already created globally
        pass

    def setUp(self):
        """Set up resources before each test."""
        # Create a new instance of the UI for each test to ensure isolation
        self.window = InventoryUI()

        # Mock the AddComponentDialog dependency for display_data
        # We only need its ui_to_backend_name_mapping reversed
        # Patch the *class* where it's imported/used in main_window.py
        self.mock_dialog_patcher = patch(f'{MODULE_PATH_PREFIX}.AddComponentDialog', autospec=True)
        self.mock_AddComponentDialog = self.mock_dialog_patcher.start()

        # Configure the mock instance returned when AddComponentDialog() is called
        mock_dialog_instance = self.mock_AddComponentDialog.return_value
        # Provide the mapping needed by display_data
        mock_dialog_instance.ui_to_backend_name_mapping = {
            "Resistor": "resistor",
            "Capacitor": "capacitor",
            "IC": "integrated_circuit"
            # Add other mappings used in your actual dialog
        }
        # Make sure the mock class itself also returns the instance
        self.mock_AddComponentDialog.return_value = mock_dialog_instance


    def tearDown(self):
        """Clean up resources after each test."""
        # Stop the patcher
        self.mock_dialog_patcher.stop()
        # Explicitly close the window if it's not automatically handled
        # self.window.close() # Might not be necessary if instance is local to setUp
        del self.window

    # --- Test Cases ---

    def test_initialization(self):
        """Test if UI elements are created correctly on initialization."""
        self.assertIsNotNone(self.window.central_widget)
        self.assertEqual(self.window.windowTitle(), "Electronics Inventory Manager")
        self.assertIsNotNone(self.window.add_button)
        self.assertEqual(self.window.add_button.text(), "Add Component")
        self.assertIsNotNone(self.window.remove_button)
        self.assertEqual(self.window.remove_button.text(), "Remove Component")
        self.assertFalse(self.window.remove_button.isEnabled(), "Remove button should be disabled initially")
        self.assertIsNotNone(self.window.export_button)
        self.assertEqual(self.window.export_button.text(), "Export to .TXT")
        self.assertIsNotNone(self.window.import_button)
        self.assertEqual(self.window.import_button.text(), "Import from .TXT")
        self.assertIsNotNone(self.window.table)
        self.assertEqual(self.window.table.columnCount(), 7)
        self.assertEqual(self.window.table.horizontalHeaderItem(0).text(), "Part Number")
        self.assertEqual(self.window.table.horizontalHeaderItem(6).text(), "Datasheet")

    def test_add_button_emits_signal(self):
        """Test if clicking the Add button emits the add_component_requested signal."""
        mock_slot = Mock()
        self.window.add_component_requested.connect(mock_slot)
        self.window.add_button.click() # Simulate click
        mock_slot.assert_called_once()

    def test_export_button_emits_signal(self):
        """Test if clicking the Export button emits the export_requested signal."""
        mock_slot = Mock()
        self.window.export_requested.connect(mock_slot)
        self.window.export_button.click()
        mock_slot.assert_called_once()

    def test_import_button_emits_signal(self):
        """Test if clicking the Import button emits the import_requested signal."""
        mock_slot = Mock()
        self.window.import_requested.connect(mock_slot)
        self.window.import_button.click()
        mock_slot.assert_called_once()

    def test_remove_button_state_and_signal(self):
        """Test remove button enable/disable state and signal emission."""
        # 1. Populate table with some data
        mock_data = [MockComponent("PN123", "R1", "resistor", "10k", 50)]
        self.window.display_data(mock_data)
        self.assertEqual(self.window.table.rowCount(), 1)
        # Should be disabled initially after display_data clears selection
        self.assertFalse(self.window.remove_button.isEnabled())

        # 2. Select a row
        self.window.table.selectRow(0)
        # Now it should be enabled
        self.assertTrue(self.window.remove_button.isEnabled())

        # 3. Test signal emission
        mock_slot = Mock()
        self.window.remove_component_requested.connect(mock_slot)
        self.window.remove_button.click()
        mock_slot.assert_called_once_with("PN123") # Check it emits the correct part number

        # 4. Clear selection
        self.window.table.clearSelection()
        # Should be disabled again
        self.assertFalse(self.window.remove_button.isEnabled())

    def test_get_selected_part_number(self):
        """Test retrieving the part number from the selected row."""
        mock_data = [
            MockComponent("PN101", "C1", "capacitor", "1uF", 10),
            MockComponent("PN202", "U1", "integrated_circuit", "OpAmp", 5)
        ]
        self.window.display_data(mock_data)

        # No selection
        self.assertIsNone(self.window.get_selected_part_number())

        # Select first row
        self.window.table.selectRow(0)
        self.assertEqual(self.window.get_selected_part_number(), "PN101")

        # Select second row
        self.window.table.selectRow(1)
        self.assertEqual(self.window.get_selected_part_number(), "PN202")

    def test_display_data(self):
        """Test if display_data correctly populates the table."""
        mock_data = [
            MockComponent("PN-R1", "Resistor 1", "resistor", "1k", 100, "http://buy.co/r1", "http://data.co/r1"),
            MockComponent("PN-C1", "Capacitor 1", "capacitor", "10uF", 50, datasheet_link="http://data.co/c1"),
            MockComponent("PN-IC1", "IC 1", "integrated_circuit", "Logic Gate", 20),
            MockComponent("PN-X1", "Xtal", "crystal", "16MHz", 5, "invalid-link", "file://local/data.pdf"), # Test unknown type & links
        ]

        self.window.display_data(mock_data)

        self.assertEqual(self.window.table.rowCount(), 4)

        # Check Row 0 (Resistor)
        self.assertEqual(self.window.table.item(0, 0).text(), "PN-R1")
        self.assertEqual(self.window.table.item(0, 1).text(), "Resistor 1")
        self.assertEqual(self.window.table.item(0, 2).text(), "Resistor") # Check UI name mapping
        self.assertEqual(self.window.table.item(0, 3).text(), "1k")
        self.assertEqual(self.window.table.item(0, 4).text(), "100")
        # Purchase Link
        purchase_item_r1 = self.window.table.item(0, 5)
        self.assertEqual(purchase_item_r1.text(), "Link")
        self.assertIsInstance(purchase_item_r1.data(Qt.UserRole), QUrl)
        self.assertEqual(purchase_item_r1.data(Qt.UserRole).toString(), "http://buy.co/r1")
        # Datasheet Link
        datasheet_item_r1 = self.window.table.item(0, 6)
        self.assertEqual(datasheet_item_r1.text(), "Link")
        self.assertIsInstance(datasheet_item_r1.data(Qt.UserRole), QUrl)
        self.assertEqual(datasheet_item_r1.data(Qt.UserRole).toString(), "http://data.co/r1")

        # Check Row 1 (Capacitor - no purchase link)
        self.assertEqual(self.window.table.item(1, 0).text(), "PN-C1")
        self.assertEqual(self.window.table.item(1, 2).text(), "Capacitor") # Check UI name mapping
        self.assertEqual(self.window.table.item(1, 5).text(), "") # No purchase link text
        datasheet_item_c1 = self.window.table.item(1, 6)
        self.assertEqual(datasheet_item_c1.text(), "Link")
        self.assertEqual(datasheet_item_c1.data(Qt.UserRole).toString(), "http://data.co/c1")

        # Check Row 2 (IC - no links)
        self.assertEqual(self.window.table.item(2, 0).text(), "PN-IC1")
        self.assertEqual(self.window.table.item(2, 2).text(), "IC") # Check UI name mapping
        self.assertEqual(self.window.table.item(2, 5).text(), "")
        self.assertEqual(self.window.table.item(2, 6).text(), "")

        # Check Row 3 (Unknown type, invalid http link, file link)
        self.assertEqual(self.window.table.item(3, 0).text(), "PN-X1")
        self.assertEqual(self.window.table.item(3, 2).text(), "crystal") # Type name passed through if not in map
        # Purchase Link (invalid gets http scheme added)
        purchase_item_x1 = self.window.table.item(3, 5)
        self.assertEqual(purchase_item_x1.text(), "Link")
        self.assertEqual(purchase_item_x1.data(Qt.UserRole).toString(), "http:invalid-link")
        # Datasheet Link (file scheme preserved)
        datasheet_item_x1 = self.window.table.item(3, 6)
        self.assertEqual(datasheet_item_x1.text(), "Link")
        self.assertEqual(datasheet_item_x1.data(Qt.UserRole).toString(), "file://local/data.pdf")


    def test_link_click_emits_signal(self):
        """Test clicking a link cell emits the link_clicked signal."""
        mock_data = [MockComponent("PN1", "Comp1", "resistor", "1k", 1, purchase_link="http://link.com")]
        self.window.display_data(mock_data)

        mock_slot = Mock()
        self.window.link_clicked.connect(mock_slot)

        # Simulate click on the purchase link cell (row 0, col 5)
        # Directly emitting the table's signal is often easiest for unit tests
        link_item = self.window.table.item(0, 5)
        expected_url = link_item.data(Qt.UserRole)
        self.assertIsInstance(expected_url, QUrl)
        self.window.table.cellClicked.emit(0, 5) # Emit signal with row/col

        mock_slot.assert_called_once_with(expected_url)

        # Simulate click on a non-link cell (row 0, col 0)
        mock_slot.reset_mock() # Reset the mock call count
        self.window.table.cellClicked.emit(0, 0)
        mock_slot.assert_not_called() # Should not be called for non-link cells

    def test_set_remove_button_enabled(self):
        """Test the direct slot for setting remove button state."""
        self.window.set_remove_button_enabled(True)
        self.assertTrue(self.window.remove_button.isEnabled())
        self.window.set_remove_button_enabled(False)
        self.assertFalse(self.window.remove_button.isEnabled())


if __name__ == '__main__':
    unittest.main()