from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QWidget, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QSpinBox, QDialogButtonBox, QLabel
)
from backend.inventory import get_all_components, add_component

class InventoryUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Electronics Inventory Manager")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        # Table to display components
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)  # No "ID" column
        self.table.setHorizontalHeaderLabels(["Part Number", "Name", "Type", "Value", "Quantity"])
        self.layout.addWidget(self.table)

        # Button to open popup for adding components
        self.add_button = QPushButton("Add Component", self)
        self.add_button.clicked.connect(self.open_add_component_dialog)
        self.layout.addWidget(self.add_button)

        # Set the main layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.load_data()  # Load inventory data on startup

    def load_data(self):
        """ Load inventory data into the table. """
        components = get_all_components()
        self.table.setRowCount(len(components))

        for row, component in enumerate(components):
            self.table.setItem(row, 0, QTableWidgetItem(component.part_number or ""))
            self.table.setItem(row, 1, QTableWidgetItem(component.name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(component.component_type))
            self.table.setItem(row, 3, QTableWidgetItem(component.value))
            self.table.setItem(row, 4, QTableWidgetItem(str(component.quantity)))

    def open_add_component_dialog(self):
        """ Opens the Add Component popup window. """
        dialog = AddComponentDialog(self)
        if dialog.exec_():  # If the dialog is successfully closed with "OK"
            self.load_data()  # Refresh the table with new data


class AddComponentDialog(QDialog):
    """ Popup dialog for adding a new component """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Component")

        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.type_input = QComboBox(self)
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

        self.type_input.addItems(self.component_types.keys())
        self.type_input.currentTextChanged.connect(self.update_fields)  # Update fields on selection change
        self.form_layout.addRow("Type:", self.type_input)

        # Input fields
        self.part_number_input = QLineEdit(self)
        self.form_layout.addRow("Part Number:", self.part_number_input)

        self.name_input = QLineEdit(self)
        self.form_layout.addRow("Name:", self.name_input)

        self.dynamic_fields = {}  # Dictionary to hold dynamically changing input fields
        self.update_fields()  # Initialize with the first component type

        self.layout.addLayout(self.form_layout)

        # OK & Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.add_component)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def update_fields(self):
        """ Update input fields dynamically based on selected component type. """
        # Remove existing dynamic fields
        for label, input_field in self.dynamic_fields.values():
            self.form_layout.removeRow(label)

        self.dynamic_fields.clear()

        # Get the selected component type
        selected_type = self.type_input.currentText()
        fields = self.component_types.get(selected_type, [])

        # Create new dynamic fields
        for field_name in fields:
            label = QLabel(field_name)
            input_field = QLineEdit(self)
            self.form_layout.addRow(label, input_field)
            self.dynamic_fields[field_name] = (label, input_field)

    def add_component(self):
        """ Collects input data and adds the component to the database """
        part_number = self.part_number_input.text().strip() or None
        name = self.name_input.text().strip() or None
        comp_type = self.type_input.currentText().strip()
        quantity = 1  # Default quantity

        # Collect dynamic input values
        values = []
        for field_name, (_, input_field) in self.dynamic_fields.items():
            value = input_field.text().strip()
            values.append(f"{field_name}: {value}")

        value_str = ", ".join(values)  # Combine values into a single string

        success = add_component(part_number, name, comp_type, value_str, quantity, parent=self)

        if success:
            self.accept()  # Close the popup if adding is successful
        else:
            QMessageBox.warning(self, "Database Error", "Failed to add the component.")
