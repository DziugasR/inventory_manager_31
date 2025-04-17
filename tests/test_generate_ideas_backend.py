import unittest
import io
import sys
from contextlib import redirect_stdout

from backend.generate_ideas_backend import construct_generation_prompt, process_ideas

class MockComponent:
    def __init__(self, part_number, component_type, value):
        self.part_number = part_number
        self.component_type = component_type
        self.value = value

class DummyBackendInstance:
    pass

class TestGenerateIdeasBackendSimple(unittest.TestCase):

    def setUp(self):
        self.components = [
            MockComponent("R101", "RES", "10k"),
            MockComponent("C202", "CAP", "100nF"),
            MockComponent("U303", "IC", None),
            MockComponent("LED404", "LED", "RED"),
            MockComponent("T505", "TRANSISTOR_BJT", "BC547")
        ]
        self.type_mapping = {
            "RES": "Resistor",
            "CAP": "Capacitor",
            "IC": "Integrated Circuit",
            "LED": "Light Emitting Diode"
        }
        self.dummy_instance = DummyBackendInstance()

    def test_construct_prompt_no_selected_components(self):
        selected_quantities = {"R101": 0, "C202": 0}
        prompt = construct_generation_prompt(self.components, selected_quantities, self.type_mapping)
        self.assertIsNone(prompt)

    def test_construct_prompt_no_components_list(self):
        selected_quantities = {"R101": 1}
        prompt = construct_generation_prompt([], selected_quantities, self.type_mapping)
        self.assertIsNone(prompt)

    def test_construct_prompt_basic_selection_and_none_value(self):
        selected_quantities = {"R101": 2, "C202": 1, "U303": 1}
        expected_component_lines = [
            "  - R101 (Type: Resistor, Value: 10k): Quantity 2",
            "  - C202 (Type: Capacitor, Value: 100nF): Quantity 1",
            "  - U303 (Type: Integrated Circuit, Value: N/A): Quantity 1"
        ]
        expected_component_block = "\n".join(expected_component_lines)

        prompt = construct_generation_prompt(self.components, selected_quantities, self.type_mapping)
        self.assertIsNotNone(prompt)
        self.assertIn("Available Components:", prompt)
        self.assertIn(expected_component_block, prompt)
        self.assertTrue(prompt.endswith("Be extremely direct and brief."))
        self.assertTrue(prompt.startswith("You are an electronics lecturer"))
        self.assertIn("--Project Title:--", prompt)
        self.assertIn("--Description:--", prompt)
        self.assertIn("--Component Usage:--", prompt)

    def test_construct_prompt_type_mapping_miss(self):
        selected_quantities = {"T505": 1}
        expected_component_lines = [
            "  - T505 (Type: TRANSISTOR_BJT, Value: BC547): Quantity 1"
        ]
        expected_component_block = "\n".join(expected_component_lines)

        prompt = construct_generation_prompt(self.components, selected_quantities, self.type_mapping)
        self.assertIsNotNone(prompt)
        self.assertIn(expected_component_block, prompt)


    def test_process_ideas_no_data(self):
        f = io.StringIO()
        with redirect_stdout(f):
            process_ideas(self.dummy_instance, None)
        output_none = f.getvalue()

        f = io.StringIO()
        with redirect_stdout(f):
            process_ideas(self.dummy_instance, [])
        output_empty = f.getvalue()

        expected_msg = "[Backend] No components data received."
        self.assertIn(expected_msg, output_none)
        self.assertIn(expected_msg, output_empty)
        self.assertTrue(output_none.strip().startswith("--- [Backend] Generating Ideas"))
        self.assertTrue(output_none.strip().endswith("-----------------------------------------------------------"))
        self.assertTrue(output_empty.strip().startswith("--- [Backend] Generating Ideas"))
        self.assertTrue(output_empty.strip().endswith("-----------------------------------------------------------"))


    def test_process_ideas_with_data(self):
        selected_data = [
            {"part_number": "R1", "type": "Resistor", "value": "1k", "project_quantity": 5},
            {"part_number": "C1", "type": "Capacitor", "value": "10uF", "project_quantity": 2},
        ]
        f = io.StringIO()
        with redirect_stdout(f):
            process_ideas(self.dummy_instance, selected_data)
        output = f.getvalue()

        expected_line1 = "  - Part: R1, Type: Resistor, Value: 1k, Project Qty: 5"
        expected_line2 = "  - Part: C1, Type: Capacitor, Value: 10uF, Project Qty: 2"

        self.assertIn(expected_line1, output)
        self.assertIn(expected_line2, output)
        self.assertTrue(output.strip().startswith("--- [Backend] Generating Ideas"))
        self.assertTrue(output.strip().endswith("-----------------------------------------------------------"))


    def test_process_ideas_with_missing_keys(self):
        selected_data = [
            {"part_number": "R1", "type": "Resistor", "project_quantity": 5},
            {"part_number": "C1", "value": "10uF", "project_quantity": 2},
            {"part_number": "U1"},
        ]
        f = io.StringIO()
        with redirect_stdout(f):
            process_ideas(self.dummy_instance, selected_data)
        output = f.getvalue()

        expected_line1 = "  - Part: R1, Type: Resistor, Value: N/A, Project Qty: 5"
        expected_line2 = "  - Part: C1, Type: N/A, Value: 10uF, Project Qty: 2"
        expected_line3 = "  - Part: U1, Type: N/A, Value: N/A, Project Qty: ?"

        self.assertIn(expected_line1, output)
        self.assertIn(expected_line2, output)
        self.assertIn(expected_line3, output)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)