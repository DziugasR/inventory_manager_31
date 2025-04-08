from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QCheckBox, QPushButton, QSpinBox, QScrollArea
)
from PyQt5.QtCore import Qt
from functools import partial

class GenerateIdeasDialog(QDialog):
    SELECT_COL_IDX = 0
    PART_NUMBER_COL_IDX = 1
    TYPE_COL_IDX = 2
    VALUE_COL_IDX = 3
    QUANTITY_COL_IDX = 4

    def __init__(self, components, parent=None):
        super().__init__(parent)
        self.components = components
        self._checkboxes = []
        self.project_quantities = {}
        self._spinboxes = {}
        self.setWindowTitle("Generate Project Ideas")
        self.setGeometry(200, 200, 800, 500)
        self._init_ui()
        self._update_quantity_controls()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left Side (Table) ---
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        title_label = QLabel("Selected Components:")
        table_layout.addWidget(title_label)
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

        # --- Right Side (Controls Area & Button) ---
        placeholder_widget = QWidget()
        right_vertical_layout = QVBoxLayout(placeholder_widget)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.controls_container = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_container)
        self.controls_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.controls_container)
        right_vertical_layout.addWidget(self.scroll_area, 1)

        self.generate_button = QPushButton("Generate Ideas")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setStyleSheet("""
            QPushButton { font-size: 16px; font-weight: bold; padding: 10px;
                          background-color: #4CAF50; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3e8e41; } """)
        # *** Connect Button Signal Here ***
        self.generate_button.clicked.connect(self._on_generate_ideas_clicked)
        right_vertical_layout.addWidget(self.generate_button, 0)

        placeholder_widget.setLayout(right_vertical_layout)

        # --- Add Widgets to Main Layout ---
        main_layout.addWidget(table_widget, 3)
        main_layout.addWidget(placeholder_widget, 2)

        self.setLayout(main_layout)
        self._populate_table()

    def _populate_table(self):
        self.components_table.setRowCount(len(self.components))
        self._checkboxes.clear()
        self._spinboxes.clear()

        try:
            from frontend.ui.add_component_dialog import AddComponentDialog
            temp_dialog = AddComponentDialog()
            backend_to_ui_name_mapping = {v: k for k, v in temp_dialog.ui_to_backend_name_mapping.items()}
            del temp_dialog
        except ImportError:
            backend_to_ui_name_mapping = {}

        for row, component in enumerate(self.components):
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_quantity_controls)
            self._checkboxes.append(checkbox)
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
            ui_type = backend_to_ui_name_mapping.get(component.component_type, component.component_type)
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

    def _update_quantity_controls(self):
        self._clear_layout(self.controls_layout)
        self._spinboxes.clear()
        new_project_quantities = {}

        try:
            from frontend.ui.add_component_dialog import AddComponentDialog
            temp_dialog = AddComponentDialog()
            backend_to_ui_name_mapping = {v: k for k, v in temp_dialog.ui_to_backend_name_mapping.items()}
            del temp_dialog
        except ImportError:
            backend_to_ui_name_mapping = {}

        for i, checkbox in enumerate(self._checkboxes):
            if checkbox.isChecked():
                component = self.components[i]
                part_number = component.part_number
                available_qty = component.quantity
                ui_type = backend_to_ui_name_mapping.get(component.component_type, component.component_type)

                current_proj_qty = self.project_quantities.get(part_number, 1)
                current_proj_qty = min(current_proj_qty, available_qty)
                current_proj_qty = max(1, current_proj_qty) if available_qty > 0 else 0
                new_project_quantities[part_number] = current_proj_qty

                control_widget = QWidget()
                control_layout = QHBoxLayout(control_widget)
                control_layout.setContentsMargins(2,2,2,2)
                label_text = f"{part_number} ({ui_type}):"
                label = QLabel(label_text)
                label.setToolTip(f"Value: {component.value or 'N/A'}\nAvailable: {available_qty}")
                spinbox = QSpinBox()
                spinbox.setMinimum(1 if available_qty > 0 else 0)
                spinbox.setMaximum(available_qty)
                spinbox.setValue(current_proj_qty)
                spinbox.setFixedWidth(70)
                self._spinboxes[part_number] = spinbox
                spinbox.valueChanged.connect(
                    partial(self._on_spinbox_value_changed, part_number)
                )
                control_layout.addWidget(label, 1)
                control_layout.addWidget(spinbox, 0)
                self.controls_layout.addWidget(control_widget)

        self.project_quantities = new_project_quantities

    def _on_spinbox_value_changed(self, part_number, new_value):
        if part_number in self.project_quantities:
             self.project_quantities[part_number] = new_value

    # *** New Method for Button Click ***
    def _on_generate_ideas_clicked(self):
        print("\n--- Generating Ideas Based On Selected Components ---")

        selected_data = self.get_project_component_quantities() # Get {PN: custom_qty}

        if not selected_data:
            print("No components selected or quantities adjusted.")
            print("---------------------------------------------------\n")
            return

        # Need the type mapping again here
        try:
            from frontend.ui.add_component_dialog import AddComponentDialog
            temp_dialog = AddComponentDialog()
            backend_to_ui_name_mapping = {v: k for k, v in temp_dialog.ui_to_backend_name_mapping.items()}
            del temp_dialog
        except ImportError:
            backend_to_ui_name_mapping = {}

        # Iterate through original components to get full details
        for component in self.components:
            part_number = component.part_number
            # Check if this component was selected (i.e., has an entry in selected_data)
            if part_number in selected_data:
                custom_quantity = selected_data[part_number]
                ui_type = backend_to_ui_name_mapping.get(component.component_type, component.component_type)
                value = component.value or "N/A" # Use "N/A" if value is empty

                print(f"  - Part: {part_number}, Type: {ui_type}, Value: {value}, Project Qty: {custom_quantity}")

        print("---------------------------------------------------\n")
        # Future: Add actual idea generation logic here


    def get_selected_components_in_dialog(self):
        selected_in_dialog = []
        for i, checkbox in enumerate(self._checkboxes):
            if checkbox.isChecked():
                if i < len(self.components):
                     selected_in_dialog.append(self.components[i])
        return selected_in_dialog

    def get_project_component_quantities(self):
        current_project_quantities = {}
        for i, checkbox in enumerate(self._checkboxes):
             if checkbox.isChecked():
                 component = self.components[i]
                 part_number = component.part_number
                 if part_number in self._spinboxes:
                     current_project_quantities[part_number] = self._spinboxes[part_number].value()
                 elif part_number in self.project_quantities: # Fallback (should not be needed ideally)
                     current_project_quantities[part_number] = self.project_quantities[part_number]
        return current_project_quantities