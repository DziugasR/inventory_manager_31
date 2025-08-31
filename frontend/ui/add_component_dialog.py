import os
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QDialogButtonBox, QLabel, QVBoxLayout, QMessageBox, QPushButton, QHBoxLayout, QTextEdit,
    QFileDialog, QGroupBox
)
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QPixmap
from backend.type_manager import type_manager
from backend.exceptions import InvalidInputError
from backend.models import Component


class AddComponentDialog(QDialog):
    component_data_collected = pyqtSignal(dict)
    manage_types_requested = pyqtSignal(QObject)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Component")
        self.setMinimumWidth(500)
        self._source_image_path = None

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        type_layout = QHBoxLayout()
        self.type_input = QComboBox(self)
        self.type_input.addItems(type_manager.get_all_ui_names())
        self.manage_types_button = QPushButton("Manage Types...")
        type_layout.addWidget(self.type_input)
        type_layout.addWidget(self.manage_types_button)
        self.form_layout.addRow("Type:", type_layout)

        self.part_number_input = QLineEdit(self)
        self.form_layout.addRow("Part Number:", self.part_number_input)

        self.properties_group_box = QGroupBox("Properties")
        self.properties_layout = QFormLayout()
        self.properties_group_box.setLayout(self.properties_layout)
        self.form_layout.addRow(self.properties_group_box)
        self.dynamic_fields = {}

        self.quantity_input = QSpinBox(self)
        self.quantity_input.setRange(0, 999999)
        self.quantity_input.setValue(1)
        self.form_layout.addRow("Quantity:", self.quantity_input)

        self.purchase_link_input = QLineEdit(self)
        self.form_layout.addRow("Purchase Link:", self.purchase_link_input)
        self.datasheet_link_input = QLineEdit(self)
        self.form_layout.addRow("Datasheet Link:", self.datasheet_link_input)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g., Drawer A5, Resistor Box #2")
        self.form_layout.addRow("Location:", self.location_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any personal notes...")
        self.notes_input.setFixedHeight(80)
        self.form_layout.addRow("Notes:", self.notes_input)

        image_layout = QHBoxLayout()
        self.image_label = QLabel("No Image Selected")
        self.image_label.setFixedSize(100, 100)
        self.image_label.setStyleSheet("border: 1px solid grey;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        change_image_button = QPushButton("Select Image...")
        change_image_button.clicked.connect(self._select_image)
        image_layout.addWidget(self.image_label)
        image_layout.addWidget(change_image_button, 1, Qt.AlignTop)
        self.form_layout.addRow("Image:", image_layout)

        self.layout.addLayout(self.form_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.handle_accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.type_input.currentTextChanged.connect(self.update_fields)
        self.manage_types_button.clicked.connect(lambda: self.manage_types_requested.emit(self))

        self.update_fields()

    def _select_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Component Image", "",
                                                  "Image Files (*.png *.jpg *.jpeg)")
        if filepath:
            self._source_image_path = filepath
            pixmap = QPixmap(filepath)
            self.image_label.setPixmap(pixmap)

    def refresh_type_list(self):
        current_selection = self.type_input.currentText()
        self.type_input.blockSignals(True)
        self.type_input.clear()
        self.type_input.addItems(type_manager.get_all_ui_names())
        index = self.type_input.findText(current_selection)
        if index != -1: self.type_input.setCurrentIndex(index)
        self.type_input.blockSignals(False)
        self.update_fields()

    def update_fields(self):
        self._clear_dynamic_fields()
        self._create_dynamic_fields()

    # --- START OF FIX: This is a more robust way to clear the layout ---
    def _clear_dynamic_fields(self):
        """Removes all rows from the properties layout."""
        while self.properties_layout.rowCount() > 0:
            self.properties_layout.removeRow(0)
        self.dynamic_fields.clear()

    # --- END OF FIX ---

    def _create_dynamic_fields(self):
        selected_type = self.type_input.currentText()
        fields = type_manager.get_properties(selected_type)

        if not fields:
            self.properties_group_box.setVisible(False)
            return

        self.properties_group_box.setVisible(True)
        for field_name in fields:
            label = QLabel(field_name)
            input_field = QLineEdit(self)
            self.properties_layout.addRow(label, input_field)
            self.dynamic_fields[field_name] = (label, input_field)

    def validate_inputs(self):
        if not self.part_number_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Part number is required.")
            return False
        return True

    def get_component_data(self):
        selected_ui_type = self.type_input.currentText()
        backend_type_id = type_manager.get_backend_id(selected_ui_type)
        if backend_type_id is None:
            raise InvalidInputError(f"Internal error mapping type: {selected_ui_type}")
        dynamic_values = [f"{fn}: {fi.text().strip()}" for fn, (_, fi) in self.dynamic_fields.items() if
                          fi.text().strip()]
        value_str = ", ".join(dynamic_values)
        return {
            'part_number': self.part_number_input.text().strip(),
            'component_type': backend_type_id,
            'value': value_str,
            'quantity': self.quantity_input.value(),
            'purchase_link': self.purchase_link_input.text().strip(),
            'datasheet_link': self.datasheet_link_input.text().strip(),
            'location': self.location_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip(),
            'source_image_path': self._source_image_path
        }

    def populate_from_component(self, component: Component, app_path: str):
        self.setWindowTitle("Duplicate Component")
        self.type_input.blockSignals(True)

        ui_name = type_manager.get_ui_name(component.component_type)
        if ui_name:
            self.type_input.setCurrentText(ui_name)

        self.update_fields()

        value_data = {k.strip(): v.strip() for p in component.value.split(',') if ':' in p for k, v in
                      [p.split(':', 1)]}
        for prop_name, (_, prop_input) in self.dynamic_fields.items():
            matching_key = next((k for k in value_data if prop_name.startswith(k)), None)
            if matching_key:
                prop_input.setText(value_data.get(matching_key, ""))

        self.part_number_input.clear()
        self.part_number_input.setPlaceholderText("Enter a NEW, unique part number")
        self.quantity_input.setValue(1)
        self.purchase_link_input.setText(component.purchase_link or "")
        self.datasheet_link_input.setText(component.datasheet_link or "")
        self.location_input.setText(component.location or "")
        self.notes_input.setPlainText(component.notes or "")

        if component.image_path:
            full_image_path = os.path.join(app_path, component.image_path)
            if os.path.exists(full_image_path):
                self._source_image_path = full_image_path
                self.image_label.setPixmap(QPixmap(full_image_path))

        self.type_input.blockSignals(False)

    def handle_accept(self):
        if self.validate_inputs():
            try:
                component_data = self.get_component_data()
                self.component_data_collected.emit(component_data)
                self.accept()
            except InvalidInputError as e:
                QMessageBox.critical(self, "Internal Error", str(e))