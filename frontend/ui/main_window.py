import uuid
import os
from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QCheckBox, QStyle, QAbstractItemView, QHeaderView,
    QLineEdit, QMenu, QComboBox, QLabel, QApplication
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtCore import QUrl, Qt, pyqtSignal
from backend.component_constants import BACKEND_TO_UI_TYPE_MAP
from .menu_bar import AppMenuBar
from .custom_widgets import ComponentTableWidgetItem


class InventoryUI(QMainWindow):
    # --- Signals (Unchanged) ---
    add_component_requested = pyqtSignal()
    remove_components_requested = pyqtSignal(list)
    generate_ideas_requested = pyqtSignal(list)
    export_requested = pyqtSignal()
    import_requested = pyqtSignal()
    load_data_requested = pyqtSignal()
    link_clicked = pyqtSignal(QUrl)
    search_text_changed = pyqtSignal(str)
    selection_changed = pyqtSignal(bool)
    component_data_updated = pyqtSignal(uuid.UUID, dict)
    details_requested = pyqtSignal(uuid.UUID)
    type_filter_changed = pyqtSignal(str)
    duplicate_requested = pyqtSignal(uuid.UUID)
    delete_component_requested = pyqtSignal(uuid.UUID)

    # --- REFACTORED: Column Constants (Img column removed) ---
    PART_NUMBER_COL = 0
    TYPE_COL = 1
    VALUE_COL = 2
    QUANTITY_COL = 3
    PURCHASE_LINK_COL = 4
    DATASHEET_COL = 5
    LOCATION_COL = 6
    CHECKBOX_COL = 7

    def __init__(self, icon_path: str | None = None, app_path: str = "."):
        super().__init__()
        self.app_path = app_path
        self.setWindowTitle("Electronics Inventory Manager")
        self.setGeometry(100, 100, 1100, 600)
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # This list is no longer needed and was part of the problem
        # self._checkboxes = []
        self._row_id_map = {}
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.menu_bar_handler = AppMenuBar(self)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # --- UI elements (unchanged) ---
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
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Type:"))
        self.type_filter_combo = QComboBox()
        filter_layout.addWidget(self.type_filter_combo, 1)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by Part Number, Value, or Location...")
        filter_layout.addWidget(self.search_bar, 2)
        self.layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)

        # --- REFACTORED: Column count and labels updated ---
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Part Number", "Type", "Value", "Quantity", "Purchase Link", "Datasheet", "Location", "Select"
        ])
        self.table.setColumnWidth(self.PART_NUMBER_COL, 160)
        self.table.setColumnWidth(self.TYPE_COL, 100)
        self.table.setColumnWidth(self.VALUE_COL, 300)
        self.table.setColumnWidth(self.QUANTITY_COL, 70)
        self.table.setColumnWidth(self.PURCHASE_LINK_COL, 90)
        self.table.setColumnWidth(self.DATASHEET_COL, 80)
        self.table.setColumnWidth(self.LOCATION_COL, 120)
        self.table.setColumnWidth(self.CHECKBOX_COL, 60)
        self.layout.addWidget(self.table)

    def populate_type_filter(self, type_names: list[str]):
        self.type_filter_combo.blockSignals(True)
        self.type_filter_combo.clear()
        self.type_filter_combo.addItem("All Types")
        self.type_filter_combo.addItems(sorted(type_names))
        self.type_filter_combo.blockSignals(False)

    def _connect_signals(self):
        self.add_button.clicked.connect(self.add_component_requested)
        self.remove_button.clicked.connect(self._on_remove_clicked)
        self.generate_ideas_button.clicked.connect(self._on_generate_ideas_clicked)
        self.export_button.clicked.connect(self._on_export_clicked)
        self.import_button.clicked.connect(self._on_import_clicked)
        self.table.cellClicked.connect(self._handle_cell_click)
        self.search_bar.textChanged.connect(self.search_text_changed.emit)
        self.table.itemDoubleClicked.connect(self._handle_double_click)
        self.table.itemChanged.connect(self._handle_item_changed)
        self.type_filter_combo.currentTextChanged.connect(self.type_filter_changed.emit)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _adjust_window_width(self):
        total_width = self.table.verticalHeader().width()
        for i in range(self.table.columnCount()):
            total_width += self.table.columnWidth(i)
        scrollbar_width = self.table.style().pixelMetric(
            QStyle.PM_ScrollBarExtent) if self.table.verticalScrollBar().isVisible() else 0
        padding = 40
        self.resize(int(total_width + scrollbar_width + padding), self.height())

    def _adjust_table_columns_for_resize(self):
        if hasattr(self, 'table'):
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            for col in [self.PART_NUMBER_COL, self.TYPE_COL, self.QUANTITY_COL, self.CHECKBOX_COL,
                        self.PURCHASE_LINK_COL, self.DATASHEET_COL, self.LOCATION_COL]:
                header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_table_columns_for_resize()

    def _show_context_menu(self, position):
        item = self.table.itemAt(position)
        if not item: return
        component_id = self.get_id_for_row(item.row())
        if not component_id: return

        menu = QMenu()
        details_action = menu.addAction("More Details...")
        duplicate_action = menu.addAction("Duplicate Component")
        menu.addSeparator()
        copy_pn_action = menu.addAction("Copy Part Number")
        copy_val_action = menu.addAction("Copy Value")

        menu.addSeparator()
        delete_action = menu.addAction("Remove Component Permanently...")
        font = delete_action.font()
        font.setBold(True)
        delete_action.setFont(font)

        action = menu.exec_(self.table.mapToGlobal(position))

        if action == details_action:
            self.details_requested.emit(component_id)
        elif action == duplicate_action:
            self.duplicate_requested.emit(component_id)
        elif action == copy_pn_action:
            if pn_item := self.table.item(item.row(), self.PART_NUMBER_COL): QApplication.clipboard().setText(
                pn_item.text())
        elif action == copy_val_action:
            if val_item := self.table.item(item.row(), self.VALUE_COL): QApplication.clipboard().setText(
                val_item.text())
        elif action == delete_action:
            self.delete_component_requested.emit(component_id)

    def _handle_double_click(self, item: QTableWidgetItem):
        if not (component_id := self.get_id_for_row(item.row())): return
        if item.column() == self.PART_NUMBER_COL:
            self.details_requested.emit(component_id)
        elif item.column() in [self.VALUE_COL, self.QUANTITY_COL, self.LOCATION_COL]:
            self.table.editItem(item)

    def _handle_item_changed(self, item: QTableWidgetItem):
        if not (component_id := self.get_id_for_row(item.row())) or not self.table.isPersistentEditorOpen(item): return
        col, new_value, update_data = item.column(), item.text(), {}
        if col == self.QUANTITY_COL:
            try:
                update_data['quantity'] = int(new_value)
            except (ValueError, TypeError):
                self.load_data_requested.emit(); return
        elif col == self.VALUE_COL:
            update_data['value'] = new_value
        elif col == self.LOCATION_COL:
            update_data['location'] = new_value
        if update_data: self.component_data_updated.emit(component_id, update_data)

    def _handle_cell_click(self, row, column):
        if column in [self.PURCHASE_LINK_COL, self.DATASHEET_COL]:
            if (item := self.table.item(row, column)) and (link_data := item.data(Qt.UserRole)) and isinstance(
                    link_data, QUrl) and link_data.isValid():
                self.link_clicked.emit(link_data)

    def get_id_for_row(self, row: int) -> uuid.UUID | None:
        return self._row_id_map.get(row)

    def display_data(self, components: list):
        # 1. Preparation: Block signals and preserve state
        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)
        current_selection_id = self.get_selected_id()

        self.table.clearContents()
        self._row_id_map.clear()

        self.table.setRowCount(len(components) if components else 0)

        if not components:
            self._update_buttons_state_on_checkbox()
            self.table.blockSignals(False)
            self.table.setSortingEnabled(True)
            return

        new_selection_row = -1
        for row, component in enumerate(components):
            # Validate the component ID
            if not (component_id := component.id) or not isinstance(component_id, uuid.UUID):
                self.table.setRowHidden(row, True)
                continue

            self._row_id_map[row] = component_id

            if component_id == current_selection_id:
                new_selection_row = row

            part_number_text = component.part_number or ""
            pn_item = QTableWidgetItem(part_number_text)
            pn_item.setFlags(pn_item.flags() & ~Qt.ItemIsEditable)
            if component.image_path:

                pn_item.setForeground(QColor("#569cd6"))

                full_image_path = os.path.join(self.app_path, component.image_path).replace("\\", "/")
                if os.path.exists(full_image_path):
                    pn_item.setToolTip(f'<img src="file:///{full_image_path}" width="250">')
            self.table.setItem(row, self.PART_NUMBER_COL, pn_item)

            ui_type = BACKEND_TO_UI_TYPE_MAP.get(component.component_type, component.component_type)
            type_item = QTableWidgetItem(ui_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, self.TYPE_COL, type_item)

            self.table.setItem(row, self.VALUE_COL, QTableWidgetItem(component.value or ""))
            self.table.setItem(row, self.LOCATION_COL, QTableWidgetItem(component.location or ""))

            qty_item = QTableWidgetItem()
            try:
                qty_item.setData(Qt.DisplayRole, int(component.quantity))
            except (ValueError, TypeError):
                qty_item.setData(Qt.DisplayRole, 0)
            self.table.setItem(row, self.QUANTITY_COL, qty_item)

            def set_link_item(col_idx, link_url):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                if link_url:
                    item.setText("Link")
                    item.setForeground(QColor("#569cd6"))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    url = QUrl(link_url)
                    if not url.scheme(): url.setScheme("http")
                    item.setData(Qt.UserRole, url)
                else:
                    item.setText("")
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.table.setItem(row, col_idx, item)

            set_link_item(self.PURCHASE_LINK_COL, component.purchase_link)
            set_link_item(self.DATASHEET_COL, component.datasheet_link)

            checkbox = QCheckBox()

            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            checkbox.stateChanged.connect(self._update_buttons_state_on_checkbox)
            self.table.setCellWidget(row, self.CHECKBOX_COL, cell_widget)

        self.table.blockSignals(False)
        self.table.setSortingEnabled(True)

        if new_selection_row != -1:
            self.table.selectRow(new_selection_row)
        else:
            self.table.clearSelection()

        self._update_buttons_state_on_checkbox()

    def _on_remove_clicked(self):
        if ids := self.get_checked_ids(): self.remove_components_requested.emit(ids)

    def _on_generate_ideas_clicked(self):
        if ids := self.get_checked_ids(): self.generate_ideas_requested.emit(ids)

    def _on_export_clicked(self):
        self.export_requested.emit()

    def _on_import_clicked(self):
        self.import_requested.emit()

    def get_checked_ids(self) -> list[uuid.UUID]:
        return [self._row_id_map[row] for row in range(self.table.rowCount()) if
                (w := self.table.cellWidget(row, self.CHECKBOX_COL)) and (
                    cb := w.findChild(QCheckBox)) and cb.isChecked() and row in self._row_id_map]

    def _update_buttons_state_on_checkbox(self):
        enable = bool(self.get_checked_ids())
        self.remove_button.setEnabled(enable)
        self.generate_ideas_button.setEnabled(enable)
        self.selection_changed.emit(enable)

    def get_selected_id(self) -> uuid.UUID | None:
        if (selected_row := self.table.currentRow()) >= 0: return self._row_id_map.get(selected_row)
        return None

    def _adjust_table_columns_for_resize(self):
        if hasattr(self, 'table'):
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            for col in [self.PART_NUMBER_COL, self.TYPE_COL, self.QUANTITY_COL, self.CHECKBOX_COL,
                        self.PURCHASE_LINK_COL, self.DATASHEET_COL, self.LOCATION_COL]:
                header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_table_columns_for_resize()

    def select_all_items(self):
        for row in range(self.table.rowCount()):
            if (widget := self.table.cellWidget(row, self.CHECKBOX_COL)) and (checkbox := widget.findChild(QCheckBox)):
                checkbox.setChecked(True)

    def deselect_all_items(self):
        for row in range(self.table.rowCount()):
            if (widget := self.table.cellWidget(row, self.CHECKBOX_COL)) and (checkbox := widget.findChild(QCheckBox)):
                checkbox.setChecked(False)