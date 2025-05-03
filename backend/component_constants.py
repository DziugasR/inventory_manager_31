UI_TO_BACKEND_TYPE_MAP = {
    "Resistor": "resistor",
    "Capacitor": "capacitor",
    "Inductor": "inductor",
    "Diode": "diode",
    "Transistor": "transistor",
    "LED": "led",
    "Relay": "relay",
    "Op-Amp": "op_amp",
    "Voltage Regulator": "voltage_regulator",
    "Microcontroller": "microcontroller",
    "IC": "ic",
    "MOSFET": "mosfet",
    "Photodiode": "photodiode",
    "Switch": "switch",
    "Transformer": "transformer",
    "Speaker": "speaker",
    "Motor": "motor",
    "Heat Sink": "heat_sink",
    "Connector": "connector",
    "Crystal Oscillator": "crystal_oscillator",
    "Buzzer": "buzzer",
    "Thermistor": "thermistor",
    "Varistor": "varistor",
    "Fuse": "fuse",
    "Sensor": "sensor",
    "Antenna": "antenna",
    "Breadboard": "breadboard",
    "Wire": "wire",
    "Battery": "battery",
    "Power Supply": "power_supply"
}

BACKEND_TO_UI_TYPE_MAP = {v: k for k, v in UI_TO_BACKEND_TYPE_MAP.items()}

UI_TYPE_NAMES = sorted(list(UI_TO_BACKEND_TYPE_MAP.keys()))
