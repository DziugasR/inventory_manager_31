import uuid
import json
from sqlalchemy import Column, String, Text, UniqueConstraint
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declarative_base

# Use a new Base for the config DB to keep it separate from inventory models
Base = declarative_base()


class Inventory(Base):
    __tablename__ = 'inventories'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    db_path = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return f"<Inventory(id='{self.id}', name='{self.name}', path='{self.db_path}')>"


class ComponentTypeDefinition(Base):
    __tablename__ = 'component_type_definitions'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ui_name = Column(String, nullable=False, unique=True)
    backend_id = Column(String, nullable=False, unique=True)
    properties_json = Column(Text, nullable=False, default='[]')

    __table_args__ = (
        UniqueConstraint('ui_name', name='uq_ui_name'),
        UniqueConstraint('backend_id', name='uq_backend_id'),
    )

    @property
    def properties(self):
        try:
            return json.loads(self.properties_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @properties.setter
    def properties(self, value):
        if isinstance(value, list):
            self.properties_json = json.dumps(value)
        else:
            raise TypeError("Properties must be a list of strings.")

    @validates('backend_id')
    def validate_backend_id(self, key, backend_id):
        if ' ' in backend_id or backend_id.lower() != backend_id:
            raise ValueError("backend_id must be lowercase and contain no spaces.")
        return backend_id

    def __repr__(self):
        return f"<ComponentTypeDefinition(ui_name='{self.ui_name}', backend_id='{self.backend_id}')>"


class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True, nullable=False)
    value = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Setting(key='{self.key}', value='{self.value}')>"