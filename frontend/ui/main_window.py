import uuid

from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QCheckBox, QStyle, QAbstractItemView, QHeaderView
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QUrl, Qt, pyqtSignal

from .utils import load_stylesheet
from backend.component_constants import BACKEND_TO_UI_TYPE_MAP
from pathlib import Path

class InventoryUI(QMainWindow):
    add_component_requested = pyqtSignal()
    remove_components_requested = pyqtSignal(list)
    generate_ideas_requested = pyqtSignal(list)
    export_requested = pyqtSignal()
    import_requested = pyqtSignal()
    load_data_requested = pyqtSignal()
    link_clicked = pyqtSignal(QUrl)

    PART_NUMBER_COL = 0
    TYPE_COL = 1
    VALUE_COL = 2
    QUANTITY_COL = 3
    PURCHASE_LINK_COL = 4
    DATASHEET_COL = 5
    CHECKBOX_COL = 6

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Electronics Inventory Manager")
        self.setGeometry(100, 100, 950, 500)
        self._checkboxes = []
        self._row_id_map = {}
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        button_stylesheet = load_stylesheet()

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Component")
        self.add_button.setObjectName("addButton")

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.setObjectName("removeButton")
        self.remove_button.setEnabled(False)

        self.generate_ideas_button = QPushButton("Generate Ideas")
        self.generate_ideas_button.setObjectName("generateButton")
        self.generate_ideas_button.setEnabled(False)

        self.export_button = QPushButton("Export to Excel")
        self.export_button.setObjectName("exportButton")

        self.import_button = QPushButton("Import from Excel")
        self.import_button.setObjectName("importButton")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.generate_ideas_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.import_button)

        self.layout.addLayout(button_layout)

        self.table = QTableWidget()

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.table.setSortingEnabled(True)

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Part Number", "Type", "Value", "Quantity", "Purchase Link", "Datasheet", "Select"
        ])
        self.table.setColumnWidth(self.PART_NUMBER_COL, 150)
        self.table.setColumnWidth(self.TYPE_COL, 100)
        self.table.setColumnWidth(self.VALUE_COL, 300)
        self.table.setColumnWidth(self.QUANTITY_COL, 70)
        self.table.setColumnWidth(self.PURCHASE_LINK_COL, 90)
        self.table.setColumnWidth(self.DATASHEET_COL, 80)
        self.table.setColumnWidth(self.CHECKBOX_COL, 60)
        self.layout.addWidget(self.table)

        if button_stylesheet:
            self.central_widget.setStyleSheet(button_stylesheet)

        self._adjust_window_width()

    def _connect_signals(self):
        self.add_button.clicked.connect(self.add_component_requested)
        self.remove_button.clicked.connect(self._on_remove_clicked)
        self.generate_ideas_button.clicked.connect(self._on_generate_ideas_clicked)
        self.export_button.clicked.connect(self._on_export_clicked)
        self.import_button.clicked.connect(self._on_import_clicked)
        self.table.cellClicked.connect(self._handle_cell_click)

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

    def _adjust_table_columns_for_resize(self):
        if hasattr(self, 'table'):
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)

            header.setSectionResizeMode(self.PART_NUMBER_COL, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(self.TYPE_COL, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(self.QUANTITY_COL, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(self.CHECKBOX_COL, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(self.PURCHASE_LINK_COL, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(self.DATASHEET_COL, QHeaderView.ResizeToContents)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_table_columns_for_resize()

    def _on_remove_clicked(self):
        ids_to_remove = self.get_checked_ids()
        if ids_to_remove:
            self.remove_components_requested.emit(ids_to_remove)

    def _on_generate_ideas_clicked(self):
        checked_ids = self.get_checked_ids()
        if checked_ids:
            self.generate_ideas_requested.emit(checked_ids)

    def _on_export_clicked(self):
        self.export_requested.emit()

    def _on_import_clicked(self):
        self.import_requested.emit()

    def _handle_cell_click(self, row, column):
        if column in [self.PURCHASE_LINK_COL, self.DATASHEET_COL]:
            item = self.table.item(row, column)
            if item:
                link_data = item.data(Qt.UserRole)
                if isinstance(link_data, QUrl) and link_data.isValid():
                    self.link_clicked.emit(link_data)

    def get_checked_ids(self) -> list[uuid.UUID]:
        checked_ids = []
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, self.CHECKBOX_COL)
            if isinstance(widget, QWidget):
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    component_id = self._row_id_map.get(row)
                    if component_id:
                        checked_ids.append(component_id)
                    else:
                        print(f"Warning: No ID found in map for checked row {row}")
        return checked_ids

    def _update_buttons_state_on_checkbox(self):
        checked_items = self.get_checked_ids()
        enable = len(checked_items) > 0
        self.remove_button.setEnabled(enable)
        self.generate_ideas_button.setEnabled(enable)

    def get_selected_id(self) -> uuid.UUID | None:
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            return self._row_id_map.get(selected_row)
        return None

    def get_selected_row_data(self) -> dict | None:
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None

        headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount() - 1)] # Exclude checkbox col header
        data = {}
        component_id = self._row_id_map.get(selected_row)
        if component_id:
            data['id'] = str(component_id)

        for col, header in enumerate(headers):
            item = self.table.item(selected_row, col)
            data[header] = item.text() if item else ""
            if col in [self.PURCHASE_LINK_COL, self.DATASHEET_COL] and item:
                 link_data = item.data(Qt.UserRole)
                 if isinstance(link_data, QUrl):
                     data[header + "_url"] = link_data.toString()
        return data

    def display_data(self, components: list):
        self.table.setSortingEnabled(False)

        current_selection_id = self.get_selected_id()

        self.table.setRowCount(0)
        self._checkboxes.clear()
        self._row_id_map.clear()
        self.table.setRowCount(len(components))

        backend_to_ui_name_mapping = BACKEND_TO_UI_TYPE_MAP

        if not components:
            self._update_buttons_state_on_checkbox()
            self.table.setSortingEnabled(True)
            return

        self.table.setRowCount(len(components))

        new_selection_row = -1
        for row, component in enumerate(components):
            component_id = component.id
            if not isinstance(component_id, uuid.UUID):
                print(
                    f"Warning: Invalid or missing ID for component {component.part_number} at row {row}. Skipping row.")
                self.table.setRowHidden(row, True)
                continue

            self._row_id_map[row] = component_id
            if component_id == current_selection_id:
                new_selection_row = row

            # Use the mapping with a fallback to the original backend ID if not found
            ui_component_type = backend_to_ui_name_mapping.get(component.component_type, component.component_type)

            pn_item = QTableWidgetItem(component.part_number or "")
            pn_item.setData(Qt.UserRole, component_id)
            self.table.setItem(row, self.PART_NUMBER_COL, pn_item)

            self.table.setItem(row, self.TYPE_COL, QTableWidgetItem(ui_component_type))

            self.table.setItem(row, self.VALUE_COL, QTableWidgetItem(component.value or ""))

            qty_item = QTableWidgetItem()
            try:
                numeric_quantity = int(component.quantity)
                qty_item.setData(Qt.EditRole, numeric_quantity)
            except (ValueError, TypeError):
                qty_item.setData(Qt.EditRole, 0)
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, self.QUANTITY_COL, qty_item)

            def set_link_item(row_idx, col_idx, link_url):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                if link_url:
                    item.setText("Link")
                    item.setForeground(QColor("blue"))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    url = QUrl(link_url)
                    if not url.scheme():
                        url.setScheme("http")
                    item.setData(Qt.UserRole, url)
                else:
                    item.setText("")
                    item.setFlags(Qt.ItemIsEnabled)
                self.table.setItem(row_idx, col_idx, item)

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
            item_for_checkbox_cell = QTableWidgetItem()
            item_for_checkbox_cell.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, self.CHECKBOX_COL, item_for_checkbox_cell)

        self.table.setSortingEnabled(True)
        if new_selection_row != -1:
            self.table.selectRow(new_selection_row)
        else:
            self.table.clearSelection()
        self._update_buttons_state_on_checkbox()
        self._adjust_window_width()