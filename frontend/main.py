from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QWidget, QLineEdit, QLabel, QHBoxLayout,
    QComboBox, QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QMessageBox
)
from backend.inventory import get_all_components, add_component, remove_component_quantity

from faker import Faker
import random

class InventoryApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Electronics Inventory Manager")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        self.layout = QVBoxLayout()

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(6)  # Increased to 5 for part number
        self.table.setHorizontalHeaderLabels(["Part Number", "Name", "Type", "Value", "Quantity", "ID"])
        self.table.setSortingEnabled(True)  # Enable sorting by column
        self.layout.addWidget(self.table)

        # Form to add new components
        form_layout = QHBoxLayout()

        self.part_number_input = QLineEdit(self)
        self.part_number_input.setPlaceholderText("Part Number")
        form_layout.addWidget(QLabel("Part Number:"))
        form_layout.addWidget(self.part_number_input)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Component Name")
        form_layout.addWidget(QLabel("Name:"))
        form_layout.addWidget(self.name_input)

        self.type_input = QComboBox(self)  # Dropdown for component types
        # Add all possible component types
        component_types = [
            "Resistor", "Capacitor", "Inductor", "Diode", "Transistor", "LED", "Relay", "Op-Amp",
            "Voltage Regulator", "Microcontroller", "IC", "MOSFET", "Photodiode", "Switch", "Transformer",
            "Speaker", "Motor", "Heat Sink", "Connector", "Crystal Oscillator", "Buzzer", "Thermistor",
            "Varistor", "Fuse", "Sensor", "Antenna", "Breadboard", "Wire", "Battery", "Power Supply",
            "Fuse Holder", "PCB"
        ]
        self.type_input.addItems(component_types)
        form_layout.addWidget(QLabel("Type:"))
        form_layout.addWidget(self.type_input)

        self.value_input = QLineEdit(self)
        self.value_input.setPlaceholderText("Specification (e.g., 10kΩ)")
        form_layout.addWidget(QLabel("Value:"))
        form_layout.addWidget(self.value_input)

        self.quantity_input = QLineEdit(self)
        self.quantity_input.setPlaceholderText("Quantity")
        form_layout.addWidget(QLabel("Qty:"))
        form_layout.addWidget(self.quantity_input)

        self.layout.addLayout(form_layout)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()

        # Add Button
        self.add_button = QPushButton("Add Component", self)
        self.add_button.setStyleSheet("background-color: green; color: white;")
        self.add_button.clicked.connect(self.add_component_to_db)
        button_layout.addWidget(self.add_button)

        # Remove Button
        self.remove_button = QPushButton("Remove Component", self)
        self.remove_button.setStyleSheet("background-color: red; color: white;")
        self.remove_button.setEnabled(False)  # Initially disabled
        self.remove_button.clicked.connect(self.remove_component_dialog)
        button_layout.addWidget(self.remove_button)

        self.test_button = QPushButton("Generate Random Components", self)
        self.test_button.setStyleSheet("background-color: blue; color: white;")
        self.test_button.clicked.connect(self.generate_random_components)
        button_layout.addWidget(self.test_button)

        # Add the button layout to the main layout
        self.layout.addLayout(button_layout)

        # Set Main Widget
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Load existing components into the table
        self.load_data()

        self.update_remove_button_state()
        # Connect the table selection signal to enable/disable the Remove button
        self.table.selectionModel().selectionChanged.connect(self.update_remove_button_state)

    def generate_random_components(self):
        """ Generate and add 100 random components for testing. """
        fake = Faker()

        for _ in range(100):
            part_number = fake.uuid4()  # Random UUID for part number
            name = fake.word()  # Random name for component
            component_type = random.choice([
                "Resistor", "Capacitor", "Inductor", "Diode", "Transistor", "LED", "Relay", "Op-Amp",
                "Voltage Regulator", "Microcontroller", "IC", "MOSFET", "Photodiode", "Switch", "Transformer",
                "Speaker", "Motor", "Heat Sink", "Connector", "Crystal Oscillator", "Buzzer", "Thermistor",
                "Varistor", "Fuse", "Sensor", "Antenna", "Breadboard", "Wire", "Battery", "Power Supply",
                "Fuse Holder", "PCB"
            ])
            value = fake.word()  # Random specification value (e.g., "10kΩ")
            quantity = random.randint(1, 1000)  # Random quantity between 1 and 1000

            # Add this random component to the database
            success = add_component(part_number, name, component_type, value, quantity, parent=self)

            if not success:
                QMessageBox.warning(self, "Error", "Failed to add random component.")

        self.load_data()  # Refresh table with the new data

    def load_data(self):
        """ Load inventory data into the table. """
        components = get_all_components()
        self.table.setRowCount(len(components))

        for row, component in enumerate(components):
            self.table.setItem(row, 0, QTableWidgetItem(component.part_number))
            self.table.setItem(row, 1, QTableWidgetItem(component.name))
            self.table.setItem(row, 2, QTableWidgetItem(component.component_type))
            self.table.setItem(row, 3, QTableWidgetItem(component.value))
            self.table.setItem(row, 4, QTableWidgetItem(str(component.quantity)))
            self.table.setItem(row, 5, QTableWidgetItem(str(component.id)))

    def add_component_to_db(self):
        """ Add a new component from user input, allowing blank part_number and name. """
        part_number = self.part_number_input.text().strip() or None  # Allow blank
        name = self.name_input.text().strip() or None  # Allow blank
        comp_type = self.type_input.currentText().strip()
        value = self.value_input.text().strip()
        quantity_text = self.quantity_input.text().strip()

        # Ensure quantity is a valid positive integer
        if not quantity_text.isdigit() or int(quantity_text) <= 0:
            QMessageBox.warning(self, "Invalid Quantity", "Quantity must be a positive number.")
            return

        quantity = int(quantity_text)

        # Ensure required fields are filled
        if not comp_type or not value:
            QMessageBox.warning(self, "Invalid Input", "Component Type and Value must be filled.")
            return

        # Add component to database (allows blank part_number and name)
        success = add_component(part_number, name, comp_type, value, quantity, parent=self)

        if success:
            self.load_data()  # Refresh table
            self.part_number_input.clear()
            self.name_input.clear()
            self.type_input.setCurrentIndex(0)  # Reset dropdown to first option
            self.value_input.clear()
            self.quantity_input.clear()
        else:
            QMessageBox.warning(self, "Database Error", "Failed to add the component.")

    def remove_component_dialog(self):
        """ Open a dialog to remove components. """
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            # Fetch part number and name from the selected row (even if empty)
            part_number_item = self.table.item(selected_row, 0)
            component_name_item = self.table.item(selected_row, 1)

            # Allow empty part number and name, but handle missing names gracefully
            part_number = part_number_item.text() if part_number_item else "Unknown Part Number"
            component_name = component_name_item.text() if component_name_item else "Unnamed Component"

            quantity_available = int(
                self.table.item(selected_row, 4).text())  # Get available quantity from the selected row

            # Open a dialog to choose how many components to remove
            dialog = RemoveComponentDialog(part_number, component_name, quantity_available, self)
            dialog.exec_()

        else:
            QMessageBox.warning(self, "Selection Error", "Please select a component to remove.")

    def update_remove_button_state(self):
        """ Enable or disable the remove button based on selection. """
        if self.table.selectionModel().hasSelection():
            self.remove_button.setEnabled(True)
            self.remove_button.setStyleSheet("background-color: red; color: white;")  # Red when enabled
        else:
            self.remove_button.setEnabled(False)
            self.remove_button.setStyleSheet("background-color: rgba(128, 128, 128, 0.5); color: white;")  # Gray when disabled

    def update_after_removal(self):
        """ Reload the data after a component is removed. """
        self.load_data()


class RemoveComponentDialog(QDialog):
    def __init__(self, part_number, component_name, quantity_available, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Remove Components - {component_name}")

        self.part_number = part_number
        self.quantity_available = quantity_available

        # Form layout for the dialog
        layout = QFormLayout()

        # Quantity input field for removing components
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(quantity_available)
        self.quantity_input.setValue(1)
        layout.addRow("Quantity to Remove:", self.quantity_input)

        # Buttons (OK, Cancel)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.remove_component)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def remove_component(self):
        """ Remove the component from the inventory. """
        quantity_to_remove = self.quantity_input.value()

        if quantity_to_remove <= self.quantity_available:
            # Perform the actual removal from the backend (remove quantity)
            success = remove_component_quantity(self.part_number, quantity_to_remove)
            if success:
                self.parent().update_after_removal()  # Refresh the data in the main window
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove component.")
        else:
            # Display a warning if the removal quantity exceeds available quantity
            QMessageBox.warning(self, "Invalid Quantity",
                                f"You cannot remove more than {self.quantity_available} components.")


if __name__ == "__main__":
    app = QApplication([])
    window = InventoryApp()
    window.show()
    app.exec_()
