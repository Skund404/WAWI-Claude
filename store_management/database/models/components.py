# path: database/models/components.py
"""
Component models for the store management application.

This module defines the database models for components used in projects,
patterns, and products, including their relationships and attributes.
"""

import enum
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Float, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref

# Import the Base from the updated base module
from database.models.base import Base
from database.models.enums import ComponentType


class Component(Base):
    """
    Base model for all components in the system.

    This is the foundation for specific component types like
    PatternComponent and ProjectComponent.
    """
    __tablename__ = 'components'

    # Add this line to handle the "Table already defined" error
    __table_args__ = {'extend_existing': True}

    # Polymorphic base configuration
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Component attributes
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    component_type: Mapped[ComponentType] = mapped_column(nullable=False)
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Polymorphic configuration for single-table inheritance
    __mapper_args__ = {
        'polymorphic_identity': 'component',
        'polymorphic_on': type
    }

    def calculate_cost(self) -> float:
        """Calculate the cost of the component."""
        return self.cost or 0.0

    def validate(self) -> bool:
        """Validate the component data."""
        # Basic validation
        if not self.name:
            return False
        if self.quantity <= 0:
            return False
        return True


# For Pattern and Project components, use single-table inheritance
# This avoids the column conflict issue entirely by using one table
class PatternComponent(Component):
    """
    Component used in a pattern template.

    PatternComponents define the theoretical components needed for a pattern,
    without being tied to a specific project instance.
    """
    # Add this line to extend the parent table
    __table_args__ = {'extend_existing': True}

    # Pattern relationship attributes
    # Pattern relationships stored in same table
    pattern_id: Mapped[Optional[int]] = mapped_column(ForeignKey('patterns.id'), nullable=True)
    min_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    pattern_notes: Mapped[Optional[str]] = mapped_column('notes', Text, nullable=True)

    # Many-to-one: PatternComponent => Pattern
    pattern = relationship("Pattern", back_populates="components")

    # Polymorphic configuration for single-table inheritance
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
    # Add this line to extend the parent table
    __table_args__ = {'extend_existing': True}

    # Project relationship attributes
    # Project relationships stored in same table
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey('projects.id'), nullable=True)
    planned_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wastage: Mapped[float] = mapped_column(Float, default=0.0, nullable=True)
    efficiency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    project_notes: Mapped[Optional[str]] = mapped_column('project_notes', Text, nullable=True)

    # Many-to-one: ProjectComponent => Project
    project = relationship("Project", back_populates="components")

    # Polymorphic configuration for single-table inheritance
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