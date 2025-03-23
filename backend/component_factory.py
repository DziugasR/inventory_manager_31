from backend.models import (
    Resistor, Capacitor, Inductor, Diode, Transistor, LED, Relay,
    OpAmp, VoltageRegulator, Microcontroller, IC, MOSFET,
    Photodiode, Switch, Transformer, Speaker, Motor, HeatSink,
    Connector, CrystalOscillator, Buzzer, Thermistor, Varistor,
    Fuse, Sensor, Antenna, Breadboard, Wire, Battery, PowerSupply
)

class ComponentFactory:
    _component_types = {
        "Resistor": Resistor,
        "Capacitor": Capacitor,
        "Inductor": Inductor,
        "Diode": Diode,
        "Transistor": Transistor,
        "LED": LED,
        "Relay": Relay,
        "Op-Amp": OpAmp,
        "Voltage Regulator": VoltageRegulator,
        "Microcontroller": Microcontroller,
        "IC": IC,
        "MOSFET": MOSFET,
        "Photodiode": Photodiode,
        "Switch": Switch,
        "Transformer": Transformer,
        "Speaker": Speaker,
        "Motor": Motor,
        "Heat Sink": HeatSink,
        "Connector": Connector,
        "Crystal Oscillator": CrystalOscillator,
        "Buzzer": Buzzer,
        "Thermistor": Thermistor,
        "Varistor": Varistor,
        "Fuse": Fuse,
        "Sensor": Sensor,
        "Antenna": Antenna,
        "Breadboard": Breadboard,
        "Wire": Wire,
        "Battery": Battery,
        "Power Supply": PowerSupply
    }

    @staticmethod
    def create_component(component_type, **kwargs):
        if component_type in ComponentFactory._component_types:
            return ComponentFactory._component_types[component_type](**kwargs)
        else:
            raise ValueError(f"Unknown component type: {component_type}")

    @staticmethod
    def register_component(name, cls):
        """Dynamically add new components"""
        ComponentFactory._component_types[name] = cls
