# database/models/components.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from typing import Dict, Any, Optional

from .base import Base, BaseModel
from .enums import (
    MaterialType,
    ComponentType,
    StitchType,
    EdgeFinishType
)
from .mixins import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin
)


class Component(BaseModel, TimestampMixin, ValidationMixin, CostingMixin):
    """Base class for all component types."""
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    material_type = Column(Enum(MaterialType), nullable=False)
    component_type = Column(Enum(ComponentType), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    unit_cost = Column(Float, nullable=False, default=0.0)
    # Add the discriminator column
    component_type_discriminator = Column(String(50), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'base_component',
        'polymorphic_on': component_type_discriminator
    }

    def __repr__(self) -> str:
        return f"<Component {self.name}>"

    def calculate_total_cost(self) -> float:
        """Calculate the total cost for this component."""
        return self.quantity * self.unit_cost

    def validate_component(self) -> None:
        """Validate component data."""
        self.validate_required_fields([
            'name',
            'material_type',
            'component_type',
            'quantity',
            'unit_cost'
        ])

    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """Base to_dict implementation."""
        exclude_fields = exclude_fields or []
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'material_type': self.material_type.name if self.material_type else None,
            'component_type': self.component_type.name if self.component_type else None,
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'total_cost': self.calculate_total_cost()
        }


class ProjectComponent(Component):
    """Component within a specific project."""
    __tablename__ = 'project_components'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    actual_quantity_used = Column(Float)
    wastage = Column(Float, default=0.0)

    # Relationships
    project = relationship("Project", back_populates="components")

    __mapper_args__ = {
        'polymorphic_identity': 'project_component',
    }

    def calculate_material_efficiency(self, actual_material_used: float, planned_material: float) -> float:
        """Calculate material usage efficiency."""
        if planned_material <= 0:
            return 0.0
        return (1 - abs(actual_material_used - planned_material) / planned_material) * 100

    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """Convert to dictionary with additional project component fields."""
        base_dict = super().to_dict(exclude_fields)
        base_dict.update({
            'project_id': self.project_id,
            'actual_quantity_used': self.actual_quantity_used,
            'wastage': self.wastage,
            'efficiency': self.calculate_material_efficiency(
                self.actual_quantity_used or 0.0,
                self.quantity
            ) if self.actual_quantity_used is not None else None
        })
        return base_dict


class PatternComponent(Component):
    """Component template used in patterns."""
    __tablename__ = 'pattern_components'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=False)
    minimum_quantity = Column(Float, default=0.0)
    substitutable = Column(Boolean, default=False)
    stitch_type = Column(Enum(StitchType))
    edge_finish_type = Column(Enum(EdgeFinishType))

    # Relationships
    pattern = relationship("Pattern", back_populates="components")

    __mapper_args__ = {
        'polymorphic_identity': 'pattern_component',
    }

    def can_substitute(self, alternate_material_type: MaterialType) -> bool:
        """Check if material can be substituted."""
        return self.substitutable and alternate_material_type != self.material_type

    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """Convert to dictionary with additional pattern component fields."""
        base_dict = super().to_dict(exclude_fields)
        base_dict.update({
            'pattern_id': self.pattern_id,
            'minimum_quantity': self.minimum_quantity,
            'substitutable': self.substitutable,
            'stitch_type': self.stitch_type.name if self.stitch_type else None,
            'edge_finish_type': self.edge_finish_type.name if self.edge_finish_type else None
        })
        return base_dict