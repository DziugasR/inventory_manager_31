import json
import re
from .database import get_config_session
from .models import Component, create_component_class
from .models_custom import ComponentTypeDefinition
from .component_constants import UI_TO_BACKEND_TYPE_MAP
from .component_factory import ComponentFactory


class TypeManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TypeManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        print("INFO: TypeManager initializing...")
        self.ui_to_backend_map = {}
        self.backend_to_ui_map = {}
        self.type_properties = {}
        self._initialized = False

    def load_types(self):
        print("INFO: TypeManager loading/reloading types...")
        self.ui_to_backend_map = {}
        self.backend_to_ui_map = {}
        self.type_properties = {}

        self._load_hardcoded_types()
        self._load_custom_types_from_db()
        self._register_all_component_classes()
        self._initialized = True

        print(f"INFO: TypeManager loaded and registered {len(self.ui_to_backend_map)} total types.")

    def _load_hardcoded_types(self):
        print("DEBUG: Loading hardcoded types...")
        hardcoded_properties = {
            "Resistor": ["Resistance (Ω)", "Tolerance (%)"], "Capacitor": ["Capacitance (µF)", "Voltage (V)"],
            "Inductor": ["Inductance (H)", "Current Rating (A)"],
            "Diode": ["Forward Voltage (V)", "Current Rating (A)"],
            "Transistor": ["Gain (hFE)", "Voltage Rating (V)"], "LED": ["Wavelength (nm)", "Luminous Intensity (mcd)"],
            "Relay": ["Coil Voltage (V)", "Contact Rating (A)"], "Op-Amp": ["Gain Bandwidth (Hz)", "Slew Rate (V/µs)"],
            "Voltage Regulator": ["Output Voltage (V)", "Current Rating (A)"],
            "Microcontroller": ["Architecture", "Flash Memory (KB)"],
            "IC": ["Number of Pins", "Function"], "MOSFET": ["Drain-Source Voltage (V)", "Rds(on) (Ω)"],
            "Photodiode": ["Wavelength Range (nm)", "Sensitivity (A/W)"],
            "Switch": ["Current Rating (A)", "Number of Positions"],
            "Transformer": ["Primary Voltage (V)", "Secondary Voltage (V)"],
            "Speaker": ["Impedance (Ω)", "Power Rating (W)"],
            "Motor": ["Voltage (V)", "RPM"], "Heat Sink": ["Thermal Resistance (°C/W)", "Size (mm)"],
            "Connector": ["Number of Pins", "Pitch (mm)"],
            "Crystal Oscillator": ["Frequency (MHz)", "Load Capacitance (pF)"],
            "Buzzer": ["Operating Voltage (V)", "Sound Level (dB)"],
            "Thermistor": ["Resistance at 25°C (Ω)", "Beta Value (K)"],
            "Varistor": ["Voltage Rating (V)", "Clamping Voltage (V)"],
            "Fuse": ["Current Rating (A)", "Voltage Rating (V)"],
            "Sensor": ["Type", "Output Signal"], "Antenna": ["Frequency Range (MHz)", "Gain (dBi)"],
            "Breadboard": ["Size (mm)", "Number of Tie Points"], "Wire": ["Gauge (AWG)", "Length (m)"],
            "Battery": ["Voltage (V)", "Capacity (mAh)"], "Power Supply": ["Output Voltage (V)", "Output Current (A)"],
            "Thermo Couple": ["Temperature range C"]
        }

        for ui_name, backend_id in UI_TO_BACKEND_TYPE_MAP.items():
            self.ui_to_backend_map[ui_name] = backend_id
            self.backend_to_ui_map[backend_id] = ui_name
            self.type_properties[ui_name] = hardcoded_properties.get(ui_name, [])

    def _load_custom_types_from_db(self):
        print("DEBUG: Loading custom types from DB...")
        session = get_config_session()
        try:
            custom_types = session.query(ComponentTypeDefinition).all()
            for custom_type in custom_types:
                self.ui_to_backend_map[custom_type.ui_name] = custom_type.backend_id
                self.backend_to_ui_map[custom_type.backend_id] = custom_type.ui_name
                self.type_properties[custom_type.ui_name] = custom_type.properties
            print(f"DEBUG: Found and loaded {len(custom_types)} custom types.")
        except Exception as e:
            print(f"CRITICAL: Failed to load custom component types from database: {e}")
        finally:
            session.close()

    def _register_all_component_classes(self):
        print(f"DEBUG: Registering all {len(self.backend_to_ui_map)} component classes with factory...")
        ComponentFactory._component_types.clear()

        for backend_id, ui_name in self.backend_to_ui_map.items():
            class_name = ui_name.replace(" ", "").replace("-", "")

            properties = self.get_properties(ui_name)
            spec_format = properties[0] if properties else "Value"

            component_class = create_component_class(
                class_name=class_name,
                polymorphic_id=backend_id,
                spec_format_string=spec_format
            )
            ComponentFactory.register_component(backend_id, component_class)
        print("DEBUG: Component class registration complete.")

    def add_new_type(self, ui_name: str, properties: list[str]):
        session = get_config_session()
        try:
            backend_id = re.sub(r'\s+', '_', ui_name.strip()).lower()
            backend_id = re.sub(r'[^a-z0-9_]', '', backend_id)
            if not backend_id:
                raise ValueError("Could not generate a valid backend_id from the given UI name.")

            existing = session.query(ComponentTypeDefinition).filter(
                (ComponentTypeDefinition.ui_name == ui_name) |
                (ComponentTypeDefinition.backend_id == backend_id)
            ).first()
            if existing:
                raise ValueError(f"A type with the name '{ui_name}' or ID '{backend_id}' already exists.")

            new_type = ComponentTypeDefinition(
                ui_name=ui_name,
                backend_id=backend_id,
                properties=properties
            )
            session.add(new_type)
            session.commit()
            print(f"INFO: Successfully added new custom type '{ui_name}' to the database.")

            self.load_types()
            return True, f"Successfully added new type '{ui_name}'."
        except Exception as e:
            session.rollback()
            print(f"ERROR: Failed to add custom type '{ui_name}': {e}")
            return False, str(e)
        finally:
            session.close()

    def get_all_ui_names(self):
        return sorted(list(self.ui_to_backend_map.keys()))

    def get_backend_id(self, ui_name):
        return self.ui_to_backend_map.get(ui_name)

    def get_ui_name(self, backend_id):
        return self.backend_to_ui_map.get(backend_id)

    def get_properties(self, ui_name):
        return self.type_properties.get(ui_name, [])


type_manager = TypeManager()