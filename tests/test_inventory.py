import unittest
import uuid
from unittest.mock import patch, MagicMock

from backend import inventory
from backend.models import Component
from backend.exceptions import (
    InvalidInputError, InvalidQuantityError, ComponentNotFoundError, StockError,
    DatabaseError, ComponentError
)

# Use simple Component mocks for testing purposes
class MockComponent(MagicMock):
    def __init__(self, id=None, part_number="PN123", component_type="Resistor", value="10k", quantity=100, purchase_link=None, datasheet_link=None, **kwargs):
        super().__init__(**kwargs)
        self.id = id if id else uuid.uuid4()
        self.part_number = part_number
        self.component_type = component_type
        self.value = value
        self.quantity = quantity
        self.purchase_link = purchase_link
        self.datasheet_link = datasheet_link

    # Need to define __eq__ for comparisons in tests if using MagicMock directly
    def __eq__(self, other):
        if not isinstance(other, MockComponent):
            return NotImplemented
        return self.id == other.id

# Test suite for inventory functions
class TestInventory(unittest.TestCase):

    def setUp(self):
        # Create some mock components for use in tests
        self.comp1_id = uuid.uuid4()
        self.comp2_id = uuid.uuid4()
        self.mock_comp1 = MockComponent(id=self.comp1_id, part_number="PN101", quantity=50)
        self.mock_comp2 = MockComponent(id=self.comp2_id, part_number="PN102", quantity=10)
        self.mock_comp_zero_qty = MockComponent(id=uuid.uuid4(), part_number="PN000", quantity=0)

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_success(self, mock_factory, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_component_instance = MockComponent(part_number="TEST-PN", component_type="Capacitor", value="10uF", quantity=50)
        mock_factory.create_component.return_value = mock_component_instance

        result = inventory.add_component("TEST-PN", "Capacitor", "10uF", 50, "link1", "link2")

        mock_factory.create_component.assert_called_once_with(
            "Capacitor", part_number="TEST-PN", value="10uF", quantity=50, purchase_link="link1", datasheet_link="link2"
        )
        mock_session.add.assert_called_once_with(mock_component_instance)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_component_instance)

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_invalid_part_number(self, mock_factory, mock_get_session):
        with self.assertRaisesRegex(InvalidInputError, "Part number cannot be empty."):
            inventory.add_component("", "Resistor", "1k", 100, None, None)
        mock_get_session.assert_not_called() # Should fail before getting session

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_invalid_quantity(self, mock_factory, mock_get_session):
        with self.assertRaisesRegex(InvalidQuantityError, "Quantity cannot be negative."):
            inventory.add_component("PN999", "Resistor", "1k", -1, None, None)
        mock_get_session.assert_not_called() # Should fail before getting session

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_factory_error(self, mock_factory, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_factory.create_component.side_effect = ValueError("Invalid component type")

        with self.assertRaisesRegex(ValueError, "Invalid component type"):
             inventory.add_component("PN-ERR", "InvalidType", "N/A", 10, None, None)

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once() # Factory error happens before add/commit
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_database_error_on_add(self, mock_factory, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_component_instance = MockComponent()
        mock_factory.create_component.return_value = mock_component_instance
        mock_session.add.side_effect = Exception("Simulated DB error on add")

        with self.assertRaisesRegex(DatabaseError, "Database error during add: Simulated DB error on add"):
            inventory.add_component("PN-DB", "Resistor", "1k", 10, None, None)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    @patch('backend.inventory.ComponentFactory')
    def test_add_component_database_error_on_commit(self, mock_factory, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_component_instance = MockComponent()
        mock_factory.create_component.return_value = mock_component_instance
        mock_session.commit.side_effect = Exception("Simulated DB error on commit")

        with self.assertRaisesRegex(DatabaseError, "Database error during add: Simulated DB error on commit"):
            inventory.add_component("PN-DB", "Resistor", "1k", 10, None, None)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_success_partial(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        # Make a copy to avoid modifying the original mock in setUp
        component_to_update = MockComponent(id=self.comp1_id, part_number="PN101", quantity=50)
        mock_session.query.return_value.filter_by.return_value.first.return_value = component_to_update

        result = inventory.remove_component_quantity(self.comp1_id, 10)

        mock_session.query.return_value.filter_by.assert_called_once_with(id=self.comp1_id)
        self.assertEqual(component_to_update.quantity, 40)
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, component_to_update)
        self.assertEqual(result.quantity, 40)

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_success_full(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        component_to_delete = MockComponent(id=self.comp2_id, part_number="PN102", quantity=10)
        mock_session.query.return_value.filter_by.return_value.first.return_value = component_to_delete

        result = inventory.remove_component_quantity(self.comp2_id, 10)

        mock_session.query.return_value.filter_by.assert_called_once_with(id=self.comp2_id)
        self.assertEqual(component_to_delete.quantity, 0) # Quantity is updated first
        mock_session.delete.assert_called_once_with(component_to_delete)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertIsNone(result)

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_invalid_quantity_zero(self, mock_get_session):
        with self.assertRaisesRegex(InvalidQuantityError, "Quantity must be a positive integer"):
            inventory.remove_component_quantity(self.comp1_id, 0)
        mock_get_session.assert_not_called()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_invalid_quantity_negative(self, mock_get_session):
        with self.assertRaisesRegex(InvalidQuantityError, "Quantity must be a positive integer"):
            inventory.remove_component_quantity(self.comp1_id, -5)
        mock_get_session.assert_not_called()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_invalid_quantity_type(self, mock_get_session):
        with self.assertRaisesRegex(InvalidQuantityError, "Quantity must be a positive integer"):
            inventory.remove_component_quantity(self.comp1_id, "abc") # type: ignore
        mock_get_session.assert_not_called()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_not_found(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        non_existent_id = uuid.uuid4()

        with self.assertRaisesRegex(ComponentNotFoundError, f"Component with id {non_existent_id} not found"):
            inventory.remove_component_quantity(non_existent_id, 5)

        mock_session.query.return_value.filter_by.assert_called_once_with(id=non_existent_id)
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once() # Exception occurred
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_stock_error(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = self.mock_comp2 # Has quantity 10

        with self.assertRaisesRegex(StockError, "Not enough stock"):
            inventory.remove_component_quantity(self.comp2_id, 15)

        mock_session.query.return_value.filter_by.assert_called_once_with(id=self.comp2_id)
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once() # Exception occurred
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_database_error_on_commit(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        component_to_update = MockComponent(id=self.comp1_id, quantity=50)
        mock_session.query.return_value.filter_by.return_value.first.return_value = component_to_update
        mock_session.commit.side_effect = Exception("Simulated DB error on commit")

        with self.assertRaisesRegex(DatabaseError, "Error while removing component: Simulated DB error on commit"):
            inventory.remove_component_quantity(self.comp1_id, 10)

        self.assertEqual(component_to_update.quantity, 40) # Update happens before commit
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_remove_component_quantity_database_error_on_delete_commit(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        component_to_delete = MockComponent(id=self.comp2_id, quantity=10)
        mock_session.query.return_value.filter_by.return_value.first.return_value = component_to_delete
        mock_session.commit.side_effect = Exception("Simulated DB error on commit during delete")

        with self.assertRaisesRegex(DatabaseError, "Error while removing component: Simulated DB error on commit during delete"):
            inventory.remove_component_quantity(self.comp2_id, 10)

        self.assertEqual(component_to_delete.quantity, 0) # Update happens before delete/commit
        mock_session.delete.assert_called_once_with(component_to_delete)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_get_component_by_id_found(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = self.mock_comp1

        result = inventory.get_component_by_id(self.comp1_id)

        mock_session.query.return_value.filter_by.assert_called_once_with(id=self.comp1_id)
        mock_session.close.assert_called_once()
        self.assertEqual(result, self.mock_comp1)

    @patch('backend.inventory.get_session')
    def test_get_component_by_id_not_found(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        non_existent_id = uuid.uuid4()

        result = inventory.get_component_by_id(non_existent_id)

        mock_session.query.return_value.filter_by.assert_called_once_with(id=non_existent_id)
        mock_session.close.assert_called_once()
        self.assertIsNone(result)

    @patch('backend.inventory.get_session')
    def test_get_component_by_id_database_error(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        test_id = uuid.uuid4()
        mock_session.query.return_value.filter_by.return_value.first.side_effect = Exception("DB Read Error")

        with self.assertRaisesRegex(DatabaseError, f"Error while fetching component by id {test_id}: DB Read Error"):
            inventory.get_component_by_id(test_id)

        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_get_all_components_success(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_components_list = [self.mock_comp1, self.mock_comp2]
        # Simulate the chain query().order_by().all()
        mock_session.query.return_value.order_by.return_value.all.return_value = mock_components_list

        result = inventory.get_all_components()

        mock_session.query.assert_called_once_with(Component)
        mock_session.query.return_value.order_by.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, mock_components_list)

    @patch('backend.inventory.get_session')
    def test_get_all_components_empty(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.order_by.return_value.all.return_value = []

        result = inventory.get_all_components()

        mock_session.query.assert_called_once_with(Component)
        mock_session.close.assert_called_once()
        self.assertEqual(result, [])

    @patch('backend.inventory.get_session')
    def test_get_all_components_database_error(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.order_by.return_value.all.side_effect = Exception("DB Read All Error")

        with self.assertRaisesRegex(DatabaseError, "Error while fetching all components: DB Read All Error"):
            inventory.get_all_components()

        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_success(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        component_to_update = MockComponent(id=self.comp1_id, quantity=50)
        mock_session.query.return_value.filter_by.return_value.first.return_value = component_to_update

        new_quantity = 75
        result = inventory.update_component_quantity(self.comp1_id, new_quantity)

        mock_session.query.return_value.filter_by.assert_called_once_with(id=self.comp1_id)
        self.assertEqual(component_to_update.quantity, new_quantity)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, component_to_update)
        self.assertEqual(result.quantity, new_quantity)

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_invalid_quantity_negative(self, mock_get_session):
        with self.assertRaisesRegex(InvalidQuantityError, "Quantity must be a non-negative integer"):
            inventory.update_component_quantity(self.comp1_id, -10)
        mock_get_session.assert_not_called()

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_invalid_quantity_type(self, mock_get_session):
        with self.assertRaisesRegex(InvalidQuantityError, "Quantity must be a non-negative integer"):
            inventory.update_component_quantity(self.comp1_id, "invalid") # type: ignore
        mock_get_session.assert_not_called()

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_not_found(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        non_existent_id = uuid.uuid4()

        with self.assertRaisesRegex(ComponentNotFoundError, f"Component with ID {non_existent_id} not found"):
            inventory.update_component_quantity(non_existent_id, 100)

        mock_session.query.return_value.filter_by.assert_called_once_with(id=non_existent_id)
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once() # Exception occurred
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_update_component_quantity_database_error_on_commit(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        component_to_update = MockComponent(id=self.comp1_id, quantity=50)
        mock_session.query.return_value.filter_by.return_value.first.return_value = component_to_update
        mock_session.commit.side_effect = Exception("Simulated DB error on commit")

        with self.assertRaisesRegex(DatabaseError, "Error while updating component quantity: Simulated DB error on commit"):
            inventory.update_component_quantity(self.comp1_id, 100)

        self.assertEqual(component_to_update.quantity, 100) # Update happens before commit
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_select_multiple_components_success(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        ids_to_select = [self.comp1_id, self.comp2_id]
        expected_components = [self.mock_comp1, self.mock_comp2]

        mock_query_obj = MagicMock()
        mock_filter_obj = MagicMock()
        mock_session.query.return_value = mock_query_obj
        mock_query_obj.filter.return_value = mock_filter_obj
        mock_filter_obj.all.return_value = expected_components

        result = inventory.select_multiple_components(ids_to_select)

        mock_session.query.assert_called_once_with(Component)
        mock_query_obj.filter.assert_called_once()
        mock_filter_obj.all.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, expected_components)

    @patch('backend.inventory.get_session')
    def test_select_multiple_components_empty_list(self, mock_get_session):
        result = inventory.select_multiple_components([])
        mock_get_session.assert_not_called()
        self.assertEqual(result, [])

    @patch('backend.inventory.get_session')
    def test_select_multiple_components_no_match(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        ids_to_select = [uuid.uuid4()] # Non-existent ID
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = inventory.select_multiple_components(ids_to_select)

        mock_session.query.return_value.filter.assert_called_once()
        mock_session.close.assert_called_once()
        self.assertEqual(result, [])

    @patch('backend.inventory.get_session')
    def test_select_multiple_components_database_error(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        ids_to_select = [self.comp1_id]
        mock_session.query.return_value.filter.return_value.all.side_effect = Exception("DB Multi Select Error")

        with self.assertRaisesRegex(DatabaseError, "Error selecting multiple components: DB Multi Select Error"):
            inventory.select_multiple_components(ids_to_select)

        mock_session.close.assert_called_once()

    @patch('backend.inventory.get_session')
    def test_get_components_by_part_number_success(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        part_number_to_find = "PN101"
        expected_components = [self.mock_comp1]
        mock_session.query.return_value.filter_by.return_value.all.return_value = expected_components

        result = inventory.get_components_by_part_number(part_number_to_find)

        mock_session.query.return_value.filter_by.assert_called_once_with(part_number=part_number_to_find)
        mock_session.close.assert_called_once()
        self.assertEqual(result, expected_components)

    @patch('backend.inventory.get_session')
    def test_get_components_by_part_number_not_found(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        part_number_to_find = "PN-NOT-FOUND"
        mock_session.query.return_value.filter_by.return_value.all.return_value = []

        result = inventory.get_components_by_part_number(part_number_to_find)

        mock_session.query.return_value.filter_by.assert_called_once_with(part_number=part_number_to_find)
        mock_session.close.assert_called_once()
        self.assertEqual(result, [])

    @patch('backend.inventory.get_session')
    def test_get_components_by_part_number_database_error(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        part_number_to_find = "PN-ERR"
        mock_session.query.return_value.filter_by.return_value.all.side_effect = Exception("DB Part Number Error")

        with self.assertRaisesRegex(DatabaseError, f"Error fetching components by part number {part_number_to_find}: DB Part Number Error"):
            inventory.get_components_by_part_number(part_number_to_find)

        mock_session.close.assert_called_once()


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)