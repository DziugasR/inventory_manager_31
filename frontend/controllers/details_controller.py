from PyQt5.QtWidgets import QDialog
from frontend.ui.component_details_dialog import ComponentDetailsDialog
from backend import inventory, exceptions

class DetailsController:
    def __init__(self, component, properties, parent_view):
        self.component = component
        self.properties = properties
        self._parent_view = parent_view
        self._dialog = ComponentDetailsDialog(self.component, self.properties, self._parent_view)
        self._was_successful = False

    def show_dialog(self) -> bool:
        """Shows the dialog and handles the update logic."""
        if self._dialog.exec_() == QDialog.Accepted:
            try:
                new_data = self._dialog.get_data()
                inventory.update_component(self.component.id, new_data)
                self._was_successful = True
            except exceptions.DatabaseError as e:
                # This should be replaced with a proper message box if possible
                print(f"ERROR: Could not update component: {e}")
                self._was_successful = False
        return self._was_successful