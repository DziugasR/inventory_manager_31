# test_main_controller.py
import sys
import unittest
from unittest.mock import patch, MagicMock, ANY, call

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QUrl, pyqtSignal, QObject

from frontend.controllers.main_controller import MainController
from frontend.ui.main_window import InventoryUI
from frontend.ui.add_component_dialog import AddComponentDialog
from frontend.controllers.generate_ideas_controller import GenerateIdeasController

from backend import inventory
from backend.exceptions import (
    InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError,
    DuplicateComponentError, InvalidInputError
)

def create_mock_component(**kwargs):
    mock = MagicMock()
    for key, value in kwargs.items():
        setattr(mock, key, value)
    if 'quantity' not in kwargs: mock.quantity = 0
    if 'id' not in kwargs: mock.id = MagicMock()
    if 'part_number' not in kwargs: mock.part_number = "DEFAULT_PN"
    if 'name' not in kwargs: mock.name = "Default Name"
    if 'component_type' not in kwargs: mock.component_type = "TYPE"
    if 'value' not in kwargs: mock.value = "VAL"
    if 'purchase_link' not in kwargs: mock.purchase_link = None
    if 'datasheet_link' not in kwargs: mock.datasheet_link = None
    return mock

class MockInventoryUI(QObject):
    load_data_requested = pyqtSignal()
    add_component_requested = pyqtSignal()
    remove_components_requested = pyqtSignal(list)
    generate_ideas_requested = pyqtSignal(list)
    link_clicked = pyqtSignal(QUrl)

    display_data = MagicMock()
    show = MagicMock()

    def __init__(self):
        super().__init__()
        self.display_data.reset_mock()
        self.show.reset_mock()

app = QApplication(sys.argv)

class TestMainController(unittest.TestCase):

    def setUp(self):
        self.mock_view = MockInventoryUI()
        self.patcher_get_all = patch('frontend.controllers.main_controller.get_all_components')
        self.patcher_add_comp = patch('frontend.controllers.main_controller.add_component')
        self.patcher_remove_qty = patch('frontend.controllers.main_controller.remove_component_quantity')
        self.patcher_get_by_pn = patch('frontend.controllers.main_controller.get_component_by_part_number')
        self.patcher_qmessagebox = patch('frontend.controllers.main_controller.QMessageBox')
        self.patcher_qinputdialog = patch('frontend.controllers.main_controller.QInputDialog')
        self.patcher_qdesktopservices = patch('frontend.controllers.main_controller.QDesktopServices')
        self.patcher_adddialog = patch('frontend.controllers.main_controller.AddComponentDialog')
        self.patcher_ideascontroller = patch('frontend.controllers.main_controller.GenerateIdeasController')

        self.mock_get_all = self.patcher_get_all.start()
        self.mock_add_comp = self.patcher_add_comp.start()
        self.mock_remove_qty = self.patcher_remove_qty.start()
        self.mock_get_by_pn = self.patcher_get_by_pn.start()
        self.mock_qmessagebox = self.patcher_qmessagebox.start()
        self.mock_qinputdialog = self.patcher_qinputdialog.start()
        self.mock_qdesktopservices = self.patcher_qdesktopservices.start()
        self.mock_adddialog_class = self.patcher_adddialog.start()
        self.mock_ideascontroller_class = self.patcher_ideascontroller.start()

        # --- FIX for AddComponentDialog signal ---
        self.mock_adddialog_instance = MagicMock(spec=AddComponentDialog) # Use spec for better mocking
        # Make component_data_collected a MagicMock itself to ensure it has mock methods like connect
        self.mock_adddialog_instance.component_data_collected = MagicMock()
        self.mock_adddialog_class.return_value = self.mock_adddialog_instance
        # --- End Fix ---

        with patch.object(MainController, '_load_initial_data', return_value=None) as mock_load_initial:
             self.controller = MainController(self.mock_view)
             mock_load_initial.assert_called_once()

    def tearDown(self):
        self.patcher_get_all.stop()
        self.patcher_add_comp.stop()
        self.patcher_remove_qty.stop()
        self.patcher_get_by_pn.stop()
        self.patcher_qmessagebox.stop()
        self.patcher_qinputdialog.stop()
        self.patcher_qdesktopservices.stop()
        self.patcher_adddialog.stop()
        self.patcher_ideascontroller.stop()
        del self.controller
        del self.mock_view

    def test_load_inventory_data_on_request_signal(self):
        self.mock_get_all.reset_mock()
        self.mock_view.display_data.reset_mock()
        mock_components = [create_mock_component(part_number="L1")]
        self.mock_get_all.return_value = mock_components
        self.mock_view.load_data_requested.emit()
        self.mock_get_all.assert_called_once()
        self.mock_view.display_data.assert_called_once_with(mock_components)

    def test_load_inventory_data_success(self):
        mock_components = [create_mock_component(part_number="C1"), create_mock_component(part_number="C2")]
        self.mock_get_all.return_value = mock_components
        self.controller.load_inventory_data()
        self.mock_get_all.assert_called_once()
        self.mock_view.display_data.assert_called_once_with(mock_components)
        self.mock_qmessagebox.critical.assert_not_called()

    def test_load_inventory_data_db_error(self):
        error_message = "Connection failed"
        self.mock_get_all.side_effect = DatabaseError(error_message)
        self.controller.load_inventory_data()
        self.mock_get_all.assert_called_once()
        self.mock_view.display_data.assert_not_called()
        self.mock_qmessagebox.critical.assert_called_once_with(
            self.mock_view, "Database Error", f"Failed to load inventory: {error_message}"
        )

    def test_load_inventory_data_unexpected_error(self):
        error_message = "Something broke"
        self.mock_get_all.side_effect = Exception(error_message)
        self.controller.load_inventory_data()
        self.mock_get_all.assert_called_once()
        self.mock_view.display_data.assert_not_called()
        self.mock_qmessagebox.critical.assert_called_once_with(
            self.mock_view, "Error", f"An unexpected error occurred while loading data: {error_message}"
        )

    def test_open_add_component_dialog(self):
        self.controller.open_add_component_dialog()
        self.mock_adddialog_class.assert_called_once_with(self.mock_view)
        # Now assert that the connect method of the *mocked* signal attribute was called
        self.mock_adddialog_instance.component_data_collected.connect.assert_called_once_with(
             self.controller._add_new_component
        )
        self.mock_adddialog_instance.exec_.assert_called_once()

    def test_add_new_component_success(self):
        component_data = {"part_number": "R1", "name": "Res", "quantity": 10}
        with patch.object(self.controller, 'load_inventory_data') as mock_load:
            # To simulate signal emission, we need to call the connected slot directly
            # or configure the mock signal's connect method to store the slot
            # and then call it. Direct call is simpler here:
            self.controller._add_new_component(component_data)
            self.mock_add_comp.assert_called_once_with(**component_data)
            self.mock_qmessagebox.information.assert_called_once_with(
                self.mock_view, "Success", f"Component '{component_data['part_number']}' added successfully."
            )
            mock_load.assert_called_once()
            self.mock_qmessagebox.warning.assert_not_called()
            self.mock_qmessagebox.critical.assert_not_called()

    def test_add_new_component_duplicate_error(self):
        component_data = {"part_number": "R_DUP", "name": "Dup Res", "quantity": 5}
        error_message = f"Component with part number {component_data['part_number']} already exists"
        self.mock_add_comp.side_effect = DuplicateComponentError(error_message)
        with patch.object(self.controller, 'load_inventory_data') as mock_load:
            self.controller._add_new_component(component_data)
            self.mock_add_comp.assert_called_once_with(**component_data)
            self.mock_qmessagebox.warning.assert_called_once_with(
                self.mock_view, "Duplicate Component", error_message
            )
            mock_load.assert_not_called()
            self.mock_qmessagebox.information.assert_not_called()
            self.mock_qmessagebox.critical.assert_not_called()

    def test_add_new_component_invalid_input_error(self):
        component_data = {"part_number": "R_BAD", "name": "Bad Res", "quantity": -5}
        error_message = "Quantity cannot be negative"
        self.mock_add_comp.side_effect = InvalidInputError(error_message)
        with patch.object(self.controller, 'load_inventory_data') as mock_load:
            self.controller._add_new_component(component_data)
            self.mock_add_comp.assert_called_once_with(**component_data)
            self.mock_qmessagebox.warning.assert_called_once_with(
                 self.mock_view, "Invalid Input", f"Failed to add component: {error_message}"
             )
            mock_load.assert_not_called()

    def test_handle_remove_components_no_selection(self):
        with patch.object(self.controller, 'load_inventory_data') as mock_load:
            self.controller.handle_remove_components([])
            self.mock_qmessagebox.warning.assert_called_once_with(
                self.mock_view, "Selection Error", "No components selected."
            )
            self.mock_qmessagebox.question.assert_not_called()
            self.mock_qinputdialog.getInt.assert_not_called()
            self.mock_remove_qty.assert_not_called()
            mock_load.assert_not_called()

    def test_handle_remove_components_user_cancels_confirmation(self):
        part_numbers = ["PN1", "PN2"]
        # --- FIX for QMessageBox comparison ---
        # Define a simple value to represent No
        mock_cancel_value = 0
        self.mock_qmessagebox.question.return_value = mock_cancel_value
        # Patch the actual QMessageBox.No value within this test's scope
        with patch('frontend.controllers.main_controller.QMessageBox.No', mock_cancel_value):
        # --- End Fix ---
            with patch.object(self.controller, 'load_inventory_data') as mock_load:
                self.controller.handle_remove_components(part_numbers)
                self.mock_qmessagebox.question.assert_called_once()
                self.mock_get_by_pn.assert_not_called()
                self.mock_qinputdialog.getInt.assert_not_called()
                self.mock_remove_qty.assert_not_called()
                mock_load.assert_not_called()
                self.mock_qmessagebox.information.assert_not_called()
                self.mock_qmessagebox.warning.assert_not_called()

    def test_handle_remove_components_success_single(self):
        part_number = "PN_OK"
        initial_qty = 10
        remove_qty = 3
        mock_comp = create_mock_component(part_number=part_number, quantity=initial_qty)
        # --- Need to patch Yes as well if patching No ---
        mock_confirm_value = 1
        self.mock_qmessagebox.question.return_value = mock_confirm_value
        with patch('frontend.controllers.main_controller.QMessageBox.Yes', mock_confirm_value):
        # --- End Patch ---
            self.mock_get_by_pn.return_value = mock_comp
            self.mock_qinputdialog.getInt.return_value = (remove_qty, True)
            self.mock_remove_qty.return_value = None
            with patch.object(self.controller, 'load_inventory_data') as mock_load:
                self.controller.handle_remove_components([part_number])
                self.mock_qmessagebox.question.assert_called_once()
                self.mock_get_by_pn.assert_called_once_with(part_number)
                self.mock_qinputdialog.getInt.assert_called_once_with(
                    self.mock_view, ANY, ANY, value=1, min=1, max=initial_qty
                )
                self.mock_remove_qty.assert_called_once_with(part_number, remove_qty)
                self.mock_qmessagebox.information.assert_called_once()
                self.assertIn(f"Successfully removed: 1", self.mock_qmessagebox.information.call_args[0][2])
                self.assertIn(f"Failed/Cancelled: 0", self.mock_qmessagebox.information.call_args[0][2])
                self.assertIn(f"- {part_number}: Removed {remove_qty} units", self.mock_qmessagebox.information.call_args[0][2])
                mock_load.assert_called_once()

    def test_handle_remove_components_component_not_found(self):
        part_number = "PN_MISSING"
        mock_confirm_value = 1
        self.mock_qmessagebox.question.return_value = mock_confirm_value
        with patch('frontend.controllers.main_controller.QMessageBox.Yes', mock_confirm_value):
            self.mock_get_by_pn.return_value = None
            with patch.object(self.controller, 'load_inventory_data') as mock_load:
                self.controller.handle_remove_components([part_number])
                self.mock_get_by_pn.assert_called_once_with(part_number)
                self.mock_qinputdialog.getInt.assert_not_called()
                self.mock_remove_qty.assert_not_called()
                self.mock_qmessagebox.warning.assert_called_once()
                self.assertIn(f"Successfully removed: 0", self.mock_qmessagebox.warning.call_args[0][2])
                self.assertIn(f"Failed/Cancelled: 1", self.mock_qmessagebox.warning.call_args[0][2])
                self.assertIn(f"- {part_number}: Not found in database.", self.mock_qmessagebox.warning.call_args[0][2])
                mock_load.assert_not_called()

    def test_handle_remove_components_user_cancels_input_dialog(self):
        part_number = "PN_CANCEL"
        initial_qty = 5
        mock_comp = create_mock_component(part_number=part_number, quantity=initial_qty)
        mock_confirm_value = 1
        self.mock_qmessagebox.question.return_value = mock_confirm_value
        with patch('frontend.controllers.main_controller.QMessageBox.Yes', mock_confirm_value):
            self.mock_get_by_pn.return_value = mock_comp
            self.mock_qinputdialog.getInt.return_value = (1, False)
            with patch.object(self.controller, 'load_inventory_data') as mock_load:
                 self.controller.handle_remove_components([part_number])
                 self.mock_get_by_pn.assert_called_once_with(part_number)
                 self.mock_qinputdialog.getInt.assert_called_once()
                 self.mock_remove_qty.assert_not_called()
                 self.mock_qmessagebox.warning.assert_called_once()
                 self.assertIn(f"Failed/Cancelled: 1", self.mock_qmessagebox.warning.call_args[0][2])
                 self.assertIn(f"- {part_number}: Removal cancelled by user.", self.mock_qmessagebox.warning.call_args[0][2])
                 mock_load.assert_not_called()

    def test_handle_remove_components_backend_stock_error(self):
        part_number = "PN_STOCK"
        initial_qty = 2
        remove_qty = 5
        mock_comp = create_mock_component(part_number=part_number, quantity=initial_qty)
        error_message = f"Not enough stock to remove {remove_qty}. Available: {initial_qty}"
        mock_confirm_value = 1
        self.mock_qmessagebox.question.return_value = mock_confirm_value
        with patch('frontend.controllers.main_controller.QMessageBox.Yes', mock_confirm_value):
            self.mock_get_by_pn.return_value = mock_comp
            self.mock_qinputdialog.getInt.return_value = (remove_qty, True)
            self.mock_remove_qty.side_effect = StockError(error_message)
            with patch.object(self.controller, 'load_inventory_data') as mock_load:
                 self.controller.handle_remove_components([part_number])
                 self.mock_get_by_pn.assert_called_once_with(part_number)
                 self.mock_qinputdialog.getInt.assert_called_once()
                 self.mock_remove_qty.assert_called_once_with(part_number, remove_qty)
                 self.mock_qmessagebox.warning.assert_called_once()
                 self.assertIn(f"Failed/Cancelled: 1", self.mock_qmessagebox.warning.call_args[0][2])
                 self.assertIn(f"- {part_number}: Removal error - {error_message}", self.mock_qmessagebox.warning.call_args[0][2])
                 mock_load.assert_not_called()

    def test_handle_remove_components_mixed_results(self):
        pn_ok = "PN_OK"
        pn_cancel = "PN_CANCEL"
        pn_stock = "PN_STOCK"
        part_numbers = [pn_ok, pn_cancel, pn_stock]
        mock_comp_ok = create_mock_component(part_number=pn_ok, quantity=10)
        mock_comp_cancel = create_mock_component(part_number=pn_cancel, quantity=5)
        mock_comp_stock = create_mock_component(part_number=pn_stock, quantity=2)

        def get_by_pn_side_effect(pn):
            if pn == pn_ok: return mock_comp_ok
            if pn == pn_cancel: return mock_comp_cancel
            if pn == pn_stock: return mock_comp_stock
            return None
        self.mock_get_by_pn.side_effect = get_by_pn_side_effect

        def get_int_side_effect(parent, title, label, value, min, max):
            if pn_ok in label: return (3, True)
            if pn_cancel in label: return (1, False)
            if pn_stock in label: return (5, True)
            return (0, False)
        self.mock_qinputdialog.getInt.side_effect = get_int_side_effect

        def remove_qty_side_effect(pn, qty):
            if pn == pn_ok: return None
            if pn == pn_stock: raise StockError("Not enough stock")
        self.mock_remove_qty.side_effect = remove_qty_side_effect

        mock_confirm_value = 1
        self.mock_qmessagebox.question.return_value = mock_confirm_value
        with patch('frontend.controllers.main_controller.QMessageBox.Yes', mock_confirm_value):
            with patch.object(self.controller, 'load_inventory_data') as mock_load:
                 self.controller.handle_remove_components(part_numbers)
                 self.assertEqual(self.mock_get_by_pn.call_count, 3)
                 self.assertEqual(self.mock_qinputdialog.getInt.call_count, 3)
                 self.assertEqual(self.mock_remove_qty.call_count, 2)
                 self.mock_remove_qty.assert_has_calls([call(pn_ok, 3), call(pn_stock, 5)], any_order=True)
                 self.mock_qmessagebox.warning.assert_called_once()
                 summary_text = self.mock_qmessagebox.warning.call_args[0][2]
                 self.assertIn(f"Successfully removed: 1", summary_text)
                 self.assertIn(f"Failed/Cancelled: 2", summary_text)
                 self.assertIn(f"- {pn_ok}: Removed 3 units", summary_text)
                 self.assertIn(f"- {pn_cancel}: Removal cancelled by user", summary_text)
                 self.assertIn(f"- {pn_stock}: Removal error - Not enough stock", summary_text)
                 mock_load.assert_called_once()

    def test_open_generate_ideas_dialog_no_selection(self):
        self.controller.open_generate_ideas_dialog([])
        self.mock_qmessagebox.warning.assert_called_once_with(
            self.mock_view, "Generate Ideas", "No components selected."
        )
        self.mock_ideascontroller_class.assert_not_called()
        self.mock_get_by_pn.assert_not_called()

    def test_open_generate_ideas_dialog_success(self):
        part_numbers = ["IDEA_PN1", "IDEA_PN2"]
        mock_comp1 = create_mock_component(part_number=part_numbers[0])
        mock_comp2 = create_mock_component(part_number=part_numbers[1])
        expected_components = [mock_comp1, mock_comp2]

        def get_by_pn_side_effect(pn):
             if pn == part_numbers[0]: return mock_comp1
             if pn == part_numbers[1]: return mock_comp2
             return None
        self.mock_get_by_pn.side_effect = get_by_pn_side_effect

        mock_ideas_instance = MagicMock()
        self.mock_ideascontroller_class.return_value = mock_ideas_instance

        self.controller.open_generate_ideas_dialog(part_numbers)

        self.assertEqual(self.mock_get_by_pn.call_count, 2)
        self.mock_get_by_pn.assert_has_calls([call(part_numbers[0]), call(part_numbers[1])])
        self.mock_ideascontroller_class.assert_called_once_with(expected_components, self.mock_view)
        mock_ideas_instance.show.assert_called_once()
        self.mock_qmessagebox.warning.assert_not_called()

    def test_open_generate_ideas_dialog_fetch_error_some_found(self):
        part_numbers = ["IDEA_OK", "IDEA_ERR"]
        mock_comp_ok = create_mock_component(part_number=part_numbers[0])
        error_message = "DB lookup failed"

        def get_by_pn_side_effect(pn):
             if pn == part_numbers[0]: return mock_comp_ok
             if pn == part_numbers[1]: raise DatabaseError(error_message)
             return None
        self.mock_get_by_pn.side_effect = get_by_pn_side_effect

        mock_ideas_instance = MagicMock()
        self.mock_ideascontroller_class.return_value = mock_ideas_instance

        self.controller.open_generate_ideas_dialog(part_numbers)

        self.assertEqual(self.mock_get_by_pn.call_count, 2)
        self.mock_qmessagebox.warning.assert_called_once()
        self.assertIn(f"Database error fetching {part_numbers[1]}", self.mock_qmessagebox.warning.call_args[0][2])
        self.mock_ideascontroller_class.assert_called_once_with([mock_comp_ok], self.mock_view)
        mock_ideas_instance.show.assert_called_once()

    def test_open_generate_ideas_dialog_fetch_error_none_found(self):
        part_numbers = ["IDEA_ERR1", "IDEA_ERR2"]
        self.mock_get_by_pn.side_effect = DatabaseError("Fetch failed")
        self.controller.open_generate_ideas_dialog(part_numbers)
        self.assertEqual(self.mock_get_by_pn.call_count, 2)
        self.mock_qmessagebox.warning.assert_any_call(
            self.mock_view, "Data Fetch Warning", ANY
        )
        self.mock_qmessagebox.warning.assert_any_call(
             self.mock_view, "Generate Ideas", "Could not retrieve details for any selected components."
        )
        self.mock_ideascontroller_class.assert_not_called()

    def test_open_link_in_browser_success(self):
        url_string = "http://example.com"
        url = QUrl(url_string)
        self.controller.open_link_in_browser(url)
        self.mock_qdesktopservices.openUrl.assert_called_once_with(url)
        self.mock_qmessagebox.warning.assert_not_called()

    def test_open_link_in_browser_invalid(self):
        url_invalid = QUrl("")
        url_none = None
        self.controller.open_link_in_browser(url_invalid)
        self.mock_qdesktopservices.openUrl.assert_not_called()
        self.mock_qmessagebox.warning.assert_called_once_with(
            self.mock_view, "Invalid Link", "The selected link is not valid."
        )
        self.mock_qmessagebox.warning.reset_mock()
        self.controller.open_link_in_browser(url_none)
        self.mock_qdesktopservices.openUrl.assert_not_called()
        self.mock_qmessagebox.warning.assert_called_once_with(
            self.mock_view, "Invalid Link", "The selected link is not valid."
        )

    def test_show_message_levels(self):
        title = "Test Title"
        text = "Test message text."
        self.controller._show_message(title, text, level="info")
        self.mock_qmessagebox.information.assert_called_once_with(self.mock_view, title, text)
        self.mock_qmessagebox.warning.assert_not_called()
        self.mock_qmessagebox.critical.assert_not_called()
        self.mock_qmessagebox.information.reset_mock()
        self.controller._show_message(title, text, level="warning")
        self.mock_qmessagebox.warning.assert_called_once_with(self.mock_view, title, text)
        self.mock_qmessagebox.information.assert_not_called()
        self.mock_qmessagebox.critical.assert_not_called()
        self.mock_qmessagebox.warning.reset_mock()
        self.controller._show_message(title, text, level="critical")
        self.mock_qmessagebox.critical.assert_called_once_with(self.mock_view, title, text)
        self.mock_qmessagebox.information.assert_not_called()
        self.mock_qmessagebox.warning.assert_not_called()
        self.mock_qmessagebox.critical.reset_mock()
        self.controller._show_message(title, text)
        self.mock_qmessagebox.information.assert_called_once_with(self.mock_view, title, text)
        self.mock_qmessagebox.information.reset_mock()

    def test_show_view(self):
        self.controller.show_view()
        self.mock_view.show.assert_called_once()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)