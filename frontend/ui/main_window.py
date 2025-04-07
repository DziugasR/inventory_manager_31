from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QAction, QToolButton, QMenu, QCheckBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QUrl, Qt, pyqtSignal

from frontend.ui.add_component_dialog import AddComponentDialog
from frontend.ui.toolbar import setup_toolbar

class InventoryUI(QMainWindow):
    """ Main application window UI definition. """
    add_component_requested = pyqtSignal()
    remove_components_requested = pyqtSignal(list)
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

    PART_NUMBER_COL = 0
    NAME_COL = 1
    TYPE_COL = 2
    VALUE_COL = 3
    QUANTITY_COL = 4
    PURCHASE_LINK_COL = 5
    DATASHEET_COL = 6
    CHECKBOX_COL = 7

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Electronics Inventory Manager")
        self.setGeometry(100, 100, 1060, 600)
        self._checkboxes = []
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

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.remove_button)

        self.layout.addLayout(button_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Part Number", "Name", "Type", "Value", "Quantity", "Purchase Link", "Datasheet", "Select"
        ])
        self.table.setColumnWidth(self.VALUE_COL, 300)
        self.table.setColumnWidth(self.CHECKBOX_COL, 50)
        self.layout.addWidget(self.table)

    def _connect_signals(self):
        """ Connect internal UI signals. """
        self.add_button.clicked.connect(self.add_component_requested)
        self.remove_button.clicked.connect(self._on_remove_clicked)

        # Handle link clicks within the table
        self.table.cellClicked.connect(self._handle_cell_click)

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
        """ Internal handler to get checked part numbers before emitting signal. """
        part_numbers_to_remove = self.get_checked_part_numbers()
        if part_numbers_to_remove:
            self.remove_components_requested.emit(part_numbers_to_remove)

    def _handle_cell_click(self, row, column):
        """ Handle clicks on link cells. """
        # Check if the click is on the link columns (indices unchanged)
        if column in [self.PURCHASE_LINK_COL, self.DATASHEET_COL]:
            item = self.table.item(row, column)
            if item:
                link_data = item.data(Qt.UserRole)
                if isinstance(link_data, QUrl) and link_data.isValid():
                    self.link_clicked.emit(link_data)

    def _handle_cell_click(self, row, column):
        if column in [self.PURCHASE_LINK_COL, self.DATASHEET_COL]:
            item = self.table.item(row, column)
            if item:
                link_data = item.data(Qt.UserRole)
                if isinstance(link_data, QUrl) and link_data.isValid():
                    self.link_clicked.emit(link_data)

    def get_checked_part_numbers(self):
        """ Returns a list of part numbers for rows where the checkbox is checked. """
        checked_part_numbers = []
        for row in range(self.table.rowCount()):
            # Get the container widget from the checkbox column
            container_widget = self.table.cellWidget(row, self.CHECKBOX_COL)

            # Check if the container widget exists
            if container_widget:
                # Find the QCheckBox within the container widget
                checkbox = container_widget.findChild(QCheckBox)

                # Check if a checkbox was found and if it's checked
                if checkbox and checkbox.isChecked():
                    # Get the item from the part number column for the same row
                    part_number_item = self.table.item(row, self.PART_NUMBER_COL)

                    # Check if the part number item exists and has text
                    if part_number_item and part_number_item.text():
                        checked_part_numbers.append(part_number_item.text())

        return checked_part_numbers

    def _update_remove_button_state_on_checkbox(self):
        """ Enable/disable remove button based on whether any checkbox is checked. """
        checked_items = self.get_checked_part_numbers()
        self.remove_button.setEnabled(len(checked_items) > 0)

    def _update_remove_button_state(self):
        """ Enable/disable remove button based on table selection. """
        self.remove_button.setEnabled(self.table.selectionModel().hasSelection())

    def get_selected_part_number(self):
        """ Returns the part number of the currently *highlighted* row, or None. """
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None
        # Part number is always in the first column (index 0) of the selected row
        selected_row = self.table.currentRow()
        if selected_row < 0: # No row selected
             return None
        part_number_item = self.table.item(selected_row, self.PART_NUMBER_COL)
        return part_number_item.text() if part_number_item else None

    def get_selected_row_data(self):
        """ Returns data for the currently *highlighted* row as a dictionary, or None. """
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None

    def get_selected_part_number(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None
        # Part number is always in the first column (index 0) of the selected row
        selected_row = self.table.currentRow()
        if selected_row < 0: # No row selected
             return None
        part_number_item = self.table.item(selected_row, self.PART_NUMBER_COL)
        return part_number_item.text() if part_number_item else None

    def get_selected_row_data(self):
        """ Returns data for the currently *highlighted* row as a dictionary, or None. """
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None

        # Headers now include "Select", but we might not want it in the output dict
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount() -1 )] # Exclude Select column header
        data = {}
        for col, header in enumerate(headers):
            item = self.table.item(selected_row, col)
            data[header] = item.text() if item else ""
            # Store link data if available (indices unchanged)
            if col in [self.PURCHASE_LINK_COL, self.DATASHEET_COL] and item:
                 link_data = item.data(Qt.UserRole)
                 if isinstance(link_data, QUrl):
                     data[header + "_url"] = link_data.toString() # Store URL string
        return data

    # --- Slots for Controller Interaction ---

    def display_data(self, components):
        """ Populates the table with component data received from the controller. """
        self.table.setRowCount(0) # Clear existing rows
        self._checkboxes.clear() # Clear tracked checkboxes

        if not components: # Handle empty data case
             self.table.setRowCount(0)
             self._update_remove_button_state_on_checkbox() # Ensure button is disabled
             return

        self.table.setRowCount(len(components))

        backend_to_ui_name_mapping = {v: k for k, v in AddComponentDialog().ui_to_backend_name_mapping.items()}

        for row, component in enumerate(components):
            # Map backend type name back to UI display name
            ui_component_type = backend_to_ui_name_mapping.get(component.component_type, component.component_type)

            # Populate original data columns (indices unchanged)
            self.table.setItem(row, self.PART_NUMBER_COL, QTableWidgetItem(component.part_number or ""))
            self.table.setItem(row, self.NAME_COL, QTableWidgetItem(component.name or ""))
            self.table.setItem(row, self.TYPE_COL, QTableWidgetItem(ui_component_type)) # Use UI name
            self.table.setItem(row, self.VALUE_COL, QTableWidgetItem(component.value))
            self.table.setItem(row, self.QUANTITY_COL, QTableWidgetItem(str(component.quantity)))

            # Clickable Purchase Link
            if component.purchase_link:
                purchase_item = QTableWidgetItem("Link")
                purchase_item.setForeground(QColor("blue"))
                purchase_item.setTextAlignment(Qt.AlignCenter)
                url = QUrl(component.purchase_link)
                if not url.scheme(): url.setScheme("http")
                purchase_item.setData(Qt.UserRole, url)
                self.table.setItem(row, self.PURCHASE_LINK_COL, purchase_item)
            else:
                self.table.setItem(row, self.PURCHASE_LINK_COL, QTableWidgetItem(""))

            # Clickable Datasheet Link
            if component.datasheet_link:
                datasheet_item = QTableWidgetItem("Link")
                datasheet_item.setForeground(QColor("blue"))
                datasheet_item.setTextAlignment(Qt.AlignCenter)
                url = QUrl(component.datasheet_link)
                if not url.scheme(): url.setScheme("http")
                datasheet_item.setData(Qt.UserRole, url)
                self.table.setItem(row, self.DATASHEET_COL, datasheet_item)
            else:
                 self.table.setItem(row, self.DATASHEET_COL, QTableWidgetItem(""))

            # --- Add Checkbox ---
            checkbox = QCheckBox()
            # Center the checkbox in the cell
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            cell_widget.setLayout(layout)

            # Connect the checkbox's state change signal to update the remove button
            checkbox.stateChanged.connect(self._update_remove_button_state_on_checkbox)
            self._checkboxes.append(checkbox) # Keep track if needed, maybe not necessary here

            # Set the widget in the new checkbox column
            self.table.setCellWidget(row, self.CHECKBOX_COL, cell_widget)
            # Ensure the checkbox cell itself isn't selectable/editable by normal means
            item = QTableWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.table.setItem(row, self.CHECKBOX_COL, item)


        # Reset selection state and update button based on checkboxes (which are all off initially)
        self.table.clearSelection()
        self._update_remove_button_state_on_checkbox()