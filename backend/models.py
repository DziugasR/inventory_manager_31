import uuid
from sqlalchemy import Column, Integer, String, UUID, Text
from sqlalchemy.ext.declarative import declarative_base
from abc import abstractmethod

Base = declarative_base()

class Component(Base):
    __tablename__ = "components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_number = Column(String, nullable=False)
    component_type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    purchase_link = Column(String, nullable=True)
    datasheet_link = Column(String, nullable=True)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": component_type,
        "polymorphic_identity": "component"
    }

    @abstractmethod
    def get_specifications(self):
        pass

def create_component_class(class_name, polymorphic_id, spec_format_string):
    """Dynamically creates a Component subclass."""

    def generated_get_specifications(self):
        return f"{self.value}"

    class_attributes = {
        "__mapper_args__": {"polymorphic_identity": polymorphic_id},
        "get_specifications": generated_get_specifications
    }

    internal_class_name = f"{class_name}_{polymorphic_id}"

    if internal_class_name in globals() or hasattr(Base, internal_class_name):
        return globals().get(internal_class_name) or getattr(Base, internal_class_name)

    new_class = type(internal_class_name, (Component,), class_attributes)
    globals()[internal_class_name] = new_class
    return new_class