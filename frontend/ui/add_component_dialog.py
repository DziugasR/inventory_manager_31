from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QLabel, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import pyqtSignal

from backend.component_constants import UI_TYPE_NAMES, UI_TO_BACKEND_TYPE_MAP
from backend.exceptions import InvalidInputError


class AddComponentDialog(QDialog):
    component_data_collected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Component")

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.component_types = {
            "Resistor": ["Resistance (Ω)", "Tolerance (%)"],
            "Capacitor": ["Capacitance (µF)", "Voltage (V)"],
            "Inductor": ["Inductance (H)", "Current Rating (A)"],
            "Diode": ["Forward Voltage (V)", "Current Rating (A)"],
            "Transistor": ["Gain (hFE)", "Voltage Rating (V)"],
            "LED": ["Wavelength (nm)", "Luminous Intensity (mcd)"],
            "Relay": ["Coil Voltage (V)", "Contact Rating (A)"],
            "Op-Amp": ["Gain Bandwidth (Hz)", "Slew Rate (V/µs)"],
            "Voltage Regulator": ["Output Voltage (V)", "Current Rating (A)"],
            "Microcontroller": ["Architecture", "Flash Memory (KB)"],
            "IC": ["Number of Pins", "Function"],
            "MOSFET": ["Drain-Source Voltage (V)", "Rds(on) (Ω)"],
            "Photodiode": ["Wavelength Range (nm)", "Sensitivity (A/W)"],
            "Switch": ["Current Rating (A)", "Number of Positions"],
            "Transformer": ["Primary Voltage (V)", "Secondary Voltage (V)"],
            "Speaker": ["Impedance (Ω)", "Power Rating (W)"],
            "Motor": ["Voltage (V)", "RPM"],
            "Heat Sink": ["Thermal Resistance (°C/W)", "Size (mm)"],
            "Connector": ["Number of Pins", "Pitch (mm)"],
            "Crystal Oscillator": ["Frequency (MHz)", "Load Capacitance (pF)"],
            "Buzzer": ["Operating Voltage (V)", "Sound Level (dB)"],
            "Thermistor": ["Resistance at 25°C (Ω)", "Beta Value (K)"],
            "Varistor": ["Voltage Rating (V)", "Clamping Voltage (V)"],
            "Fuse": ["Current Rating (A)", "Voltage Rating (V)"],
            "Sensor": ["Type", "Output Signal"],
            "Antenna": ["Frequency Range (MHz)", "Gain (dBi)"],
            "Breadboard": ["Size (mm)", "Number of Tie Points"],
            "Wire": ["Gauge (AWG)", "Length (m)"],
            "Battery": ["Voltage (V)", "Capacity (mAh)"],
            "Power Supply": ["Output Voltage (V)", "Output Current (A)"]
        }

        self.type_input = QComboBox(self)

        self.type_input.addItems(UI_TYPE_NAMES)
        self.type_input.currentTextChanged.connect(self.update_fields)
        self.form_layout.addRow("Type:", self.type_input)

        self.part_number_input = QLineEdit(self)
        self.form_layout.addRow("Part Number:", self.part_number_input)

        self.dynamic_fields = {}

        self.quantity_input = QSpinBox(self)
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(1)
        self.form_layout.addRow("Quantity:", self.quantity_input)

        self.purchase_link_input = QLineEdit(self)
        self.form_layout.addRow("Purchase Link:", self.purchase_link_input)

        self.datasheet_link_input = QLineEdit(self)
        self.form_layout.addRow("Datasheet Link:", self.datasheet_link_input)

        self._create_dynamic_fields()

        self.layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.handle_accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def update_fields(self):
        self._clear_dynamic_fields()
        self._create_dynamic_fields()

    def _clear_dynamic_fields(self):
        for label, input_field in self.dynamic_fields.values():
            self.form_layout.removeWidget(label)
            self.form_layout.removeWidget(input_field)
            label.deleteLater()
            input_field.deleteLater()
        self.dynamic_fields.clear()

    def _create_dynamic_fields(self):
        selected_type = self.type_input.currentText()
        fields = self.component_types.get(selected_type, [])

        quantity_row_index = -1
        for i in range(self.form_layout.rowCount()):
            label_item = self.form_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item and isinstance(label_item.widget(), QLabel) and label_item.widget().text() == "Quantity:":
                quantity_row_index = i
                break

        insert_position = quantity_row_index if quantity_row_index != -1 else self.form_layout.rowCount() - 2

        for field_name in reversed(fields):
            label = QLabel(field_name)
            input_field = QLineEdit(self)
            self.form_layout.insertRow(insert_position, label, input_field)
            self.dynamic_fields[field_name] = (label, input_field)

    def validate_inputs(self):
        part_number = self.part_number_input.text().strip()
        if not part_number:
            QMessageBox.warning(self, "Input Error", "Part number is required.")
            return False

        selected_type = self.type_input.currentText()
        fields_for_type = self.component_types.get(selected_type, [])
        primary_value_field_name = fields_for_type[0] if fields_for_type else None

        for field_name, (_, input_field) in self.dynamic_fields.items():
            value = input_field.text().strip()
            if field_name == primary_value_field_name and not value:
                QMessageBox.warning(self, "Input Error",
                                    f"Primary value '{field_name}' is required for {selected_type}.")
                return False

        return True

    def get_component_data(self):
        selected_ui_type = self.type_input.currentText()
        backend_type_id = UI_TO_BACKEND_TYPE_MAP.get(selected_ui_type)

        if backend_type_id is None:
            QMessageBox.critical(self, "Internal Error",
                                 f"Could not map component type '{selected_ui_type}' to a backend identifier.")
            raise InvalidInputError(f"Internal error mapping type: {selected_ui_type}")

        dynamic_values = []
        for field_name, (_, input_field) in self.dynamic_fields.items():
            value = input_field.text().strip()
            if value:
                dynamic_values.append(f"{field_name}: {value}")

        value_str = ", ".join(dynamic_values)

        return {
            'part_number': self.part_number_input.text().strip(),
            'component_type': backend_type_id,
            'value': value_str,
            'quantity': self.quantity_input.value(),
            'purchase_link': self.purchase_link_input.text().strip(),
            'datasheet_link': self.datasheet_link_input.text().strip()
        }

    def handle_accept(self):
        if self.validate_inputs():
            try:
                component_data = self.get_component_data()
                self.component_data_collected.emit(component_data)
                self.accept()
            except InvalidInputError as e:
                print(f"Error collecting component data: {e}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred while gathering data: {e}")
                print(f"Unexpected error in handle_accept: {e}")
