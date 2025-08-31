import random
import uuid
from backend.type_manager import type_manager


def _generate_random_property_value(prop_name: str) -> str:
    """Generates a plausible random value based on the property name."""
    name = prop_name.lower()
    if "resistance" in name or "(ω)" in name:
        return str(random.choice([10, 100, 470, 1000, 2200, 4700, 10000, 100000]))
    if "capacitance" in name:
        return str(random.choice([0.1, 0.47, 1, 10, 100, 1000]))
    if "voltage" in name:
        return str(random.choice([3.3, 5, 9, 12, 24]))
    if "tolerance" in name:
        return str(random.choice([1, 5, 10]))
    if "current" in name:
        return f"{random.uniform(0.1, 2.0):.1f}"
    if "pins" in name:
        return str(random.choice([3, 8, 14, 16, 20, 40]))
    if "architecture" in name:
        return random.choice(["ARM Cortex-M", "AVR", "RISC-V", "ESP32"])
    if "memory" in name:
        return str(random.choice([32, 64, 128, 256, 512]))
    if "function" in name:
        return random.choice(["Timer", "Amplifier", "Logic Gate", "Multiplexer"])
    # Fallback for any other property
    return str(random.randint(1, 100))


def generate_random_components(amount: int) -> list[dict]:
    """
    Generates a list of dictionaries, each containing the data for a random component.
    """
    if not type_manager._initialized:
        type_manager.load_types()

    component_data_list = []
    all_ui_types = type_manager.get_all_ui_names()
    if not all_ui_types:
        return []

    for _ in range(amount):
        ui_type = random.choice(all_ui_types)
        backend_id = type_manager.get_backend_id(ui_type)
        properties = type_manager.get_properties(ui_type)

        value_parts = []
        if properties:
            for prop in properties:
                prop_value = _generate_random_property_value(prop)
                value_parts.append(f"{prop}: {prop_value}")

        value_string = ", ".join(value_parts)

        component_data = {
            'part_number': f"RAND-{str(uuid.uuid4())[:8].upper()}",
            'component_type': backend_id,
            'value': value_string,
            'quantity': random.randint(1, 500),
            'purchase_link': "",
            'datasheet_link': "",
            'location': random.choice(["Drawer A1", "Bin C4", "Shelf B2", "Project Box 7", "Loose Parts Tray"]),
            'notes': "This is an auto-generated component.",
            'image_path': None  # Explicitly set to None
        }
        component_data_list.append(component_data)

    return component_data_list