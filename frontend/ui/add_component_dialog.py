from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QLabel, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import pyqtSignal

class AddComponentDialog(QDialog):
    component_data_collected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Component")
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # --- Component Types (UI definition remains) ---
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
        # TODO Mapping for controller/backend use i kita faila krc
        self.ui_to_backend_name_mapping = {
            "Resistor": "resistor", "Capacitor": "capacitor", "Inductor": "inductor",
            "Diode": "diode", "Transistor": "transistor", "LED": "led", "Relay": "relay",
            "Op-Amp": "op_amp", "Voltage Regulator": "voltage_regulator",
            "Microcontroller": "microcontroller", "IC": "ic", "MOSFET": "mosfet",
            "Photodiode": "photodiode", "Switch": "switch", "Transformer": "transformer",
            "Speaker": "speaker", "Motor": "motor", "Heat Sink": "heat_sink",
            "Connector": "connector", "Crystal Oscillator": "crystal_oscillator",
            "Buzzer": "buzzer", "Thermistor": "thermistor", "Varistor": "varistor",
            "Fuse": "fuse", "Sensor": "sensor", "Antenna": "antenna",
            "Breadboard": "breadboard", "Wire": "wire", "Battery": "battery",
            "Power Supply": "power_supply"
        }

        self.type_input = QComboBox(self)
        self.type_input.addItems(self.component_types.keys())
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

        self._create_dynamic_fields()  # Initial population

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

        quantity_row_index = self.form_layout.rowCount() - 3

        for field_name in fields:
            label = QLabel(field_name)
            input_field = QLineEdit(self)
            self.form_layout.insertRow(quantity_row_index, label, input_field)
            self.dynamic_fields[field_name] = (label, input_field)
            quantity_row_index += 1

    def validate_inputs(self):
        part_number = self.part_number_input.text().strip()

        if not part_number:
            QMessageBox.warning(self, "Input Error", "Part number is required.")
            return False

        primary_value_field_name = None
        if fields := self.component_types.get(self.type_input.currentText()):
            primary_value_field_name = fields[0]

        for field_name, (_, input_field) in self.dynamic_fields.items():
            value = input_field.text().strip()

            if field_name == primary_value_field_name and not value:
                QMessageBox.warning(self, "Input Error", f"Primary value '{field_name}' is required.")
                return False
        return True

    def get_component_data(self):

        dynamic_values = []
        for field_name, (_, input_field) in self.dynamic_fields.items():
            value = input_field.text().strip()
            dynamic_values.append(f"{field_name}: {value}")

        return {
            'part_number': self.part_number_input.text().strip(),
            'component_type': self.ui_to_backend_name_mapping[self.type_input.currentText()],
            'value': ", ".join(dynamic_values),
            'quantity': self.quantity_input.value(),
            'purchase_link': self.purchase_link_input.text().strip(),
            'datasheet_link': self.datasheet_link_input.text().strip()
        }

    def handle_accept(self):
        if self.validate_inputs():
            component_data = self.get_component_data()
            self.component_data_collected.emit(component_data)
            self.accept()