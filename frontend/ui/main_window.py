from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QAction, QToolButton, QMenu
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QUrl, Qt, pyqtSignal

from frontend.ui.add_component_dialog import AddComponentDialog

from frontend.ui.toolbar import setup_toolbar

class InventoryUI(QMainWindow):
    """ Main application window UI definition. """
    add_component_requested = pyqtSignal()
    remove_component_requested = pyqtSignal(str)
    export_requested = pyqtSignal()
    import_requested = pyqtSignal()
    load_data_requested = pyqtSignal()
    link_clicked = pyqtSignal(QUrl)
    # File Menu
    new_inventory_triggered = pyqtSignal()
    open_inventory_triggered = pyqtSignal()
    save_inventory_triggered = pyqtSignal()
    save_inventory_as_triggered = pyqtSignal()
    exit_triggered = pyqtSignal()
    # Edit Menu
    copy_row_triggered = pyqtSignal()
    paste_row_triggered = pyqtSignal()
    find_triggered = pyqtSignal()
    # Tools Menu
    export_xls_triggered = pyqtSignal()
    import_xls_triggered = pyqtSignal()
    chatgpt_triggered = pyqtSignal()
    # View Menu
    table_size_triggered = pyqtSignal()
    dark_mode_triggered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Electronics Inventory Manager")
        self.setGeometry(100, 100, 960, 600)
        self._init_ui()
        self._connect_signals()
        self._connect_toolbar_signals()

    def _init_ui(self):
        """ Initialize UI elements. """
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        setup_toolbar(self)

        self.layout = QVBoxLayout(self.central_widget)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Component")
        button_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove Component")
        self.remove_button.setEnabled(False) # Initially disabled
        button_layout.addWidget(self.remove_button)

        self.layout.addLayout(button_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Part Number", "Name", "Type", "Value", "Quantity", "Purchase Link", "Datasheet"
        ])
        self.table.setSortingEnabled(True)
        self.table.setColumnWidth(3, 300) # Value column wider
        self.layout.addWidget(self.table)

    def _connect_signals(self):
        """ Connect internal UI signals. """
        self.add_button.clicked.connect(self.add_component_requested)
        self.remove_button.clicked.connect(self._on_remove_clicked)

        # Handle link clicks within the table
        self.table.cellClicked.connect(self._handle_cell_click)
        # Update remove button state based on selection
        self.table.selectionModel().selectionChanged.connect(self._update_remove_button_state)

    def _connect_toolbar_signals(self):
        """ Connect signals from toolbar actions to the UI's signals. """
        # Check if attributes exist before connecting (good practice)
        if hasattr(self, 'new_action'):
            self.new_action.triggered.connect(self.new_inventory_triggered)
        if hasattr(self, 'open_action'):
            self.open_action.triggered.connect(self.open_inventory_triggered)
        if hasattr(self, 'save_action'):
            self.save_action.triggered.connect(self.save_inventory_triggered)
        if hasattr(self, 'save_as_action'):
            self.save_as_action.triggered.connect(self.save_inventory_as_triggered)
        if hasattr(self, 'exit_action'):
            self.exit_action.triggered.connect(self.exit_triggered)
        if hasattr(self, 'copy_action'):
            self.copy_action.triggered.connect(self.copy_row_triggered)
        if hasattr(self, 'paste_action'):
            self.paste_action.triggered.connect(self.paste_row_triggered)
        if hasattr(self, 'find_action'):
            self.find_action.triggered.connect(self.find_triggered)
        if hasattr(self, 'help_action'):
            self.help_action.triggered.connect(self.help_triggered)

    def _on_remove_clicked(self):
        """ Internal handler to get part number before emitting signal. """
        part_number = self.get_selected_part_number()
        if part_number:
            self.remove_component_requested.emit(part_number)

    def _handle_cell_click(self, row, column):
        """ Handle clicks on link cells. """
        if column in [5, 6]: # Purchase Link or Datasheet Link column
            item = self.table.item(row, column)
            if item:
                link_data = item.data(Qt.UserRole)
                if isinstance(link_data, QUrl) and link_data.isValid():
                    self.link_clicked.emit(link_data) # Emit signal with the QUrl

    def _update_remove_button_state(self):
        """ Enable/disable remove button based on table selection. """
        self.remove_button.setEnabled(self.table.selectionModel().hasSelection())

    def get_selected_part_number(self):
        """ Returns the part number of the currently selected row, or None. """
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None
        # Part number is always in the first column (index 0) of the selected row
        selected_row = self.table.currentRow()
        part_number_item = self.table.item(selected_row, 0)
        return part_number_item.text() if part_number_item else None

    def get_selected_row_data(self):
        """ Returns data for the selected row as a dictionary, or None. """
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None

        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
        data = {}
        for col, header in enumerate(headers):
            item = self.table.item(selected_row, col)
            data[header] = item.text() if item else ""
            # Store link data if available
            if col in [5, 6] and item:
                 link_data = item.data(Qt.UserRole)
                 if isinstance(link_data, QUrl):
                     data[header + "_url"] = link_data.toString() # Store URL string
        return data

    # --- Slots for Controller Interaction ---

    def display_data(self, components):
        """ Populates the table with component data received from the controller. """
        self.table.setRowCount(0) # Clear existing rows
        self.table.setRowCount(len(components))

        backend_to_ui_name_mapping = {v: k for k, v in AddComponentDialog().ui_to_backend_name_mapping.items()}

        for row, component in enumerate(components):
            # Map backend type name back to UI display name
            ui_component_type = backend_to_ui_name_mapping.get(component.component_type, component.component_type)

            self.table.setItem(row, 0, QTableWidgetItem(component.part_number or ""))
            self.table.setItem(row, 1, QTableWidgetItem(component.name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(ui_component_type)) # Use UI name
            self.table.setItem(row, 3, QTableWidgetItem(component.value))
            self.table.setItem(row, 4, QTableWidgetItem(str(component.quantity)))

            # Clickable Purchase Link
            if component.purchase_link:
                purchase_item = QTableWidgetItem("Link")
                purchase_item.setForeground(QColor("blue"))
                purchase_item.setTextAlignment(Qt.AlignCenter)
                # Ensure URL has a scheme
                url = QUrl(component.purchase_link)
                if not url.scheme():
                    url.setScheme("http") # Default to http if missing
                purchase_item.setData(Qt.UserRole, url)
                self.table.setItem(row, 5, purchase_item)
            else:
                self.table.setItem(row, 5, QTableWidgetItem("")) # Empty cell if no link

            # Clickable Datasheet Link
            if component.datasheet_link:
                datasheet_item = QTableWidgetItem("Link")
                datasheet_item.setForeground(QColor("blue"))
                datasheet_item.setTextAlignment(Qt.AlignCenter)
                url = QUrl(component.datasheet_link)
                if not url.scheme():
                    url.setScheme("http")
                datasheet_item.setData(Qt.UserRole, url)
                self.table.setItem(row, 6, datasheet_item)
            else:
                 self.table.setItem(row, 6, QTableWidgetItem("")) # Empty cell if no link

        # Reset selection state which might disable the button initially
        self.table.clearSelection()
        self._update_remove_button_state()

    def set_remove_button_enabled(self, enabled):
        """ Sets the enabled state of the remove button. """
        self.remove_button.setEnabled(enabled)