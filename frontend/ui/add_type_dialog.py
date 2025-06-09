from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QHBoxLayout, QPushButton, QFrame
)
from PyQt5.QtCore import pyqtSignal


class AddTypeDialog(QDialog):
    new_type_data_collected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Component Type")
        self.setMinimumWidth(400)

        # Main layout
        self.layout = QVBoxLayout(self)

        # Form for inputs
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(10)

        # Type Name
        self.type_name_input = QLineEdit(self)
        self.type_name_input.setPlaceholderText("e.g., Potentiometer, Sensor Array")
        self.form_layout.addRow(QLabel("New Type Name:"), self.type_name_input)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(separator)

        # Properties section
        properties_layout = QVBoxLayout()
        properties_label = QLabel("Define up to 4 properties for this type:")
        properties_label.setStyleSheet("font-weight: bold;")
        properties_layout.addWidget(properties_label)

        self.properties_form_layout = QFormLayout()
        self.property_inputs = []
        for i in range(4):
            placeholder = f"e.g., Resistance (Ω), Taper" if i == 0 else "Optional property"
            prop_input = QLineEdit(self)
            prop_input.setPlaceholderText(placeholder)
            self.properties_form_layout.addRow(QLabel(f"Property {i + 1}:"), prop_input)
            self.property_inputs.append(prop_input)

        properties_layout.addLayout(self.properties_form_layout)
        self.layout.addLayout(properties_layout)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_data)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def accept_data(self):
        type_name = self.type_name_input.text().strip()

        properties = []
        for prop_input in self.property_inputs:
            prop_text = prop_input.text().strip()
            if prop_text:
                properties.append(prop_text)

        if not type_name:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "Type Name cannot be empty.")
            return

        if not properties:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "At least one property is required.")
            return

        data = {
            "ui_name": type_name,
            "properties": properties
        }
        self.new_type_data_collected.emit(data)
        self.accept()