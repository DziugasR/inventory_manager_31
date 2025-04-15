import uuid
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QObject

from frontend.ui.main_window import InventoryUI
from backend.import_export_logic import export_to_excel, import_from_excel
from backend.exceptions import DatabaseError, InvalidInputError, ComponentError

class ImportExportController(QObject):
    def __init__(self, view: InventoryUI, main_controller):
        super().__init__()
        self._view = view
        self._main_controller = main_controller

    def handle_export_request(self):
        default_filename = "inventory_export.xlsx"
        excel_filter = "Excel Files (*.xlsx)"

        filename, selected_filter = QFileDialog.getSaveFileName(
            self._view,
            "Export Inventory to Excel",
            default_filename,
            excel_filter
        )

        if filename:
            if not filename.lower().endswith('.xlsx'):
                filename += '.xlsx'
            try:
                success = export_to_excel(filename)
                if success:
                    # Use main_controller's message function for consistency
                    self._main_controller._show_message(
                        "Export Successful",
                        f"Inventory successfully exported to:\n{filename}",
                        level="info"
                    )
                else:
                    self._main_controller._show_message(
                        "Export Failed",
                        "An unknown error occurred during export.",
                        level="warning"
                    )
            except (DatabaseError, IOError, ComponentError, Exception) as e:
                 error_type = type(e).__name__
                 self._main_controller._show_message(
                     "Export Error",
                     f"Failed to export inventory ({error_type}):\n{e}",
                     level="critical"
                 )

    def handle_import_request(self):
        """Handles the request to import inventory data from an Excel file."""
        confirm = QMessageBox.question(
            self._view,
            "Confirm Import",
            "Importing data from Excel will OVERWRITE your current inventory!\n"
            "Are you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            excel_filter = "Excel Files (*.xlsx *.xls)"
            filename, selected_filter = QFileDialog.getOpenFileName(
                self._view,
                "Import Inventory from Excel",
                "",
                excel_filter
            )

            if filename:
                try:
                    success = import_from_excel(filename)
                    if success:
                        self._main_controller._show_message(
                            "Import Successful",
                            f"Inventory successfully imported from:\n{filename}",
                            level="info"
                        )
                        self._main_controller.load_inventory_data()
                    else:
                         self._main_controller._show_message(
                             "Import Failed",
                             "An unknown error occurred during import.",
                             level="warning"
                         )
                except FileNotFoundError:
                     self._main_controller._show_message(
                         "Import Error",
                         f"File not found:\n{filename}",
                         level="critical"
                     )
                except (DatabaseError, InvalidInputError, ValueError, ComponentError, Exception) as e:
                     error_type = type(e).__name__
                     self._main_controller._show_message(
                         "Import Error",
                         f"Failed to import inventory ({error_type}):\n{e}",
                         level="critical"
                     )