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


def remove_component_by_part_number(part_number):
    """Removes a component from the database using the part number."""
    session = get_session()
    try:
        component = session.query(Component).filter_by(part_number=part_number).first()
        if not component:
            raise ComponentNotFoundError(f"Component with part number {part_number} not found")

        session.delete(component)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        if not isinstance(e, ComponentError):
            raise DatabaseError(f"Error while deleting component: {e}") from e
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

# TODO scrap this shit and import/export from excel instead

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