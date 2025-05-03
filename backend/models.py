import uuid

from sqlalchemy import Column, Integer, String, UUID
from sqlalchemy.ext.declarative import declarative_base
from abc import abstractmethod

Base = declarative_base()


class Component(Base):
    __tablename__ = "components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_number = Column(String, nullable=False)
    component_type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_link = Column(String, nullable=True)
    datasheet_link = Column(String, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": component_type,
        "polymorphic_identity": "component"
    }

    @abstractmethod
    def get_specifications(self):
        pass


def create_component_class(class_name, polymorphic_id, spec_format_string):
    """Dynamically creates a Component subclass."""

    def generated_get_specifications(self):
        unit = ""
        parts = spec_format_string.split()

        if len(parts) > 1:
            unit = " " + parts[-1]  # Assumes last word is the unit

        return f"{spec_format_string}: {self.value}{unit}"

    class_attributes = {
        "__mapper_args__": {"polymorphic_identity": polymorphic_id},
        "get_specifications": generated_get_specifications
    }

    new_class = type(class_name, (Component,), class_attributes)
    return new_class


Resistor = create_component_class(
    class_name="Resistor",
    polymorphic_id="resistor",
    spec_format_string="Resistance Ω"
)

Capacitor = create_component_class(
    class_name="Capacitor",
    polymorphic_id="capacitor",
    spec_format_string="Capacitance F"
)

Inductor = create_component_class(
    class_name="Inductor",
    polymorphic_id="inductor",
    spec_format_string="Inductance H"
)

Diode = create_component_class(
    class_name="Diode",
    polymorphic_id="diode",
    spec_format_string="Forward Voltage V"
)

Transistor = create_component_class(
    class_name="Transistor",
    polymorphic_id="transistor",
    spec_format_string="Gain (hFE)"
)

LED = create_component_class(
    class_name="LED",
    polymorphic_id="led",
    spec_format_string="Wavelength nm"
)

Relay = create_component_class(
    class_name="Relay",
    polymorphic_id="relay",
    spec_format_string="Coil Voltage V"
)

OpAmp = create_component_class(
    class_name="OpAmp",
    polymorphic_id="op_amp",
    spec_format_string="Gain Bandwidth Hz"
)

VoltageRegulator = create_component_class(
    class_name="VoltageRegulator",
    polymorphic_id="voltage_regulator",
    spec_format_string="Output Voltage V"
)

Microcontroller = create_component_class(
    class_name="Microcontroller",
    polymorphic_id="microcontroller",
    spec_format_string="Architecture"
)

IC = create_component_class(
    class_name="IC",
    polymorphic_id="ic",
    spec_format_string="Function"
)

MOSFET = create_component_class(
    class_name="MOSFET",
    polymorphic_id="mosfet",
    spec_format_string="Drain-Source Voltage V"
)

Photodiode = create_component_class(
    class_name="Photodiode",
    polymorphic_id="photodiode",
    spec_format_string="Sensitivity A/W"
)

Switch = create_component_class(
    class_name="Switch",
    polymorphic_id="switch",
    spec_format_string="Number of Positions"
)

Transformer = create_component_class(
    class_name="Transformer",
    polymorphic_id="transformer",
    spec_format_string="Primary Voltage V"
)

Speaker = create_component_class(
    class_name="Speaker",
    polymorphic_id="speaker",
    spec_format_string="Impedance Ω"
)

Motor = create_component_class(
    class_name="Motor",
    polymorphic_id="motor",
    spec_format_string="RPM"
)

HeatSink = create_component_class(
    class_name="HeatSink",
    polymorphic_id="heat_sink",
    spec_format_string="Thermal Resistance °C/W"
)

Connector = create_component_class(
    class_name="Connector",
    polymorphic_id="connector",
    spec_format_string="Number of Pins"
)

CrystalOscillator = create_component_class(
    class_name="CrystalOscillator",
    polymorphic_id="crystal_oscillator",
    spec_format_string="Frequency MHz"
)

Buzzer = create_component_class(
    class_name="Buzzer",
    polymorphic_id="buzzer",
    spec_format_string="Sound Level dB"
)

Thermistor = create_component_class(
    class_name="Thermistor",
    polymorphic_id="thermistor",
    spec_format_string="Resistance at 25°C Ω"
)

Varistor = create_component_class(
    class_name="Varistor",
    polymorphic_id="varistor",
    spec_format_string="Voltage Rating V"
)

Fuse = create_component_class(
    class_name="Fuse",
    polymorphic_id="fuse",
    spec_format_string="Current Rating A"
)

Sensor = create_component_class(
    class_name="Sensor",
    polymorphic_id="sensor",
    spec_format_string="Type"
)

Antenna = create_component_class(
    class_name="Antenna",
    polymorphic_id="antenna",
    spec_format_string="Frequency Range MHz"
)

Breadboard = create_component_class(
    class_name="Breadboard",
    polymorphic_id="breadboard",
    spec_format_string="Size mm"
)

Wire = create_component_class(
    class_name="Wire",
    polymorphic_id="wire",
    spec_format_string="Gauge AWG"
)

Battery = create_component_class(
    class_name="Battery",
    polymorphic_id="battery",
    spec_format_string="Voltage V"
)

PowerSupply = create_component_class(
    class_name="PowerSupply",
    polymorphic_id="power_supply",
    spec_format_string="Output Voltage V"
)
