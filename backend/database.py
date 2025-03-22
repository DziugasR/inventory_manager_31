from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = "sqlite:///inventory.db"
engine = create_engine(DATABASE_URL, echo=True)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    """ Returns a new database session. """
    return Session()
