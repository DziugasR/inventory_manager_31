from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox, QDialog

from frontend.ui.add_type_dialog import AddTypeDialog
from backend.type_manager import type_manager


class TypeController(QObject):
    def __init__(self, parent_view):
        super().__init__()
        self._parent_view = parent_view
        self._was_successful = False

    def open_add_type_dialog(self):
        """Opens the dialog and returns True if a type was successfully added, otherwise False."""
        self._was_successful = False
        dialog = AddTypeDialog(self._parent_view)
        dialog.new_type_data_collected.connect(self.handle_add_new_type)

        dialog.exec_()

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
        else:
            self._show_message("Error Adding Type", f"Failed to add new type:\n{message}", "critical")
            self._was_successful = False

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