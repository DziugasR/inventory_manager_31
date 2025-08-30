from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton, QSpinBox, QComboBox, QDialogButtonBox, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from backend.models import Component
from backend.models_custom import Inventory


class TransferDialog(QDialog):
    # Signal emits: destination_inventory_id, {component_id: quantity_to_transfer}
    transfer_requested = pyqtSignal(Inventory, dict)

    def __init__(self, components: list[Component], inventories: list[Inventory], parent=None):
        super().__init__(parent)
        self._spinboxes = {}
        self._components = components
        self._inventories = inventories

        self.setWindowTitle("Transfer Components")
        self.setMinimumSize(500, 300)
        self._init_ui()
        self._populate_data()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)

        # --- Destination Selection ---
        form_layout = QFormLayout()
        self.destination_combo = QComboBox()
        form_layout.addRow(QLabel("Transfer to Inventory:"), self.destination_combo)
        self.layout.addLayout(form_layout)

        # --- Components Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Part Number", "Available", "Quantity to Transfer"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.layout.addWidget(self.table)

        # --- Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Transfer")
        button_box.accepted.connect(self.accept_transfer)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

    def _populate_data(self):
        # Populate inventories dropdown
        for inv in self._inventories:
            self.destination_combo.addItem(inv.name, inv)  # Store the whole object

        # Populate components table
        self.table.setRowCount(len(self._components))
        for row, component in enumerate(self._components):
            part_number_item = QTableWidgetItem(component.part_number)
            part_number_item.setFlags(part_number_item.flags() & ~Qt.ItemIsEditable)

            available_qty_item = QTableWidgetItem(str(component.quantity))
            available_qty_item.setFlags(available_qty_item.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(row, 0, part_number_item)
            self.table.setItem(row, 1, available_qty_item)

            spinbox = QSpinBox()
            spinbox.setRange(0, component.quantity)
            spinbox.setValue(1 if component.quantity > 0 else 0)
            self.table.setCellWidget(row, 2, spinbox)
            self._spinboxes[component.id] = spinbox

    def accept_transfer(self):
        destination_inventory = self.destination_combo.currentData()
        if not destination_inventory:
            # Should not happen if list is populated, but a good safeguard
            return

        transfer_data = {
            comp_id: spinbox.value()
            for comp_id, spinbox in self._spinboxes.items()
            if spinbox.value() > 0
        }

        if not transfer_data:
            # Nothing to transfer
            self.reject()
            return

        self.transfer_requested.emit(destination_inventory, transfer_data)
        self.accept()