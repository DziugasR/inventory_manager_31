from PyQt5.QtWidgets import QMessageBox, QInputDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QObject, QUrl

from frontend.ui.main_window import InventoryUI
from frontend.ui.add_component_dialog import AddComponentDialog
from frontend.controllers.generate_ideas_controller import GenerateIdeasController # Import the new dialog

from backend.inventory import (
    get_all_components, add_component, remove_component_quantity, get_component_by_part_number
)
from backend.exceptions import (
    InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError,
    DuplicateComponentError, InvalidInputError
)

class MainController(QObject):
    def __init__(self, view: InventoryUI):
        super().__init__()
        self.view = view
        self._connect_signals()
        self._load_initial_data()

    def _connect_signals(self):
        self.view.load_data_requested.connect(self.load_inventory_data)
        self.view.add_component_requested.connect(self.open_add_component_dialog)
        self.view.remove_components_requested.connect(self.handle_remove_components)
        self.view.generate_ideas_requested.connect(self.open_generate_ideas_dialog) # Connect the signal
        self.view.link_clicked.connect(self.open_link_in_browser)
        # Removed: self.view.table.selectionModel().selectionChanged.connect(self.view._update_remove_button_state)

    def _load_initial_data(self):
        self.load_inventory_data()

    def load_inventory_data(self):
        try:
            components = get_all_components()
            self.view.display_data(components)
        except DatabaseError as e:
            self._show_message("Database Error", f"Failed to load inventory: {e}", level="critical")
        except Exception as e:
             self._show_message("Error", f"An unexpected error occurred while loading data: {e}", level="critical")

    def open_add_component_dialog(self):
        dialog = AddComponentDialog(self.view)
        dialog.component_data_collected.connect(self._add_new_component)
        dialog.exec_()

    def _add_new_component(self, component_data: dict):
        try:
            add_component(**component_data)
            self._show_message("Success", f"Component '{component_data['part_number']}' added successfully.", level="info")
            self.load_inventory_data()
        except DuplicateComponentError as e:
            self._show_message("Duplicate Component", str(e), level="warning")
        except InvalidQuantityError as e:
             self._show_message("Invalid Quantity", str(e), level="warning")
        except DatabaseError as e:
            self._show_message("Database Error", f"Failed to add component: {e}", level="critical")
        except InvalidInputError as e:
             self._show_message("Invalid Input", f"Failed to add component: {e}", level="warning")
        except Exception as e:
            self._show_message("Unexpected Error", f"An unexpected error occurred while adding: {e}", level="critical")

    def handle_remove_components(self, part_numbers: list[str]):
        success_count = 0
        failure_count = 0
        messages = []

        if not part_numbers:
            self._show_message("Selection Error", "No components selected.", level="warning")
            return

        confirm = QMessageBox.question(
            self.view,
            "Confirm Removal",
            f"You are about to interact with {len(part_numbers)} selected component(s).\n"
            "Proceed with removal quantity input for each?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if confirm == QMessageBox.No:
            return

        for part_number in part_numbers:
            try:
                component = get_component_by_part_number(part_number)
                if not component:
                     messages.append(f"- {part_number}: Not found in database.")
                     failure_count += 1
                     continue
                current_quantity = component.quantity

                quantity_to_remove, ok = QInputDialog.getInt(
                    self.view,
                    "Remove Quantity",
                    f"Component: {part_number}\nAvailable: {current_quantity}\nEnter quantity to remove:",
                    value=1, min=1, max=current_quantity
                )

                if not ok:
                     messages.append(f"- {part_number}: Removal cancelled by user.")
                     failure_count += 1
                     continue

                if quantity_to_remove <= 0:
                     messages.append(f"- {part_number}: Invalid quantity ({quantity_to_remove}) entered.")
                     failure_count += 1
                     continue

                try:
                    remove_component_quantity(part_number, quantity_to_remove)
                    messages.append(f"- {part_number}: Removed {quantity_to_remove} units (remaining: {current_quantity - quantity_to_remove}).")
                    success_count += 1
                except (InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError) as e:
                    messages.append(f"- {part_number}: Removal error - {e}")
                    failure_count += 1
                except Exception as e:
                     messages.append(f"- {part_number}: Unexpected removal error - {e}")
                     failure_count += 1

            except ComponentNotFoundError as e:
                 messages.append(f"- {part_number}: Error fetching details - {e}")
                 failure_count += 1
            except DatabaseError as e:
                messages.append(f"- {part_number}: DB error fetching details - {e}")
                failure_count += 1
            except Exception as e:
                messages.append(f"- {part_number}: Unexpected error - {e}")
                failure_count += 1

        summary_title = "Removal Summary"
        summary_message = f"Processed {len(part_numbers)} component(s):\n"
        summary_message += f"Successfully removed: {success_count}\n"
        summary_message += f"Failed/Cancelled: {failure_count}\n\nDetails:\n" + "\n".join(messages)

        if failure_count > 0:
            self._show_message(summary_title, summary_message, level="warning")
        else:
            self._show_message(summary_title, summary_message, level="info")

        if success_count > 0:
            self.load_inventory_data()

    # Removed the single handle_remove_component method as handle_remove_components now iterates

    def open_generate_ideas_dialog(self, checked_part_numbers: list):
        if not checked_part_numbers:
            self._show_message("Generate Ideas", "No components selected.", level="warning")
            return

        selected_components = []
        errors = []
        for pn in checked_part_numbers:
            try:
                component = get_component_by_part_number(pn)
                if component:
                    selected_components.append(component)
                else:
                    # This case should ideally not happen if part number came from table
                    errors.append(f"Could not find details for {pn} (already removed?).")
            except DatabaseError as e:
                errors.append(f"Database error fetching {pn}: {e}")
            except Exception as e:
                 errors.append(f"Unexpected error fetching {pn}: {e}")

        if errors:
            # Decide how to handle errors: show message and continue, or stop?
            # Let's show a warning but still open the dialog with found components.
            error_message = "Could not fetch details for all selected components:\n" + "\n".join(errors)
            self._show_message("Data Fetch Warning", error_message, level="warning")

        if not selected_components:
            self._show_message("Generate Ideas", "Could not retrieve details for any selected components.",
                               level="warning")
            return

        idea_controller = GenerateIdeasController(selected_components, self.view)
        idea_controller.show()

    def open_link_in_browser(self, url: QUrl):
        if url and url.isValid():
            QDesktopServices.openUrl(url)
        else:
            self._show_message("Invalid Link", "The selected link is not valid.", level="warning")

    def _show_message(self, title: str, text: str, level: str = "info"):
        if level == "info":
            QMessageBox.information(self.view, title, text)
        elif level == "warning":
            QMessageBox.warning(self.view, title, text)
        elif level == "critical":
            QMessageBox.critical(self.view, title, text)
        else:
            QMessageBox.information(self.view, title, text)

    def show_view(self):
        self.view.show()