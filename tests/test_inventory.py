import unittest
from unittest.mock import patch, MagicMock, PropertyMock

# Modules to test
from backend import inventory
# Dependencies to mock or use
from backend.models import Component
from backend.exceptions import (
    InvalidInputError, DuplicateComponentError, ComponentError, DatabaseError,
    InvalidQuantityError, ComponentNotFoundError, StockError
)

# Helper to create mock Component instances easily
def create_mock_component(**kwargs):
    mock = MagicMock(spec=Component)
    # Set attributes provided in kwargs
    for key, value in kwargs.items():
        setattr(mock, key, value)
    # Ensure 'quantity' attribute exists if not provided, default to 0
    if 'quantity' not in kwargs:
        mock.quantity = 0
    # Ensure 'id' attribute exists if not provided, default to None or a mock value
    if 'id' not in kwargs:
        mock.id = MagicMock() # Or a specific int if needed for tests
    return mock

class TestInventoryFunctions(unittest.TestCase):

    # --- Test add_component ---

    @patch('backend.inventory.ComponentFactory.create_component')
    @patch('backend.inventory.get_session')
    def test_add_component_success(self, mock_get_session, mock_create_component):
        """Test successfully adding a new component."""
        # Arrange Mocks
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        # Simulate component NOT found
        mock_filter_by.first.return_value = None
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        mock_comp_instance = create_mock_component(part_number="PN123", quantity=10)
        mock_create_component.return_value = mock_comp_instance

        # Act
        result = inventory.add_component(
            part_number="PN123", name="Test Comp", component_type="RES", value="1k",
            quantity=10, purchase_link="link1", datasheet_link="link2"
        )

        # Assert
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        mock_filter_by.first.assert_called_once()
        mock_create_component.assert_called_once_with(
            "RES", part_number="PN123", name="Test Comp", value="1k",
            quantity=10, purchase_link="link1", datasheet_link="link2"
        )
        mock_session.add.assert_called_once_with(mock_comp_instance)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_comp_instance)

    @patch('backend.inventory.ComponentFactory.create_component')
    @patch('backend.inventory.get_session')
    def test_add_component_duplicate(self, mock_get_session, mock_create_component):
        """Test adding a component that already exists."""
        # Arrange Mocks
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        # Simulate component IS found
        mock_filter_by.first.return_value = create_mock_component(part_number="PN123")
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act & Assert
        with self.assertRaises(DuplicateComponentError) as cm:
            inventory.add_component(
                part_number="PN123", name="Test Comp", component_type="RES", value="1k",
                quantity=10, purchase_link="link1", datasheet_link="link2"
            )
        self.assertIn("Component with part number PN123 already exists", str(cm.exception))
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN123")
        mock_filter_by.first.assert_called_once()
        mock_create_component.assert_not_called()
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once() # Rolled back after exception
        mock_session.close.assert_called_once()

    @patch('backend.inventory.ComponentFactory.create_component')
    @patch('backend.inventory.get_session')
    def test_add_component_factory_error(self, mock_get_session, mock_create_component):
        """Test error during component creation by factory."""
        # Arrange Mocks
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_filter_by.first.return_value = None # Simulate not found initially
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        mock_create_component.side_effect = InvalidInputError("Bad factory input")

        # Act & Assert
        with self.assertRaises(InvalidInputError) as cm:
            inventory.add_component("PN456", "Name", "CAP", "1uF", 5, None, None)
        self.assertEqual(str(cm.exception), "Bad factory input")
        mock_create_component.assert_called_once()
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.ComponentFactory.create_component')
    @patch('backend.inventory.get_session')
    def test_add_component_database_error_on_commit(self, mock_get_session, mock_create_component):
        """Test a generic database error during commit."""
        # Arrange Mocks
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_filter_by.first.return_value = None # Simulate not found
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session
        mock_session.commit.side_effect = Exception("DB connection lost") # Generic Exception

        mock_comp_instance = create_mock_component(part_number="PN789")
        mock_create_component.return_value = mock_comp_instance

        # Act & Assert
        with self.assertRaises(DatabaseError) as cm:
             inventory.add_component("PN789", "Name", "DIODE", "1N4001", 20, None, None)
        self.assertIn("Database error: DB connection lost", str(cm.exception))
        mock_session.add.assert_called_once_with(mock_comp_instance)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    # --- Test remove_component_quantity ---

    def test_remove_component_quantity_invalid_input(self):
        """Test removing quantity with invalid (non-positive) input."""
        with self.assertRaises(InvalidQuantityError):
            inventory.remove_component_quantity("PN1", 0)
        with self.assertRaises(InvalidQuantityError):
            inventory.remove_component_quantity("PN1", -5)
        with self.assertRaises(InvalidQuantityError):
            inventory.remove_component_quantity("PN1", "abc") # Type check

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_success_reduces(self, mock_get_session):
        """Test successfully removing quantity, reducing stock."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_comp = create_mock_component(part_number="PN1", quantity=10)
        mock_filter_by.first.return_value = mock_comp
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act
        result = inventory.remove_component_quantity("PN1", 3)

        # Assert
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="PN1")
        mock_filter_by.first.assert_called_once()
        self.assertEqual(mock_comp.quantity, 7) # Quantity reduced
        mock_session.delete.assert_not_called() # Not deleted
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_comp)

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_success_deletes(self, mock_get_session):
        """Test successfully removing quantity which results in deletion."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_comp = create_mock_component(part_number="PN2", quantity=5)
        mock_filter_by.first.return_value = mock_comp
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act
        result = inventory.remove_component_quantity("PN2", 5)

        # Assert
        self.assertEqual(mock_comp.quantity, 0) # Quantity becomes zero
        mock_session.delete.assert_called_once_with(mock_comp) # Should be deleted
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_comp)

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_not_found(self, mock_get_session):
        """Test removing quantity from a non-existent component."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_filter_by.first.return_value = None # Simulate not found
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act & Assert
        with self.assertRaises(ComponentNotFoundError) as cm:
            inventory.remove_component_quantity("PN_NOT_EXIST", 2)
        self.assertIn("Component with part number PN_NOT_EXIST not found", str(cm.exception))
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_not_enough_stock(self, mock_get_session):
        """Test removing more quantity than available."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_comp = create_mock_component(part_number="PN3", quantity=3)
        mock_filter_by.first.return_value = mock_comp
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act & Assert
        with self.assertRaises(StockError) as cm:
            inventory.remove_component_quantity("PN3", 5)
        self.assertIn("Not enough stock to remove 5. Available: 3", str(cm.exception))
        self.assertEqual(mock_comp.quantity, 3) # Quantity unchanged
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_db_error(self, mock_get_session):
        """Test database error during remove operation."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_comp = create_mock_component(part_number="PN4", quantity=10)
        mock_filter_by.first.return_value = mock_comp
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session
        mock_session.commit.side_effect = Exception("DB write failed")

        # Act & Assert
        with self.assertRaises(DatabaseError) as cm:
            inventory.remove_component_quantity("PN4", 2)
        self.assertIn("Error while removing component: DB write failed", str(cm.exception))
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    # --- Test get_component_by_part_number ---

    @patch('backend.inventory.get_session')
    def test_get_component_by_part_number_found(self, mock_get_session):
        """Test finding an existing component by part number."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_comp = create_mock_component(part_number="GET_PN1")
        mock_filter_by.first.return_value = mock_comp
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act
        result = inventory.get_component_by_part_number("GET_PN1")

        # Assert
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="GET_PN1")
        mock_filter_by.first.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_comp)

    @patch('backend.inventory.get_session')
    def test_get_component_by_part_number_not_found(self, mock_get_session):
        """Test getting a component that doesn't exist."""
         # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_filter_by.first.return_value = None # Simulate not found
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act
        result = inventory.get_component_by_part_number("GET_PN_MISSING")

        # Assert
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(part_number="GET_PN_MISSING")
        mock_filter_by.first.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertIsNone(result)

    @patch('backend.inventory.get_session')
    def test_get_component_by_part_number_db_error(self, mock_get_session):
        """Test database error during get component by part number."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter_by.side_effect = Exception("DB read failed") # Error on filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act & Assert
        with self.assertRaises(DatabaseError) as cm:
            inventory.get_component_by_part_number("GET_PN_ERROR")
        self.assertIn("Error while fetching component by part number GET_PN_ERROR: DB read failed", str(cm.exception))
        mock_session.close.assert_called_once() # Finally block should still close


    # --- Test get_all_components ---

    @patch('backend.inventory.get_session')
    def test_get_all_components_success(self, mock_get_session):
        """Test successfully fetching all components."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_comps = [create_mock_component(part_number="ALL1"), create_mock_component(part_number="ALL2")]
        mock_query.all.return_value = mock_comps
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act
        result = inventory.get_all_components()

        # Assert
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.all.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_comps)

    @patch('backend.inventory.get_session')
    def test_get_all_components_db_error(self, mock_get_session):
        """Test database error during fetch all."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.all.side_effect = Exception("Fetch all failed")
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act & Assert
        with self.assertRaises(DatabaseError) as cm:
            inventory.get_all_components()
        self.assertIn("Error while fetching components: Fetch all failed", str(cm.exception))
        mock_session.close.assert_called_once()

    # --- Test update_component_quantity ---

    def test_update_component_quantity_invalid_input(self):
        """Test updating quantity with invalid (negative or non-int) input."""
        with self.assertRaises(InvalidQuantityError):
            inventory.update_component_quantity(1, -1)
        with self.assertRaises(InvalidQuantityError):
            inventory.update_component_quantity(1, "abc")

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_success(self, mock_get_session):
        """Test successfully updating component quantity."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_comp = create_mock_component(id=5, part_number="UPD1", quantity=10)
        mock_filter_by.first.return_value = mock_comp
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act
        result = inventory.update_component_quantity(5, 25)

        # Assert
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        mock_query.filter_by.assert_called_once_with(id=5)
        mock_filter_by.first.assert_called_once()
        self.assertEqual(mock_comp.quantity, 25) # Quantity updated
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_comp)

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_not_found(self, mock_get_session):
        """Test updating quantity for a component not found by ID."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_filter_by.first.return_value = None # Simulate not found
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        # Act & Assert
        with self.assertRaises(ComponentNotFoundError) as cm:
            inventory.update_component_quantity(999, 10)
        self.assertIn("Component with ID 999 not found", str(cm.exception))
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_db_error(self, mock_get_session):
        """Test database error during update quantity."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter_by = MagicMock()
        mock_comp = create_mock_component(id=6, quantity=5)
        mock_filter_by.first.return_value = mock_comp
        mock_query.filter_by.return_value = mock_filter_by
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session
        mock_session.commit.side_effect = Exception("Update failed")

        # Act & Assert
        with self.assertRaises(DatabaseError) as cm:
            inventory.update_component_quantity(6, 10)
        self.assertIn("Error while updating component quantity: Update failed", str(cm.exception))
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    # --- Test select_multiple_components ---

    def test_select_multiple_components_empty_input(self):
        """Test selecting with an empty list of part numbers."""
        result = inventory.select_multiple_components([])
        self.assertEqual(result, [])
        # Crucially, get_session should not be called for an empty input list
        # (Need to check if patch was active - better to test this way)
        with patch('backend.inventory.get_session') as mock_get_session_local:
             inventory.select_multiple_components([])
             mock_get_session_local.assert_not_called()


    @patch('backend.inventory.get_session')
    def test_select_multiple_components_success(self, mock_get_session):
        """Test selecting multiple components successfully."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_comps = [create_mock_component(part_number="MULTI1"), create_mock_component(part_number="MULTI3")]
        mock_filter.all.return_value = mock_comps
        # Mock the 'in_' operator filtering
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        part_numbers = ["MULTI1", "MULTI2", "MULTI3"]

        # Act
        result = inventory.select_multiple_components(part_numbers)

        # Assert
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        # Check that filter was called with the 'in_' condition (tricky to assert precisely without complex mock setup)
        # We'll rely on checking that filter().all() was called and returns the correct result.
        self.assertTrue(mock_query.filter.called)
        mock_filter.all.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_comps)

    @patch('backend.inventory.get_session')
    def test_select_multiple_components_none_found(self, mock_get_session):
        """Test selecting multiple components where none match."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = [] # Simulate none found
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        part_numbers = ["MISSING1", "MISSING2"]

        # Act
        result = inventory.select_multiple_components(part_numbers)

        # Assert
        mock_get_session.assert_called_once()
        mock_session.query.assert_called_once_with(Component)
        self.assertTrue(mock_query.filter.called)
        mock_filter.all.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, [])

    @patch('backend.inventory.get_session')
    def test_select_multiple_components_db_error(self, mock_get_session):
        """Test database error during select multiple."""
        # Arrange
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.side_effect = Exception("Multi-select failed")
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query
        mock_get_session.return_value = mock_session

        part_numbers = ["PN_ERR1", "PN_ERR2"]

        # Act & Assert
        with self.assertRaises(DatabaseError) as cm:
            inventory.select_multiple_components(part_numbers)
        self.assertIn("Error selecting multiple components: Multi-select failed", str(cm.exception))
        mock_session.close.assert_called_once()


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)