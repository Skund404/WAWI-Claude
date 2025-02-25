# path: database/models/components.py
"""
Component models for the store management application.

This module defines the database models for components used in projects,
patterns, and products, including their relationships and attributes.
"""

import enum
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum, Boolean, DateTime, Text
from sqlalchemy.orm import relationship, backref

# Import the SQLAlchemy declarative base and mixins carefully
from database.models.base import BaseModel
from sqlalchemy.ext.declarative import declarative_base

# Create a local Base to avoid conflicts
Base = declarative_base()


# Import mixins if needed but avoid circular dependencies
class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ValidationMixin:
    """Mixin to add validation functionality to models."""

    def validate(self) -> bool:
        """Validate the model data."""
        return True


class CostingMixin:
    """Mixin to add costing functionality to models."""
    cost = Column(Float, nullable=True)

    def calculate_cost(self) -> float:
        """Calculate the cost of the component."""
        return self.cost or 0.0


class ComponentType(enum.Enum):
    """Enumeration of component types."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    LINING = "lining"
    ADHESIVE = "adhesive"
    OTHER = "other"


class Component(Base):
    """
    Base model for all components in the system.

    This is the foundation for specific component types like
    PatternComponent and ProjectComponent.
    """
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    component_type = Column(Enum(ComponentType), nullable=False)
    quantity = Column(Float, default=1.0)
    unit = Column(String(20), nullable=True)
    cost = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Discriminator column for polymorphic identity
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'component',
        'polymorphic_on': type
    }

    def __repr__(self) -> str:
        return f"<Component(id={self.id}, name='{self.name}', type={self.component_type})>"

    def calculate_cost(self) -> float:
        """Calculate the cost of the component."""
        return self.cost or 0.0

    def validate(self) -> bool:
        """Validate the component data."""
        return True


class PatternComponent(Component):
    """
    Component used in a pattern template.

    PatternComponents define the theoretical components needed for a pattern,
    without being tied to a specific project instance.
    """
    __tablename__ = 'pattern_components'

    id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=True)

    # Optional sizing information
    min_quantity = Column(Float, nullable=True)
    max_quantity = Column(Float, nullable=True)
    is_optional = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    # Many-to-one: PatternComponent => Pattern
    pattern = relationship("Pattern", backref=backref("components", cascade="all, delete-orphan"))

    __mapper_args__ = {
        'polymorphic_identity': 'pattern_component',
    }

    def __repr__(self) -> str:
        return f"<PatternComponent(id={self.id}, name='{self.name}', pattern_id={self.pattern_id})>"


class ProjectComponent(Component):
    """
    Component used in a specific project.

    ProjectComponents represent actual materials used in a concrete project,
    with actual quantities and costs.
    """
    __tablename__ = 'project_components'

    id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)

    # Usage tracking
    planned_quantity = Column(Float, nullable=True)
    actual_quantity = Column(Float, nullable=True)
    wastage = Column(Float, default=0.0)
    efficiency = Column(Float, nullable=True)

    # Status and notes
    is_completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    # Many-to-one: ProjectComponent => Project
    project = relationship("Project", backref=backref("components", cascade="all, delete-orphan"))

    __mapper_args__ = {
        'polymorphic_identity': 'project_component',
    }

    def __repr__(self) -> str:
        return f"<ProjectComponent(id={self.id}, name='{self.name}', project_id={self.project_id})>"

    def calculate_efficiency(self) -> float:
        """Calculate the material efficiency for this component."""
        if not self.planned_quantity or not self.actual_quantity:
            return 0.0

        used = self.actual_quantity - self.wastage
        return (used / self.planned_quantity) * 100.0