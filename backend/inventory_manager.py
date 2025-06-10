from .database import get_config_session
from .models_custom import Inventory
from . import exceptions


def get_all_inventories():
    session = get_config_session()
    try:
        return session.query(Inventory).order_by(Inventory.name).all()
    except Exception as e:
        raise exceptions.DatabaseError(f"Error fetching all inventories: {e}") from e
    finally:
        session.close()


def add_new_inventory(name: str, db_path: str) -> Inventory:
    session = get_config_session()
    try:
        if session.query(Inventory).filter_by(name=name).first():
            raise exceptions.DuplicateComponentError(f"Inventory with name '{name}' already exists.")
        if session.query(Inventory).filter_by(db_path=db_path).first():
            raise exceptions.DuplicateComponentError(f"Inventory with db_path '{db_path}' already exists.")

        new_inventory = Inventory(name=name, db_path=db_path)
        session.add(new_inventory)
        session.commit()
        session.refresh(new_inventory)
        return new_inventory
    except Exception as e:
        session.rollback()
        if isinstance(e, exceptions.DuplicateComponentError):
            raise
        raise exceptions.DatabaseError(f"Database error while adding new inventory: {e}") from e
    finally:
        session.close()