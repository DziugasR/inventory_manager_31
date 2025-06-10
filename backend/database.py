from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SessionType
from sqlalchemy.engine import Engine
from typing import Optional
from .models import Base as InventoryBase
from .models_custom import Base as ConfigBase
from .models_custom import Inventory


config_engine: Optional[Engine] = None
inventory_engine: Optional[Engine] = None

ConfigSession: Optional[sessionmaker[SessionType]] = None
InventorySession: Optional[sessionmaker[SessionType]] = None

def initialize_databases(config_db_url: str, inventory_db_url: str):
    global config_engine, inventory_engine, ConfigSession, InventorySession

    if config_engine or inventory_engine:
        print("Warning: Databases may already be initialized.")

    print(f"INFO: Initializing Config DB with URL: {config_db_url}")
    try:
        config_engine = create_engine(config_db_url, echo=False)
        ConfigBase.metadata.create_all(config_engine)
        ConfigSession = sessionmaker(bind=config_engine)
        with config_engine.connect():
             print("INFO: Config DB connection successful (test).")
    except Exception as e:
        print(f"CRITICAL: Failed during Config DB engine creation: {e}")
        raise

    print(f"INFO: Initializing Inventory DB with URL: {inventory_db_url}")
    try:
        inventory_engine = create_engine(inventory_db_url, echo=False)
        InventoryBase.metadata.create_all(inventory_engine)
        InventorySession = sessionmaker(bind=inventory_engine)
        with inventory_engine.connect():
            print("INFO: Inventory DB connection successful (test).")
    except Exception as e:
        print(f"CRITICAL: Failed during Inventory DB engine creation: {e}")
        raise

    with ConfigSession() as session:
        if not session.query(Inventory).first():
            print("INFO: No default inventory found. Creating 'Main Inventory'.")
            default_inventory = Inventory(name="Main Inventory", db_path=inventory_db_url.split('///')[1])
            session.add(default_inventory)
            session.commit()

def switch_inventory_db(inventory_db_url: str):
    global inventory_engine, InventorySession

    print(f"INFO: Switching to Inventory DB: {inventory_db_url}")
    try:
        inventory_engine = create_engine(inventory_db_url, echo=False)
        InventoryBase.metadata.create_all(inventory_engine)
        InventorySession = sessionmaker(bind=inventory_engine)
        with inventory_engine.connect():
            print("INFO: New Inventory DB connection successful (test).")
    except Exception as e:
        print(f"CRITICAL: Failed during Inventory DB switch: {e}")
        raise

def get_config_session() -> SessionType:
    if ConfigSession is None:
        raise RuntimeError("Config Database has not been initialized. Call initialize_databases() first.")
    return ConfigSession()

def get_inventory_session() -> SessionType:
    if InventorySession is None:
        raise RuntimeError("Inventory Database has not been initialized. Call initialize_databases() first.")
    return InventorySession()

# For backward compatibility with existing code
get_session = get_inventory_session