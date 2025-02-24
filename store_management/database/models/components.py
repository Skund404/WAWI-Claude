# database/models/components.py
"""
Component models for the store management system.

This module defines base and specialized component classes
for projects and patterns in the leatherworking management system.
"""

from typing import Optional, Dict, Any
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.ext.declarative import declared_attr

from .base import Base, BaseModel
from .enums import ComponentType, MaterialType
from .mixins import TimestampMixin, ValidationMixin, CostingMixin


class Component(Base, TimestampMixin, ValidationMixin, CostingMixin):
    """
    Base component class for all project and pattern components.

    Provides common attributes and methods for components
    used in leatherworking projects and patterns.

    Attributes:
        id (int): Unique identifier for the component
        name (str): Name of the component
        description (str, optional): Detailed description of the component
        component_type (ComponentType): Type of the component
        material_type (MaterialType): Type of material used
        quantity (float): Quantity of the component
        unit_cost (float): Cost per unit of the component
    """
    __tablename__ = 'components'
    __mapper_args__ = {
        'polymorphic_identity': 'component',
        'polymorphic_on': 'type'
    }

    id = Column(Integer, primary_key=True)
    type = Column(String(50))
    name = Column(String, nullable=False)
    description = Column(String)
    component_type = Column(Enum(ComponentType), nullable=False)
    material_type = Column(Enum(MaterialType), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_cost = Column(Float, nullable=False, default=0.0)

    def __repr__(self) -> str:
        """
        String representation of the component.

        Returns:
            str: Readable representation of the component
        """
        return (f"<Component(id={self.id}, name='{self.name}', "
                f"type={self.component_type}, material={self.material_type})>")

    def calculate_total_cost(self) -> float:
        """
        Calculate the total cost of the component.

        Returns:
            float: Total cost (quantity * unit cost)
        """
        return self.quantity * self.unit_cost

    def validate_component(self) -> bool:
        """
        Validate the component's data integrity.

        Returns:
            bool: True if component data is valid, False otherwise
        """
        # Validate required fields
        if not self.validate_required_fields(['name', 'component_type', 'material_type']):
            return False

        # Validate numeric fields
        if not all([
            self.validate_numeric_range(self.quantity, min_val=0),
            self.validate_numeric_range(self.unit_cost, min_val=0)
        ]):
            return False

        return True


class ProjectComponent(Component):
    """
    Specialized component class for project-specific components.

    Extends the base Component class with project-specific attributes
    and methods.

    Attributes:
        project_id (int): Foreign key to the associated project
        project (Project): Relationship to the parent project
        efficiency (float, optional): Material usage efficiency
    """
    __mapper_args__ = {
        'polymorphic_identity': 'project_component'
    }
    __tablename__ = 'project_components'

    # Use the base class's primary key as foreign key
    id = Column(Integer, ForeignKey('components.id'), primary_key=True)

    # Use an optional relationship to project, which can be defined in the Project model
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    efficiency = Column(Float)

    def calculate_material_efficiency(
            self,
            actual_material_used: float,
            planned_material: float
    ) -> float:
        """
        Calculate material efficiency for the project component.

        Args:
            actual_material_used (float): Amount of material actually used
            planned_material (float): Amount of material originally planned

        Returns:
            float: Material efficiency percentage
        """
        if planned_material <= 0:
            return 0.0

        efficiency = (planned_material - actual_material_used) / planned_material * 100
        return max(0.0, min(efficiency, 100.0))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the project component to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary of component attributes
        """
        base_dict = super().to_dict() if hasattr(super(), 'to_dict') else {}
        base_dict.update({
            'project_id': self.project_id,
            'efficiency': self.efficiency
        })
        return base_dict


class RecipeComponent(Component):
    """
    Specialized component class for pattern-specific components.

    Extends the base Component class with pattern-specific attributes
    and methods.

    Attributes:
        recipe_id (int): Foreign key to the associated pattern
        pattern (Project): Relationship to the parent pattern
        minimum_quantity (float, optional): Minimum required quantity
        substitutable (bool, optional): Whether the component can be substituted
    """
    __mapper_args__ = {
        'polymorphic_identity': 'recipe_component'
    }
    __tablename__ = 'recipe_components'

    # Use the base class's primary key as foreign key
    id = Column(Integer, ForeignKey('components.id'), primary_key=True)

    # Use an optional relationship to pattern, which can be defined in the Project model
    recipe_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    minimum_quantity = Column(Float)
    substitutable = Column(sa.Boolean, default=False)

    def can_substitute(self, alternate_material_type: MaterialType) -> bool:
        """
        Check if this component can be substituted with another material type.

        Args:
            alternate_material_type (MaterialType): Material type to check for substitution

        Returns:
            bool: True if substitution is possible, False otherwise
        """
        return (
                self.substitutable and
                alternate_material_type != self.material_type
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the pattern component to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary of component attributes
        """
        base_dict = super().to_dict() if hasattr(super(), 'to_dict') else {}
        base_dict.update({
            'recipe_id': self.recipe_id,
            'minimum_quantity': self.minimum_quantity,
            'substitutable': self.substitutable
        })
        return base_dict