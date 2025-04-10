from backend.models import Component
from backend.database import get_session
from backend.component_factory import ComponentFactory

from backend.exceptions import InvalidInputError, DuplicateComponentError, ComponentError, DatabaseError, InvalidQuantityError, \
    ComponentNotFoundError, StockError

def add_component(part_number, name, component_type, value, quantity, purchase_link, datasheet_link):
    session = get_session()
    try:
        if session.query(Component).filter_by(part_number=part_number).first():
            raise DuplicateComponentError(f"Component with part number {part_number} already exists")

        print("2")
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
        return component
    except Exception as e:
        session.rollback()
        if not isinstance(e, ComponentError):
            raise DatabaseError(f"Database error: {e}") from e
        raise
    finally:
        session.close()


def remove_component_quantity(part_number, quantity):
    """Removes a specified quantity of the component from the database."""
    if not isinstance(quantity, int) or quantity <= 0:
        raise InvalidQuantityError("Quantity must be a positive number")

    session = get_session()
    try:
        component = session.query(Component).filter_by(part_number=part_number).first()
        if not component:
            raise ComponentNotFoundError(f"Component with part number {part_number} not found")

        if component.quantity < quantity:
            raise StockError(f"Not enough stock to remove {quantity}. Available: {component.quantity}")

        component.quantity -= quantity
        if component.quantity == 0:
            session.delete(component)
        session.commit()
        return component
    except Exception as e:
        session.rollback()
        if not isinstance(e, ComponentError):
            raise DatabaseError(f"Error while removing component: {e}") from e
        raise
    finally:
        session.close()

def get_component_by_part_number(part_number: str) -> Component | None:
    session = get_session()
    try:
        component = session.query(Component).filter_by(part_number=part_number).first()
        return component
    except Exception as e:
        # Catch specific SQLAlchemy errors if needed, otherwise a general catch
        raise DatabaseError(f"Error while fetching component by part number {part_number}: {e}") from e
    finally:
        session.close()

def get_all_components():
    """Fetches all components from the database."""
    session = get_session()
    try:
        return session.query(Component).all()
    except Exception as e:
        raise DatabaseError(f"Error while fetching components: {e}") from e
    finally:
        session.close()


def update_component_quantity(component_id, new_quantity):
    """Updates the quantity of a specific component based on its ID."""
    if not isinstance(new_quantity, int) or new_quantity < 0:
        raise InvalidQuantityError("Quantity must be a non-negative integer")

    session = get_session()
    try:
        component = session.query(Component).filter_by(id=component_id).first()
        if not component:
            raise ComponentNotFoundError(f"Component with ID {component_id} not found")

        component.quantity = new_quantity
        session.commit()
        return component
    except Exception as e:
        session.rollback()
        if not isinstance(e, ComponentError):
            raise DatabaseError(f"Error while updating component quantity: {e}") from e
        raise
    finally:
        session.close()

def select_multiple_components(part_numbers: list[str]) -> list[Component]:
    if not part_numbers:
        return []

    session = get_session()
    try:
        selected_components = session.query(Component)\
                                     .filter(Component.part_number.in_(part_numbers))\
                                     .all()
        return selected_components
    except Exception as e:
        raise DatabaseError(f"Error selecting multiple components: {e}") from e
    finally:
        session.close()