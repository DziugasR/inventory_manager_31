
from PyQt5.QtWidgets import QMessageBox
from backend.models import Component
from backend.database import get_session
from backend.component_factory import ComponentFactory

def add_component(part_number, name, component_type, value, quantity, parent=None):
    """ Uses Factory Pattern to create and add a new component to the database. """
    if not part_number:
        QMessageBox.warning(parent, "Missing Part Number", "Every component must have a unique part number.")
        return False

    session = get_session()
    try:
        existing_component = session.query(Component).filter_by(part_number=part_number).first()
        if existing_component:
            QMessageBox.warning(parent, "Duplicate Part", "A component with this part number already exists.")
            return False

        component = ComponentFactory.create_component(
            component_type, part_number=part_number, name=name, value=value, quantity=quantity
        )
        session.add(component)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        QMessageBox.warning(parent, "Database Error", f"Error while adding component: {e}")
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
    """ Removes a component by part number. """
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


