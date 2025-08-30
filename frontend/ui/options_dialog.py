from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QFormLayout, QLabel,
    QLineEdit, QComboBox, QDialogButtonBox
)
from backend.models_custom import Inventory


class OptionsDialog(QDialog):
    def __init__(self, inventories: list[Inventory], current_settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Options")
        self.setMinimumWidth(450)

        self.layout = QVBoxLayout(self)

        # --- AI/API Settings ---
        api_group = QGroupBox("AI & API Settings")
        api_layout = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Leave blank to keep current key")
        api_layout.addRow(QLabel("OpenAI API Key:"), self.api_key_input)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"])
        api_layout.addRow(QLabel("AI Model:"), self.model_combo)

        api_group.setLayout(api_layout)
        self.layout.addWidget(api_group)

        # --- Application Behavior ---
        app_group = QGroupBox("Application Behavior")
        app_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System Default", "Light", "Dark"])
        app_layout.addRow(QLabel("Theme (requires restart):"), self.theme_combo)

        self.startup_inventory_combo = QComboBox()
        app_layout.addRow(QLabel("Load on startup:"), self.startup_inventory_combo)

        app_group.setLayout(app_layout)
        self.layout.addWidget(app_group)

        # --- Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

        self._inventories = inventories
        self._populate_fields(current_settings)

    def _populate_fields(self, settings: dict):
        self.model_combo.setCurrentText(settings.get('ai_model', 'gpt-4o-mini'))
        self.theme_combo.setCurrentText(settings.get('theme', 'System Default'))

        self.startup_inventory_combo.addItem("Last Used Inventory", "last_used")
        for inv in self._inventories:
            self.startup_inventory_combo.addItem(inv.name, inv.id)

        startup_id = settings.get('startup_inventory_id', 'last_used')
        index = self.startup_inventory_combo.findData(startup_id)
        if index != -1:
            self.startup_inventory_combo.setCurrentIndex(index)

    def get_data(self) -> dict:
        """Returns the selected settings from the dialog widgets."""
        data = {
            'ai_model': self.model_combo.currentText(),
            'theme': self.theme_combo.currentText(),
            'startup_inventory_id': self.startup_inventory_combo.currentData()
        }
        if self.api_key_input.text():
            data['api_key'] = self.api_key_input.text()
        return data


