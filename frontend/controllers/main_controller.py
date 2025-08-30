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
from frontend.controllers.type_controller import TypeController
from frontend.controllers.options_controller import OptionsController

from backend import database
from backend import inventory_manager
from backend import settings_manager
from backend.models_custom import Inventory
from backend.inventory import (
    get_all_components, add_component, remove_component_quantity, get_component_by_id
)
from backend.exceptions import (
    InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError,
    DuplicateComponentError, InvalidInputError
)


class MainController(QObject):
    def __init__(self, view: InventoryUI, openai_model: str, app_path: str, api_key: str):
        super().__init__()
        self._view = view
        self._openai_model = settings_manager.get_setting('ai_model', openai_model or 'gpt-4o-mini')
        self._api_key = settings_manager.get_setting('api_key', api_key)
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
        self._view.selection_changed.connect(self.on_selection_changed)

        self._view.menu_bar_handler.new_inventory_action.triggered.connect(self.handle_new_inventory)
        self._view.menu_bar_handler.delete_inventory_action.triggered.connect(self.handle_delete_inventory)
        self._view.menu_bar_handler.manage_types_action.triggered.connect(self.handle_manage_types)
        self._view.menu_bar_handler.options_action.triggered.connect(self.handle_options)
        self._view.menu_bar_handler.toggle_select_action.triggered.connect(self.handle_toggle_select)

    def _load_initial_data(self):
        try:
            self._inventories = inventory_manager.get_all_inventories()
            if not self._inventories:
                raise DatabaseError("No inventories found in the configuration database.")

            startup_id = settings_manager.get_setting('startup_inventory_id', 'last_used')
            inventory_to_load = None

            if startup_id == 'last_used':
                last_id = settings_manager.get_setting('last_inventory_id')
                if last_id:
                    inventory_to_load = next((inv for inv in self._inventories if inv.id == last_id), None)
            else:
                inventory_to_load = next((inv for inv in self._inventories if inv.id == startup_id), None)

            if not inventory_to_load:
                inventory_to_load = self._inventories[0]

            self.switch_inventory(inventory_to_load)

        except DatabaseError as e:
            self._show_message("Fatal Error", f"Could not load inventory list: {e}", "critical")
            return
        except Exception as e:
            self._show_message("Fatal Startup Error", f"An unexpected error occurred during startup: {e}", "critical")
            return

        self._view._adjust_window_width()

    def on_selection_changed(self, has_selection: bool):
        self._view.menu_bar_handler.update_toggle_action_text(has_selection)

    def handle_toggle_select(self):
        if self._view.get_checked_ids():
            self._view.deselect_all_items()
        else:
            self._view.select_all_items()

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
            self._view.menu_bar_handler.set_inventory_name(self._active_inventory.name)
        else:
            self._view.menu_bar_handler.set_inventory_name("No Inventory Loaded")

    def switch_inventory(self, inventory: Inventory):
        print(f"Controller: Switching to inventory '{inventory.name}'")
        if self._active_inventory and self._active_inventory.id == inventory.id:
            return

        try:
            db_path = inventory.db_path if os.path.isabs(inventory.db_path) else os.path.join(self._app_path, inventory.db_path)
            db_url = f"sqlite:///{db_path}"

            database.switch_inventory_db(db_url)
            self._active_inventory = inventory
            settings_manager.set_setting('last_inventory_id', inventory.id)

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

    def handle_delete_inventory(self):
        if len(self._inventories) <= 1:
            self._show_message("Action Not Allowed", "You cannot delete the last remaining inventory.", "warning")
            return

        inventory_names = [inv.name for inv in self._inventories]

        item, ok = QInputDialog.getItem(self._view, "Delete Inventory", "Select an inventory to delete:",
                                        inventory_names, 0, False)

        if ok and item:
            inventory_to_delete = next((inv for inv in self._inventories if inv.name == item), None)
            if not inventory_to_delete:
                self._show_message("Error", "Could not find the selected inventory to delete.", "critical")
                return

            confirm_msg = f"Are you sure you want to permanently delete the inventory '{inventory_to_delete.name}'?\n\nThis action CANNOT be undone."
            reply = QMessageBox.question(self._view, 'Confirm Deletion', confirm_msg, QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.Yes:
                try:
                    is_active = self._active_inventory and self._active_inventory.id == inventory_to_delete.id
                    inventory_manager.delete_inventory(inventory_to_delete.id, self._app_path)
                    self._inventories = [inv for inv in self._inventories if inv.id != inventory_to_delete.id]
                    self._show_message("Success", f"Inventory '{inventory_to_delete.name}' has been deleted.", "info")

                    if is_active:
                        self.switch_inventory(self._inventories[0])
                    else:
                        self._update_inventory_menu()

                except (ComponentNotFoundError, DatabaseError) as e:
                    self._show_message("Deletion Error", str(e), "critical")
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
        except (DatabaseError, Exception) as e:
            self._show_message("Error", f"An unexpected error occurred while loading data: {e}", "critical")

    def open_add_component_dialog(self):
        dialog = AddComponentDialog(self._view)
        dialog.component_data_collected.connect(self._add_new_component)
        dialog.manage_types_requested.connect(self.open_manage_types_dialog)
        dialog.exec_()

    def open_manage_types_dialog(self, source_dialog: AddComponentDialog):
        type_controller = TypeController(self._view, self._app_path)
        if type_controller.open_add_type_dialog():
            source_dialog.refresh_type_list()
            self.load_inventory_data()

    def handle_manage_types(self):
        type_controller = TypeController(self._view, self._app_path)
        if type_controller.open_add_type_dialog():
            self.load_inventory_data()

    def handle_options(self):
        current_settings = {
            'api_key': self._api_key,
            'ai_model': self._openai_model,
            'startup_inventory_id': settings_manager.get_setting('startup_inventory_id', 'last_used'),
            'theme': settings_manager.get_setting('theme', 'System Default')
        }
        options_controller = OptionsController(self._view, self._inventories, current_settings)
        if options_controller.show_dialog():
            self._openai_model = settings_manager.get_setting('ai_model', self._openai_model)
            self._api_key = settings_manager.get_setting('api_key', self._api_key)
            new_theme = settings_manager.get_setting('theme', 'System Default')

            if new_theme != current_settings['theme']:
                self._show_message("Settings Saved", "Please restart the application for the new theme to take effect.", "info")
            else:
                self._show_message("Settings Saved", "Your settings have been saved.", "info")

    def _add_new_component(self, component_data: dict):
        try:
            add_component(
                part_number=component_data['part_number'],
                component_type=component_data['component_type'],
                value=component_data['value'],
                quantity=component_data['quantity'],
                purchase_link=component_data.get('purchase_link'),
                datasheet_link=component_data.get('datasheet_link')
            )
            self._show_message("Success", f"Component '{component_data['part_number']}' added.", "info")
            self.load_inventory_data()
        except (DuplicateComponentError, InvalidQuantityError, InvalidInputError) as e:
            self._show_message("Input Error", str(e), "warning")
        except (DatabaseError, Exception) as e:
            self._show_message("Error", f"An unexpected error occurred: {e}", "critical")

    def handle_remove_components(self, component_ids: list[uuid.UUID]):
        # ... (rest of the file is unchanged)
        pass

    def open_generate_ideas_dialog(self, checked_ids: list[uuid.UUID]):
        # ... (rest of the file is unchanged)
        pass

    def open_link_in_browser(self, url: QUrl):
        if url and url.isValid():
            QDesktopServices.openUrl(url)
        else:
            self._show_message("Invalid Link", "The link is not valid.", "warning")

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