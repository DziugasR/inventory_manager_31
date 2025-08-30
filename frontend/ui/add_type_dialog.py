from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QHBoxLayout, QPushButton, QFrame,
    QGroupBox, QComboBox
)
from PyQt5.QtCore import pyqtSignal


class AddTypeDialog(QDialog):
    new_type_data_collected = pyqtSignal(dict)
    delete_type_requested = pyqtSignal(str)

    def __init__(self, custom_type_names: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Component Types")
        self.setMinimumWidth(400)

        # Main layout
        self.layout = QVBoxLayout(self)

        # --- Create New Type Section ---
        add_group = QGroupBox("Create New Type")
        add_layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.type_name_input = QLineEdit(self)
        self.type_name_input.setPlaceholderText("e.g., Potentiometer, Sensor Array")
        form_layout.addRow(QLabel("New Type Name:"), self.type_name_input)

        add_layout.addLayout(form_layout)

        properties_label = QLabel("Define at least one property for the new type:")
        properties_label.setStyleSheet("font-weight: bold;")
        add_layout.addWidget(properties_label)

        properties_form_layout = QFormLayout()
        self.property_inputs = []
        for i in range(4):
            placeholder = f"e.g., Resistance (Ω)" if i == 0 else "Optional property"
            prop_input = QLineEdit(self)
            prop_input.setPlaceholderText(placeholder)
            properties_form_layout.addRow(QLabel(f"Property {i + 1}:"), prop_input)
            self.property_inputs.append(prop_input)

        add_layout.addLayout(properties_form_layout)
        add_group.setLayout(add_layout)
        self.layout.addWidget(add_group)

        # --- Delete Type Section ---
        delete_group = QGroupBox("Delete Custom Type")
        delete_layout = QHBoxLayout()

        self.delete_combo = QComboBox(self)
        self.delete_button = QPushButton("Delete Selected Type", self)
        self.delete_button.clicked.connect(self._emit_delete_request)

        delete_layout.addWidget(self.delete_combo)
        delete_layout.addWidget(self.delete_button)
        delete_group.setLayout(delete_layout)
        self.layout.addWidget(delete_group)

        # --- Dialog Buttons (OK/Cancel for adding) ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("Add New Type")
        self.button_box.accepted.connect(self.accept_data)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # Initial population of the delete list
        self.refresh_delete_list(custom_type_names)

    def refresh_delete_list(self, custom_type_names: list[str]):
        self.delete_combo.clear()
        self.delete_combo.addItems(custom_type_names)
        is_empty = not custom_type_names
        self.delete_combo.setEnabled(not is_empty)
        self.delete_button.setEnabled(not is_empty)
        if is_empty:
            self.delete_combo.setPlaceholderText("No custom types to delete")

    def _emit_delete_request(self):
        selected_type = self.delete_combo.currentText()
        if selected_type:
            self.delete_type_requested.emit(selected_type)

    def accept_data(self):
        type_name = self.type_name_input.text().strip()
        properties = [p.text().strip() for p in self.property_inputs if p.text().strip()]

        if not type_name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "Type Name cannot be empty to create a new type.")
            return

        if not properties:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "At least one property is required to create a new type.")
            return

        data = {"ui_name": type_name, "properties": properties}
        self.new_type_data_collected.emit(data)

        # Clear the inputs after successful emission
        self.type_name_input.clear()
        for prop_input in self.property_inputs:
            prop_input.clear()