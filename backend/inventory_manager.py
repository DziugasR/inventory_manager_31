import os
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


def delete_inventory(inventory_id: str, app_path: str) -> bool:
    session = get_config_session()
    db_file_path = None

    try:
        inventory_to_delete = session.query(Inventory).filter_by(id=inventory_id).first()
        if not inventory_to_delete:
            raise exceptions.ComponentNotFoundError(f"Inventory with ID '{inventory_id}' not found.")

        db_file_path = inventory_to_delete.db_path
        if not os.path.isabs(db_file_path):
            db_file_path = os.path.join(app_path, db_file_path)

        session.delete(inventory_to_delete)
        session.commit()

    except Exception as e:
        session.rollback()
        if isinstance(e, exceptions.ComponentNotFoundError):
            raise
        raise exceptions.DatabaseError(f"Database error while deleting inventory record: {e}") from e
    finally:
        session.close()

    if db_file_path:
        try:
            if os.path.exists(db_file_path):
                os.remove(db_file_path)
                print(f"INFO: Successfully deleted inventory file: {db_file_path}")
            else:
                # The record was deleted, but the file was already gone. This is not an error.
                print(f"WARNING: Inventory DB entry removed, but associated file was not found at '{db_file_path}'.")
        except (IOError, OSError) as e:
            # The DB record is gone, but the file could not be deleted. This leaves an orphaned file.
            print(f"WARNING: Could not delete inventory file '{db_file_path}'. The file may be orphaned. DB entry was removed. Error: {e}")

    return True