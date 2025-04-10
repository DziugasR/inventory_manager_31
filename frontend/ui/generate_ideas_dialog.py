from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton, QSpinBox, QTextEdit, QToolTip
)
from PyQt5.QtCore import Qt, pyqtSignal
from functools import partial

class GenerateIdeasDialog(QDialog):
    quantity_changed = pyqtSignal(str, int)
    generate_requested = pyqtSignal()

    PART_NUMBER_COL_IDX = 0
    TYPE_COL_IDX = 1
    VALUE_COL_IDX = 2
    QUANTITY_COL_IDX = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._spinboxes = {}
        self.setWindowTitle("Generate Project Ideas")
        self.setGeometry(200, 150, 800, 600)
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        left_title_label = QLabel("Available Components:")
        table_layout.addWidget(left_title_label)
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(4)
        self.components_table.setHorizontalHeaderLabels(["Part Number", "Type", "Value", "Project Qty"])
        self.components_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.components_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.components_table.verticalHeader().setVisible(False)
        self.components_table.verticalHeader().setDefaultSectionSize(24)
        self.components_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        header = self.components_table.horizontalHeader()
        header.setSectionResizeMode(self.PART_NUMBER_COL_IDX, QHeaderView.Interactive)
        header.setSectionResizeMode(self.TYPE_COL_IDX, QHeaderView.Interactive)
        header.setSectionResizeMode(self.VALUE_COL_IDX, QHeaderView.Stretch)
        header.setSectionResizeMode(self.QUANTITY_COL_IDX, QHeaderView.Fixed)
        self.components_table.setColumnWidth(self.PART_NUMBER_COL_IDX, 120)
        self.components_table.setColumnWidth(self.TYPE_COL_IDX, 100)
        self.components_table.setColumnWidth(self.QUANTITY_COL_IDX, 85)
        table_layout.addWidget(self.components_table)

        controls_widget = QWidget()
        right_vertical_layout = QVBoxLayout(controls_widget)

        response_title_label = QLabel("Generated Ideas:")
        right_vertical_layout.addWidget(response_title_label)
        self.response_display = QTextEdit()
        self.response_display.setReadOnly(True)
        self.response_display.setPlaceholderText("Click 'Generate Ideas' to get suggestions...")
        right_vertical_layout.addWidget(self.response_display, 1)

        self.generate_button = QPushButton("Generate Ideas")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setStyleSheet("""
            QPushButton {
                font-size: 16px; font-weight: bold; color: white;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #5cb85c, stop: 1 #4cae4c);
                border: 1px solid #4cae4c; border-radius: 5px; padding: 10px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4cae4c, stop: 1 #449d44);
                border: 1px solid #398439;
            }
            QPushButton:pressed { background-color: #449d44; border: 1px solid #398439; }
            QPushButton:disabled { background-color: #cccccc; border: 1px solid #bbbbbb; color: #888888; }
        """)
        self.generate_button.clicked.connect(self.generate_requested)
        right_vertical_layout.addWidget(self.generate_button, 0)

        controls_widget.setLayout(right_vertical_layout)

        main_layout.addWidget(table_widget, 2)
        main_layout.addWidget(controls_widget, 1)
        self.setLayout(main_layout)

    def populate_table(self, components, type_mapping):
        self.components_table.setRowCount(len(components))
        self._spinboxes.clear()

        for row, component in enumerate(components):
            part_number = component.part_number or ""
            ui_type = type_mapping.get(component.component_type, component.component_type)
            value = component.value or ""
            available_quantity = component.quantity

            pn_item = QTableWidgetItem(part_number)
            type_item = QTableWidgetItem(ui_type)
            value_item = QTableWidgetItem(value)

            self.components_table.setItem(row, self.PART_NUMBER_COL_IDX, pn_item)
            self.components_table.setItem(row, self.TYPE_COL_IDX, type_item)
            self.components_table.setItem(row, self.VALUE_COL_IDX, value_item)

            spinbox = QSpinBox()
            spinbox.setMinimum(0)
            spinbox.setMaximum(available_quantity)
            initial_project_qty = 1 if available_quantity > 0 else 0
            spinbox.setValue(initial_project_qty)
            spinbox.setAlignment(Qt.AlignCenter)
            spinbox.setToolTip(f"Available: {available_quantity}")
            spinbox.valueChanged.connect(partial(self._handle_internal_spinbox_change, part_number))

            self.components_table.setCellWidget(row, self.QUANTITY_COL_IDX, spinbox)
            self._spinboxes[part_number] = spinbox

            row_tooltip = f"Part: {part_number}\nType: {ui_type}\nValue: {value or 'N/A'}\nAvailable: {available_quantity}"
            for col in range(self.components_table.columnCount()):
                 item = self.components_table.item(row, col)
                 if item:
                     item.setToolTip(row_tooltip)
                 widget = self.components_table.cellWidget(row, col)
                 if widget:
                    widget.setToolTip(row_tooltip + f"\n\nCurrent project quantity: {spinbox.value()}")


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
        self.components_table.setEnabled(not is_processing)
        if is_processing:
            self.response_display.setPlaceholderText("Generating ideas from ChatGPT...")
            self.response_display.clear()
        else:
            if not self.response_display.toPlainText():
                 self.response_display.setPlaceholderText("Click 'Generate Ideas' to get suggestions...")

    def _handle_internal_spinbox_change(self, part_number, new_value):
        self.quantity_changed.emit(part_number, new_value)
        if part_number in self._spinboxes:
            spinbox = self._spinboxes[part_number]
            current_tooltip = spinbox.toolTip()
            if "\nCurrent project quantity:" in current_tooltip:
                base_tooltip = current_tooltip.split("\nCurrent project quantity:")[0]
                spinbox.setToolTip(base_tooltip + f"\n\nCurrent project quantity: {new_value}")