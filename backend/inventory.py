from PyQt5.QtWidgets import QMessageBox
from backend.models import Component
from backend.database import get_session
from backend.component_factory import ComponentFactory

# TODO nemaišyt UI su backend

def add_component(part_number, name, component_type, value, quantity, purchase_link, datasheet_link, parent=None):
    session = get_session()
    try:
        if session.query(Component).filter_by(part_number=part_number).first():
            # Duplicate found; warn and return False.
            return False
        component = ComponentFactory.create_component(
            component_type,
            part_number=part_number,
            name=name,
            value=value,
            quantity=quantity,
            purchase_link=purchase_link,
            datasheet_link=datasheet_link
        )
        session.add(component)
        session.commit()
        return True
    except Exception as e:
        QMessageBox.warning(parent, "Add error", f" {e}")
        session.rollback()
        return False
    finally:
        session.close()

def remove_component_quantity(part_number, quantity, parent=None):
    """ Removes a specified quantity of the component from the database. """
    if not isinstance(quantity, int) or quantity <= 0:
        QMessageBox.warning(parent, "Invalid Quantity", "Quantity must be a positive number.")
        return False

    session = get_session()
    try:
        component = session.query(Component).filter_by(part_number=part_number).first()
        if component:
            if component.quantity >= quantity:
                component.quantity -= quantity
                if component.quantity == 0:  # If no stock left, remove the item
                    session.delete(component)
                session.commit()
                return True
            else:
                QMessageBox.warning(parent, "Stock Error", f"Not enough stock to remove {quantity}. Available: {component.quantity}")
                return False
        else:
            QMessageBox.warning(parent, "Not Found", f"Component with part number {part_number} not found.")
            return False
    except Exception as e:
        session.rollback()
        QMessageBox.warning(parent, "Database Error", f"Error while removing component: {e}")
        return False
    finally:
        session.close()

def remove_component_by_part_number(part_number, parent=None):
    """ Removes a component from the database using the part number. """
    session = get_session()
    try:
        component = session.query(Component).filter_by(part_number=part_number).first()
        if component:
            session.delete(component)
            session.commit()
            return True
        else:
            QMessageBox.warning(parent, "Not Found", f"Component with part number {part_number} not found.")
            return False
    except Exception as e:
        session.rollback()
        QMessageBox.warning(parent, "Database Error", f"Error while deleting component: {e}")
        return False
    finally:
        session.close()

def get_all_components():
    """ Fetches all components from the database. """
    session = get_session()
    try:
        return session.query(Component).all()  # No need to reference `id`
    except Exception as e:
        QMessageBox.warning(None, "Database Error", f"Error while fetching components: {e}")
        return []
    finally:
        session.close()

def update_component_quantity(component_id, new_quantity, parent=None):
    """ Updates the quantity of a specific component based on its ID. """
    if not isinstance(new_quantity, int) or new_quantity < 0:
        QMessageBox.warning(parent, "Invalid Quantity", "Quantity must be a non-negative integer.")
        return False

    session = get_session()
    try:
        component = session.query(Component).filter_by(id=component_id).first()
        if component:
            component.quantity = new_quantity
            session.commit()
            return True
        else:
            QMessageBox.warning(parent, "Not Found", f"Component with ID {component_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        QMessageBox.warning(parent, "Database Error", f"Error while updating component quantity: {e}")
        return False
    finally:
        session.close()

def export_components_to_txt(file_path):
    """ Export all components from database to a TXT file. """
    session = get_session()
    components = session.query(Component).all()
    session.close()

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("Part Number | Name | Type | Value | Quantity | Purchase_link | Datasheet_link |\n")
            file.write("-" * 100 + "\n")

            for component in components:
                file.write(f"{component.part_number or 'N/A'} | {component.name or 'N/A'} | "
                           f"{component.component_type} | {component.value} | {component.quantity} | {component.purchase_link or 'N/A'} | {component.datasheet_link or 'N/A'}\n")

        return True  # Success
    except Exception as e:
        print(f"Error exporting to TXT: {e}")
        return False  # Failure

# TODO scrap this shit and import/export from excel instead
def import_components_from_txt(file_path):
    """ Import components from a TXT file into the database using the Factory Pattern. """
    session = get_session()

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        if len(lines) < 3:  # Ensure file has data
            return False, "File is empty or incorrectly formatted."

        for line in lines[2:]:  # Skip headers
            parts = line.strip().split(" | ")
            if len(parts) != 7:
                continue  # Skip invalid lines

            part_number = parts[0] if parts[0] != "N/A" else None
            name = parts[1] if parts[1] != "N/A" else None
            component_type = parts[2]
            value = parts[3]
            quantity = int(parts[4])
            purchase_link = parts[5] if parts[5] != "N/A" else None
            datasheet_link = parts[6] if parts[6] != "N/A" else None

            if session.query(Component).filter_by(part_number=part_number).first():
                continue  # Skip duplicates

            # Use Factory Pattern to create the component
            component = ComponentFactory.create_component(
                component_type,
                part_number=part_number,
                name=name,
                value=value,
                quantity=quantity,
                purchase_link=purchase_link,
                datasheet_link=datasheet_link
            )
            session.add(component)

        session.commit()
        return True, "Components successfully imported."

    except Exception as e:
        session.rollback()
        return False, f"Error importing data: {e}"
    finally:
        session.close()