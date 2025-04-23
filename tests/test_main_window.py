import pytest
import uuid
from unittest.mock import MagicMock, patch

from PyQt5.QtWidgets import QApplication, QCheckBox, QWidget, QHBoxLayout
from PyQt5.QtCore import QUrl, Qt

from frontend.ui.main_window import InventoryUI
from frontend.ui import utils as ui_utils
from backend import component_constants

class MockComponent:
    def __init__(self, id, part_number, component_type, value, quantity, purchase_link=None, datasheet_link=None):
        self.id = id
        self.part_number = part_number
        self.component_type = component_type
        self.value = value
        self.quantity = quantity
        self.purchase_link = purchase_link
        self.datasheet_link = datasheet_link

MOCK_COMPONENTS = [
    MockComponent(uuid.uuid4(), "R101", "resistor", "10k Ohms", 50, "http://buy.res", "http://data.res"),
    MockComponent(uuid.uuid4(), "C202", "capacitor", "10uF", 25, None, "http://data.cap"),
    MockComponent(uuid.uuid4(), "U303", "ic", "OpAmp", 10),
]

@pytest.fixture
def window(qtbot):
    with patch.object(ui_utils, 'load_stylesheet', return_value=""):
        test_window = InventoryUI()
        qtbot.addWidget(test_window)
        yield test_window

def test_window_initialization(window, qtbot):
    assert window.windowTitle() == "Electronics Inventory Manager"
    assert window.table is not None
    assert window.add_button is not None
    assert window.remove_button is not None
    assert window.generate_ideas_button is not None
    assert window.export_button is not None
    assert window.import_button is not None
    assert not window.remove_button.isEnabled()
    assert not window.generate_ideas_button.isEnabled()

def test_display_data_populates_table(window, qtbot):
    window.display_data(MOCK_COMPONENTS)
    assert window.table.rowCount() == len(MOCK_COMPONENTS)
    assert window.table.item(0, window.PART_NUMBER_COL).text() == "R101"
    expected_ui_type = component_constants.BACKEND_TO_UI_TYPE_MAP.get("resistor", "resistor")
    assert window.table.item(0, window.TYPE_COL).text() == expected_ui_type
    assert window.table.item(0, window.VALUE_COL).text() == "10k Ohms"
    assert window.table.item(0, window.QUANTITY_COL).text() == "50"
    assert window.table.item(0, window.QUANTITY_COL).data(Qt.EditRole) == 50
    assert window.table.item(0, window.PURCHASE_LINK_COL).text() == "Link"
    assert window.table.item(0, window.DATASHEET_COL).text() == "Link"
    assert window.table.cellWidget(0, window.CHECKBOX_COL) is not None
    assert window.table.item(2, window.PURCHASE_LINK_COL).text() == ""
    assert window.table.item(2, window.DATASHEET_COL).text() == ""
    assert window.table.cellWidget(2, window.CHECKBOX_COL) is not None

def test_display_data_empty(window, qtbot):
    window.display_data([])
    assert window.table.rowCount() == 0

def test_button_signals_simple(window, qtbot):
    with qtbot.waitSignal(window.add_component_requested, timeout=500) as blocker:
        qtbot.mouseClick(window.add_button, Qt.LeftButton)
    assert blocker.signal_triggered
    with qtbot.waitSignal(window.export_requested, timeout=500) as blocker:
        qtbot.mouseClick(window.export_button, Qt.LeftButton)
    assert blocker.signal_triggered
    with qtbot.waitSignal(window.import_requested, timeout=500) as blocker:
        qtbot.mouseClick(window.import_button, Qt.LeftButton)
    assert blocker.signal_triggered

def test_checkbox_enables_buttons(window, qtbot):
    window.display_data(MOCK_COMPONENTS)
    assert not window.remove_button.isEnabled()
    assert not window.generate_ideas_button.isEnabled()
    cell_widget = window.table.cellWidget(0, window.CHECKBOX_COL)
    checkbox = cell_widget.findChild(QCheckBox)
    assert checkbox is not None
    checkbox.setChecked(True)
    window._update_buttons_state_on_checkbox()
    assert window.remove_button.isEnabled()
    assert window.generate_ideas_button.isEnabled()
    checkbox.setChecked(False)
    window._update_buttons_state_on_checkbox()
    assert not window.remove_button.isEnabled()
    assert not window.generate_ideas_button.isEnabled()

def test_get_checked_ids(window, qtbot):
    window.display_data(MOCK_COMPONENTS)
    checkbox0_widget = window.table.cellWidget(0, window.CHECKBOX_COL)
    checkbox0 = checkbox0_widget.findChild(QCheckBox)
    checkbox2_widget = window.table.cellWidget(2, window.CHECKBOX_COL)
    checkbox2 = checkbox2_widget.findChild(QCheckBox)
    checkbox0.setChecked(True)
    checkbox2.setChecked(True)
    checked_ids = window.get_checked_ids()
    assert len(checked_ids) == 2
    assert MOCK_COMPONENTS[0].id in checked_ids
    assert MOCK_COMPONENTS[2].id in checked_ids
    assert MOCK_COMPONENTS[1].id not in checked_ids

def test_get_checked_ids_empty(window, qtbot):
    window.display_data([])
    assert window.get_checked_ids() == []
    window.display_data(MOCK_COMPONENTS)
    assert window.get_checked_ids() == []

def test_remove_button_signal_with_checked(window, qtbot):
    window.display_data(MOCK_COMPONENTS)
    checkbox0_widget = window.table.cellWidget(0, window.CHECKBOX_COL)
    checkbox0 = checkbox0_widget.findChild(QCheckBox)
    assert not window.remove_button.isEnabled()
    with qtbot.waitSignal(window.remove_components_requested, timeout=100, raising=False) as blocker:
        qtbot.mouseClick(window.remove_button, Qt.LeftButton)
    assert not blocker.signal_triggered
    checkbox0.setChecked(True)
    window._update_buttons_state_on_checkbox()
    assert window.remove_button.isEnabled()
    with qtbot.waitSignal(window.remove_components_requested, timeout=500) as blocker:
        qtbot.mouseClick(window.remove_button, Qt.LeftButton)
    assert blocker.signal_triggered
    assert blocker.args == [[MOCK_COMPONENTS[0].id]]

def test_generate_ideas_button_signal_with_checked(window, qtbot):
    window.display_data(MOCK_COMPONENTS)
    checkbox1_widget = window.table.cellWidget(1, window.CHECKBOX_COL)
    checkbox1 = checkbox1_widget.findChild(QCheckBox)
    assert not window.generate_ideas_button.isEnabled()
    with qtbot.waitSignal(window.generate_ideas_requested, timeout=100, raising=False) as blocker:
        qtbot.mouseClick(window.generate_ideas_button, Qt.LeftButton)
    assert not blocker.signal_triggered
    checkbox1.setChecked(True)
    window._update_buttons_state_on_checkbox()
    assert window.generate_ideas_button.isEnabled()
    with qtbot.waitSignal(window.generate_ideas_requested, timeout=500) as blocker:
        qtbot.mouseClick(window.generate_ideas_button, Qt.LeftButton)
    assert blocker.signal_triggered
    assert blocker.args == [[MOCK_COMPONENTS[1].id]]

def test_handle_cell_click_links(window, qtbot):
    window.display_data(MOCK_COMPONENTS)
    purchase_link_item = window.table.item(0, window.PURCHASE_LINK_COL)
    datasheet_link_item = window.table.item(0, window.DATASHEET_COL)
    with qtbot.waitSignal(window.link_clicked, timeout=500) as blocker:
        window._handle_cell_click(0, window.PURCHASE_LINK_COL)
    assert blocker.signal_triggered
    assert blocker.args == [QUrl(MOCK_COMPONENTS[0].purchase_link)]
    with qtbot.waitSignal(window.link_clicked, timeout=500) as blocker:
        window._handle_cell_click(0, window.DATASHEET_COL)
    assert blocker.signal_triggered
    assert blocker.args == [QUrl(MOCK_COMPONENTS[0].datasheet_link)]

def test_handle_cell_click_no_link(window, qtbot):
    window.display_data(MOCK_COMPONENTS)
    with qtbot.waitSignal(window.link_clicked, timeout=100, raising=False) as blocker:
        window._handle_cell_click(2, window.PURCHASE_LINK_COL)
    assert not blocker.signal_triggered
    with qtbot.waitSignal(window.link_clicked, timeout=100, raising=False) as blocker:
        window._handle_cell_click(0, window.PART_NUMBER_COL)
    assert not blocker.signal_triggered