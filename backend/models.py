from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from abc import ABC, abstractmethod

# Ensure SQLAlchemy’s Base works with ABC
Base = declarative_base()

class Component(Base):
    __tablename__ = "components"

    part_number = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    component_type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_link = Column(String, nullable=True)
    datasheet_link = Column(String, nullable=True)

    __mapper_args__ = {"polymorphic_on": component_type, "polymorphic_identity": "component"}

    @abstractmethod
    def get_specifications(self):
        """ This method will be implemented in subclasses. """
        pass


class Resistor(Component):
    __mapper_args__ = {"polymorphic_identity": "resistor"}

    def get_specifications(self):
        return f"Resistance: {self.value}"


class Capacitor(Component):
    __mapper_args__ = {"polymorphic_identity": "capacitor"}

    def get_specifications(self):
        return f"Capacitance: {self.value}"


class Inductor(Component):
    __mapper_args__ = {"polymorphic_identity": "inductor"}

    def get_specifications(self):
        return f"Inductance: {self.value}"


class Diode(Component):
    __mapper_args__ = {"polymorphic_identity": "diode"}

    def get_specifications(self):
        return f"Forward Voltage: {self.value}"


class Transistor(Component):
    __mapper_args__ = {"polymorphic_identity": "transistor"}

    def get_specifications(self):
        return f"Gain (hFE): {self.value}"


class LED(Component):
    __mapper_args__ = {"polymorphic_identity": "led"}

    def get_specifications(self):
        return f"Wavelength: {self.value} nm"


class Relay(Component):
    __mapper_args__ = {"polymorphic_identity": "relay"}

    def get_specifications(self):
        return f"Coil Voltage: {self.value} V"


class OpAmp(Component):
    __mapper_args__ = {"polymorphic_identity": "opamp"}

    def get_specifications(self):
        return f"Gain Bandwidth: {self.value} Hz"


class VoltageRegulator(Component):
    __mapper_args__ = {"polymorphic_identity": "voltage_regulator"}

    def get_specifications(self):
        return f"Output Voltage: {self.value} V"


class Microcontroller(Component):
    __mapper_args__ = {"polymorphic_identity": "microcontroller"}

    def get_specifications(self):
        return f"Architecture: {self.value}"


class IC(Component):
    __mapper_args__ = {"polymorphic_identity": "ic"}

    def get_specifications(self):
        return f"Function: {self.value}"


class MOSFET(Component):
    __mapper_args__ = {"polymorphic_identity": "mosfet"}

    def get_specifications(self):
        return f"Drain-Source Voltage: {self.value} V"


class Photodiode(Component):
    __mapper_args__ = {"polymorphic_identity": "photodiode"}

    def get_specifications(self):
        return f"Sensitivity: {self.value} A/W"


class Switch(Component):
    __mapper_args__ = {"polymorphic_identity": "switch"}

    def get_specifications(self):
        return f"Number of Positions: {self.value}"


class Transformer(Component):
    __mapper_args__ = {"polymorphic_identity": "transformer"}

    def get_specifications(self):
        return f"Primary Voltage: {self.value} V"


class Speaker(Component):
    __mapper_args__ = {"polymorphic_identity": "speaker"}

    def get_specifications(self):
        return f"Impedance: {self.value} Ω"


class Motor(Component):
    __mapper_args__ = {"polymorphic_identity": "motor"}

    def get_specifications(self):
        return f"RPM: {self.value}"


class HeatSink(Component):
    __mapper_args__ = {"polymorphic_identity": "heat_sink"}

    def get_specifications(self):
        return f"Thermal Resistance: {self.value} °C/W"


class Connector(Component):
    __mapper_args__ = {"polymorphic_identity": "connector"}

    def get_specifications(self):
        return f"Number of Pins: {self.value}"


class CrystalOscillator(Component):
    __mapper_args__ = {"polymorphic_identity": "crystal_oscillator"}

    def get_specifications(self):
        return f"Frequency: {self.value} MHz"


class Buzzer(Component):
    __mapper_args__ = {"polymorphic_identity": "buzzer"}

    def get_specifications(self):
        return f"Sound Level: {self.value} dB"


class Thermistor(Component):
    __mapper_args__ = {"polymorphic_identity": "thermistor"}

    def get_specifications(self):
        return f"Resistance at 25°C: {self.value} Ω"


class Varistor(Component):
    __mapper_args__ = {"polymorphic_identity": "varistor"}

    def get_specifications(self):
        return f"Voltage Rating: {self.value} V"


class Fuse(Component):
    __mapper_args__ = {"polymorphic_identity": "fuse"}

    def get_specifications(self):
        return f"Current Rating: {self.value} A"


class Sensor(Component):
    __mapper_args__ = {"polymorphic_identity": "sensor"}

    def get_specifications(self):
        return f"Type: {self.value}"


class Antenna(Component):
    __mapper_args__ = {"polymorphic_identity": "antenna"}

    def get_specifications(self):
        return f"Frequency Range: {self.value} MHz"


class Breadboard(Component):
    __mapper_args__ = {"polymorphic_identity": "breadboard"}

    def get_specifications(self):
        return f"Size: {self.value} mm"


class Wire(Component):
    __mapper_args__ = {"polymorphic_identity": "wire"}

    def get_specifications(self):
        return f"Gauge: {self.value} AWG"


class Battery(Component):
    __mapper_args__ = {"polymorphic_identity": "battery"}

    def get_specifications(self):
        return f"Voltage: {self.value} V"


class PowerSupply(Component):
    __mapper_args__ = {"polymorphic_identity": "power_supply"}

    def get_specifications(self):
        return f"Output Voltage: {self.value} V"

