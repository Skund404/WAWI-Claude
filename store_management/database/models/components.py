# database/models/components.py
"""
Component models for the database.
"""

from sqlalchemy import Column, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, BaseModel
from .mixins import TimestampMixin, ValidationMixin, CostingMixin

class Component(BaseModel, Base, TimestampMixin, ValidationMixin, CostingMixin):
    """
    Base component model for various types of components in the system.
    """
    __tablename__ = 'components'

    # Common attributes for all components
    name = Column(String, nullable=False)
    description = Column(String)
    quantity = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)

    # Relationship to project can be defined here or in specific subclasses
    project_id = Column(ForeignKey('projects.id'), nullable=True)
    project = relationship('Project', back_populates='components')

    def __repr__(self):
        """
        String representation of the component.

        Returns:
            str: A string describing the component
        """
        return (
            f"<Component(id={self.id}, "
            f"name='{self.name}', "
            f"quantity={self.quantity}, "
            f"unit_price={self.unit_price})>"
        )

class ProjectComponent(Component):
    """
    Specific component type associated with projects.
    """
    __tablename__ = 'project_components'

    # Additional project-specific attributes can be added here
    material_type = Column(String)
    estimated_quantity = Column(Float)

class PatternComponent(Component):
    """
    Components specific to patterns/recipes.
    """
    __tablename__ = 'pattern_components'

    # Additional pattern-specific attributes
    cutting_instructions = Column(String)
    complexity_rating = Column(Float)

def can_substitute_material(component, alternate_material_type):
    """
    Check if a material can be substituted.

    Args:
        component: The original component
        alternate_material_type: The type of alternate material

    Returns:
        bool: Whether the material can be substituted
    """
    # Implement substitution logic here
    return True