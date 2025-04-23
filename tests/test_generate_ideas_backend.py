import unittest

from backend.generate_ideas_backend import construct_generation_prompt

class MockComponent:
    def __init__(self, part_number, component_type, value, quantity):
        self.part_number = part_number
        self.component_type = component_type
        self.value = value
        self.quantity = quantity

class TestConstructGenerationPrompt(unittest.TestCase):

    def test_prompt_generation_with_selected_components(self):
        comp1 = MockComponent("R101", "resistor", "10k", 10)
        comp2 = MockComponent("C202", "capacitor", "100uF", 5)
        comp3 = MockComponent("LED3", "led", None, 20) # Component with None value
        comp4 = MockComponent("IC404", "ic", "LM555", 2)

        components = [comp1, comp2, comp3, comp4]
        selected_quantities = {"R101": 2, "C202": 0, "LED3": 5, "IC404": 1}
        type_mapping = {"resistor": "Resistor", "capacitor": "Capacitor", "led": "LED", "ic": "Integrated Circuit"}

        expected_r101_line = "  - R101 (Type: Resistor, Value: 10k): Quantity 2"
        expected_led3_line = "  - LED3 (Type: LED, Value: N/A): Quantity 5"
        expected_ic404_line = "  - IC404 (Type: Integrated Circuit, Value: LM555): Quantity 1"
        unexpected_c202_line = "C202"

        prompt = construct_generation_prompt(components, selected_quantities, type_mapping)

        self.assertIsNotNone(prompt)
        self.assertIn("You are an electronics lecturer", prompt)
        self.assertIn("Available Components:", prompt)
        self.assertIn(expected_r101_line, prompt)
        self.assertIn(expected_led3_line, prompt)
        self.assertIn(expected_ic404_line, prompt)
        self.assertNotIn(unexpected_c202_line, prompt)
        self.assertIn("--Project Title:--", prompt)
        self.assertIn("--Description:--", prompt)
        self.assertIn("--Component Usage:--", prompt)

    def test_prompt_generation_no_components_selected(self):
        comp1 = MockComponent("R101", "resistor", "10k", 10)
        comp2 = MockComponent("C202", "capacitor", "100uF", 5)

        components = [comp1, comp2]
        selected_quantities = {"R101": 0, "C202": 0}
        type_mapping = {"resistor": "Resistor", "capacitor": "Capacitor"}

        prompt = construct_generation_prompt(components, selected_quantities, type_mapping)

        self.assertIsNone(prompt)

    def test_prompt_generation_empty_component_list(self):
        components = []
        selected_quantities = {"R101": 1}
        type_mapping = {"resistor": "Resistor"}

        prompt = construct_generation_prompt(components, selected_quantities, type_mapping)

        self.assertIsNone(prompt)

    def test_prompt_generation_uses_fallback_type_name(self):
        comp1 = MockComponent("UNK01", "unknown_type", "Special", 1)
        components = [comp1]
        selected_quantities = {"UNK01": 1}
        type_mapping = {"known": "Known Type"}

        expected_unk01_line = "  - UNK01 (Type: unknown_type, Value: Special): Quantity 1"

        prompt = construct_generation_prompt(components, selected_quantities, type_mapping)

        self.assertIsNotNone(prompt)
        self.assertIn(expected_unk01_line, prompt)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)