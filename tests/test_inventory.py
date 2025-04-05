import unittest
from unittest.mock import patch, MagicMock, ANY # ANY helps match arguments flexibly

# Assuming your project structure allows these imports
# If 'backend' is not directly importable, adjust sys.path or run tests differently
from backend import inventory
from backend.models import Component # We might mock instances, but import is good practice
from backend.exceptions import (
    InvalidInputError, DuplicateComponentError, ComponentError, DatabaseError,
    InvalidQuantityError, ComponentNotFoundError, StockError
)

# Define dummy component types if ComponentFactory relies on them
# Or mock ComponentFactory.create_component directly
DUMMY_COMPONENT_TYPE = "Resistor"

class TestInventory(unittest.TestCase):

    def setUp(self):
        """Set up mocks common to multiple tests."""
        # Mock the Component class minimally if needed for type checks or basic attrs
        # Often, MagicMock instances returned by the mocked session are enough
        self.mock_component_instance = MagicMock(spec=Component)
        self.mock_component_instance.id = 1
        self.mock_component_instance.part_number = "PN123"
        self.mock_component_instance.name = "Test Resistor"
        self.mock_component_instance.component_type = DUMMY_COMPONENT_TYPE
        self.mock_component_instance.value = "10k"
        self.mock_component_instance.quantity = 100
        self.mock_component_instance.purchase_link = "http://example.com/buy"
        self.mock_component_instance.datasheet_link = "http://example.com/data"

    # --- Test add_component ---

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_success(self, mock_component_factory, mock_get_session):
        """Test successfully adding a new component."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None # No existing component
        mock_get_session.return_value = mock_session

        # Configure ComponentFactory mock
        created_component = MagicMock(spec=Component) # Simulate the created component
        mock_component_factory.create_component.return_value = created_component

        part_number = "NEWPN456"
        name = "New Cap"
        component_type = "Capacitor"
        value = "10uF"
        quantity = 50
        purchase_link = "link1"
        datasheet_link = "link2"

        result = inventory.add_component(
            part_number, name, component_type, value, quantity, purchase_link, datasheet_link
        )

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number=part_number)
        mock_component_factory.create_component.assert_called_once_with(
            component_type,
            part_number=part_number,
            name=name,
            value=value,
            quantity=quantity,
            purchase_link=purchase_link,
            datasheet_link=datasheet_link
        )
        mock_session.add.assert_called_once_with(created_component)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertEqual(result, created_component)

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_duplicate(self, mock_component_factory, mock_get_session):
        """Test adding a component that already exists."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        # Simulate finding an existing component
        mock_query.filter_by.return_value.first.return_value = self.mock_component_instance
        mock_get_session.return_value = mock_session

        with self.assertRaises(DuplicateComponentError) as cm:
            inventory.add_component("PN123", "Name", "Type", "Value", 10, "link1", "link2")

        self.assertEqual(
            str(cm.exception),
            "Component with part number PN123 already exists"
        )
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        mock_component_factory.create_component.assert_not_called()
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once() # Rollback called on exception
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_factory_error(self, mock_component_factory, mock_get_session):
        """Test error during component creation by factory."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None # Not a duplicate
        mock_get_session.return_value = mock_session

        # Simulate ComponentFactory raising an error (e.g., InvalidInputError)
        mock_component_factory.create_component.side_effect = InvalidInputError("Bad type")

        with self.assertRaises(InvalidInputError) as cm:
             inventory.add_component("PN789", "Name", "BadType", "Val", 5, "l1", "l2")

        self.assertEqual(str(cm.exception), "Bad type")
        mock_get_session.assert_called_once()
        mock_query.filter_by.assert_called_once_with(part_number="PN789")
        mock_component_factory.create_component.assert_called_once() # It was called
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_database_error_on_commit(self, mock_component_factory, mock_get_session):
        """Test a database error during commit."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None
        mock_get_session.return_value = mock_session
        mock_component_factory.create_component.return_value = MagicMock(spec=Component)

        # Simulate commit error
        mock_session.commit.side_effect = Exception("DB connection lost")

        with self.assertRaises(DatabaseError) as cm:
            inventory.add_component("PN789", "Name", "Type", "Val", 5, "l1", "l2")

        self.assertTrue("Database error: DB connection lost" in str(cm.exception))
        mock_get_session.assert_called_once()
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    # --- Test remove_component_quantity ---

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_success_partial(self, mock_get_session):
        """Test removing a quantity less than the total stock."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        # Clone the component mock to avoid side effects between tests if needed
        test_component = MagicMock(spec=Component, quantity=100, part_number="PN123")
        mock_query.filter_by.return_value.first.return_value = test_component
        mock_get_session.return_value = mock_session

        quantity_to_remove = 20
        result = inventory.remove_component_quantity("PN123", quantity_to_remove)

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        self.assertEqual(test_component.quantity, 100 - quantity_to_remove)
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertEqual(result, test_component) # Returns the updated component

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_success_full_delete(self, mock_get_session):
        """Test removing the exact quantity, leading to deletion."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        test_component = MagicMock(spec=Component, quantity=30, part_number="PN123")
        mock_query.filter_by.return_value.first.return_value = test_component
        mock_get_session.return_value = mock_session

        quantity_to_remove = 30
        result = inventory.remove_component_quantity("PN123", quantity_to_remove)

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        self.assertEqual(test_component.quantity, 0)
        mock_session.delete.assert_called_once_with(test_component) # Should be deleted
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertEqual(result, test_component) # Returns the component *before* delete commit? Or None? Check logic. Returns component.

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_not_found(self, mock_get_session):
        """Test removing quantity from a non-existent component."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None # Not found
        mock_get_session.return_value = mock_session

        with self.assertRaises(ComponentNotFoundError) as cm:
            inventory.remove_component_quantity("PN_NOT_EXIST", 10)

        self.assertEqual(
            str(cm.exception),
            "Component with part number PN_NOT_EXIST not found"
        )
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN_NOT_EXIST")
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_not_enough_stock(self, mock_get_session):
        """Test removing more quantity than available."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        test_component = MagicMock(spec=Component, quantity=5, part_number="PN123")
        mock_query.filter_by.return_value.first.return_value = test_component
        mock_get_session.return_value = mock_session

        with self.assertRaises(StockError) as cm:
            inventory.remove_component_quantity("PN123", 10)

        self.assertEqual(
            str(cm.exception),
            "Not enough stock to remove 10. Available: 5"
        )
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        self.assertEqual(test_component.quantity, 5) # Quantity should be unchanged
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_remove_component_quantity_invalid_quantity(self):
        """Test removing with invalid quantity values."""
        with self.assertRaises(InvalidQuantityError):
            inventory.remove_component_quantity("PN123", 0)
        with self.assertRaises(InvalidQuantityError):
            inventory.remove_component_quantity("PN123", -5)
        with self.assertRaises(InvalidQuantityError):
            inventory.remove_component_quantity("PN123", "abc") # Should also fail type check
        with self.assertRaises(InvalidQuantityError):
             inventory.remove_component_quantity("PN123", 5.5) # Should also fail type check

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_database_error(self, mock_get_session):
        """Test database error during quantity removal commit."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        test_component = MagicMock(spec=Component, quantity=100, part_number="PN123")
        mock_query.filter_by.return_value.first.return_value = test_component
        mock_get_session.return_value = mock_session

        # Simulate commit error
        mock_session.commit.side_effect = Exception("DB Write Lock")

        with self.assertRaises(DatabaseError) as cm:
            inventory.remove_component_quantity("PN123", 10)

        self.assertTrue("Error while removing component: DB Write Lock" in str(cm.exception))
        self.assertEqual(test_component.quantity, 90) # Change happens before commit fails
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    # --- Test remove_component_by_part_number ---

    @patch('backend.inventory.get_session')
    def test_remove_component_by_part_number_success(self, mock_get_session):
        """Test successfully removing a component by part number."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = self.mock_component_instance
        mock_get_session.return_value = mock_session

        result = inventory.remove_component_by_part_number("PN123")

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        mock_session.delete.assert_called_once_with(self.mock_component_instance)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertTrue(result)

    @patch('backend.inventory.get_session')
    def test_remove_component_by_part_number_not_found(self, mock_get_session):
        """Test removing a non-existent component by part number."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None # Not found
        mock_get_session.return_value = mock_session

        with self.assertRaises(ComponentNotFoundError) as cm:
            inventory.remove_component_by_part_number("PN_NOT_EXIST")

        self.assertEqual(
            str(cm.exception),
            "Component with part number PN_NOT_EXIST not found"
        )
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN_NOT_EXIST")
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_remove_component_by_part_number_database_error(self, mock_get_session):
        """Test database error during component deletion commit."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = self.mock_component_instance
        mock_get_session.return_value = mock_session

        # Simulate commit error
        mock_session.commit.side_effect = Exception("Constraint Violation")

        with self.assertRaises(DatabaseError) as cm:
            inventory.remove_component_by_part_number("PN123")

        self.assertTrue("Error while deleting component: Constraint Violation" in str(cm.exception))
        mock_session.delete.assert_called_once_with(self.mock_component_instance) # Delete called before commit
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    # --- Test get_component_by_part_number ---

    @patch('backend.inventory.get_session')
    def test_get_component_by_part_number_found(self, mock_get_session):
        """Test retrieving an existing component by part number."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = self.mock_component_instance
        mock_get_session.return_value = mock_session

        result = inventory.get_component_by_part_number("PN123")

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        mock_session.close.assert_called_once()
        self.assertEqual(result, self.mock_component_instance)

    @patch('backend.inventory.get_session')
    def test_get_component_by_part_number_not_found(self, mock_get_session):
        """Test retrieving a non-existent component by part number."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None # Not found
        mock_get_session.return_value = mock_session

        result = inventory.get_component_by_part_number("PN_NOT_EXIST")

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN_NOT_EXIST")
        mock_session.close.assert_called_once()
        self.assertIsNone(result)

    @patch('backend.inventory.get_session')
    def test_get_component_by_part_number_database_error(self, mock_get_session):
        """Test database error during component retrieval."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        # Simulate query error
        mock_query.filter_by.return_value.first.side_effect = Exception("Query Failed")
        mock_get_session.return_value = mock_session

        with self.assertRaises(DatabaseError) as cm:
            inventory.get_component_by_part_number("PN123")

        self.assertTrue("Error while fetching component by part number PN123: Query Failed" in str(cm.exception))
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        mock_session.close.assert_called_once() # Finally block ensures close

    # --- Test get_all_components ---

    @patch('backend.inventory.get_session')
    def test_get_all_components_success(self, mock_get_session):
        """Test retrieving all components."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_components_list = [self.mock_component_instance, MagicMock(spec=Component)]
        mock_query.all.return_value = mock_components_list
        mock_get_session.return_value = mock_session

        result = inventory.get_all_components()

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.all.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_components_list)

    @patch('backend.inventory.get_session')
    def test_get_all_components_empty(self, mock_get_session):
        """Test retrieving all components when the database is empty."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.all.return_value = [] # Empty list
        mock_get_session.return_value = mock_session

        result = inventory.get_all_components()

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.all.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, [])

    @patch('backend.inventory.get_session')
    def test_get_all_components_database_error(self, mock_get_session):
        """Test database error during retrieval of all components."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        # Simulate query error
        mock_query.all.side_effect = Exception("Table Lock")
        mock_get_session.return_value = mock_session

        with self.assertRaises(DatabaseError) as cm:
            inventory.get_all_components()

        self.assertTrue("Error while fetching components: Table Lock" in str(cm.exception))
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.all.assert_called_once()
        mock_session.close.assert_called_once() # Finally block

    # --- Test update_component_quantity ---

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_success(self, mock_get_session):
        """Test successfully updating a component's quantity."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        test_component = MagicMock(spec=Component, id=5, quantity=50)
        mock_query.filter_by.return_value.first.return_value = test_component
        mock_get_session.return_value = mock_session

        new_quantity = 75
        result = inventory.update_component_quantity(5, new_quantity)

        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(id=5)
        self.assertEqual(test_component.quantity, new_quantity)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertEqual(result, test_component) # Returns updated component

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_not_found(self, mock_get_session):
        """Test updating quantity for a non-existent component ID."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None # Not found
        mock_get_session.return_value = mock_session

        with self.assertRaises(ComponentNotFoundError) as cm:
            inventory.update_component_quantity(999, 10)

        self.assertEqual(
            str(cm.exception),
            "Component with ID 999 not found"
        )
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(id=999)
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_update_component_quantity_invalid_quantity(self):
        """Test updating with invalid quantity values."""
        with self.assertRaises(InvalidQuantityError):
            inventory.update_component_quantity(1, -1)
        with self.assertRaises(InvalidQuantityError):
            inventory.update_component_quantity(1, "abc")
        with self.assertRaises(InvalidQuantityError):
            inventory.update_component_quantity(1, 10.5)

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_database_error(self, mock_get_session):
        """Test database error during quantity update commit."""
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        test_component = MagicMock(spec=Component, id=5, quantity=50)
        mock_query.filter_by.return_value.first.return_value = test_component
        mock_get_session.return_value = mock_session

        # Simulate commit error
        mock_session.commit.side_effect = Exception("DB Update Failed")

        with self.assertRaises(DatabaseError) as cm:
            inventory.update_component_quantity(5, 75)

        self.assertTrue("Error while updating component quantity: DB Update Failed" in str(cm.exception))
        self.assertEqual(test_component.quantity, 75) # Update happens before commit
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False) # Use exit=False if running in interactive env like Jupyter