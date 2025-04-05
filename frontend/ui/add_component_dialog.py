from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QLabel, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import pyqtSignal

class AddComponentDialog(QDialog):
    """ Popup dialog for adding a new component. UI only. """
    # Signal emitted when the user clicks OK and basic validation passes
    # Returns the collected data as a dictionary
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
        # Mapping for controller/backend use
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
        # --- End Component Types ---

        self.type_input = QComboBox(self)
        self.type_input.addItems(self.component_types.keys())
        self.type_input.currentTextChanged.connect(self.update_fields)
        self.form_layout.addRow("Type:", self.type_input)

        self.part_number_input = QLineEdit(self)
        self.form_layout.addRow("Part Number:", self.part_number_input)

        self.name_input = QLineEdit(self)
        self.form_layout.addRow("Name:", self.name_input)

        self.dynamic_fields = {}
        self._create_dynamic_fields() # Initial population

        self.quantity_input = QSpinBox(self)
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(1)
        self.form_layout.addRow("Quantity:", self.quantity_input)

        self.purchase_link_input = QLineEdit(self)
        self.form_layout.addRow("Purchase Link:", self.purchase_link_input)

        self.datasheet_link_input = QLineEdit(self)
        self.form_layout.addRow("Datasheet Link:", self.datasheet_link_input)

        self.layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.handle_accept) # Connect to custom handler
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def update_fields(self):
        """ Remove old dynamic fields and add new ones based on type selection. """
        self._clear_dynamic_fields()
        self._create_dynamic_fields()

    def _clear_dynamic_fields(self):
        """ Helper to remove dynamic fields from layout and clear dict. """
        for label, input_field in self.dynamic_fields.values():
            self.form_layout.removeWidget(label)
            self.form_layout.removeWidget(input_field)
            label.deleteLater()
            input_field.deleteLater()
        self.dynamic_fields.clear()

    def _create_dynamic_fields(self):
        """ Helper to create and add dynamic fields to the layout. """
        selected_type = self.type_input.currentText()
        fields = self.component_types.get(selected_type, [])

        # Find insert position (after Name field)
        # Note: QFormLayout row indices are complex; inserting by index can be tricky.
        # A simpler way for this case is to add them sequentially and let update_fields manage removal/re-addition.
        # We'll insert *before* the quantity field.
        quantity_row_index = self.form_layout.rowCount() - 3 # Quantity, Purch Link, Data Link

        for field_name in fields:
            label = QLabel(field_name)
            input_field = QLineEdit(self)
            # Insert before the quantity row
            self.form_layout.insertRow(quantity_row_index, label, input_field)
            self.dynamic_fields[field_name] = (label, input_field)
            quantity_row_index += 1 # Adjust index for next insertion


    def validate_inputs(self):
        """ Basic UI validation for required fields. Returns True if valid, False otherwise. """
        part_number = self.part_number_input.text().strip()
        name = self.name_input.text().strip()

        if not part_number:
            QMessageBox.warning(self, "Input Error", "Part number is required.")
            return False
        if not name:
            QMessageBox.warning(self, "Input Error", "Name is required.")
            return False

        # Validate dynamic fields (ensure they are not empty)
        for field_name, (_, input_field) in self.dynamic_fields.items():
            value = input_field.text().strip()
            if not value:
                QMessageBox.warning(self, "Input Error", f"'{field_name}' is required.")
                return False
        return True

    def get_component_data(self):
        """ Collect and return all component data as a dictionary. """
        dynamic_values = []
        for field_name, (_, input_field) in self.dynamic_fields.items():
            value = input_field.text().strip()
            dynamic_values.append(f"{field_name}: {value}")

        return {
            'part_number': self.part_number_input.text().strip(),
            'name': self.name_input.text().strip(),
            # Send the backend-friendly type name
            'component_type': self.ui_to_backend_name_mapping[self.type_input.currentText()],
            'value': ", ".join(dynamic_values),
            'quantity': self.quantity_input.value(),
            'purchase_link': self.purchase_link_input.text().strip(),
            'datasheet_link': self.datasheet_link_input.text().strip()
        }

    def handle_accept(self):
        """ Validate inputs before accepting and emitting the signal. """
        if self.validate_inputs():
            component_data = self.get_component_data()
            self.component_data_collected.emit(component_data)
            self.accept() # Close the dialog successfully
        # Else: validation failed, message shown, dialog stays open.