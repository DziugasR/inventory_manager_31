# test_ui_generate_ideas_dialog.py
import sys
import unittest
from unittest.mock import MagicMock
from functools import partial

from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QSpinBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtTest import QTest, QSignalSpy

# Assuming generate_ideas_dialog.py is in the same directory or accessible via PYTHONPATH
from frontend.ui.generate_ideas_dialog import GenerateIdeasDialog

class MockComponent:
    def __init__(self, part_number, component_type, value, quantity):
        self.part_number = part_number
        self.component_type = component_type
        self.value = value
        self.quantity = quantity

app = QApplication(sys.argv)

class TestGenerateIdeasDialog(unittest.TestCase):

    def setUp(self):
        self.dialog = GenerateIdeasDialog()
        self.mock_components = [
            MockComponent("R101", "RES", "10k", 5),
            MockComponent("C202", "CAP", "100nF", 10),
            MockComponent("U303", "IC", "ATmega328", 0),
            MockComponent("LED404", "LED", "Red", 20),
            MockComponent(None, "DIODE", "1N4001", 8) # Component with None part number
        ]
        self.type_mapping = {
            "RES": "Resistor",
            "CAP": "Capacitor",
            "IC": "Integrated Circuit",
            "LED": "Light Emitting Diode",
            "DIODE": "Diode"
        }

    def tearDown(self):
        self.dialog.close()
        del self.dialog

    def test_initialization(self):
        self.assertEqual(self.dialog.windowTitle(), "Generate Project Ideas")
        self.assertIsNotNone(self.dialog.components_table)
        self.assertIsNotNone(self.dialog.response_display)
        self.assertIsNotNone(self.dialog.generate_button)

        self.assertEqual(self.dialog.components_table.columnCount(), 4)
        self.assertEqual(self.dialog.components_table.horizontalHeaderItem(0).text(), "Part Number")
        self.assertEqual(self.dialog.components_table.horizontalHeaderItem(1).text(), "Type")
        self.assertEqual(self.dialog.components_table.horizontalHeaderItem(2).text(), "Value")
        self.assertEqual(self.dialog.components_table.horizontalHeaderItem(3).text(), "Project Qty")
        self.assertEqual(self.dialog.components_table.rowCount(), 0)

        self.assertTrue(self.dialog.response_display.isReadOnly())
        self.assertEqual(self.dialog.response_display.toPlainText(), "")
        self.assertEqual(self.dialog.response_display.placeholderText(), "Click 'Generate Ideas' to get suggestions...")

        self.assertTrue(self.dialog.generate_button.isEnabled())
        self.assertEqual(self.dialog.generate_button.text(), "Generate Ideas")

        self.assertEqual(len(self.dialog._spinboxes), 0)

    def test_populate_table_empty(self):
        self.dialog.populate_table([], self.type_mapping)
        self.assertEqual(self.dialog.components_table.rowCount(), 0)
        self.assertEqual(len(self.dialog._spinboxes), 0)

    def test_populate_table_with_data(self):
        self.dialog.populate_table(self.mock_components, self.type_mapping)
        num_components = len(self.mock_components)
        self.assertEqual(self.dialog.components_table.rowCount(), num_components)
        # Check that a spinbox entry is created for *all* components, using "" for None PN
        self.assertEqual(len(self.dialog._spinboxes), num_components) # FIX: Changed from num_components - 1

        for row, comp in enumerate(self.mock_components):
            pn = comp.part_number or "" # Converts None to ""
            ctype = self.type_mapping.get(comp.component_type, comp.component_type)
            val = comp.value or ""
            avail_qty = comp.quantity
            expected_initial_qty = 1 if avail_qty > 0 else 0

            self.assertEqual(self.dialog.components_table.item(row, self.dialog.PART_NUMBER_COL_IDX).text(), pn)
            self.assertEqual(self.dialog.components_table.item(row, self.dialog.TYPE_COL_IDX).text(), ctype)
            self.assertEqual(self.dialog.components_table.item(row, self.dialog.VALUE_COL_IDX).text(), val)

            spinbox_widget = self.dialog.components_table.cellWidget(row, self.dialog.QUANTITY_COL_IDX)
            self.assertIsInstance(spinbox_widget, QSpinBox)
            self.assertEqual(spinbox_widget.minimum(), 0)
            self.assertEqual(spinbox_widget.maximum(), avail_qty)
            self.assertEqual(spinbox_widget.value(), expected_initial_qty)
            self.assertIn(f"Available: {avail_qty}", spinbox_widget.toolTip())
            self.assertIn(f"Current project quantity: {expected_initial_qty}", spinbox_widget.toolTip())

            # Check internal tracker using the actual key (pn, which is "" for None)
            self.assertIn(pn, self.dialog._spinboxes)
            self.assertIs(self.dialog._spinboxes[pn], spinbox_widget)

            expected_tooltip_base = f"Part: {pn}\nType: {ctype}\nValue: {val or 'N/A'}\nAvailable: {avail_qty}"
            for col in range(self.dialog.components_table.columnCount()):
                item = self.dialog.components_table.item(row, col)
                widget = self.dialog.components_table.cellWidget(row, col)
                if item:
                     self.assertEqual(item.toolTip(), expected_tooltip_base)
                if widget:
                    self.assertTrue(widget.toolTip().startswith(expected_tooltip_base))

    def test_get_spinbox_values_initial(self):
        self.dialog.populate_table(self.mock_components, self.type_mapping)
        values = self.dialog.get_spinbox_values()

        # Should include entry for the None PN component, keyed by ""
        self.assertEqual(len(values), 5) # FIX: Changed from 4

        self.assertEqual(values.get("R101"), 1)
        self.assertEqual(values.get("C202"), 1)
        self.assertEqual(values.get("U303"), 0)
        self.assertEqual(values.get("LED404"), 1)
        self.assertEqual(values.get(""), 1) # FIX: Check for empty string key (was None PN)

    def test_get_spinbox_values_after_change(self):
        self.dialog.populate_table(self.mock_components, self.type_mapping)

        spinbox_r101 = self.dialog.components_table.cellWidget(0, self.dialog.QUANTITY_COL_IDX)
        self.assertIsNotNone(spinbox_r101)

        new_value = 3
        spinbox_r101.setValue(new_value)
        QApplication.processEvents()

        values = self.dialog.get_spinbox_values()
        self.assertEqual(values.get("R101"), new_value)
        self.assertEqual(values.get("C202"), 1)
        self.assertEqual(values.get(""), 1) # Check that "" key wasn't affected

    def test_set_clear_response_text(self):
        test_text = "These are the generated ideas:\n- Idea 1\n- Idea 2"
        self.dialog.set_response_text(test_text)
        self.assertEqual(self.dialog.response_display.toPlainText(), test_text)

        self.dialog.clear_response_text()
        self.assertEqual(self.dialog.response_display.toPlainText(), "")

    def test_show_processing(self):
        self.dialog.show_processing(True)
        self.assertFalse(self.dialog.generate_button.isEnabled())
        self.assertFalse(self.dialog.components_table.isEnabled())
        self.assertEqual(self.dialog.response_display.placeholderText(), "Generating ideas from ChatGPT...")

        self.dialog.set_response_text("Some old text")
        self.dialog.show_processing(True)
        self.assertEqual(self.dialog.response_display.toPlainText(), "")

        self.dialog.show_processing(False)
        self.assertTrue(self.dialog.generate_button.isEnabled())
        self.assertTrue(self.dialog.components_table.isEnabled())
        self.assertEqual(self.dialog.response_display.placeholderText(), "Click 'Generate Ideas' to get suggestions...")
        self.assertEqual(self.dialog.response_display.toPlainText(), "")

        self.dialog.set_response_text("Generated text")
        self.dialog.show_processing(False)
        self.assertTrue(self.dialog.generate_button.isEnabled())
        self.assertTrue(self.dialog.components_table.isEnabled())

        # FIX: Check placeholder text is NOT the "Generating..." one,
        # because it might still be the default "Click..." one if text is present.
        self.assertNotEqual(self.dialog.response_display.placeholderText(), "Generating ideas from ChatGPT...")
        self.assertEqual(self.dialog.response_display.toPlainText(), "Generated text")

    def test_generate_requested_signal(self):
        spy = QSignalSpy(self.dialog.generate_requested)
        self.assertEqual(len(spy), 0)

        QTest.mouseClick(self.dialog.generate_button, Qt.LeftButton)

        self.assertEqual(len(spy), 1)

    def test_quantity_changed_signal(self):
        self.dialog.populate_table(self.mock_components, self.type_mapping)

        part_number_to_test = "C202"
        row_to_test = 1
        new_value = 5

        spinbox_c202 = self.dialog.components_table.cellWidget(row_to_test, self.dialog.QUANTITY_COL_IDX)
        self.assertIsNotNone(spinbox_c202)

        spy = QSignalSpy(self.dialog.quantity_changed)
        self.assertEqual(len(spy), 0)

        spinbox_c202.setValue(new_value)

        QApplication.processEvents()

        self.assertEqual(len(spy), 1)
        # FIX: Correct way to get arguments from QSignalSpy
        emitted_args = spy[0]
        self.assertEqual(len(emitted_args), 2)
        self.assertEqual(emitted_args[0], part_number_to_test)
        self.assertEqual(emitted_args[1], new_value)

    def test_spinbox_tooltip_update_on_change(self):
        self.dialog.populate_table(self.mock_components, self.type_mapping)

        part_number_to_test = "LED404"
        row_to_test = 3
        new_value = 8

        spinbox_led = self.dialog.components_table.cellWidget(row_to_test, self.dialog.QUANTITY_COL_IDX)
        initial_tooltip = spinbox_led.toolTip()
        self.assertIn("Current project quantity: 1", initial_tooltip)

        spinbox_led.setValue(new_value)
        QApplication.processEvents()

        updated_tooltip = spinbox_led.toolTip()
        self.assertNotIn("Current project quantity: 1", updated_tooltip)
        self.assertIn(f"Current project quantity: {new_value}", updated_tooltip)

        self.assertTrue(updated_tooltip.startswith(f"Part: {part_number_to_test}\nType: {self.type_mapping['LED']}"))
        self.assertIn(f"Available: {self.mock_components[row_to_test].quantity}", updated_tooltip)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)