import uuid
import os
import re
import sys
from PyQt5.QtWidgets import QMessageBox, QInputDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QObject, QUrl

from frontend.ui.main_window import InventoryUI
from frontend.ui.add_component_dialog import AddComponentDialog
from frontend.ui.add_type_dialog import AddTypeDialog
from backend.type_manager import type_manager
from frontend.controllers.generate_ideas_controller import GenerateIdeasController
from frontend.controllers.import_export_controller import ImportExportController

from backend import database
from backend import inventory_manager
from backend.models_custom import Inventory
from backend.inventory import (
    get_all_components, add_component, remove_component_quantity, get_component_by_id
)
from backend.exceptions import (
    InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError,
    DuplicateComponentError, InvalidInputError
)


class MainController(QObject):
    def __init__(self, view: InventoryUI, openai_model: str, app_path: str):
        super().__init__()
        self._view = view
        self._openai_model = openai_model
        self._app_path = app_path
        self._current_search_term = ""
        self._import_export_controller = ImportExportController(self._view, self)

        self._active_inventory: Inventory | None = None
        self._inventories: list[Inventory] = []

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
        self._view.search_text_changed.connect(self.handle_search_query)

        self._view.menu_bar_handler.new_inventory_action.triggered.connect(self.handle_new_inventory)

    def _load_initial_data(self):
        try:
            self._inventories = inventory_manager.get_all_inventories()
            if not self._inventories:
                raise DatabaseError("No inventories found in the configuration database.")

            self._active_inventory = self._inventories[0]
            self._update_inventory_menu()
            self._update_window_title()

        except DatabaseError as e:
            self._show_message("Fatal Error", f"Could not load inventory list: {e}", "critical")
            return

        self.load_inventory_data()
        self._view._adjust_window_width()

    def _update_inventory_menu(self):
        menu = self._view.menu_bar_handler.open_inventory_menu
        menu.clear()

        for inv in self._inventories:
            action = menu.addAction(inv.name)
            action.triggered.connect(lambda checked=False, inventory=inv: self.switch_inventory(inventory))
            if self._active_inventory and self._active_inventory.id == inv.id:
                font = action.font()
                font.setBold(True)
                action.setFont(font)

    def _update_window_title(self):
        if self._active_inventory:
            self._view.menu_bar_handler.table_name_label.setText(self._active_inventory.name)
        else:
            self._view.menu_bar_handler.table_name_label.setText("No Inventory Loaded")

    def switch_inventory(self, inventory: Inventory):
        print(f"Controller: Switching to inventory '{inventory.name}'")
        if self._active_inventory and self._active_inventory.id == inventory.id:
            print("Controller: Already on this inventory. No switch needed.")
            return

        try:
            if os.path.isabs(inventory.db_path):
                db_path = inventory.db_path
            else:
                db_path = os.path.join(self._app_path, inventory.db_path)

            db_url = f"sqlite:///{db_path}"
            print(f"Controller: Switching DB connection to URL: {db_url}")

            database.switch_inventory_db(db_url)
            self._active_inventory = inventory

            self.load_inventory_data()
            self._update_window_title()
            self._update_inventory_menu()

        except Exception as e:
            self._show_message("Switch Error", f"Failed to switch to inventory '{inventory.name}':\n{e}", "critical")

    def handle_new_inventory(self):
        name, ok = QInputDialog.getText(self._view, "New Inventory", "Enter a name for the new inventory:")
        if ok and name:
            name = name.strip()
            if not name:
                self._show_message("Invalid Name", "Inventory name cannot be empty.", "warning")
                return

            sanitized_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_').lower()
            db_filename = f"inventory_{sanitized_name}.db"

            try:
                new_inventory = inventory_manager.add_new_inventory(name, db_filename)
                self._inventories.append(new_inventory)
                self._inventories.sort(key=lambda x: x.name)

                self._update_inventory_menu()
                self.switch_inventory(new_inventory)
                self._show_message("Success", f"Successfully created and switched to inventory '{name}'.", "info")

            except (DuplicateComponentError, DatabaseError) as e:
                self._show_message("Creation Error", str(e), "critical")
            except Exception as e:
                self._show_message("Unexpected Error", f"An unexpected error occurred: {e}", "critical")

    def handle_search_query(self, query: str):
        self._current_search_term = query.strip().lower()
        self.load_inventory_data()

    def load_inventory_data(self):
        try:
            components = get_all_components()

            if self._current_search_term:
                search_term = self._current_search_term
                filtered_components = [
                    c for c in components if
                    search_term in str(c.part_number or "").lower() or
                    search_term in str(c.component_type or "").lower() or
                    search_term in str(c.value or "").lower()
                ]
                self._view.display_data(filtered_components)
            else:
                self._view.display_data(components)

        except DatabaseError as e:
            self._show_message("Database Error", f"Failed to load inventory: {e}", level="critical")
        except Exception as e:
            self._show_message("Error", f"An unexpected error occurred while loading data: {e}", level="critical")

    def open_add_component_dialog(self):
        dialog = AddComponentDialog(self._view)
        dialog.component_data_collected.connect(self._add_new_component)
        dialog.manage_types_requested.connect(self.open_manage_types_dialog)
        dialog.exec_()

    def open_manage_types_dialog(self, source_dialog: AddComponentDialog):
        type_dialog = AddTypeDialog(self._view)
        type_dialog.new_type_data_collected.connect(
            lambda data: self._add_new_type(data, source_dialog)
        )
        type_dialog.exec_()

    def _add_new_type(self, type_data: dict, source_dialog_to_refresh: AddComponentDialog):
        try:
            ui_name = type_data['ui_name']
            properties = type_data['properties']
            success, message = type_manager.add_new_type(ui_name, properties)

            if success:
                self._show_message("Success", message, level="info")
                source_dialog_to_refresh.refresh_type_list()
            else:
                self._show_message("Error Adding Type", f"Could not add the new type: {message}", level="critical")

        except KeyError:
            self._show_message("Error", "Invalid data received from the type dialog.", level="critical")
        except Exception as e:
            self._show_message("Unexpected Error", f"An unexpected error occurred while adding the type: {e}",
                               level="critical")

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
            self._show_message("Success", f"Component '{component_data['part_number']}' added successfully.",
                               level="info")
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
                messages.append(
                    f"- {part_number_display}: Removed {quantity_to_remove} units "
                    f"(remaining: {current_quantity - quantity_to_remove})."
                )
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

        idea_controller = GenerateIdeasController(selected_components, self._openai_model, self._view)
        idea_controller.show()

    def open_link_in_browser(self, url: QUrl):
        if url and url.isValid():
            QDesktopServices.openUrl(url)
        else:
            self._show_message("Invalid Link", "The selected link is not valid.", level="warning")

    def _show_message(self, title: str, text: str, level: str = "info"):
        msg_box = QMessageBox(self._view)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        if level == "info":
            msg_box.setIcon(QMessageBox.Information)
        elif level == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif level == "critical":
            msg_box.setIcon(QMessageBox.Critical)
        else:
            msg_box.setIcon(QMessageBox.NoIcon)
        msg_box.exec_()

    def show_view(self):
        self._view.show()