from PyQt5.QtWidgets import QMenuBar, QAction, QMessageBox, QLabel, QMenu, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics


# This custom label adds the mouse wheel scrolling capability
class ScrollableElidedLabel(QLabel):
    wheel_up = pyqtSignal()
    wheel_down = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._full_text = ""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(250)
        self.setMaximumWidth(450)
        self.setToolTip("Scroll to switch inventories")

    def setText(self, text: str):
        self._full_text = text
        super().setToolTip(f"{text}\n(Scroll mouse wheel to switch)")
        self._update_elided_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided_text()

    def _update_elided_text(self):
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self._full_text, Qt.ElideRight, self.width())
        super().setText(elided)

    def wheelEvent(self, event):
        """Called when the mouse wheel is used over the widget."""
        if event.angleDelta().y() > 0:
            self.wheel_up.emit()  # Scrolled Up
        elif event.angleDelta().y() < 0:
            self.wheel_down.emit()  # Scrolled Down
        event.accept()


class AppMenuBar:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.table_name_label = None
        self.open_inventory_menu = None
        self.new_inventory_action = None
        self.delete_inventory_action = None
        self.manage_types_action = None
        self.options_action = None
        self.toggle_select_action = None
        self.add_random_action = None
        self.transfer_components_action = None
        self._create_menu_bar()

    def set_inventory_name(self, name: str):
        if self.table_name_label:
            self.table_name_label.setText(name)

    def update_toggle_action_text(self, has_selection: bool):
        if self.toggle_select_action:
            if has_selection:
                self.toggle_select_action.setText("Deselect All Items")
            else:
                self.toggle_select_action.setText("Select All Items")

    def _create_menu_bar(self):
        menu_bar = self.parent.menuBar()

        # --- File Menu ---
        file_menu = menu_bar.addMenu("&File")
        self.new_inventory_action = QAction("New Inventory...", self.parent)
        self.open_inventory_menu = QMenu("Open Inventory", self.parent)
        self.delete_inventory_action = QAction("Delete Inventory...", self.parent)
        exit_action = QAction("Exit", self.parent)
        exit_action.triggered.connect(self.parent.close)

        file_menu.addAction(self.new_inventory_action)
        file_menu.addMenu(self.open_inventory_menu)
        file_menu.addAction(self.delete_inventory_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # --- Tools Menu ---
        tools_menu = menu_bar.addMenu("&Tools")
        self.options_action = QAction("Options...", self.parent)
        self.manage_types_action = QAction("Manage Component Types...", self.parent)
        self.toggle_select_action = QAction("Select All Items", self.parent)
        self.transfer_components_action = QAction("Transfer Selected Components...", self.parent)
        self.add_random_action = QAction("Add Random Components...", self.parent)

        tools_menu.addAction(self.options_action)
        tools_menu.addAction(self.manage_types_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.toggle_select_action)
        tools_menu.addAction(self.transfer_components_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.add_random_action)

        # --- Inventory Name Label ---
        self.table_name_label = ScrollableElidedLabel(self.parent)
        self.table_name_label.setObjectName("inventoryNameLabel")
        self.table_name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table_name_label.setStyleSheet(
            "padding-right: 15px; padding-top: 3px; font-weight: bold; font-style: normal;")
        menu_bar.setCornerWidget(self.table_name_label, Qt.TopRightCorner)

        # --- Help Menu (As specified) ---
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("About", self.parent)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        help_menu.addSeparator()
        help_table_action = QAction("How to use: The Table", self.parent)
        help_table_action.triggered.connect(self._show_help_table)
        help_menu.addAction(help_table_action)
        help_add_action = QAction("How to use: Add Component", self.parent)
        help_add_action.triggered.connect(self._show_help_add)
        help_menu.addAction(help_add_action)
        help_remove_action = QAction("How to use: Remove Selected", self.parent)
        help_remove_action.triggered.connect(self._show_help_remove)
        help_menu.addAction(help_remove_action)
        help_generate_action = QAction("How to use: Generate Ideas", self.parent)
        help_generate_action.triggered.connect(self._show_help_generate)
        help_menu.addAction(help_generate_action)
        help_export_action = QAction("How to use: Export to Excel", self.parent)
        help_export_action.triggered.connect(self._show_help_export)
        help_menu.addAction(help_export_action)
        help_import_action = QAction("How to use: Import from Excel", self.parent)
        help_import_action.triggered.connect(self._show_help_import)
        help_menu.addAction(help_import_action)

    def _show_about_dialog(self):
        QMessageBox.about(
            self.parent,
            "About Electronics Inventory Manager",
            "A simple application to manage your electronics components inventory.\n\n"
            "This tool helps you keep track of your components, find them easily, and "
            "even get inspiration for new projects. Use the 'Help' menu for detailed "
            "guides on each feature."
        )

    def _show_help_message(self, title: str, message: str):
        QMessageBox.information(self.parent, title, message)

    def _show_help_table(self):
        self._show_help_message(
            "Help: Using the Table",
            "The main table displays your entire component inventory.\n\n"
            "• Search: Use the search bar above the table to instantly filter your "
            "inventory by Part Number, Type, or Value.\n\n"
            "• Sorting: Click on any column header (e.g., 'Quantity', 'Type') to "
            "sort the entire table by that column. Click again to reverse the sort order.\n\n"
            "• Links: If a component has a 'Purchase Link' or 'Datasheet' URL, the "
            "cell will say 'Link'. Click it to open the URL in your web browser.\n\n"
            "• Selection: Use the checkbox in the 'Select' column to mark components for "
            "batch actions like 'Remove Selected' or 'Generate Ideas'."
        )

    def _show_help_add(self):
        self._show_help_message(
            "Help: Add Component",
            "Click the 'Add Component' button to open a dialog for adding a new part to your inventory.\n\n"
            "• Required Fields: 'Part Number', 'Component Type', and 'Quantity' are required.\n\n"
            "• Optional Fields: 'Value', 'Purchase Link', and 'Datasheet Link' are optional but recommended for better tracking.\n\n"
            "• Manage Types: If a component type is not in the list (e.g., 'Sensor', 'Module'), you can click 'Manage Types...' to create new categories."
        )

    def _show_help_remove(self):
        self._show_help_message(
            "Help: Remove Selected",
            "This function allows you to decrease the quantity of components you have used.\n\n"
            "1. Select: First, check the box in the 'Select' column for each component you want to modify.\n\n"
            "2. Activate: The 'Remove Selected' button will become enabled once at least one component is selected.\n\n"
            "3. Remove: Click the button. For each selected component, you will be prompted to enter the quantity you wish to remove. This subtracts from the current stock."
        )

    def _show_help_generate(self):
        self._show_help_message(
            "Help: Generate Ideas",
            "Get AI-powered project ideas based on the components you have.\n\n"
            "1. Select: Check the box in the 'Select' column for one or more components you want to use in a project.\n\n"
            "2. Activate: The 'Generate Ideas' button becomes enabled when components are selected.\n\n"
            "3. Generate: Click the button. A new window will appear where the AI will suggest project ideas that incorporate your selected parts."
        )

    def _show_help_export(self):
        self._show_help_message(
            "Help: Export to Excel",
            "You can save your entire inventory to an Excel file (.xlsx) for backup or sharing.\n\n"
            "1. Click 'Export to Excel'.\n\n"
            "2. A file dialog will appear. Choose a location and name for your file, then click 'Save'.\n\n"
            "All components currently in your inventory will be written to the spreadsheet."
        )

    def _show_help_import(self):
        self._show_help_message(
            "Help: Import from Excel",
            "You can add or update components in bulk from an Excel file (.xlsx).\n\n"
            "1. Click 'Import from Excel' and select your file.\n\n"
            "2. The Excel file MUST have a header row with the following exact column names:\n"
            "   • Part Number\n"
            "   • Type\n"
            "   • Value\n"
            "   • Quantity\n"
            "   • Purchase Link (optional)\n"
            "   • Datasheet Link (optional)\n\n"
            "If a component with the same Part Number already exists, its details will be updated. Otherwise, a new component will be added."
        )