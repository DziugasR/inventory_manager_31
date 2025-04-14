import uuid

from PyQt5.QtWidgets import QMessageBox, QInputDialog, QFileDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QObject, QUrl

from frontend.ui.main_window import InventoryUI
from frontend.ui.add_component_dialog import AddComponentDialog
from frontend.controllers.generate_ideas_controller import GenerateIdeasController
from frontend.controllers.import_export_controller import ImportExportController

from backend.inventory import (
    get_all_components, add_component, remove_component_quantity, get_component_by_id
)
from backend.exceptions import (
    InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError,
    DuplicateComponentError, InvalidInputError
)

class MainController(QObject):
    def __init__(self, view: InventoryUI):
        super().__init__()
        self._view = view
        self._import_export_controller = ImportExportController(self._view, self)
        self._connect_signals()
        self._load_initial_data()

    def _connect_signals(self):
        self._view.load_data_requested.connect(self.load_inventory_data)
        self._view.add_component_requested.connect(self.open_add_component_dialog)
        self._view.remove_components_requested.connect(self.handle_remove_components)
        self._view.generate_ideas_requested.connect(self.open_generate_ideas_dialog)
        self._view.export_requested.connect(self._import_export_controller.handle_export_request)
        self._view.import_requested.connect(self._import_export_controller.handle_import_request)
        self._view.link_clicked.connect(self.open_link_in_browser)

    def _load_initial_data(self):
        self.load_inventory_data()

    def load_inventory_data(self):
        try:
            components = get_all_components()
            self._view.display_data(components) # View needs to handle Component objects correctly
        except DatabaseError as e:
            self._show_message("Database Error", f"Failed to load inventory: {e}", level="critical")
        except Exception as e:
             self._show_message("Error", f"An unexpected error occurred while loading data: {e}", level="critical")

    def open_add_component_dialog(self):
        dialog = AddComponentDialog(self._view)
        dialog.component_data_collected.connect(self._add_new_component)
        dialog.exec_()

    def _add_new_component(self, component_data: dict):
        try:
            required_keys = ['part_number', 'component_type', 'value', 'quantity']
            if not all(key in component_data for key in required_keys):
                 raise InvalidInputError("Missing required component data from dialog.")

            add_component(
                part_number=component_data['part_number'],
                component_type=component_data['component_type'],
                value=component_data['value'],
                quantity=component_data['quantity'],
                purchase_link=component_data.get('purchase_link'),
                datasheet_link=component_data.get('datasheet_link')
            )
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

    def handle_remove_components(self, component_ids: list[uuid.UUID]):
        success_count = 0
        failure_count = 0
        messages = []

        if not component_ids:
            self._show_message("Selection Error", "No components selected.", level="warning")
            return

        confirm = QMessageBox.question(
            self._view,
            "Confirm Removal",
            f"You are about to interact with {len(component_ids)} selected component(s).\n"
            "Proceed with removal quantity input for each?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if confirm == QMessageBox.No:
            return

        for component_id in component_ids:
            component = None
            part_number_display = f"ID: {component_id}"
            current_quantity = 0

            try:
                component = get_component_by_id(component_id)
                if not component:
                     messages.append(f"- ID {component_id}: Not found in database (might be removed already?).")
                     failure_count += 1
                     continue
                current_quantity = component.quantity
                part_number_display = component.part_number

            except DatabaseError as e:
                messages.append(f"- ID {component_id}: DB error fetching details - {e}")
                failure_count += 1
                continue
            except Exception as e:
                messages.append(f"- ID {component_id}: Unexpected error fetching details - {e}")
                failure_count += 1
                continue

            if current_quantity <= 0:
                messages.append(f"- {part_number_display} (ID: {component_id}): Already has quantity 0 or less.")
                failure_count += 1
                continue

            quantity_to_remove, ok = QInputDialog.getInt(
                self._view,
                "Remove Quantity",
                f"Component: {part_number_display}\nAvailable: {current_quantity}\nEnter quantity to remove:",
                value=1, min=1, max=current_quantity
            )

            if not ok:
                 messages.append(f"- {part_number_display}: Removal cancelled by user.")
                 failure_count += 1
                 continue

            if quantity_to_remove <= 0:
                 messages.append(f"- {part_number_display}: Invalid quantity ({quantity_to_remove}) entered.")
                 failure_count += 1
                 continue

            try:
                remove_component_quantity(component_id, quantity_to_remove)
                messages.append(f"- {part_number_display}: Removed {quantity_to_remove} units (remaining: {current_quantity - quantity_to_remove}).")
                success_count += 1
            except (InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError) as e:

                messages.append(f"- {part_number_display}: Removal error - {e}")
                failure_count += 1
            except Exception as e:
                 messages.append(f"- {part_number_display}: Unexpected removal error - {e}")
                 failure_count += 1

        summary_title = "Removal Summary"
        summary_message = f"Processed {len(component_ids)} component(s):\n"
        summary_message += f"Successfully removed: {success_count}\n"
        summary_message += f"Failed/Cancelled: {failure_count}\n\nDetails:\n" + "\n".join(messages)

        if failure_count > 0:
            self._show_message(summary_title, summary_message, level="warning")
        else:
            self._show_message(summary_title, summary_message, level="info")

        if success_count > 0:
            self.load_inventory_data()


    def open_generate_ideas_dialog(self, checked_ids: list[uuid.UUID]):
        if not checked_ids:
            self._show_message("Generate Ideas", "No components selected.", level="warning")
            return

        selected_components = []
        errors = []
        for cid in checked_ids:
            try:
                component = get_component_by_id(cid)
                if component:
                    selected_components.append(component)
                else:
                    errors.append(f"Could not find details for ID {cid} (already removed?).")
            except DatabaseError as e:
                errors.append(f"Database error fetching ID {cid}: {e}")
            except Exception as e:
                 errors.append(f"Unexpected error fetching ID {cid}: {e}")

        if errors:
            error_message = "Could not fetch details for all selected components:\n" + "\n".join(errors)
            self._show_message("Data Fetch Warning", error_message, level="warning")

        if not selected_components:
            self._show_message("Generate Ideas", "Could not retrieve details for any selected components.",
                               level="warning")
            return

        idea_controller = GenerateIdeasController(selected_components, self._view)
        idea_controller.show()

    def open_link_in_browser(self, url: QUrl):
        if url and url.isValid():
            QDesktopServices.openUrl(url)
        else:
            self._show_message("Invalid Link", "The selected link is not valid.", level="warning")

    def _show_message(self, title: str, text: str, level: str = "info"):
        msg_box = QMessageBox(self._view) # Ensure parent is set
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        if level == "info":
            msg_box.setIcon(QMessageBox.Information)
        elif level == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif level == "critical":
            msg_box.setIcon(QMessageBox.Critical)
        else:
            msg_box.setIcon(QMessageBox.NoIcon) # Or Information as default
        msg_box.exec_()

    def show_view(self):
        self._view.show()