# File: database/models/project_component.py
from enum import Enum
from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import relationship
from database.models.base import BaseModel


class ComponentType(Enum):
    """
    Enumeration of different project component types.
    """
    LEATHER_PIECE = "Leather Piece"
    HARDWARE = "Hardware"
    ACCESSORY = "Accessory"
    TOOL = "Tool"


class ProjectComponent(BaseModel):
    """
    Represents a component within a project.

    Attributes:
        id (int): Unique identifier for the project component.
        name (str): Name of the component.
        component_type (ComponentType): Type of the component.
        quantity (int): Quantity of the component used.
        project_id (int): Foreign key to the associated project.
        project (Project): Relationship to the parent project.
    """
    __tablename__ = 'project_components'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    component_type = Column(SQLAlchemyEnum(ComponentType), nullable=False)
    quantity = Column(Integer, default=1)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)

    # Optional: Establish relationship with Project model
    project = relationship("Project", back_populates="components")

    def __repr__(self):
        """
        Generate a string representation of the project component.

        Returns:
            str: A string representation of the project component.
        """
        return f"<ProjectComponent(id={self.id}, name='{self.name}', type={self.component_type})>"

    def calculate_material_efficiency(self, actual_material_used: float, planned_material: float) -> float:
        """
        Calculate the material efficiency for this project component.

        Args:
            actual_material_used (float): Amount of material actually used.
            planned_material (float): Amount of material originally planned.

        Returns:
            float: Material efficiency percentage.
        """
        if planned_material == 0:
            return 0.0
        return (1 - abs(actual_material_used - planned_material) / planned_material) * 100