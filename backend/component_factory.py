from backend.models import (
    Resistor, Capacitor, Inductor, Diode, Transistor, LED, Relay,
    OpAmp, VoltageRegulator, Microcontroller, IC, MOSFET,
    Photodiode, Switch, Transformer, Speaker, Motor, HeatSink,
    Connector, CrystalOscillator, Buzzer, Thermistor, Varistor,
    Fuse, Sensor, Antenna, Breadboard, Wire, Battery, PowerSupply
)


class ComponentFactory:
    _component_types = {
        "resistor": Resistor,
        "capacitor": Capacitor,
        "inductor": Inductor,
        "diode": Diode,
        "transistor": Transistor,
        "led": LED,
        "relay": Relay,
        "op_amp": OpAmp,
        "voltage_regulator": VoltageRegulator,
        "microcontroller": Microcontroller,
        "ic": IC,
        "mosfet": MOSFET,
        "photodiode": Photodiode,
        "switch": Switch,
        "transformer": Transformer,
        "speaker": Speaker,
        "motor": Motor,
        "heat_sink": HeatSink,
        "connector": Connector,
        "crystal_oscillator": CrystalOscillator,
        "buzzer": Buzzer,
        "thermistor": Thermistor,
        "varistor": Varistor,
        "fuse": Fuse,
        "sensor": Sensor,
        "antenna": Antenna,
        "breadboard": Breadboard,
        "wire": Wire,
        "battery": Battery,
        "power_supply": PowerSupply
    }

    @staticmethod
    def create_component(component_type, **kwargs):
        component_type = component_type.lower()
        if component_type in ComponentFactory._component_types:
            return ComponentFactory._component_types[component_type](**kwargs)
        else:
            raise ValueError(f"Unknown component type: {component_type}")

    @staticmethod
    def register_component(name, cls):
        ComponentFactory._component_types[name] = cls
