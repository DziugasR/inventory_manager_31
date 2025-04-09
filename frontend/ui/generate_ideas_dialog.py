from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QCheckBox, QPushButton, QSpinBox, QScrollArea, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from functools import partial

class GenerateIdeasDialog(QDialog):
    checkbox_state_changed = pyqtSignal(int, bool)
    quantity_changed = pyqtSignal(str, int)
    generate_requested = pyqtSignal()

    SELECT_COL_IDX = 0
    PART_NUMBER_COL_IDX = 1
    TYPE_COL_IDX = 2
    VALUE_COL_IDX = 3
    QUANTITY_COL_IDX = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes = []
        self._spinboxes = {}
        self._quantity_control_widgets = {}
        self.setWindowTitle("Generate Project Ideas")
        self.setGeometry(200, 150, 800, 600)
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        left_title_label = QLabel("Selected Components:")
        table_layout.addWidget(left_title_label)
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(5)
        self.components_table.setHorizontalHeaderLabels(["Select", "Part Number", "Type", "Value", "Quantity"])
        self.components_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.components_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.components_table.verticalHeader().setVisible(False)
        self.components_table.verticalHeader().setDefaultSectionSize(22)
        self.components_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        header = self.components_table.horizontalHeader()
        header.setSectionResizeMode(self.SELECT_COL_IDX, QHeaderView.Fixed)
        header.setSectionResizeMode(self.PART_NUMBER_COL_IDX, QHeaderView.Interactive)
        header.setSectionResizeMode(self.TYPE_COL_IDX, QHeaderView.Interactive)
        header.setSectionResizeMode(self.VALUE_COL_IDX, QHeaderView.Stretch)
        header.setSectionResizeMode(self.QUANTITY_COL_IDX, QHeaderView.Interactive)
        self.components_table.setColumnWidth(self.SELECT_COL_IDX, 50)
        self.components_table.setColumnWidth(self.PART_NUMBER_COL_IDX, 100)
        self.components_table.setColumnWidth(self.TYPE_COL_IDX, 90)
        self.components_table.setColumnWidth(self.QUANTITY_COL_IDX, 60)
        table_layout.addWidget(self.components_table)

        controls_widget = QWidget()
        right_vertical_layout = QVBoxLayout(controls_widget)

        right_title_label = QLabel("Adjust Project Quantity:")
        right_vertical_layout.addWidget(right_title_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.controls_container = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_container)
        self.controls_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.controls_container)
        right_vertical_layout.addWidget(self.scroll_area, 1)

        response_title_label = QLabel("Generated Ideas:")
        right_vertical_layout.addWidget(response_title_label)
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setPlaceholderText("Click 'Generate Ideas' to get suggestions...")
        right_vertical_layout.addWidget(self.response_display, 3)

        self.generate_button = QPushButton("Generate Ideas")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #5cb85c, stop: 1 #4cae4c);
                border: 1px solid #4cae4c;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #4cae4c, stop: 1 #449d44);
                border: 1px solid #398439;
            }
            QPushButton:pressed {
                background-color: #449d44;
                border: 1px solid #398439;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                border: 1px solid #bbbbbb;
                color: #888888;
            }
        """)
        self.generate_button.clicked.connect(self.generate_requested)
        right_vertical_layout.addWidget(self.generate_button, 0)

        controls_widget.setLayout(right_vertical_layout)

        main_layout.addWidget(table_widget, 3)
        main_layout.addWidget(controls_widget, 2)
        self.setLayout(main_layout)

    def populate_table(self, components, type_mapping):
        self.components_table.setRowCount(len(components))
        self._checkboxes = [None] * len(components)

        for row, component in enumerate(components):
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(partial(self._handle_internal_checkbox_change, row))
            self._checkboxes[row] = checkbox
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            cell_widget.setLayout(layout)
            self.components_table.setCellWidget(row, self.SELECT_COL_IDX, cell_widget)
            select_item = QTableWidgetItem()
            select_item.setFlags(select_item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            self.components_table.setItem(row, self.SELECT_COL_IDX, select_item)

            part_number = component.part_number or ""
            ui_type = type_mapping.get(component.component_type, component.component_type)
            value = component.value or ""
            quantity = str(component.quantity)
            pn_item = QTableWidgetItem(part_number)
            type_item = QTableWidgetItem(ui_type)
            value_item = QTableWidgetItem(value)
            qty_item = QTableWidgetItem(quantity)
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.components_table.setItem(row, self.PART_NUMBER_COL_IDX, pn_item)
            self.components_table.setItem(row, self.TYPE_COL_IDX, type_item)
            self.components_table.setItem(row, self.VALUE_COL_IDX, value_item)
            self.components_table.setItem(row, self.QUANTITY_COL_IDX, qty_item)

    def add_quantity_control(self, part_number, ui_type, value_str, available_qty, initial_proj_qty):
        if part_number in self._quantity_control_widgets:
             return

        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(2, 2, 2, 2)

        label_text = f"{part_number} ({ui_type}):"
        label = QLabel(label_text)
        label.setToolTip(f"Value: {value_str or 'N/A'}\nAvailable: {available_qty}")

        spinbox = QSpinBox()
        spinbox.setMinimum(1 if available_qty > 0 else 0)
        spinbox.setMaximum(available_qty)
        spinbox.setValue(initial_proj_qty)
        spinbox.setFixedWidth(70)
        spinbox.valueChanged.connect(partial(self._handle_internal_spinbox_change, part_number))

        control_layout.addWidget(label, 1)
        control_layout.addWidget(spinbox, 0)
        self.controls_layout.addWidget(control_widget)

        self._spinboxes[part_number] = spinbox
        self._quantity_control_widgets[part_number] = control_widget

    def remove_quantity_control(self, part_number):
        if part_number in self._quantity_control_widgets:
            widget_to_remove = self._quantity_control_widgets.pop(part_number)
            widget_to_remove.deleteLater()
            self._spinboxes.pop(part_number, None)

    def clear_quantity_controls(self):
        self._clear_layout(self.controls_layout)
        self._spinboxes.clear()
        self._quantity_control_widgets.clear()

    def get_spinbox_values(self):
        values = {}
        for pn, spinbox in self._spinboxes.items():
             values[pn] = spinbox.value()
        return values

    def set_response_text(self, text):
        self.response_display.setText(text)

    def clear_response_text(self):
        self.response_display.clear()

    def show_processing(self, is_processing):
        self.generate_button.setEnabled(not is_processing)
        if is_processing:
            self.response_display.setPlaceholderText("Generating ideas from ChatGPT...")
            self.response_display.clear()
        else:
            if not self.response_display.toPlainText():
                 self.response_display.setPlaceholderText("Click 'Generate Ideas' to get suggestions...")

    def _handle_internal_checkbox_change(self, row_index, state):
        is_checked = (state == Qt.Checked)
        self.checkbox_state_changed.emit(row_index, is_checked)

    def _handle_internal_spinbox_change(self, part_number, new_value):
        self.quantity_changed.emit(part_number, new_value)

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    sub_layout = item.layout()
                    if sub_layout is not None:
                        self._clear_layout(sub_layout)