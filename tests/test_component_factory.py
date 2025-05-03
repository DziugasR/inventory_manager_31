import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from backend.models import Base, Component
from backend.component_factory import ComponentFactory

from backend.models import create_component_class


class TestComponentFactory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.session = self.Session()

    def tearDown(self):
        self.session.close()

    def test_all_component_types_creation(self):
        default_data = {
            "part_number": "TEST-",
            "value": "1",
            "quantity": 10,
            "purchase_link": "https://example.com",
            "datasheet_link": "https://datasheet.example.com"
        }

        failed_types = []

        for component_type, component_class in ComponentFactory._component_types.items():
            try:
                part_number = f"{default_data['part_number']}{component_type}"
                test_data = {**default_data, "part_number": part_number}

                component = ComponentFactory.create_component(component_type, **test_data)

                self.session.add(component)
                self.session.commit()

                retrieved = self.session.query(Component).filter_by(part_number=part_number).first()

                self.assertIsNotNone(retrieved, f"{component_type} not found in database")
                self.assertEqual(retrieved.component_type, component_type)
                self.assertEqual(retrieved.value, test_data["value"])
                self.assertEqual(retrieved.quantity, test_data["quantity"])

                self.assertIsInstance(retrieved, component_class)

                specs = retrieved.get_specifications()
                self.assertIsNotNone(specs)
                self.assertIn(retrieved.value, specs)

            except (AttributeError, ValueError, TypeError, SQLAlchemyError, KeyError):
                failed_types.append(component_type)
                self.session.rollback()

        if failed_types:
            self.fail(f"{len(failed_types)} component types failed creation test: {', '.join(failed_types)}")

    def test_error_on_unknown_component_type(self):
        with self.assertRaises(ValueError):
            ComponentFactory.create_component("nonexistent_type", part_number="TEST-X", value="1",
                                              quantity=1)

    def test_register_new_component_type(self):
        test_comp = create_component_class(
            class_name="TestComp",
            polymorphic_id="test_comp",
            spec_format_string="Test Value X"
        )

        ComponentFactory.register_component("test_comp", test_comp)

        test_data = {
            "part_number": "TEST-CUSTOM",
            "value": "42",
            "quantity": 5
        }
        component = ComponentFactory.create_component("test_comp", **test_data)
        self.session.add(component)
        self.session.commit()
        retrieved = self.session.query(Component).filter_by(part_number="TEST-CUSTOM").first()
        self.assertIsNotNone(retrieved)
        self.assertIsInstance(retrieved, test_comp)
        self.assertEqual(retrieved.component_type, "test_comp")
        self.assertEqual(retrieved.value, "42")


if __name__ == '__main__':
    unittest.main()
