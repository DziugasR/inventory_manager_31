import unittest
from backend.inventory import add_component, remove_component_by_part_number, get_all_components
from backend.database import get_session

class TestInventory(unittest.TestCase):
    def setUp(self):
        """ Create a session before each test """
        self.session = get_session()

    def tearDown(self):
        """ Rollback changes and close session after each test """
        self.session.rollback()
        self.session.close()

    def test_add_component(self):
        """ Test if components are added correctly """
        success = add_component("T3001", "Transistor", "transistor", "NPN", 5, "http://buy.com", "http://datasheet.com")
        self.assertTrue(success)

        components = get_all_components()
        self.assertTrue(any(c.part_number == "T3001" for c in components))

    def test_remove_component(self):
        """ Test if a component is removed correctly """
        add_component("L4001", "Inductor", "inductor", "10mH", 3, None, None)
        success = remove_component_by_part_number("L4001")
        self.assertTrue(success)

        components = get_all_components()
        self.assertFalse(any(c.part_number == "L4001" for c in components))

if __name__ == "__main__":
    unittest.main()