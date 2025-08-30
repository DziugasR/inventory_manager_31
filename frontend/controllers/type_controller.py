from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox, QDialog

from frontend.ui.add_type_dialog import AddTypeDialog
from backend.type_manager import type_manager


class TypeController(QObject):
    def __init__(self, parent_view, app_path: str):
        super().__init__()
        self._parent_view = parent_view
        self._app_path = app_path
        self._dialog = None
        self._was_successful = False

    def open_add_type_dialog(self):
        """Opens the dialog and returns True if a type was successfully added or deleted."""
        self._was_successful = False
        custom_types = type_manager.get_all_custom_ui_names()
        self._dialog = AddTypeDialog(custom_types, self._parent_view)
        self._dialog.new_type_data_collected.connect(self.handle_add_new_type)
        self._dialog.delete_type_requested.connect(self.handle_delete_type)

        self._dialog.exec_()

        return self._was_successful

    def handle_add_new_type(self, data):
        ui_name = data.get("ui_name")
        properties = data.get("properties")

        if not ui_name or not properties:
            self._show_message("Error", "Invalid data received from dialog.", "critical")
            return

        success, message = type_manager.add_new_type(ui_name, properties)

        if success:
            self._show_message("Success", message, "info")
            self._was_successful = True
            # Refresh the list of deletable types in the dialog
            self._dialog.refresh_delete_list(type_manager.get_all_custom_ui_names())
        else:
            self._show_message("Error Adding Type", f"Failed to add new type:\n{message}", "critical")

    def handle_delete_type(self, ui_name: str):
        if not ui_name:
            return

        reply = QMessageBox.question(
            self._parent_view,
            'Confirm Deletion',
            f"Are you sure you want to delete the type '{ui_name}'?\n\n"
            f"<b>WARNING:</b> This will permanently delete <u>all components</u> of this type "
            f"from <strong>ALL</strong> inventories. This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        success, message = type_manager.delete_custom_type(ui_name, self._app_path)

        if success:
            self._show_message("Success", message, "info")
            self._was_successful = True
            # Refresh the list of deletable types in the dialog
            if self._dialog:
                self._dialog.refresh_delete_list(type_manager.get_all_custom_ui_names())
        else:
            self._show_message("Error Deleting Type", f"Failed to delete type:\n{message}", "critical")

    def _show_message(self, title, text, level="info"):
        msg_box = QMessageBox(self._parent_view)
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