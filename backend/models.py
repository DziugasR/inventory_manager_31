from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, autoincrement=True)
    part_number = Column(String, unique=False, nullable=True)  # Allow NULL values
    name = Column(String, nullable=True)  # Allow NULL values
    component_type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Component(part_number={self.part_number}, name={self.name}, type={self.component_type}, quantity={self.quantity})>"
