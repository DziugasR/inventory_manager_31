import unittest
import uuid

from backend.models import (
    Component, create_component_class,
    Resistor, Capacitor, Inductor, Diode, Transistor, LED, Relay,
    OpAmp, VoltageRegulator, Microcontroller, IC, MOSFET,
    Photodiode, Switch, Transformer, Speaker, Motor, HeatSink,
    Connector, CrystalOscillator, Buzzer, Thermistor, Varistor,
    Fuse, Sensor, Antenna, Breadboard, Wire, Battery, PowerSupply
)


def create_basic_kwargs(component_type, value, part_number="TestPN", quantity=1):
    return {
        "id": uuid.uuid4(),
        "part_number": part_number,
        "component_type": component_type,
        "value": value,
        "quantity": quantity,
        "purchase_link": None,
        "datasheet_link": None,
    }


class TestModels(unittest.TestCase):

    def test_create_component_class_structure(self):
        test_class = create_component_class("TestComponent", "test_id", "Test Spec")
        self.assertTrue(isinstance(test_class, type))
        self.assertTrue(issubclass(test_class, Component))
        self.assertEqual(test_class.__name__, "TestComponent")
        self.assertIn("__mapper_args__", test_class.__dict__)
        self.assertEqual(test_class.__mapper_args__["polymorphic_identity"], "test_id")
        self.assertTrue(hasattr(test_class, "get_specifications"))

    def test_component_instantiation(self):
        r_kwargs = create_basic_kwargs("resistor", "1k", "R1")
        res = Resistor(**r_kwargs)
        self.assertEqual(res.part_number, "R1")
        self.assertEqual(res.component_type, "resistor")
        self.assertEqual(res.value, "1k")
        self.assertEqual(res.quantity, 1)
        self.assertIsInstance(res.id, uuid.UUID)

        c_kwargs = create_basic_kwargs("capacitor", "10uF", "C1", quantity=5)
        cap = Capacitor(**c_kwargs)
        self.assertEqual(cap.part_number, "C1")
        self.assertEqual(cap.component_type, "capacitor")
        self.assertEqual(cap.value, "10uF")
        self.assertEqual(cap.quantity, 5)

        mc_kwargs = create_basic_kwargs("microcontroller", "AVR", "MCU1")
        mc = Microcontroller(**mc_kwargs)
        self.assertEqual(mc.part_number, "MCU1")
        self.assertEqual(mc.component_type, "microcontroller")
        self.assertEqual(mc.value, "AVR")
        self.assertEqual(mc.quantity, 1)

    def test_get_specifications_with_unit(self):
        r_kwargs = create_basic_kwargs("resistor", "4.7k")
        res = Resistor(**r_kwargs)
        self.assertEqual(res.get_specifications(), "Resistance Ω: 4.7k Ω")

        c_kwargs = create_basic_kwargs("capacitor", "22pF")
        cap = Capacitor(**c_kwargs)
        self.assertEqual(cap.get_specifications(), "Capacitance F: 22pF F")

        l_kwargs = create_basic_kwargs("inductor", "10mH")
        ind = Inductor(**l_kwargs)
        self.assertEqual(ind.get_specifications(), "Inductance H: 10mH H")

        d_kwargs = create_basic_kwargs("diode", "0.7V")
        dio = Diode(**d_kwargs)
        self.assertEqual(dio.get_specifications(), "Forward Voltage V: 0.7V V")

        led_kwargs = create_basic_kwargs("led", "520nm")
        led = LED(**led_kwargs)
        self.assertEqual(led.get_specifications(), "Wavelength nm: 520nm nm")

        osc_kwargs = create_basic_kwargs("crystal_oscillator", "16MHz")
        osc = CrystalOscillator(**osc_kwargs)
        self.assertEqual(osc.get_specifications(), "Frequency MHz: 16MHz MHz")

        wire_kwargs = create_basic_kwargs("wire", "22")
        wire = Wire(**wire_kwargs)
        self.assertEqual(wire.get_specifications(), "Gauge AWG: 22 AWG")

    def test_get_specifications_without_unit(self):
        t_kwargs = create_basic_kwargs("transistor", "300")
        tran = Transistor(**t_kwargs)
        self.assertEqual(tran.get_specifications(), "Gain (hFE): 300 (hFE)")

        mc_kwargs = create_basic_kwargs("microcontroller", "ARM Cortex-M4")
        mc = Microcontroller(**mc_kwargs)
        self.assertEqual(mc.get_specifications(), "Architecture: ARM Cortex-M4")

        ic_kwargs = create_basic_kwargs("ic", "Timer")
        ic_comp = IC(**ic_kwargs)
        self.assertEqual(ic_comp.get_specifications(), "Function: Timer")

        sw_kwargs = create_basic_kwargs("switch", "2")
        sw = Switch(**sw_kwargs)
        self.assertEqual(sw.get_specifications(), "Number of Positions: 2 Positions")

        sen_kwargs = create_basic_kwargs("sensor", "Temperature")
        sen = Sensor(**sen_kwargs)
        self.assertEqual(sen.get_specifications(), "Type: Temperature")

    def test_get_specifications_all_types(self):
        all_components = {
            "resistor": (Resistor, "1k"), "capacitor": (Capacitor, "1uF"),
            "inductor": (Inductor, "1mH"), "diode": (Diode, "0.6V"),
            "transistor": (Transistor, "100"), "led": (LED, "630nm"),
            "relay": (Relay, "5V"), "op_amp": (OpAmp, "1MHz"),
            "voltage_regulator": (VoltageRegulator, "3.3V"),
            "microcontroller": (Microcontroller, "ESP32"), "ic": (IC, "Logic Gate"),
            "mosfet": (MOSFET, "50V"), "photodiode": (Photodiode, "0.5A/W"),
            "switch": (Switch, "3"), "transformer": (Transformer, "230V"),
            "speaker": (Speaker, "8 Ohms"), "motor": (Motor, "10000"),
            "heat_sink": (HeatSink, "10C/W"), "connector": (Connector, "40"),
            "crystal_oscillator": (CrystalOscillator, "8MHz"), "buzzer": (Buzzer, "85dB"),
            "thermistor": (Thermistor, "10k"), "varistor": (Varistor, "275V"),
            "fuse": (Fuse, "1A"), "sensor": (Sensor, "Humidity"),
            "antenna": (Antenna, "2.4GHz"), "breadboard": (Breadboard, "830pt"),
            "wire": (Wire, "24"), "battery": (Battery, "9V"),
            "power_supply": (PowerSupply, "12V")
        }

        for type_id, (cls, val) in all_components.items():
            with self.subTest(component_type=type_id):
                kwargs = create_basic_kwargs(type_id, val)
                instance = cls(**kwargs)
                spec = instance.get_specifications()
                self.assertIsInstance(spec, str)
                self.assertTrue(len(spec) > 0)
                self.assertIn(val, spec)

    def test_get_specifications_edge_cases(self):
        test_class_1 = create_component_class("TestNoSpace", "tn", "TestSpec")
        kwargs1 = create_basic_kwargs("tn", "Value1")
        inst1 = test_class_1(**kwargs1)
        self.assertEqual(inst1.get_specifications(), "TestSpec: Value1")

        test_class_2 = create_component_class("TestEndSpace", "ts", "Test Spec ")
        kwargs2 = create_basic_kwargs("ts", "Value2")
        inst2 = test_class_2(**kwargs2)
        spec2 = inst2.get_specifications()
        self.assertTrue(spec2.startswith("Test Spec "))
        self.assertIn(": Value2", spec2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
