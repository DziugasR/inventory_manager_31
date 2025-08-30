from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QLabel, QSpinBox, QGroupBox, QTextEdit
)
from backend.models import Component


class ComponentDetailsDialog(QDialog):
    def __init__(self, component: Component, properties: list[str], parent=None):
        super().__init__(parent)
        self.component = component
        self.properties = properties
        self.property_inputs = {}

        self.setWindowTitle("Component Details")
        self.setMinimumWidth(450)
        self._init_ui()
        self._populate_data()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Standard Fields ---
        main_group = QGroupBox("Main Information")
        main_layout = QFormLayout(main_group)
        self.part_number_input = QLineEdit()
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 999999)
        self.location_input = QLineEdit()
        main_layout.addRow(QLabel("Part Number:"), self.part_number_input)
        main_layout.addRow(QLabel("Quantity:"), self.quantity_input)
        main_layout.addRow(QLabel("Location:"), self.location_input)

        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_input = QTextEdit()
        notes_layout.addWidget(self.notes_input)

        # --- Dynamic Property Fields ---
        props_group = QGroupBox("Properties")
        self.props_layout = QFormLayout(props_group)
        for prop_name in self.properties:
            prop_input = QLineEdit()
            self.props_layout.addRow(QLabel(f"{prop_name}:"), prop_input)
            self.property_inputs[prop_name] = prop_input  # Store for later retrieval

        # --- Link Fields ---
        links_group = QGroupBox("Links")
        links_layout = QFormLayout(links_group)
        self.purchase_link_input = QLineEdit()
        self.datasheet_link_input = QLineEdit()
        links_layout.addRow(QLabel("Purchase Link:"), self.purchase_link_input)
        links_layout.addRow(QLabel("Datasheet Link:"), self.datasheet_link_input)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.layout.addWidget(main_group)
        self.layout.addWidget(props_group)
        self.layout.addWidget(links_group)
        self.layout.addWidget(notes_group)
        self.layout.addWidget(button_box)

    def _parse_value_string(self) -> dict:
        """Parses 'Prop1: Val1, Prop2: Val2' into a dictionary."""
        parsed = {}
        if not self.component.value:
            return parsed

        pairs = self.component.value.split(',')
        for pair in pairs:
            if ':' in pair:
                key, val = pair.split(':', 1)
                parsed[key.strip()] = val.strip()
        return parsed

    def _populate_data(self):
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
        """Constructs the data dictionary to be saved."""
        value_parts = []
        for prop_name, prop_input in self.property_inputs.items():
            value_parts.append(f"{prop_name}: {prop_input.text().strip()}")

        return {
            "part_number": self.part_number_input.text().strip(),
            "quantity": self.quantity_input.value(),
            "location": self.location_input.text().strip(),
            "purchase_link": self.purchase_link_input.text().strip(),
            "datasheet_link": self.datasheet_link_input.text().strip(),
            "value": ", ".join(value_parts),
            "notes": self.notes_input.toPlainText().strip()
        }