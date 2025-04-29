import pytest
from unittest.mock import MagicMock, patch

from PyQt5.QtWidgets import QDialogButtonBox, QLineEdit, QComboBox, QMessageBox, QSpinBox, QDialog
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.ui.add_component_dialog import AddComponentDialog
from backend.component_constants import UI_TYPE_NAMES, UI_TO_BACKEND_TYPE_MAP
from backend.exceptions import InvalidInputError

@pytest.fixture
def dialog(qtbot):
    test_dialog = AddComponentDialog()
    qtbot.addWidget(test_dialog)
    yield test_dialog

def test_dialog_initialization(dialog, qtbot):
    assert dialog.windowTitle() == "Add New Component"
    assert isinstance(dialog.type_input, QComboBox)
    assert isinstance(dialog.part_number_input, QLineEdit)
    assert isinstance(dialog.quantity_input, QSpinBox)
    assert isinstance(dialog.purchase_link_input, QLineEdit)
    assert isinstance(dialog.datasheet_link_input, QLineEdit)
    assert isinstance(dialog.button_box, QDialogButtonBox)
    assert dialog.type_input.count() == len(UI_TYPE_NAMES)
    assert dialog.type_input.itemText(0) == UI_TYPE_NAMES[0]
    assert dialog.type_input.itemText(dialog.type_input.count() - 1) == UI_TYPE_NAMES[-1]
    default_type = UI_TYPE_NAMES[0]
    expected_fields = dialog.component_types.get(default_type, [])
    assert len(dialog.dynamic_fields) == len(expected_fields)
    if expected_fields:
        assert all(field in dialog.dynamic_fields for field in expected_fields)

def test_dynamic_fields_update_on_type_change(dialog, qtbot):
    initial_type = UI_TYPE_NAMES[0]
    dialog.type_input.setCurrentText(initial_type)
    qtbot.wait(20)
    initial_fields = dialog.component_types.get(initial_type, [])
    assert len(dialog.dynamic_fields) == len(initial_fields)
    for field_name in initial_fields:
        assert field_name in dialog.dynamic_fields

    dialog.type_input.setCurrentText("Resistor")
    qtbot.wait(20)
    resistor_fields = dialog.component_types.get("Resistor", [])
    assert len(dialog.dynamic_fields) == len(resistor_fields)
    assert "Resistance (Ω)" in dialog.dynamic_fields
    assert "Tolerance (%)" in dialog.dynamic_fields
    for field_name in initial_fields:
        if field_name not in resistor_fields:
            assert field_name not in dialog.dynamic_fields

    dialog.type_input.setCurrentText("Capacitor")
    qtbot.wait(20)
    capacitor_fields = dialog.component_types.get("Capacitor", [])
    assert len(dialog.dynamic_fields) == len(capacitor_fields)
    assert "Capacitance (µF)" in dialog.dynamic_fields
    assert "Voltage (V)" in dialog.dynamic_fields
    assert "Resistance (Ω)" not in dialog.dynamic_fields

@patch('PyQt5.QtWidgets.QMessageBox.warning')
def test_validation_part_number_required(mock_warning, dialog, qtbot):
    dialog.part_number_input.setText("")
    assert not dialog.validate_inputs()
    mock_warning.assert_called_once_with(dialog, "Input Error", "Part number is required.")

@patch('PyQt5.QtWidgets.QMessageBox.warning')
def test_validation_primary_value_required_resistor(mock_warning, dialog, qtbot):
    dialog.type_input.setCurrentText("Resistor")
    qtbot.wait(20)
    dialog.part_number_input.setText("R100")
    resistance_label, resistance_input = dialog.dynamic_fields["Resistance (Ω)"]
    resistance_input.setText("")
    assert not dialog.validate_inputs()
    mock_warning.assert_called_once_with(dialog, "Input Error", "Primary value 'Resistance (Ω)' is required for Resistor.")

@patch('PyQt5.QtWidgets.QMessageBox.warning')
def test_validation_primary_value_required_capacitor(mock_warning, dialog, qtbot):
    dialog.type_input.setCurrentText("Capacitor")
    qtbot.wait(20)
    dialog.part_number_input.setText("C200")
    capacitance_label, capacitance_input = dialog.dynamic_fields["Capacitance (µF)"]
    capacitance_input.setText("")
    assert not dialog.validate_inputs()
    mock_warning.assert_called_once_with(dialog, "Input Error", "Primary value 'Capacitance (µF)' is required for Capacitor.")

@patch('PyQt5.QtWidgets.QMessageBox.warning')
def test_validation_passes_with_required_fields(mock_warning, dialog, qtbot):
    dialog.type_input.setCurrentText("Resistor")
    qtbot.wait(20)
    dialog.part_number_input.setText("R101")
    resistance_label, resistance_input = dialog.dynamic_fields["Resistance (Ω)"]
    resistance_input.setText("10k")
    tolerance_label, tolerance_input = dialog.dynamic_fields["Tolerance (%)"]
    tolerance_input.setText("5%")
    assert dialog.validate_inputs()
    mock_warning.assert_not_called()

def test_get_component_data_correct_resistor(dialog, qtbot):
    dialog.type_input.setCurrentText("Resistor")
    qtbot.wait(20)
    dialog.part_number_input.setText(" R102 ")
    dialog.quantity_input.setValue(123)
    dialog.purchase_link_input.setText(" https://example.com/buy ")
    dialog.datasheet_link_input.setText(" ")
    resistance_label, resistance_input = dialog.dynamic_fields["Resistance (Ω)"]
    resistance_input.setText(" 4.7k ")
    tolerance_label, tolerance_input = dialog.dynamic_fields["Tolerance (%)"]
    tolerance_input.setText(" 1% ")
    data = dialog.get_component_data()
    expected_backend_id = UI_TO_BACKEND_TYPE_MAP.get("Resistor")
    assert data['part_number'] == 'R102'
    assert data['component_type'] == expected_backend_id
    assert data['quantity'] == 123
    assert data['purchase_link'] == 'https://example.com/buy'
    assert data['datasheet_link'] == ''
    assert "Resistance (Ω): 4.7k" in data['value']
    assert "Tolerance (%): 1%" in data['value']
    if "Resistance (Ω): 4.7k" in data['value'] and "Tolerance (%): 1%" in data['value']:
        assert ", " in data['value']

def test_get_component_data_correct_capacitor_no_secondary(dialog, qtbot):
    dialog.type_input.setCurrentText("Capacitor")
    qtbot.wait(20)
    dialog.part_number_input.setText("C303")
    dialog.quantity_input.setValue(50)
    capacitance_label, capacitance_input = dialog.dynamic_fields["Capacitance (µF)"]
    capacitance_input.setText("100nF")
    voltage_label, voltage_input = dialog.dynamic_fields["Voltage (V)"]
    voltage_input.setText("  ")
    data = dialog.get_component_data()
    expected_backend_id = UI_TO_BACKEND_TYPE_MAP.get("Capacitor")
    assert data['component_type'] == expected_backend_id
    assert data['part_number'] == 'C303'
    assert data['value'] == 'Capacitance (µF): 100nF'
    assert data['quantity'] == 50

@patch.object(AddComponentDialog, 'validate_inputs', return_value=True)
@patch.object(AddComponentDialog, 'get_component_data')
@patch.object(AddComponentDialog, 'accept')
def test_handle_accept_success(mock_accept, mock_get_data, mock_validate, dialog, qtbot):
    expected_data = {'part_number': 'PN1', 'component_type': 'resistor', 'value': 'Value', 'quantity': 1}
    mock_get_data.return_value = expected_data
    with qtbot.waitSignal(dialog.component_data_collected, timeout=500) as blocker:
        ok_button = dialog.button_box.button(QDialogButtonBox.Ok)
        qtbot.mouseClick(ok_button, Qt.LeftButton)
    assert blocker.signal_triggered
    assert blocker.args == [expected_data]
    mock_validate.assert_called_once()
    mock_get_data.assert_called_once()
    mock_accept.assert_called_once()

@patch.object(AddComponentDialog, 'validate_inputs', return_value=False)
@patch.object(AddComponentDialog, 'get_component_data')
@patch.object(AddComponentDialog, 'accept')
@patch('PyQt5.QtWidgets.QMessageBox.warning')
def test_handle_accept_validation_fail(mock_warning, mock_accept, mock_get_data, mock_validate, dialog, qtbot):
    with qtbot.waitSignal(dialog.component_data_collected, timeout=100, raising=False) as blocker:
        ok_button = dialog.button_box.button(QDialogButtonBox.Ok)
        qtbot.mouseClick(ok_button, Qt.LeftButton)
    assert not blocker.signal_triggered
    mock_validate.assert_called_once()
    mock_get_data.assert_not_called()
    mock_accept.assert_not_called()

def test_reject_button(dialog, qtbot):
    cancel_button = dialog.button_box.button(QDialogButtonBox.Cancel)
    assert cancel_button is not None
    with qtbot.waitSignal(dialog.rejected, timeout=500) as blocker:
        qtbot.mouseClick(cancel_button, Qt.LeftButton)
    assert blocker.signal_triggered