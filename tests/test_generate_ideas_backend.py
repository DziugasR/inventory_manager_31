import unittest
import io
import contextlib

from backend.generate_ideas_backend import GenerateIdeasBackend

class TestGenerateIdeasBackend(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.backend = GenerateIdeasBackend()
        # Sample data for testing
        self.sample_data_full = [
            {"part_number": "R101", "type": "Resistor", "value": "10k", "project_quantity": 1},
            {"part_number": "C202", "type": "Capacitor", "value": "100nF", "project_quantity": 2},
        ]
        self.sample_data_missing_keys = [
            {"part_number": "U303", "type": "IC"}, # Missing value and quantity
            {"value": "LED", "project_quantity": 5}, # Missing part_number and type
        ]
        self.sample_data_single = [
             {"part_number": "Q1", "type": "Transistor", "value": "2N3904", "project_quantity": 3},
        ]

    def test_initialization(self):
        """Test if the backend object initializes correctly."""
        self.assertIsInstance(self.backend, GenerateIdeasBackend)

    def test_process_ideas_with_empty_list(self):
        """Test processing with an empty list of selected data."""
        with contextlib.redirect_stdout(io.StringIO()) as captured_output:
            self.backend.process_ideas([])
        output = captured_output.getvalue()

        self.assertIn("--- [Backend] Generating Ideas Based On Selected Components ---", output)
        self.assertIn("[Backend] No components data received.", output)
        self.assertIn("-----------------------------------------------------------\n", output)
        # Ensure no specific component lines are printed
        self.assertNotIn("Part:", output)

    def test_process_ideas_with_none(self):
        """Test processing with None as selected data."""
        with contextlib.redirect_stdout(io.StringIO()) as captured_output:
            self.backend.process_ideas(None)
        output = captured_output.getvalue()

        self.assertIn("--- [Backend] Generating Ideas Based On Selected Components ---", output)
        self.assertIn("[Backend] No components data received.", output)
        self.assertIn("-----------------------------------------------------------\n", output)
        self.assertNotIn("Part:", output)

    def test_process_ideas_with_full_data(self):
        """Test processing with a list of components having all keys."""
        with contextlib.redirect_stdout(io.StringIO()) as captured_output:
            self.backend.process_ideas(self.sample_data_full)
        output = captured_output.getvalue()

        self.assertIn("--- [Backend] Generating Ideas Based On Selected Components ---", output)
        self.assertIn("Part: R101, Type: Resistor, Value: 10k, Project Qty: 1", output)
        self.assertIn("Part: C202, Type: Capacitor, Value: 100nF, Project Qty: 2", output)
        self.assertIn("-----------------------------------------------------------\n", output)
        self.assertNotIn("[Backend] No components data received.", output)

    def test_process_ideas_with_single_item(self):
        """Test processing with a list containing a single component."""
        with contextlib.redirect_stdout(io.StringIO()) as captured_output:
            self.backend.process_ideas(self.sample_data_single)
        output = captured_output.getvalue()

        self.assertIn("--- [Backend] Generating Ideas Based On Selected Components ---", output)
        self.assertIn("Part: Q1, Type: Transistor, Value: 2N3904, Project Qty: 3", output)
        self.assertIn("-----------------------------------------------------------\n", output)
        self.assertNotIn("[Backend] No components data received.", output)

    def test_process_ideas_with_missing_keys(self):
        """Test processing components where some dictionary keys are missing."""
        with contextlib.redirect_stdout(io.StringIO()) as captured_output:
            self.backend.process_ideas(self.sample_data_missing_keys)
        output = captured_output.getvalue()

        self.assertIn("--- [Backend] Generating Ideas Based On Selected Components ---", output)
        # Check that defaults are used correctly (.get(key, default))
        self.assertIn("Part: U303, Type: IC, Value: N/A, Project Qty: ?", output)
        self.assertIn("Part: N/A, Type: N/A, Value: LED, Project Qty: 5", output)
        self.assertIn("-----------------------------------------------------------\n", output)
        self.assertNotIn("[Backend] No components data received.", output)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)