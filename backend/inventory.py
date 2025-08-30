import uuid
from backend.models import Component
from backend.database import get_session
from backend.component_factory import ComponentFactory
import backend.exceptions

def add_component(
        part_number: str,
        component_type: str,
        value: str,
        quantity: int,
        purchase_link: str | None,
        datasheet_link: str | None,
        location: str | None
) -> Component | None:
    if not part_number:
        raise backend.exceptions.InvalidInputError("Part number cannot be empty.")
    if quantity < 0:
        raise backend.exceptions.InvalidQuantityError("Quantity cannot be negative.")

    session = get_session()
    try:
        component = ComponentFactory.create_component(
            component_type,
            part_number=part_number,
            value=value,
            quantity=quantity,
            purchase_link=purchase_link,
            datasheet_link=datasheet_link,
            location=location
        )
        session.add(component)
        session.commit()
        return component
    except Exception as e:
        session.rollback()
        if isinstance(e, (backend.exceptions.ComponentError, ValueError)):
            raise
        raise backend.exceptions.DatabaseError(f"Database error during add: {e}") from e
    finally:
        session.close()

def remove_component_quantity(component_id: uuid.UUID, quantity: int) -> Component | None:
    if not isinstance(quantity, int) or quantity <= 0:
        raise backend.exceptions.InvalidQuantityError("Quantity must be a positive integer")

    session = get_session()
    try:
        component = session.query(Component).filter_by(id=component_id).first()
        if not component:
            raise backend.exceptions.ComponentNotFoundError(f"Component with id {component_id} not found")

        if component.quantity < quantity:
            raise backend.exceptions.StockError(
                f"Not enough stock for {component.part_number}. Available: {component.quantity}, Tried to remove: {quantity}")

        component.quantity -= quantity
        updated_component = component
        session.commit()
        return updated_component
    except Exception as e:
        session.rollback()
        if not isinstance(e, backend.exceptions.ComponentError):
            raise backend.exceptions.DatabaseError(f"Error while removing component: {e}") from e
        raise
    finally:
        session.close()

def delete_components_by_type(backend_id: str) -> int:
    session = get_session()
    try:
        num_deleted = session.query(Component).filter_by(component_type=backend_id).delete(synchronize_session=False)
        session.commit()
        print(f"INFO: Deleted {num_deleted} components of type '{backend_id}'.")
        return num_deleted
    except Exception as e:
        session.rollback()
        raise backend.exceptions.DatabaseError(f"Error deleting components by type: {e}") from e
    finally:
        session.close()

def update_component(component_id: uuid.UUID, data: dict) -> Component:
    """Updates a component's attributes from a dictionary of data."""
    session = get_session()
    try:
        component = session.query(Component).filter_by(id=component_id).first()
        if not component:
            raise backend.exceptions.ComponentNotFoundError(f"Component with ID {component_id} not found.")

        for key, value in data.items():
            if hasattr(component, key):
                setattr(component, key, value)
            else:
                print(f"WARNING: Tried to update non-existent attribute '{key}'")

        session.commit()
        session.refresh(component)
        return component
    except Exception as e:
        session.rollback()
        if isinstance(e, backend.exceptions.ComponentError):
            raise
        raise backend.exceptions.DatabaseError(f"Error while updating component: {e}") from e
    finally:
        session.close()

def get_component_by_id(component_id: uuid.UUID) -> Component | None:
    session = get_session()
    try:
        return session.query(Component).filter_by(id=component_id).first()
    except Exception as e:
        raise backend.exceptions.DatabaseError(f"Error fetching component by id {component_id}: {e}") from e
    finally:
        session.close()

def get_all_components() -> list[Component] | None:
    session = get_session()
    try:
        return session.query(Component).order_by(Component.part_number).all()
    except Exception as e:
        raise backend.exceptions.DatabaseError(f"Error fetching all components: {e}") from e
    finally:
        session.close()