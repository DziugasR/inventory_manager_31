from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog
from frontend.ui.options_dialog import OptionsDialog
from backend.models_custom import Inventory
from backend import settings_manager


class OptionsController(QObject):
    def __init__(self, parent_view, inventories: list[Inventory], current_settings: dict):
        super().__init__()
        self._parent_view = parent_view
        self._inventories = inventories
        self._current_settings = current_settings
        self._was_changed = False

    def show_dialog(self) -> bool:
        """Creates, shows, and handles the logic for the options dialog."""
        dialog = OptionsDialog(self._inventories, self._current_settings, self._parent_view)
        if dialog.exec_() == QDialog.Accepted:
            new_settings = dialog.get_data()
            for key, value in new_settings.items():
                if value is not None:
                    settings_manager.set_setting(key, str(value))
            self._was_changed = True
        return self._was_changed