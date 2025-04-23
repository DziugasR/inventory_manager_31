import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SessionType
from sqlalchemy.engine import Engine
from typing import Optional
from .models import Base

engine: Optional[Engine] = None
Session: Optional[sessionmaker[SessionType]] = None

def initialize_database(database_url: str):
    global engine, Session

    if engine is not None:
        print("Warning: Database already initialized.")
        return

    print(f"INFO: Initializing database with URL: {database_url}")
    try:
        engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        with engine.connect() as connection:
            print("INFO: Database connection successful (test).")
    except Exception as e:
        print(f"CRITICAL: Failed during database engine creation or table setup for {database_url}: {e}")
        engine = None
        Session = None
        raise

def get_session() -> SessionType:
    if Session is None:
        raise RuntimeError("Database has not been initialized. Call initialize_database() first.")
    session = Session()
    return session