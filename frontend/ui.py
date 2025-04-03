from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QVBoxLayout, QWidget, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QSpinBox, QDialogButtonBox, QLabel, QHBoxLayout, QInputDialog, QFileDialog
)

from PyQt5.QtGui import QColor, QDesktopServices
from PyQt5.QtCore import QUrl, Qt, pyqtSignal

from backend.inventory import get_all_components, add_component, remove_component_by_part_number, remove_component_quantity, import_components_from_txt

class InventoryUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Electronics Inventory Manager")
        self.setGeometry(100, 100, 800, 600)

        # Main vertical layout
        self.layout = QVBoxLayout()

        # 🔹 Button layout (TOP)
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Component", self)
        self.add_button.clicked.connect(self.open_add_component_dialog)
        button_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove Component", self)
        self.remove_button.setEnabled(False)  # Initially disabled
        self.remove_button.clicked.connect(self.remove_selected_component)
        button_layout.addWidget(self.remove_button)

        self.export_button = QPushButton("Export to TXT")
        self.export_button.clicked.connect(self.export_to_txt)
        self.layout.addWidget(self.export_button)

        self.import_button = QPushButton("Import from TXT")
        self.import_button.clicked.connect(self.import_from_txt)
        self.layout.addWidget(self.import_button)

        # Add button layout FIRST
        self.layout.addLayout(button_layout)

        # 🔹 Table (BOTTOM)
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)  # Added columns for links
        self.table.setHorizontalHeaderLabels([
            "Part Number", "Name", "Type", "Value", "Quantity", "Purchase Link", "Datasheet"
        ])
        self.layout.addWidget(self.table)  # Table BELOW the buttons

        # Set the layout to the main container
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        self.table.setSortingEnabled(True)
        self.load_data()  # Load inventory data on startup

        # Detect row selection to enable/disable the remove button
        self.table.selectionModel().selectionChanged.connect(self.update_remove_button_state)

    def load_data(self):
        """ Load inventory data into the table. """
        components = get_all_components()
        self.table.setRowCount(len(components))
        self.table.setColumnCount(7)  # Added two columns for links
        self.table.setHorizontalHeaderLabels([
            "Part Number", "Name", "Type", "Value", "Quantity", "Purchase Link", "Datasheet"
        ])

        for row, component in enumerate(components):
            self.table.setItem(row, 0, QTableWidgetItem(component.part_number or ""))
            self.table.setItem(row, 1, QTableWidgetItem(component.name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(component.component_type))
            self.table.setItem(row, 3, QTableWidgetItem(component.value))
            self.table.setItem(row, 4, QTableWidgetItem(str(component.quantity)))

            # Clickable Purchase Link
            if component.purchase_link:
                purchase_item = QTableWidgetItem("Link")
                purchase_item.setForeground(QColor("blue"))  # Set text color to blue
                purchase_item.setTextAlignment(Qt.AlignCenter)  # Center the text
                purchase_item.setData(Qt.UserRole, QUrl(component.purchase_link))  # Store the URL
                self.table.setItem(row, 5, purchase_item)

                # Clickable Datasheet Link
            if component.datasheet_link:
                datasheet_item = QTableWidgetItem("Link")
                datasheet_item.setForeground(QColor("blue"))  # Set text color to blue
                datasheet_item.setTextAlignment(Qt.AlignCenter)
                datasheet_item.setData(Qt.UserRole, QUrl(component.datasheet_link))
                self.table.setItem(row, 6, datasheet_item)

            try:
                self.table.cellClicked.disconnect(self.open_link)
            except TypeError:
                pass  # No existing connection

            self.table.cellClicked.connect(self.open_link) # Handle clicks

    def open_link(self, row, column):
        """ Opens the link only once when clicked. """
        if column in [5, 6]:  # Only trigger for Purchase & Datasheet link columns
            item = self.table.item(row, column)
            if item:
                link = item.data(Qt.UserRole)  # Retrieve the stored URL
                if link and isinstance(link, QUrl):  # Ensure it's a valid URL
                    QDesktopServices.openUrl(link)

    def update_remove_button_state(self):
        """ Enable the remove button only if a row is selected. """
        if self.table.selectionModel().hasSelection():
            self.remove_button.setEnabled(True)
        else:
            self.remove_button.setEnabled(False)

    def open_add_component_dialog(self):
        """ Opens the Add Component popup window. """
        dialog = AddComponentDialog(self)
        if dialog.exec_():  # If the dialog is successfully closed with "OK"
            self.load_data()  # Refresh the table with new data

    def remove_selected_component(self):
        """ Removes a selected quantity of the component from the database. """
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a component to remove.")
            return

        part_number_item = self.table.item(selected_row, 0)  # Get part number
        quantity_item = self.table.item(selected_row, 4)  # Get current quantity

        if not part_number_item or not quantity_item:
            QMessageBox.warning(self, "Error", "Could not retrieve the selected component.")
            return

        part_number = part_number_item.text()
        current_quantity = int(quantity_item.text())  # Get existing quantity

        # Get user input for how many to remove
        quantity_to_remove, ok = QInputDialog.getInt(self, "Remove Quantity",
                                                     f"Available: {current_quantity} units\nEnter quantity to remove:",
                                                     min=1, max=current_quantity)

        if not ok or quantity_to_remove <= 0:
            return  # User canceled or entered an invalid value

        # Confirm deletion
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to remove {quantity_to_remove} units of '{part_number}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            success = remove_component_quantity(part_number, quantity_to_remove, parent=self)
            if success:
                self.load_data()  # Refresh table after removal
            else:
                QMessageBox.warning(self, "Database Error", "Failed to remove the component.")

    def export_to_txt(self):
        """ Export components from database to a TXT file. """
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt)")

        if file_path:  # If user selected a file path
            from backend.inventory import export_components_to_txt
            success = export_components_to_txt(file_path)
            if success:
                QMessageBox.information(self, "Export Successful", f"Data exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Could not export data.")

    def import_from_txt(self):
        """ Import components from a TXT file into the database. """
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt)")

        if file_path:  # If user selected a file
            success, message = import_components_from_txt(file_path)
            if success:
                QMessageBox.information(self, "Import Successful", message)
                self.load_data()  # Refresh table
            else:
                QMessageBox.warning(self, "Import Failed", message)

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

        self.ui_to_backend_name_mapping = {
            "Resistor": "resistor",
            "Capacitor": "capacitor",
            "Inductor": "inductor",
            "Diode": "diode",
            "Transistor": "transistor",
            "LED": "led",
            "Relay": "relay",
            "Op-Amp": "op_amp",
            "Voltage Regulator": "voltage_regulator",
            "Microcontroller": "microcontroller",
            "IC": "ic",
            "MOSFET": "mosfet",
            "Photodiode": "photodiode",
            "Switch": "switch",
            "Transformer": "transformer",
            "Speaker": "speaker",
            "Motor": "motor",
            "Heat Sink": "heat_sink",
            "Connector": "connector",
            "Crystal Oscillator": "crystal_oscillator",
            "Buzzer": "buzzer",
            "Thermistor": "thermistor",
            "Varistor": "varistor",
            "Fuse": "fuse",
            "Sensor": "sensor",
            "Antenna": "antenna",
            "Breadboard": "breadboard",
            "Wire": "wire",
            "Battery": "battery",
            "Power Supply": "power_supply"
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

        self.quantity_input = QSpinBox(self)
        self.quantity_input.setRange(1, 10000)  # Allow selecting up to 10,000 units
        self.quantity_input.setValue(1)  # Default to 1
        self.form_layout.addRow("Quantity:", self.quantity_input)

        self.purchase_link_input = QLineEdit(self)
        self.form_layout.addRow("Purchase Link:", self.purchase_link_input)

        # Datasheet Link
        self.datasheet_link_input = QLineEdit(self)
        self.form_layout.addRow("Datasheet Link:", self.datasheet_link_input)

        # OK & Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.add_component)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def update_fields(self):
        """ Update input fields dynamically based on selected component type. """

        # 🔹 Remove existing dynamic fields without affecting other fields
        for label, input_field in self.dynamic_fields.values():
            self.form_layout.removeRow(label)

        self.dynamic_fields.clear()

        # 🔹 Get selected component type and its fields
        selected_type = self.type_input.currentText()
        fields = self.component_types.get(selected_type, [])

        # 🔹 Find the correct position (right after Name field)
        name_field_index = 2  # "Type" is row 0, "Part Number" is row 1, "Name" is row 2
        insert_position = name_field_index + 1  # Add dynamic fields right after Name

        # 🔹 Create and insert new dynamic fields at the correct position
        for field_name in fields:
            label = QLabel(field_name)
            input_field = QLineEdit(self)
            self.form_layout.insertRow(insert_position, label, input_field)
            self.dynamic_fields[field_name] = (label, input_field)
            insert_position += 1  # Move index forward for the next field

    def add_component(self):
        """ Collects input data and adds the component to the database """
        part_number = self.part_number_input.text().strip() or None
        name = self.name_input.text().strip() or None
        comp_type = self.ui_to_backend_name_mapping[self.type_input.currentText()]
        quantity = self.quantity_input.value()  # Default quantity
        purchase_link = self.purchase_link_input.text().strip() or None
        datasheet_link = self.datasheet_link_input.text().strip() or None

        # Collect dynamic input values
        values = []
        for field_name, (_, input_field) in self.dynamic_fields.items():
            value = input_field.text().strip()
            values.append(f"{field_name}: {value}")

        value_str = ", ".join(values)  # Combine values into a single string

        success = add_component(part_number, name, comp_type, value_str, quantity, purchase_link, datasheet_link, parent=self)

        if success:
            self.accept()  # Close the popup if adding is successful
        else:
            QMessageBox.warning(self, "Database Error", "Failed to add the component.")
