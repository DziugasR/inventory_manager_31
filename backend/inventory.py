from PyQt5.QtWidgets import QMessageBox  # Import PyQt5 popup messages
from .models import Component
from .database import get_session

# Add a new component with validation
def add_component(part_number, name, component_type, value, quantity, parent=None):
    """ Adds a new component to the database, allowing blank part_number and name. """

    # Ensure quantity is valid
    if not isinstance(quantity, int) or quantity <= 0:
        QMessageBox.warning(parent, "Invalid Quantity", "Quantity must be a positive number.")
        return False

    # Ensure required fields are filled
    if not component_type or not value:
        QMessageBox.warning(parent, "Invalid Input", "Component Type and Value must be filled.")
        return False

    session = get_session()
    try:
        # Add new component (allowing empty part_number and name)
        new_component = Component(
            part_number=part_number if part_number else None,  # Allows blank
            name=name if name else None,  # Allows blank
            component_type=component_type,
            value=value,
            quantity=quantity
        )
        session.add(new_component)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        QMessageBox.warning(parent, "Database Error", f"Error while adding component: {e}")
        return False
    finally:
        session.close()

# Remove quantity of a component with validation
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

# Remove a component entirely by its ID
def remove_component_by_id(component_id, parent=None):
    """ Removes a component entirely from the database by ID. """
    session = get_session()
    try:
        component = session.query(Component).filter_by(id=component_id).first()
        if component:
            session.delete(component)
            session.commit()
            return True
        else:
            QMessageBox.warning(parent, "Not Found", f"Component with ID {component_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        QMessageBox.warning(parent, "Database Error", f"Error while deleting component: {e}")
        return False
    finally:
        session.close()

# Get all components
def get_all_components():
    """ Fetches all components from the database. """
    session = get_session()
    try:
        return session.query(Component).all()
    except Exception as e:
        QMessageBox.warning(None, "Database Error", f"Error while fetching components: {e}")
        return []
    finally:
        session.close()

# Update component quantity with validation
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


