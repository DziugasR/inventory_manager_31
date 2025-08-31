import uuid
import os
import re
import sys
import shutil
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QFileDialog, QDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QObject, QUrl
from frontend.ui.main_window import InventoryUI
from frontend.ui.add_component_dialog import AddComponentDialog
from frontend.ui.component_details_dialog import ComponentDetailsDialog
from backend.type_manager import type_manager
from frontend.controllers.generate_ideas_controller import GenerateIdeasController
from frontend.controllers.import_export_controller import ImportExportController
from frontend.controllers.type_controller import TypeController
from frontend.controllers.options_controller import OptionsController
from backend import database, inventory_manager, settings_manager, inventory
from backend.models_custom import Inventory
from backend.inventory import get_all_components, add_component, remove_component_quantity, get_component_by_id
from backend.exceptions import *
from backend.test_data_generator import generate_random_components
from frontend.ui.transfer_dialog import TransferDialog


class MainController(QObject):
    def __init__(self, view: InventoryUI, openai_model: str, app_path: str, api_key: str):
        super().__init__()
        self._view = view
        self._openai_model = settings_manager.get_setting('ai_model', openai_model or 'gpt-4o-mini')
        self._api_key = settings_manager.get_setting('api_key', api_key)
        self._app_path = app_path
        self._current_search_term = ""
        self._current_type_filter = "All Types"
        self._import_export_controller = ImportExportController(self._view, self)
        self._idea_controller = None
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
        self._view.component_data_updated.connect(self.handle_inline_update)
        self._view.details_requested.connect(self.open_details_dialog)
        self._view.duplicate_requested.connect(self.handle_duplicate_component)
        self._view.type_filter_changed.connect(self.handle_type_filter_change)

        mbar = self._view.menu_bar_handler
        mbar.new_inventory_action.triggered.connect(self.handle_new_inventory)
        mbar.delete_inventory_action.triggered.connect(self.handle_delete_inventory)
        mbar.manage_types_action.triggered.connect(self.handle_manage_types)
        mbar.options_action.triggered.connect(self.handle_options)
        mbar.toggle_select_action.triggered.connect(self.handle_toggle_select)
        mbar.add_random_action.triggered.connect(self.handle_add_random_components)
        mbar.transfer_components_action.triggered.connect(self.handle_open_transfer_dialog)

        label = self._view.menu_bar_handler.table_name_label
        label.wheel_up.connect(self.handle_inventory_scroll_up)
        label.wheel_down.connect(self.handle_inventory_scroll_down)

    def _load_initial_data(self):
        try:
            self._inventories = inventory_manager.get_all_inventories()
            if not self._inventories: raise DatabaseError("No inventories found.")
            startup_id = settings_manager.get_setting('startup_inventory_id', 'last_used')
            inventory_to_load = None
            if startup_id == 'last_used':
                if last_id := settings_manager.get_setting('last_inventory_id'):
                    inventory_to_load = next((inv for inv in self._inventories if inv.id == last_id), None)
            else:
                inventory_to_load = next((inv for inv in self._inventories if inv.id == startup_id), None)
            self.switch_inventory(inventory_to_load or self._inventories[0])
            self._view.populate_type_filter(type_manager.get_all_ui_names())
        except (DatabaseError, Exception) as e:
            self._show_message("Fatal Startup Error", f"Could not load initial data: {e}", "critical")
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
            action.triggered.connect(lambda checked=False, i=inv: self.switch_inventory(i))
            if self._active_inventory and self._active_inventory.id == inv.id:
                font = action.font()
                font.setBold(True)
                action.setFont(font)

    def _update_window_title(self):
        name = self._active_inventory.name if self._active_inventory else "No Inventory"
        self._view.menu_bar_handler.set_inventory_name(name)

    def switch_inventory(self, inventory_obj: Inventory):
        if self._active_inventory and self._active_inventory.id == inventory_obj.id: return
        try:
            db_path = inventory_obj.db_path if os.path.isabs(inventory_obj.db_path) else os.path.join(self._app_path,
                                                                                                      inventory_obj.db_path)
            database.switch_inventory_db(f"sqlite:///{db_path}")
            self._active_inventory = inventory_obj
            settings_manager.set_setting('last_inventory_id', inventory_obj.id)
            self.load_inventory_data()
            self._update_window_title()
            self._update_inventory_menu()
        except Exception as e:
            self._show_message("Switch Error", f"Failed to switch to inventory '{inventory_obj.name}':\n{e}",
                               "critical")

    def handle_new_inventory(self):
        name, ok = QInputDialog.getText(self._view, "New Inventory", "Enter a name:")
        if ok and (name := name.strip()):
            sanitized = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_').lower()
            db_filename = f"inventory_{sanitized}.db"
            try:
                new_inv = inventory_manager.add_new_inventory(name, db_filename)
                self._inventories.append(new_inv)
                self._inventories.sort(key=lambda x: x.name)
                self.switch_inventory(new_inv)
                self._show_message("Success", f"Created and switched to inventory '{name}'.", "info")
            except (DuplicateComponentError, DatabaseError, Exception) as e:
                self._show_message("Creation Error", str(e), "critical")

    def handle_delete_inventory(self):
        if len(self._inventories) <= 1:
            self._show_message("Action Not Allowed", "Cannot delete the last inventory.", "warning")
            return
        names = [inv.name for inv in self._inventories]
        item, ok = QInputDialog.getItem(self._view, "Delete Inventory", "Select inventory to delete:", names, 0, False)
        if ok and item:
            to_delete = next((inv for inv in self._inventories if inv.name == item), None)
            if not to_delete: return
            reply = QMessageBox.question(self._view, 'Confirm Deletion', f"Permanently delete '{to_delete.name}'?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    is_active = self._active_inventory and self._active_inventory.id == to_delete.id
                    inventory_manager.delete_inventory(to_delete.id, self._app_path)
                    self._inventories = [inv for inv in self._inventories if inv.id != to_delete.id]
                    self._show_message("Success", f"Inventory '{to_delete.name}' deleted.", "info")
                    if is_active:
                        self.switch_inventory(self._inventories[0])
                    else:
                        self._update_inventory_menu()
                except (ComponentNotFoundError, DatabaseError, Exception) as e:
                    self._show_message("Deletion Error", str(e), "critical")

    def handle_search_query(self, query: str):
        self._current_search_term = query.strip().lower()
        self.load_inventory_data()

    def handle_type_filter_change(self, type_name: str):
        self._current_type_filter = type_name
        self.load_inventory_data()

    def load_inventory_data(self):
        try:
            components = get_all_components()
            if self._current_search_term:
                components = [c for c in components if
                              self._current_search_term in str(c.part_number or "").lower() or
                              self._current_search_term in str(c.value or "").lower() or
                              self._current_search_term in str(c.location or "").lower()]
            if self._current_type_filter != "All Types":
                if backend_id := type_manager.get_backend_id(self._current_type_filter):
                    components = [c for c in components if c.component_type == backend_id]
            self._view.display_data(components)
        except (DatabaseError, Exception) as e:
            self._show_message("Error", f"Could not load data: {e}", "critical")

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
            self._view.populate_type_filter(type_manager.get_all_ui_names())

    def handle_manage_types(self):
        type_controller = TypeController(self._view, self._app_path)
        if type_controller.open_add_type_dialog():
            self.load_inventory_data()
            self._view.populate_type_filter(type_manager.get_all_ui_names())

    def handle_options(self):
        current_settings = {
            'api_key': self._api_key,
            'ai_model': self._openai_model,
            'startup_inventory_id': settings_manager.get_setting('startup_inventory_id', 'last_used'),
            'theme': settings_manager.get_setting('theme', 'Fusion')
        }
        options_controller = OptionsController(self._view, self._inventories, current_settings)
        if options_controller.show_dialog():
            self._openai_model = settings_manager.get_setting('ai_model', self._openai_model)
            self._api_key = settings_manager.get_setting('api_key', self._api_key)
            if settings_manager.get_setting('theme') != current_settings['theme']:
                self._show_message("Settings Saved", "Please restart for the new theme to take effect.", "info")
            else:
                self._show_message("Settings Saved", "Your settings have been saved.", "info")

    def _add_new_component(self, component_data: dict):
        try:
            source_image_path = component_data.pop('source_image_path', None)
            new_component = add_component(**component_data)
            if source_image_path and new_component:
                self._handle_image_update(new_component.id, source_image_path)
            self._show_message("Success", f"Component '{component_data['part_number']}' added.", "info")
            self.load_inventory_data()
        except (DuplicateComponentError, InvalidInputError) as e:
            self._show_message("Input Error", str(e), "warning")
        except Exception as e:
            self._show_message("Error", f"An unexpected error occurred: {e}", "critical")

    def _handle_image_update(self, component_id: uuid.UUID, source_path: str) -> bool:
        if not source_path or not os.path.exists(source_path): return False
        try:
            dest_dir = os.path.join(self._app_path, "assets", "component_images")
            os.makedirs(dest_dir, exist_ok=True)
            _, extension = os.path.splitext(source_path)
            new_filename = f"{component_id}{extension or '.png'}"
            dest_path = os.path.join(dest_dir, new_filename)
            shutil.copy(source_path, dest_path)
            relative_path = os.path.join("assets", "component_images", new_filename)
            inventory.update_component(component_id, {"image_path": relative_path})
            return True
        except Exception as e:
            self._show_message("Image Error", f"Could not save image: {e}", "critical")
            return False

    def handle_duplicate_component(self, component_id: uuid.UUID):
        try:
            if not (component_to_duplicate := get_component_by_id(component_id)):
                raise ComponentNotFoundError("Component not found.")
            dialog = AddComponentDialog(self._view)
            dialog.populate_from_component(component_to_duplicate, self._app_path)
            dialog.component_data_collected.connect(self._add_new_component)
            dialog.manage_types_requested.connect(self.open_manage_types_dialog)
            dialog.exec_()
        except (DatabaseError, ComponentNotFoundError) as e:
            self._show_message("Error", f"Could not duplicate component: {e}", "critical")

    def handle_inline_update(self, component_id: uuid.UUID, data: dict):
        try:
            inventory.update_component(component_id, data)
        except (DatabaseError, ComponentNotFoundError) as e:
            self._show_message("Update Error", f"Could not save changes: {e}", "critical")
            self.load_inventory_data()

    def open_details_dialog(self, component_id: uuid.UUID):
        try:
            if not (component := get_component_by_id(component_id)):
                raise ComponentNotFoundError("Component may have been deleted.")
            ui_name = type_manager.get_ui_name(component.component_type)
            properties = type_manager.get_properties(ui_name)
            dialog = ComponentDetailsDialog(component, properties, self._app_path, self._view)

            def on_image_change_requested(comp_id_str):
                filepath, _ = QFileDialog.getOpenFileName(dialog, "Select New Image", "", "Image Files (*.png *.jpg)")
                if filepath and self._handle_image_update(uuid.UUID(comp_id_str), filepath):
                    if updated_comp := get_component_by_id(uuid.UUID(comp_id_str)):
                        dialog.component = updated_comp
                        dialog._populate_data()

            dialog.image_change_requested.connect(on_image_change_requested)
            if dialog.exec_() == QDialog.Accepted:
                inventory.update_component(component.id, dialog.get_data())
                self.load_inventory_data()
        except (DatabaseError, ComponentNotFoundError) as e:
            self._show_message("Error", f"Could not open details: {e}", "critical")

    def handle_remove_components(self, component_ids: list[uuid.UUID]):
        success_count, failure_count, messages = 0, 0, []
        if not component_ids:
            self._show_message("Selection Error", "No components selected.", "warning")
            return
        confirm = QMessageBox.question(self._view, "Confirm Removal",
                                       f"You are about to interact with {len(component_ids)} component(s). Proceed?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if confirm == QMessageBox.No: return
        for component_id in component_ids:
            try:
                component = get_component_by_id(component_id)
                if not component:
                    messages.append(f"- ID {component_id}: Not found (already removed?).")
                    failure_count += 1;
                    continue
                if component.quantity <= 0:
                    messages.append(f"- {component.part_number}: Already has quantity 0.")
                    failure_count += 1;
                    continue
                quantity_to_remove, ok = QInputDialog.getInt(self._view, "Remove Quantity",
                                                             f"Component: {component.part_number}\nAvailable: {component.quantity}\nEnter quantity to remove:",
                                                             1, 1, component.quantity)
                if not ok:
                    messages.append(f"- {component.part_number}: Removal cancelled.")
                    failure_count += 1;
                    continue
                remove_component_quantity(component_id, quantity_to_remove)
                messages.append(
                    f"- {component.part_number}: Removed {quantity_to_remove} (Remaining: {component.quantity - quantity_to_remove}).")
                success_count += 1
            except (InvalidQuantityError, ComponentNotFoundError, StockError, DatabaseError) as e:
                messages.append(f"- Error with ID {component_id}: {e}");
                failure_count += 1
            except Exception as e:
                messages.append(f"- Unexpected error with ID {component_id}: {e}");
                failure_count += 1
        summary = f"Processed {len(component_ids)} component(s):\nSucceeded: {success_count}\nFailed/Cancelled: {failure_count}\n\nDetails:\n" + "\n".join(
            messages)
        self._show_message("Removal Summary", summary, "info" if failure_count == 0 else "warning")
        if success_count > 0: self.load_inventory_data()

    def open_generate_ideas_dialog(self, checked_ids: list[uuid.UUID]):
        if not self._api_key or "YOUR_API_KEY" in self._api_key:
            self._show_message("API Key Required", "Set your OpenAI API key in 'Tools > Options'.", "warning")
            return
        if not checked_ids:
            self._show_message("Generate Ideas", "No components selected.", "warning")
            return
        try:
            selected_components = [get_component_by_id(cid) for cid in checked_ids if get_component_by_id(cid)]
            if not selected_components:
                self._show_message("Generate Ideas", "Could not retrieve details for selected components.", "warning")
                return
            self._idea_controller = GenerateIdeasController(selected_components, self._openai_model, self._api_key,
                                                            self._view)
            self._idea_controller.show()
        except (DatabaseError, Exception) as e:
            self._show_message("Error", f"Could not fetch component details: {e}", "critical")

    def handle_open_transfer_dialog(self):
        selected_ids = self._view.get_checked_ids()
        if not selected_ids:
            self._show_message("Selection Error", "Please select one or more components to transfer.", "warning")
            return
        destination_inventories = [inv for inv in self._inventories if inv.id != self._active_inventory.id]
        if not destination_inventories:
            self._show_message("Action Not Possible", "There are no other inventories to transfer to.", "warning")
            return
        try:
            selected_components = [c for c in [get_component_by_id(cid) for cid in selected_ids] if c]
            dialog = TransferDialog(selected_components, destination_inventories, self._view)
            dialog.transfer_requested.connect(self._perform_transfer)
            dialog.exec_()
        except Exception as e:
            self._show_message("Error", f"Could not prepare for transfer: {e}", "critical")

    def _perform_transfer(self, destination_inventory: Inventory, transfer_data: dict):
        if not (source_inventory := self._active_inventory): return
        original_db_url = f"sqlite:///{source_inventory.db_path if os.path.isabs(source_inventory.db_path) else os.path.join(self._app_path, source_inventory.db_path)}"
        success_count, fail_count, messages = 0, 0, []
        try:
            for component_id, quantity in transfer_data.items():
                try:
                    if not (source_component := get_component_by_id(component_id)):
                        raise ComponentNotFoundError(f"ID {component_id} not found in source.")
                    inventory.remove_component_quantity(component_id, quantity)
                    dest_db_path = destination_inventory.db_path if os.path.isabs(
                        destination_inventory.db_path) else os.path.join(self._app_path, destination_inventory.db_path)
                    database.switch_inventory_db(f"sqlite:///{dest_db_path}")
                    if existing_dest_comps := inventory.get_components_by_part_number(source_component.part_number):
                        dest_comp = existing_dest_comps[0]
                        inventory.update_component(dest_comp.id, {'quantity': dest_comp.quantity + quantity})
                    else:
                        inventory.add_component(part_number=source_component.part_number,
                                                component_type=source_component.component_type,
                                                value=source_component.value, quantity=quantity,
                                                purchase_link=source_component.purchase_link,
                                                datasheet_link=source_component.datasheet_link,
                                                location=source_component.location, notes=source_component.notes,
                                                image_path=source_component.image_path)
                    success_count += 1
                    messages.append(f"- Transferred {quantity} of {source_component.part_number}")
                except Exception as e:
                    fail_count += 1
                    part_num = getattr(source_component, 'part_number', f"ID {component_id}")
                    messages.append(f"- FAILED to transfer {part_num}: {e}")
                finally:
                    database.switch_inventory_db(original_db_url)
        finally:
            database.switch_inventory_db(original_db_url)
            self.load_inventory_data()
            summary = f"Transfer complete.\n\nSucceeded: {success_count}\nFailed: {fail_count}\n\n" + "\n".join(
                messages)
            self._show_message("Transfer Summary", summary, "info" if fail_count == 0 else "warning")

    def open_link_in_browser(self, url: QUrl):
        if url and url.isValid():
            QDesktopServices.openUrl(url)
        else:
            self._show_message("Invalid Link", "The link is not valid.", "warning")

    def _show_message(self, title: str, text: str, level: str = "info"):
        msg_box = QMessageBox(self._view)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        icon = {"info": QMessageBox.Information, "warning": QMessageBox.Warning, "critical": QMessageBox.Critical}.get(
            level, QMessageBox.NoIcon)
        msg_box.setIcon(icon)
        msg_box.exec_()

    def handle_add_random_components(self):
        num, ok = QInputDialog.getInt(self._view, "Add Random Components", "How many components?", 20, 1, 1000)
        if ok and num > 0:
            try:
                self._show_message("Processing...", f"Generating {num} random components...", "info")
                for component_data in generate_random_components(num):
                    inventory.add_component(**component_data)
                self.load_inventory_data()
                self._show_message("Success", f"Added {num} random components.", "info")
            except Exception as e:
                self._show_message("Error", f"An error occurred: {e}", "critical")

    def _switch_to_adjacent_inventory(self, direction: int):
        """Helper function to switch to the next/previous inventory."""
        if not self._inventories or not self._active_inventory:
            return

        try:
            current_index = self._inventories.index(self._active_inventory)
        except ValueError:
            return  # Should not happen

        new_index = (current_index + direction) % len(self._inventories)
        next_inventory = self._inventories[new_index]
        self.switch_inventory(next_inventory)

    def handle_inventory_scroll_up(self):
        # Scrolling up should go to the previous inventory in the list
        self._switch_to_adjacent_inventory(-1)

    def handle_inventory_scroll_down(self):
        # Scrolling down should go to the next inventory in the list
        self._switch_to_adjacent_inventory(1)


    def show_view(self):
        self._view.show()