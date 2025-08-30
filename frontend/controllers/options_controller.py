from PyQt5.QtCore import QObject
from frontend.ui.options_dialog import OptionsDialog
from backend.models_custom import Inventory


class OptionsController(QObject):
    def __init__(self, parent_view, inventories: list[Inventory]):
        super().__init__()
        self._parent_view = parent_view
        self._inventories = inventories

    def show_dialog(self):
        """Creates and shows the non-functional options dialog."""
        inventory_names = [inv.name for inv in self._inventories]
        dialog = OptionsDialog(inventory_names, self._parent_view)
        dialog.exec_()