import unittest
from backend.component_factory import ComponentFactory
from backend.models import Resistor, Capacitor

class TestComponentFactory(unittest.TestCase):
    def test_create_resistor(self):
        """ Test creating a Resistor using the factory """
        resistor = ComponentFactory.create_component("resistor", part_number="R1001", name="1KResistor", value="1KΩ", quantity=10)
        self.assertIsInstance(resistor, Resistor)
        self.assertEqual(resistor.part_number, "R1001")

    def test_create_capacitor(self):
        """ Test creating a Capacitor using the factory """
        capacitor = ComponentFactory.create_component("capacitor", part_number="C6001", name="10Capacitor", value="10µF", quantity=5)
        self.assertIsInstance(capacitor, Capacitor)
        self.assertEqual(capacitor.part_number, "C6001")

if __name__ == "__main__":
    unittest.main()