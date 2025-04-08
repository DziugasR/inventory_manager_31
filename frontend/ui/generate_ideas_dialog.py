from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QCheckBox, QPushButton, QSpinBox, QScrollArea # Import QSpinBox, QScrollArea
)
from PyQt5.QtCore import Qt
from functools import partial # For connecting signals with arguments

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
        # Dictionary to store {part_number: project_quantity} for checked items
        self.project_quantities = {}
        # Dictionary to map part_number to its corresponding SpinBox widget
        self._spinboxes = {}
        self.setWindowTitle("Generate Project Ideas")
        self.setGeometry(200, 200, 800, 500) # Adjusted size slightly
        self._init_ui()
        self._update_quantity_controls() # Initial setup

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left Side (Table - Mostly unchanged) ---
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

        # --- Right Side (Placeholder, Controls, and Button) ---
        placeholder_widget = QWidget()
        right_vertical_layout = QVBoxLayout(placeholder_widget)

        # Top Placeholder Label (Optional)
        # placeholder_label = QLabel("Adjust Quantities for Project")
        # placeholder_label.setAlignment(Qt.AlignCenter)
        # right_vertical_layout.addWidget(placeholder_label) # Remove if controls area is enough

        # --- Scroll Area for Dynamic Controls ---
        self.scroll_area = QScrollArea() # Use a scroll area
        self.scroll_area.setWidgetResizable(True) # Allow contained widget to resize
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Hide horizontal scrollbar
        self.controls_container = QWidget() # Container widget for the controls layout
        self.controls_layout = QVBoxLayout(self.controls_container) # Layout for dynamic controls
        self.controls_layout.setAlignment(Qt.AlignTop) # Align controls to the top
        self.scroll_area.setWidget(self.controls_container) # Put container in scroll area
        right_vertical_layout.addWidget(self.scroll_area, 1) # Add scroll area (takes most space)

        # --- Generate Button (at the bottom) ---
        self.generate_button = QPushButton("Generate Ideas")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setStyleSheet("""
            QPushButton { font-size: 16px; font-weight: bold; padding: 10px;
                          background-color: #4CAF50; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3e8e41; } """)
        right_vertical_layout.addWidget(self.generate_button, 0) # Add button at bottom

        placeholder_widget.setLayout(right_vertical_layout)
        # placeholder_widget.setStyleSheet("background-color: #f0f0f0;") # Optional styling

        # --- Add Widgets to Main Layout ---
        main_layout.addWidget(table_widget, 3)
        main_layout.addWidget(placeholder_widget, 2) # Adjust stretch factors if needed

        self.setLayout(main_layout)
        self._populate_table()

    def _populate_table(self):
        self.components_table.setRowCount(len(self.components))
        self._checkboxes.clear()
        self._spinboxes.clear() # Clear spinbox references as well

        try:
            from frontend.ui.add_component_dialog import AddComponentDialog
            temp_dialog = AddComponentDialog()
            backend_to_ui_name_mapping = {v: k for k, v in temp_dialog.ui_to_backend_name_mapping.items()}
            del temp_dialog
        except ImportError:
            backend_to_ui_name_mapping = {}

        for row, component in enumerate(self.components):
            # --- Checkbox ---
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_quantity_controls) # Connect signal
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

            # --- Other Data ---
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
        """Helper function to remove all widgets from a layout."""
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
        """Dynamically add/remove quantity SpinBoxes based on checkbox state."""
        # Clear previous controls from the dynamic layout
        self._clear_layout(self.controls_layout)
        self._spinboxes.clear() # Clear old spinbox references

        new_project_quantities = {} # Build a new dict based on current state

        for i, checkbox in enumerate(self._checkboxes):
            if checkbox.isChecked():
                component = self.components[i]
                part_number = component.part_number
                available_qty = component.quantity

                # Keep existing value if previously set, else default to 1
                current_proj_qty = self.project_quantities.get(part_number, 1)
                # Ensure project qty doesn't exceed available
                current_proj_qty = min(current_proj_qty, available_qty)
                # Ensure project qty is at least 1 if available > 0
                current_proj_qty = max(1, current_proj_qty) if available_qty > 0 else 0


                new_project_quantities[part_number] = current_proj_qty

                # Create Widgets for this component
                control_widget = QWidget() # Use a container widget for layout
                control_layout = QHBoxLayout(control_widget)
                control_layout.setContentsMargins(2,2,2,2) # Smaller margins

                label = QLabel(f"{part_number}:") # Show Part Number
                label.setToolTip(f"Type: {component.component_type}\nValue: {component.value or 'N/A'}\nAvailable: {available_qty}")

                spinbox = QSpinBox()
                spinbox.setMinimum(1 if available_qty > 0 else 0) # Minimum 1 if available
                spinbox.setMaximum(available_qty)
                spinbox.setValue(current_proj_qty)
                spinbox.setFixedWidth(70) # Adjust width as needed

                # Store reference to spinbox
                self._spinboxes[part_number] = spinbox

                # Connect signal to update project_quantities dict
                # Use partial to pass part_number to the handler
                spinbox.valueChanged.connect(
                    partial(self._on_spinbox_value_changed, part_number)
                )

                control_layout.addWidget(label, 1) # Label takes more stretch
                control_layout.addWidget(spinbox, 0) # Spinbox takes less space

                # Add this component's control widget to the main controls layout
                self.controls_layout.addWidget(control_widget)

        self.project_quantities = new_project_quantities # Update the main dict

        # Add a spacer at the end if needed to push items up
        # self.controls_layout.addStretch(1)


    def _on_spinbox_value_changed(self, part_number, new_value):
        """Update the project_quantities dictionary when a spinbox changes."""
        if part_number in self.project_quantities:
             self.project_quantities[part_number] = new_value
        # print(f"Updated project quantity for {part_number}: {new_value}") # Debug


    def get_selected_components_in_dialog(self):
        """Returns components checked in the table (original behavior)."""
        selected_in_dialog = []
        for i, checkbox in enumerate(self._checkboxes):
            if checkbox.isChecked():
                if i < len(self.components):
                     selected_in_dialog.append(self.components[i])
        return selected_in_dialog

    def get_project_component_quantities(self):
        """Returns the dictionary of {part_number: project_quantity}."""
        # Filter quantities based on currently checked items *and* valid spinboxes
        current_project_quantities = {}
        for i, checkbox in enumerate(self._checkboxes):
             if checkbox.isChecked():
                 component = self.components[i]
                 part_number = component.part_number
                 if part_number in self._spinboxes:
                     current_project_quantities[part_number] = self._spinboxes[part_number].value()
                 elif part_number in self.project_quantities: # Fallback if spinbox missing? Should not happen
                     current_project_quantities[part_number] = self.project_quantities[part_number]

        # return self.project_quantities # Return the internal dict directly
        return current_project_quantities # Return filtered dict