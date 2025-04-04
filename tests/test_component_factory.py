import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import sys

# Import the models and Base
from backend.models import (
    Base, Component, Resistor, Capacitor, Inductor, Diode, Transistor, LED, Relay,
    OpAmp, VoltageRegulator, Microcontroller, IC, MOSFET,
    Photodiode, Switch, Transformer, Speaker, Motor, HeatSink,
    Connector, CrystalOscillator, Buzzer, Thermistor, Varistor,
    Fuse, Sensor, Antenna, Breadboard, Wire, Battery, PowerSupply
)

# Import the ComponentFactory
from backend.component_factory import ComponentFactory


class TestComponentFactory(unittest.TestCase):
    """Test the ComponentFactory and ensure all component types can be created and stored in the database."""

    @classmethod
    def setUpClass(cls):
        """Set up in-memory SQLite database for testing."""
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Create a new session for each test."""
        self.session = self.Session()

    def tearDown(self):
        """Close the session after each test."""
        self.session.close()

    def test_all_component_types_creation(self):
        """Test that all component types can be created and stored in the database."""
        # Standard test data for all components
        default_data = {
            "part_number": "TEST-",
            "name": "Test Component",
            "value": "1",
            "quantity": 10,
            "purchase_link": "https://example.com",
            "datasheet_link": "https://datasheet.example.com"
        }

        print("\nTesting component creation for each type:")
        print("-" * 50)

        # Track results for summary
        success_count = 0
        failed_types = []

        # Test each component type
        for component_type, component_class in ComponentFactory._component_types.items():
            try:
                # Create unique part number for this component type
                part_number = f"{default_data['part_number']}{component_type}"
                test_data = {**default_data, "part_number": part_number}

                # Create the component using factory
                component = ComponentFactory.create_component(component_type, **test_data)

                # Save to database
                self.session.add(component)
                self.session.commit()

                # Retrieve from database
                retrieved = self.session.query(Component).filter_by(part_number=part_number).first()

                # Assertions
                self.assertIsNotNone(retrieved, f"{component_type} not found in database")
                self.assertEqual(retrieved.component_type, component_type)
                self.assertEqual(retrieved.name, test_data["name"])
                self.assertEqual(retrieved.value, test_data["value"])
                self.assertEqual(retrieved.quantity, test_data["quantity"])

                # Verify it's the correct subclass
                self.assertIsInstance(retrieved, component_class)

                # Verify specifications method works
                specs = retrieved.get_specifications()
                self.assertIsNotNone(specs)
                self.assertIn(retrieved.value, specs)

                # Print success
                print(f"{component_type}: OK")
                success_count += 1

            except Exception as e:
                print(f"{component_type}: FAILED - {str(e)}")
                failed_types.append(component_type)

                # Roll back the session to keep the test running
                self.session.rollback()

        # Print summary
        print("-" * 50)
        print(f"Summary: {success_count}/{len(ComponentFactory._component_types)} component types created successfully")

        if failed_types:
            print(f"Failed types: {', '.join(failed_types)}")
            self.fail(f"{len(failed_types)} component types failed creation test")

    def test_error_on_unknown_component_type(self):
        """Test that factory raises ValueError for unknown component types."""
        with self.assertRaises(ValueError):
            ComponentFactory.create_component("nonexistent_type", part_number="TEST-X", name="Error Test", value="1",
                                              quantity=1)

    def test_register_new_component_type(self):
        """Test that a new component type can be registered and used."""
        # Create a test component class
        from backend.models import create_component_class

        TestComp = create_component_class(
            class_name="TestComp",
            polymorphic_id="test_comp",
            spec_format_string="Test Value X"
        )

        # Register the new component
        ComponentFactory.register_component("test_comp", TestComp)

        # Test creating an instance
        test_data = {
            "part_number": "TEST-CUSTOM",
            "name": "Custom Test Component",
            "value": "42",
            "quantity": 5
        }