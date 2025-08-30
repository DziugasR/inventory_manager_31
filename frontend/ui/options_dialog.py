from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QFormLayout, QLabel,
    QLineEdit, QComboBox, QDialogButtonBox
)


class OptionsDialog(QDialog):
    def __init__(self, inventory_names: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Options")
        self.setMinimumWidth(400)

        self.layout = QVBoxLayout(self)

        # --- Suggestions for AI/API Settings ---
        api_group = QGroupBox("AI & API Settings")
        api_layout = QFormLayout()

        api_key_input = QLineEdit()
        api_key_input.setPlaceholderText("sk-...")
        api_key_input.setEnabled(False)  # Non-functional for now
        api_layout.addRow(QLabel("OpenAI API Key:"), api_key_input)

        model_combo = QComboBox()
        model_combo.addItems(["gpt-4", "gpt-3.5-turbo"])
        model_combo.setEnabled(False) # Non-functional for now
        api_layout.addRow(QLabel("AI Model:"), model_combo)

        api_group.setLayout(api_layout)
        self.layout.addWidget(api_group)

        # --- Suggestions for Application Behavior ---
        app_group = QGroupBox("Application Behavior")
        app_layout = QFormLayout()

        theme_combo = QComboBox()
        theme_combo.addItems(["System Default", "Light", "Dark"])
        theme_combo.setEnabled(False) # Non-functional for now
        app_layout.addRow(QLabel("Theme:"), theme_combo)

        startup_inventory_combo = QComboBox()
        startup_inventory_combo.addItem("Last Used Inventory")
        startup_inventory_combo.addItems(inventory_names)
        startup_inventory_combo.setEnabled(False) # Non-functional for now
        app_layout.addRow(QLabel("Load on startup:"), startup_inventory_combo)

        app_group.setLayout(app_layout)
        self.layout.addWidget(app_group)

        # --- OK and Cancel Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)