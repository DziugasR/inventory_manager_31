from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QLabel, QVBoxLayout, QMessageBox, QPushButton, QHBoxLayout, QTextEdit
)
from PyQt5.QtCore import pyqtSignal, QObject
from backend.type_manager import type_manager
from backend.exceptions import InvalidInputError
from backend.models import Component

class AddComponentDialog(QDialog):
    component_data_collected = pyqtSignal(dict)
    manage_types_requested = pyqtSignal(QObject)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Component")
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        type_layout = QHBoxLayout()
        self.type_input = QComboBox(self)
        self.type_input.addItems(type_manager.get_all_ui_names())
        self.type_input.currentTextChanged.connect(self.update_fields)
        self.manage_types_button = QPushButton("Manage Types...")
        self.manage_types_button.clicked.connect(lambda: self.manage_types_requested.emit(self))

        type_layout.addWidget(self.type_input)
        type_layout.addWidget(self.manage_types_button)
        self.form_layout.addRow("Type:", type_layout)
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
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g., Drawer A5, Resistor Box #2")
        self.form_layout.addRow(QLabel("Location:"), self.location_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any personal notes about this component...")
        self.notes_input.setFixedHeight(80)
        self.form_layout.addRow("Notes:", self.notes_input)

        self._create_dynamic_fields()
        self.layout.addLayout(self.form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.button_box.accepted.connect(self.handle_accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)

    def refresh_type_list(self):
        print("DEBUG: AddComponentDialog refreshing its type list...")
        current_selection = self.type_input.currentText()
        self.type_input.blockSignals(True)
        self.type_input.clear()
        self.type_input.addItems(type_manager.get_all_ui_names())

        index = self.type_input.findText(current_selection)
        if index == -1:
            # If the old selection is gone, maybe a new one was just added
            # This is a bit of a guess, but better than nothing.
            if type_manager.get_all_ui_names():
                # Find the last added custom type
                session = type_manager.get_session()
                try:
                    last_custom = session.query(type_manager.ComponentTypeDefinition).order_by(
                        type_manager.ComponentTypeDefinition.id.desc()).first()
                    if last_custom:
                        index = self.type_input.findText(last_custom.ui_name)
                finally:
                    session.close()

        if index != -1:
            self.type_input.setCurrentIndex(index)

        self.type_input.blockSignals(False)
        self.update_fields()

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
        fields = type_manager.get_properties(selected_type)

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
        fields_for_type = type_manager.get_properties(selected_type)
        primary_value_field_name = fields_for_type[0] if fields_for_type else None

        if primary_value_field_name:
            primary_input_widget = self.dynamic_fields.get(primary_value_field_name, (None, None))[1]
            if primary_input_widget and not primary_input_widget.text().strip():
                QMessageBox.warning(self, "Input Error",
                                    f"Primary value '{primary_value_field_name}' is required for {selected_type}.")
                return False

        return True

    def get_component_data(self):
        selected_ui_type = self.type_input.currentText()
        backend_type_id = type_manager.get_backend_id(selected_ui_type)

        if backend_type_id is None:
            raise InvalidInputError(f"Internal error mapping type: {selected_ui_type}")

        dynamic_values = [f"{fn}: {fi.text().strip()}" for fn, (_, fi) in self.dynamic_fields.items() if fi.text().strip()]
        value_str = ", ".join(dynamic_values)

        return {
            'part_number': self.part_number_input.text().strip(),
            'component_type': backend_type_id,
            'value': value_str,
            'quantity': self.quantity_input.value(),
            'purchase_link': self.purchase_link_input.text().strip(),
            'datasheet_link': self.datasheet_link_input.text().strip(),
            'location': self.location_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }

    def populate_from_component(self, component: Component):
        """Pre-fills the dialog's fields from an existing component object."""
        self.setWindowTitle("Duplicate Component")

        # Pre-fill type
        ui_name = type_manager.get_ui_name(component.component_type)
        if ui_name:
            self.type_input.setCurrentText(ui_name)

        # Pre-fill dynamic value fields
        value_data = {k.strip(): v.strip() for p in component.value.split(',') if ':' in p for k, v in
                      [p.split(':', 1)]}
        for prop_name, (_, prop_input) in self.dynamic_fields.items():
            matching_key = next((k for k in value_data if prop_name.startswith(k)), None)
            if matching_key:
                prop_input.setText(value_data.get(matching_key, ""))

        # Pre-fill standard fields
        self.part_number_input.clear()  # IMPORTANT: Force a new part number
        self.part_number_input.setPlaceholderText("Enter a NEW, unique part number")
        self.quantity_input.setValue(1)  # Default to 1 for a new entry
        self.purchase_link_input.setText(component.purchase_link or "")
        self.datasheet_link_input.setText(component.datasheet_link or "")
        self.location_input.setText(component.location or "")
        self.notes_input.setPlainText(component.notes or "")

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