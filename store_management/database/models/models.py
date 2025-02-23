# database/models/components.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from typing import Dict, Optional
from .base import BaseModel
from .interfaces import IComponent
from .enums import ComponentType, MaterialType
from .mixins import TimestampMixin, ValidationMixin, CostingMixin


class Component(BaseModel, IComponent, TimestampMixin, ValidationMixin, CostingMixin):
    """Base class for all components."""
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    component_type = Column(Enum(ComponentType))
    material_type = Column(Enum(MaterialType))
    quantity = Column(Float, default=0.0)
    unit_cost = Column(Float, default=0.0)

    __mapper_args__ = {
        'polymorphic_identity': 'component',
        'polymorphic_on': component_type
    }

    def calculate_cost(self) -> float:
        """Calculate the total cost of this component."""
        return self.quantity * self.unit_cost

    def validate(self) -> bool:
        """Validate component data."""
        required_fields = ['name', 'component_type', 'material_type', 'quantity']
        return (self.validate_required_fields(required_fields) and
                self.validate_numeric_range(self.quantity, 0, float('inf')))

    def get_material_requirements(self) -> Dict[str, float]:
        """Get the material requirements for this component."""
        return {
            'material_type': self.material_type.name,
            'quantity': self.quantity
        }


class ProjectComponent(Component):
    """Component specifically for projects."""
    __tablename__ = 'project_components'

    id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    actual_quantity = Column(Float, default=0.0)
    wastage = Column(Float, default=0.0)

    # Relationships
    project = relationship("Project", back_populates="components")

    __mapper_args__ = {
        'polymorphic_identity': 'project_component',
    }

    def calculate_efficiency(self) -> float:
        """Calculate material usage efficiency."""
        if self.quantity == 0:
            return 0.0
        return (self.actual_quantity - self.wastage) / self.quantity * 100


class RecipeComponent(Component):
    """Component specifically for recipes."""
    __tablename__ = 'recipe_components'

    id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    minimum_quantity = Column(Float, default=0.0)
    substitutable = Column(Boolean, default=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="components")

    __mapper_args__ = {
        'polymorphic_identity': 'recipe_component',
    }

    def can_substitute(self, alternate_material_type: MaterialType) -> bool:
        """Check if this component can be substituted with another material."""
        return self.substitutable


