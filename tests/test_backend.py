import unittest
from backend.inventory import add_component, get_all_components
from backend.database import get_session
from backend.models import Component


class TestInventoryFunctions(unittest.TestCase):

    def setUp(self):
        """ Set up the test environment. This will run before every test case. """
        self.session = get_session()

        # Clear all components before each test
        self.session.query(Component).delete()
        self.session.commit()

    def test_add_component(self):
        """ Test adding a new component. """
        # Add a test component
        add_component("ABC123", "Resistor", "Resistor", "10kΩ", 100)
        components = get_all_components()

        # Assert that one component is added
        self.assertEqual(len(components), 1)

        # Assert that the component's data is correct
        component = components[0]
        self.assertEqual(component.part_number, "ABC123")
        self.assertEqual(component.name, "Resistor")
        self.assertEqual(component.component_type, "Resistor")
        self.assertEqual(component.value, "10kΩ")
        self.assertEqual(component.quantity, 100)

    def test_get_all_components(self):
        """ Test fetching all components. """
        # Add multiple components
        add_component("ABC123", "Resistor", "Resistor", "10kΩ", 100)
        add_component("DEF456", "Capacitor", "Capacitor", "100uF", 200)
        add_component("XYZ789", "Transistor", "Transistor", "BC547", 150)

        components = get_all_components()

        # Assert that three components are added
        self.assertEqual(len(components), 3)

        # Check the names of the components

