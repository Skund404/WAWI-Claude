# database/models/project.py
"""
Project model module for the leatherworking store management system.

Defines classes for Project and ProjectComponent models.
"""

import enum
# database/models/project.py
"""
Project model module for the leatherworking store management system.

Defines classes for Project and ProjectComponent models.
"""

import enum
import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Enum, Boolean,
    DateTime, Text, Table
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel
from database.models.enums import ProjectType, SkillLevel, ProjectStatus



# Association table for many-to-many relationships if needed
project_components = Table(
    'project_components',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('project.id'), primary_key=True),
    Column('component_id', Integer, ForeignKey('project_component.id'), primary_key=True)
)


class Project(Base, BaseModel):
    """
    Model for leatherworking projects.

    A project represents a specific leatherwork item being created,
    based on a pattern and using specific materials.
    """
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(Enum(ProjectType), nullable=False)
    skill_level = Column(Enum(SkillLevel), nullable=False)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.NEW)

    # Relationships
    components = relationship("ProjectComponent",
                              secondary=project_components,
                              back_populates="projects")
    pattern_id = Column(Integer, ForeignKey('pattern.id'), nullable=True)
    pattern = relationship("Pattern", back_populates="projects")

    # Optional fields for quality metrics
    quality_rating = Column(Float, nullable=True)
    customer_satisfaction = Column(Float, nullable=True)

    # Fields for project complexity and tracking
    complexity_score = Column(Float, default=0.0)
    time_spent = Column(Float, default=0.0)  # In hours

    def __repr__(self):
        """Return a string representation of the project."""
        return f"<Project id={self.id}, name='{self.name}', status={self.status}>"

    def calculate_complexity(self) -> float:
        """
        Calculate the complexity score of the project.

        Returns:
            float: Complexity score based on various factors
        """
        # Simple implementation - in a real app this would be more sophisticated
        base_score = 1.0

        # Adjust based on skill level
        skill_multipliers = {
            SkillLevel.BEGINNER: 1.0,
            SkillLevel.INTERMEDIATE: 1.5,
            SkillLevel.ADVANCED: 2.0,
            SkillLevel.EXPERT: 3.0
        }
        skill_factor = skill_multipliers.get(self.skill_level, 1.0)

        # Adjust based on component count
        component_factor = 0.1 * len(self.components) if self.components else 0

        self.complexity_score = base_score * skill_factor + component_factor
        return self.complexity_score

    def update_quality_metrics(self, quality_rating: float, customer_satisfaction: float) -> None:
        """
        Update the quality metrics for the project.

        Args:
            quality_rating: Quality rating from 1 to 5
            customer_satisfaction: Customer satisfaction rating from 1 to 5
        """
        if 1 <= quality_rating <= 5 and 1 <= customer_satisfaction <= 5:
            self.quality_rating = quality_rating
            self.customer_satisfaction = customer_satisfaction
        else:
            raise ValueError("Quality ratings must be between 1 and 5")


class ProjectComponent(Base, BaseModel):
    """
    Component used in a specific project.

    ProjectComponents represent actual materials used in a concrete project,
    with actual quantities and costs.
    """
    __tablename__ = 'project_component'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_cost = Column(Float, nullable=False, default=0.0)

    # Foreign keys
    material_id = Column(Integer, ForeignKey('material.id'), nullable=True)
    part_id = Column(Integer, ForeignKey('part.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=True)

    # Relationships
    material = relationship("Material", back_populates="components")
    part = relationship("Part", back_populates="components")
    leather = relationship("Leather", back_populates="components")
    projects = relationship("Project",
                            secondary=project_components,
                            back_populates="components")

    # Efficiency tracking
    expected_quantity = Column(Float, nullable=True)
    actual_quantity = Column(Float, nullable=True)
    wastage = Column(Float, nullable=True, default=0.0)

    def __repr__(self):
        """Return a string representation of the project component."""
        return f"<ProjectComponent id={self.id}, name='{self.name}', quantity={self.quantity}>"

    def calculate_efficiency(self) -> Optional[float]:
        """
        Calculate the material efficiency for this component.

        Returns:
            float: Efficiency percentage or None if data is incomplete
        """
        if self.expected_quantity and self.actual_quantity and self.expected_quantity > 0:
            return (self.expected_quantity / self.actual_quantity) * 100
        return None