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
        datasheet_link: str | None
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
            datasheet_link=datasheet_link
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
                f"Not enough stock for component {component.part_number} (ID: {component_id}). "
                f"Available: {component.quantity}, Tried to remove: {quantity}")

        component.quantity -= quantity
        updated_component = component
        if component.quantity == 0:
            session.delete(component)
            session.commit()
            return None
        else:
            session.commit()
            return updated_component
    except Exception as e:
        session.rollback()
        if not isinstance(e, backend.exceptions.ComponentError):
            raise backend.exceptions.DatabaseError(f"Error while removing component: {e}") from e
        raise
    finally:
        session.close()


def get_component_by_id(component_id: uuid.UUID) -> Component | None:
    session = get_session()
    try:
        component = session.query(Component).filter_by(id=component_id).first()
        return component
    except Exception as e:
        raise backend.exceptions.DatabaseError(f"Error while fetching component by id {component_id}: {e}") from e
    finally:
        session.close()


def get_all_components() -> list[Component] | None:
    session = get_session()
    try:
        return session.query(Component).order_by(Component.part_number).all()
    except Exception as e:
        raise backend.exceptions.DatabaseError(f"Error while fetching all components: {e}") from e
    finally:
        session.close()


def update_component_quantity(component_id: uuid.UUID, new_quantity: int) -> Component | None:
    if not isinstance(new_quantity, int) or new_quantity < 0:
        raise backend.exceptions.InvalidQuantityError("Quantity must be a non-negative integer")

    session = get_session()
    try:
        component = session.query(Component).filter_by(id=component_id).first()
        if not component:
            raise backend.exceptions.ComponentNotFoundError(f"Component with ID {component_id} not found")

        component.quantity = new_quantity
        session.commit()
        return component
    except Exception as e:
        session.rollback()
        if not isinstance(e, backend.exceptions.ComponentError):
            raise backend.exceptions.DatabaseError(f"Error while updating component quantity: {e}") from e
        raise
    finally:
        session.close()


def select_multiple_components(component_ids: list[uuid.UUID]) -> list[Component] | None:
    if not component_ids:
        return []

    session = get_session()
    try:
        selected_components = session.query(Component) \
            .filter(Component.id.in_(component_ids)) \
            .all()
        return selected_components
    except Exception as e:
        raise backend.exceptions.DatabaseError(f"Error selecting multiple components: {e}") from e
    finally:
        session.close()


def get_components_by_part_number(part_number: str) -> list[Component] | None:
    session = get_session()
    try:
        return session.query(Component).filter_by(part_number=part_number).all()
    except Exception as e:
        raise backend.exceptions.DatabaseError(f"Error fetching components by part number {part_number}: {e}") from e
    finally:
        session.close()
