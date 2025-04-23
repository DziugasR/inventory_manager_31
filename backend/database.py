import os
import configparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

try:
    if not config.read(config_path):
         print(f"Warning: Configuration file '{config_path}' not found or empty.")
         DATABASE_URL = "sqlite:///inventory.db"
    else:
        DATABASE_URL = config.get('Database', 'url', fallback="sqlite:///inventory.db")

except configparser.Error as e:
     print(f"Error reading configuration file '{config_path}': {e}")
     DATABASE_URL = "sqlite:///inventory.db"

print(f"Using database URL: {DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=True)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()
