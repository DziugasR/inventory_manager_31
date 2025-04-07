from PyQt5.QtWidgets import QMessageBox, QInputDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QObject, QUrl # QObject needed if using signals/slots within controller

# Import UI components
from frontend.ui.main_window import InventoryUI
from frontend.ui.add_component_dialog import AddComponentDialog

# Import backend functions and exceptions
from backend.inventory import (
    get_all_components, add_component, remove_component_quantity, get_component_by_part_number
)
from backend.exceptions import (
    InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError,
    DuplicateComponentError, InvalidInputError
)

class MainController(QObject): # Inherit from QObject for slots
    def __init__(self, view: InventoryUI):
        super().__init__()
        self.view = view
        self._connect_signals()
        self._load_initial_data()

    def _connect_signals(self):
        """ Connect signals from the view to controller slots. """
        self.view.load_data_requested.connect(self.load_inventory_data)
        self.view.add_component_requested.connect(self.open_add_component_dialog)
        self.view.remove_components_requested.connect(self.handle_remove_components)
        self.view.link_clicked.connect(self.open_link_in_browser)
        self.view.table.selectionModel().selectionChanged.connect(self.view._update_remove_button_state)


    def _load_initial_data(self):
        """ Load data when the application starts. """
        self.load_inventory_data()

    # --- Slot Implementations ---

    def load_inventory_data(self):
        """ Fetch data from backend and update the view's table. """
        try:
            components = get_all_components()
            self.view.display_data(components)
        except DatabaseError as e:
            self._show_message("Database Error", f"Failed to load inventory: {e}", level="critical")
        except Exception as e:
             self._show_message("Error", f"An unexpected error occurred while loading data: {e}", level="critical")

    def open_add_component_dialog(self):
        """ Create and show the Add Component dialog. """
        # Pass the view as parent if needed for modality
        dialog = AddComponentDialog(self.view)
        # Connect the dialog's signal to the controller's handler
        dialog.component_data_collected.connect(self._add_new_component)
        dialog.exec_() # Show the dialog modally

    def _add_new_component(self, component_data: dict):
        """ Handle the actual component addition after dialog confirms. """
        try:
            # Basic validation already happened in dialog, now call backend
            print(f"Controller received data to add: {component_data}") # Debug print
            add_component(**component_data)
            self._show_message("Success", f"Component '{component_data['part_number']}' added successfully.", level="info")
            self.load_inventory_data()  # Refresh the table
        except DuplicateComponentError as e:
            self._show_message("Duplicate Component", str(e), level="warning")
        except InvalidQuantityError as e: # Should ideally not happen if SpinBox is used correctly
             self._show_message("Invalid Quantity", str(e), level="warning")
        except DatabaseError as e:
            self._show_message("Database Error", f"Failed to add component: {e}", level="critical")
        except InvalidInputError as e: # Catch potential backend validation errors
             self._show_message("Invalid Input", f"Failed to add component: {e}", level="warning")
        except Exception as e:
            self._show_message("Unexpected Error", f"An unexpected error occurred while adding: {e}", level="critical")

    def handle_remove_components(self, part_numbers: list[str]):
        for item in part_numbers:
            self.handle_remove_component(item)

    def handle_remove_component(self, part_number: str):
        """ Handle the request to remove a component quantity. """
        if not part_number:
            self._show_message("Selection Error", "No component selected.", level="warning")
            return

        try:
            # Fetch current quantity to set max value for input dialog
            # This avoids relying solely on the potentially stale table data
            component = get_component_by_part_number(part_number)
            if not component: # Should not happen if selected from table, but safety check
                 raise ComponentNotFoundError(f"Component {part_number} not found in database.")
            current_quantity = component.quantity

            # Get user input for quantity to remove (using QInputDialog in Controller)
            quantity_to_remove, ok = QInputDialog.getInt(
                self.view, # Parent window
                "Remove Quantity",
                f"Component: {part_number}\nAvailable: {current_quantity} units\nEnter quantity to remove:",
                value=1, min=1, max=current_quantity
            )

            if not ok or quantity_to_remove <= 0:
                return # User cancelled or entered invalid value

            # Confirm removal (using QMessageBox in Controller)
            confirm = QMessageBox.question(
                self.view, # Parent window
                "Confirm Removal",
                f"Are you sure you want to remove {quantity_to_remove} units of '{part_number}'?\n"
                f"Remaining quantity will be {current_quantity - quantity_to_remove}.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if confirm == QMessageBox.Yes:
                try:
                    remove_component_quantity(part_number, quantity_to_remove)
                    self._show_message("Success", f"Removed {quantity_to_remove} units of '{part_number}'.", level="info")
                    self.load_inventory_data() # Refresh table
                except (InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError) as e:
                    self._show_message("Removal Error", str(e), level="warning")
                except Exception as e:
                     self._show_message("Unexpected Error", f"An unexpected error occurred during removal: {e}", level="critical")

        except ComponentNotFoundError as e:
             self._show_message("Error", str(e), level="warning") # Error fetching current quantity
        except DatabaseError as e:
            self._show_message("Database Error", f"Could not retrieve component details: {e}", level="critical")
        except Exception as e:
            self._show_message("Error", f"An unexpected error occurred: {e}", level="critical")

    def open_link_in_browser(self, url: QUrl):
        """ Open the given URL in the default web browser. """
        if url and url.isValid():
            QDesktopServices.openUrl(url)
        else:
            self._show_message("Invalid Link", "The selected link is not valid.", level="warning")

    # --- Helper Methods ---

    def _show_message(self, title: str, text: str, level: str = "info"):
        """ Display a message box using the main window as parent. """
        if level == "info":
            QMessageBox.information(self.view, title, text)
        elif level == "warning":
            QMessageBox.warning(self.view, title, text)
        elif level == "critical":
            QMessageBox.critical(self.view, title, text)
        else: # Default to info
            QMessageBox.information(self.view, title, text)

    def show_view(self):
        """ Makes the main window visible. """
        self.view.show()