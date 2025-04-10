#TODO eliminate empty spaces between component table and main window
#TODO Better looking Add, Remove, Generate buttons

from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QCheckBox, QStyle
)
from PyQt5.QtGui import QColor, QLinearGradient
from PyQt5.QtCore import QUrl, Qt, pyqtSignal

from frontend.ui.add_component_dialog import AddComponentDialog
from frontend.ui.toolbar import setup_toolbar

from pathlib import Path

class InventoryUI(QMainWindow):
    add_component_requested = pyqtSignal()
    remove_components_requested = pyqtSignal(list)
    generate_ideas_requested = pyqtSignal(list)

    export_requested = pyqtSignal()
    import_requested = pyqtSignal()
    load_data_requested = pyqtSignal()
    link_clicked = pyqtSignal(QUrl)
    new_inventory_triggered = pyqtSignal()
    open_inventory_triggered = pyqtSignal()
    save_inventory_triggered = pyqtSignal()
    save_inventory_as_triggered = pyqtSignal()
    exit_triggered = pyqtSignal()
    copy_row_triggered = pyqtSignal()
    paste_row_triggered = pyqtSignal()
    find_triggered = pyqtSignal()
    export_xls_triggered = pyqtSignal()
    import_xls_triggered = pyqtSignal()
    chatgpt_triggered = pyqtSignal()
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
        self.setGeometry(100, 100, 800, 600)
        self._checkboxes = []
        self._init_ui()
        self._connect_signals()
        self._connect_toolbar_signals()

    def _load_stylesheet(self, filename="styles/button_styles.qss"):
        script_dir = Path(__file__).parent
        style_path = script_dir / filename
        try:
            with open(style_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Stylesheet not found at {style_path}")
            return ""  # Return empty string if not found to avoid errors
        except Exception as e:
            print(f"Warning: Error reading stylesheet {style_path}: {e}")
            return ""

    def _init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        setup_toolbar(self)

        self.layout = QVBoxLayout(self.central_widget)

        button_stylesheet = self._load_stylesheet()

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Component")
        self.add_button.setObjectName("addButton")

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setObjectName("removeButton")
        self.remove_button.setEnabled(False)

        self.generate_ideas_button = QPushButton("Generate Ideas")
        self.generate_ideas_button.setObjectName("generateButton")
        self.generate_ideas_button.setEnabled(False)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.generate_ideas_button)

        self.layout.addLayout(button_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Part Number", "Name", "Type", "Value", "Quantity", "Purchase Link", "Datasheet", "Select"
        ])
        self.table.setColumnWidth(self.PART_NUMBER_COL, 120)
        self.table.setColumnWidth(self.NAME_COL, 150)
        self.table.setColumnWidth(self.TYPE_COL, 100)
        self.table.setColumnWidth(self.VALUE_COL, 300)
        self.table.setColumnWidth(self.QUANTITY_COL, 60)
        self.table.setColumnWidth(self.PURCHASE_LINK_COL, 80)
        self.table.setColumnWidth(self.DATASHEET_COL, 80)
        self.table.setColumnWidth(self.CHECKBOX_COL, 50)
        self.layout.addWidget(self.table)

        if button_stylesheet:
            self.central_widget.setStyleSheet(button_stylesheet)

        self._adjust_window_width()

    def _connect_signals(self):
        self.add_button.clicked.connect(self.add_component_requested)
        self.remove_button.clicked.connect(self._on_remove_clicked)
        self.generate_ideas_button.clicked.connect(self._on_generate_ideas_clicked)
        self.table.cellClicked.connect(self._handle_cell_click)

    def _connect_toolbar_signals(self):
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
        if hasattr(self, 'help_action') and hasattr(self, 'help_triggered'):
             self.help_action.triggered.connect(self.help_triggered)

    def _adjust_window_width(self):
        """Adjusts window width to fit table contents."""
        # (Keep this method as it was)
        total_width = self.table.verticalHeader().width()
        for i in range(self.table.columnCount()):
            total_width += self.table.columnWidth(i)

        scrollbar_width = 0
        if self.table.verticalScrollBar().isVisible():
            scrollbar_width = self.table.style().pixelMetric(QStyle.PM_ScrollBarExtent)

        padding = 30
        target_width = total_width + scrollbar_width + padding

        current_height = self.height()
        self.resize(int(target_width), current_height)

    def _on_remove_clicked(self):
        part_numbers_to_remove = self.get_checked_part_numbers()
        if part_numbers_to_remove:
            self.remove_components_requested.emit(part_numbers_to_remove)

    def _on_generate_ideas_clicked(self):
        checked_part_numbers = self.get_checked_part_numbers()
        if checked_part_numbers:
            self.generate_ideas_requested.emit(checked_part_numbers)


    def _handle_cell_click(self, row, column):
        if column in [self.PURCHASE_LINK_COL, self.DATASHEET_COL]:
            item = self.table.item(row, column)
            if item:
                link_data = item.data(Qt.UserRole)
                if isinstance(link_data, QUrl) and link_data.isValid():
                    self.link_clicked.emit(link_data)

    def get_checked_part_numbers(self):
        checked_part_numbers = []
        for row in range(self.table.rowCount()):
            container_widget = self.table.cellWidget(row, self.CHECKBOX_COL)
            if container_widget:
                checkbox = container_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    part_number_item = self.table.item(row, self.PART_NUMBER_COL)
                    if part_number_item and part_number_item.text():
                        checked_part_numbers.append(part_number_item.text())
        return checked_part_numbers

    def _update_buttons_state_on_checkbox(self):
        checked_items = self.get_checked_part_numbers()
        enable = len(checked_items) > 0
        self.remove_button.setEnabled(enable)
        self.generate_ideas_button.setEnabled(enable)

    def get_selected_part_number(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None
        selected_row = self.table.currentRow()
        if selected_row < 0:
             return None
        part_number_item = self.table.item(selected_row, self.PART_NUMBER_COL)
        return part_number_item.text() if part_number_item else None

    def get_selected_row_data(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None
        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount() -1 )]
        data = {}
        for col, header in enumerate(headers):
            item = self.table.item(selected_row, col)
            data[header] = item.text() if item else ""
            if col in [self.PURCHASE_LINK_COL, self.DATASHEET_COL] and item:
                 link_data = item.data(Qt.UserRole)
                 if isinstance(link_data, QUrl):
                     data[header + "_url"] = link_data.toString()
        return data

    def display_data(self, components):
        self.table.setRowCount(0)
        self._checkboxes.clear()

        if not components:
             self.table.setRowCount(0)
             self._update_buttons_state_on_checkbox()
             return

        self.table.setRowCount(len(components))

        # Need AddComponentDialog just for the mapping temporarily
        temp_dialog = AddComponentDialog()
        backend_to_ui_name_mapping = {v: k for k, v in temp_dialog.ui_to_backend_name_mapping.items()}
        del temp_dialog # Clean up temporary instance

        for row, component in enumerate(components):
            ui_component_type = backend_to_ui_name_mapping.get(component.component_type, component.component_type)

            self.table.setItem(row, self.PART_NUMBER_COL, QTableWidgetItem(component.part_number or ""))
            self.table.setItem(row, self.NAME_COL, QTableWidgetItem(component.name or ""))
            self.table.setItem(row, self.TYPE_COL, QTableWidgetItem(ui_component_type))
            self.table.setItem(row, self.VALUE_COL, QTableWidgetItem(component.value))
            self.table.setItem(row, self.QUANTITY_COL, QTableWidgetItem(str(component.quantity)))

            def set_link_item(row, col, link):
                if link:
                    item = QTableWidgetItem("Link")
                    item.setForeground(QColor("blue"))
                    item.setTextAlignment(Qt.AlignCenter)
                    url = QUrl(link)
                    if not url.scheme():
                        url.setScheme("http")
                    item.setData(Qt.UserRole, url)
                else:
                    item = QTableWidgetItem("")
                self.table.setItem(row, col, item)

            set_link_item(row, self.PURCHASE_LINK_COL, component.purchase_link)
            set_link_item(row, self.DATASHEET_COL, component.datasheet_link)

            checkbox = QCheckBox()
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            cell_widget.setLayout(layout)

            checkbox.stateChanged.connect(self._update_buttons_state_on_checkbox)
            self._checkboxes.append(checkbox)

            self.table.setCellWidget(row, self.CHECKBOX_COL, cell_widget)
            item = QTableWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.table.setItem(row, self.CHECKBOX_COL, item)

        self.table.clearSelection()
        self._update_buttons_state_on_checkbox()