import unittest
from backend.database import get_session
from backend.models import Component
from backend.inventory import add_component, remove_component_by_part_number, get_all_components

class TestInventoryDatabase(unittest.TestCase):
    def setUp(self):
        """Ensure a clean state by deleting any test records."""
        self.session = get_session()
        # Remove any component with part_number "R1001" if it exists.
        self.session.query(Component).filter_by(part_number="R1001").delete()
        self.session.commit()

    def tearDown(self):
        """Rollback any changes and close the session."""
        self.session.rollback()
        self.session.close()

    def test_add_component(self):
        """Test that a component is added correctly."""
        # Call add_component using a lowercase type (or one that will be forced to lowercase)
        success = add_component(
            "R1001", "Resistor 1K", "resistor", "1KΩ", 10,
            "http://example.com", "http://example.com/datasheet"
        )
        self.assertTrue(success, "Component should be added successfully.")

        # Query the database to verify the record is present.
        result = self.session.query(Component).filter_by(part_number="R1001").first()
        self.assertIsNotNone(result, "Component with part number R1001 should be found in the database.")
        self.assertEqual(result.name, "Resistor 1K", "The component name should match.")
        self.assertEqual(result.component_type, "resistor", "Component type should be stored as 'resistor'.")

    def test_prevent_duplicate_component(self):
        """Test that a duplicate component is not added."""
        # First, ensure a component with R1001 does not exist.
        remove_component_by_part_number("R1001")
        # Add the component for the first time.
        success1 = add_component(
            "R1001", "Resistor 1K", "resistor", "1KΩ", 10,
            "http://example.com", "http://example.com/datasheet"
        )
        self.assertTrue(success1, "The first insertion should succeed.")

        # Try adding the same component again.
        success2 = add_component(
            "R1001", "Duplicate Resistor", "resistor", "1KΩ", 5,
            "http://example.com", "http://example.com/datasheet"
        )
        self.assertFalse(success2, "Duplicate insertion should fail.")

    def test_remove_component(self):
        """Test that a component can be removed correctly."""
        # Ensure no component with R1001 exists before the test.
        remove_component_by_part_number("R1001")
        # Add a component.
        add_component(
            "R1001", "Resistor 1K", "resistor", "1KΩ", 10,
            "http://example.com", "http://example.com/datasheet"
        )
        # Remove it.
        success = remove_component_by_part_number("R1001")
        self.assertTrue(success, "Component removal should succeed.")
        # Verify that it no longer exists.
        result = self.session.query(Component).filter_by(part_number="R1001").first()
        self.assertIsNone(result, "Component R1001 should no longer exist in the database.")

if __name__ == "__main__":
    unittest.main()
