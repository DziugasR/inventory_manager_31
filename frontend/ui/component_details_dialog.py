import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QSpinBox, QGroupBox, QTextEdit,
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from backend.models import Component


class ComponentDetailsDialog(QDialog):
    image_change_requested = pyqtSignal(str)

    def __init__(self, component: Component, properties: list[str], app_path: str, parent=None):
        super().__init__(parent)
        self.component = component
        self.properties = properties
        self.app_path = app_path
        self.property_inputs = {}

        self.setWindowTitle("Component Details")
        self.setMinimumWidth(500)
        self._init_ui()
        self._populate_data()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)

        image_group = QGroupBox("Image")
        image_layout = QHBoxLayout(image_group)
        self.image_label = QLabel("No Image")
        self.image_label.setFixedSize(150, 150)
        self.image_label.setStyleSheet("border: 1px solid grey;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        change_image_button = QPushButton("Change Image...")
        change_image_button.clicked.connect(lambda: self.image_change_requested.emit(str(self.component.id)))
        image_layout.addWidget(self.image_label)
        image_layout.addWidget(change_image_button, 1, Qt.AlignTop)

        main_group = QGroupBox("Main Information")
        main_layout = QFormLayout(main_group)
        self.part_number_input = QLineEdit()
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 999999)
        self.location_input = QLineEdit()
        main_layout.addRow(QLabel("Part Number:"), self.part_number_input)
        main_layout.addRow(QLabel("Quantity:"), self.quantity_input)
        main_layout.addRow(QLabel("Location:"), self.location_input)

        props_group = QGroupBox("Properties")
        self.props_layout = QFormLayout(props_group)
        for prop_name in self.properties:
            prop_input = QLineEdit()
            self.props_layout.addRow(QLabel(f"{prop_name}:"), prop_input)
            self.property_inputs[prop_name] = prop_input

        links_group = QGroupBox("Links")
        links_layout = QFormLayout(links_group)
        self.purchase_link_input = QLineEdit()
        self.datasheet_link_input = QLineEdit()
        links_layout.addRow(QLabel("Purchase Link:"), self.purchase_link_input)
        links_layout.addRow(QLabel("Datasheet Link:"), self.datasheet_link_input)

        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_input = QTextEdit()
        notes_layout.addWidget(self.notes_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.layout.addWidget(image_group)
        self.layout.addWidget(main_group)
        self.layout.addWidget(props_group)
        self.layout.addWidget(links_group)
        self.layout.addWidget(notes_group)
        self.layout.addWidget(button_box)

    def _parse_value_string(self) -> dict:
        parsed = {}
        if not self.component.value: return parsed
        for pair in self.component.value.split(','):
            if ':' in pair:
                key, val = pair.split(':', 1)
                parsed[key.strip()] = val.strip()
        return parsed

    def _populate_data(self):
        if self.component.image_path and (
        full_path := os.path.join(self.app_path, self.component.image_path)) and os.path.exists(full_path):
            self.image_label.setPixmap(QPixmap(full_path))
        else:
            self.image_label.setText("No Image")

        self.part_number_input.setText(self.component.part_number)
        self.quantity_input.setValue(self.component.quantity)
        self.location_input.setText(self.component.location or "")
        self.purchase_link_input.setText(self.component.purchase_link or "")
        self.datasheet_link_input.setText(self.component.datasheet_link or "")
        self.notes_input.setPlainText(self.component.notes or "")

        value_data = self._parse_value_string()
        for prop_name, prop_input in self.property_inputs.items():
            matching_key = next((k for k in value_data if prop_name.startswith(k)), None)
            if matching_key:
                prop_input.setText(value_data.get(matching_key, ""))

    def get_data(self) -> dict:
        value_parts = [f"{prop_name}: {prop_input.text().strip()}" for prop_name, prop_input in
                       self.property_inputs.items()]
        return {
            "part_number": self.part_number_input.text().strip(),
            "quantity": self.quantity_input.value(),
            "location": self.location_input.text().strip(),
            "purchase_link": self.purchase_link_input.text().strip(),
            "datasheet_link": self.datasheet_link_input.text().strip(),
            "value": ", ".join(value_parts),
            "notes": self.notes_input.toPlainText().strip()
        }