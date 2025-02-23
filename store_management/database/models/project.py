# database/models/project.py

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.base import BaseModel
from database.models.base import Base



class ProjectType(Enum):
    """Enumeration of possible project types."""
    LEATHER_BAG = "leather_bag"
    WALLET = "wallet"
    BELT = "belt"
    CUSTOM = "custom"
    OTHER = "other"


class SkillLevel(Enum):
    """Enumeration of required skill levels for projects."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ProductionStatus(Enum):
    """Enumeration of possible production statuses."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(BaseModel):
    """
    Project model representing a leatherworking project with all its attributes
    and relationships.
    """
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    project_type = Column(SQLEnum(ProjectType), nullable=False)
    skill_level = Column(SQLEnum(SkillLevel), nullable=False)
    status = Column(SQLEnum(ProductionStatus), nullable=False, default=ProductionStatus.PLANNED)

    # Timeline
    start_date = Column(DateTime, default=datetime.utcnow)
    target_completion_date = Column(DateTime)
    actual_completion_date = Column(DateTime)

    # Complexity and time tracking
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0.0)
    complexity_score = Column(Float)

    # Quality metrics
    quality_rating = Column(Integer)
    customer_satisfaction = Column(Integer)

    # Relationships
    components = relationship("ProjectComponent", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of the Project."""
        return f"<Project(id={self.id}, name='{self.name}', type={self.project_type}, status={self.status})>"

    def calculate_complexity(self) -> float:
        """
        Calculate the project complexity score based on components and requirements.

        Returns:
            float: Calculated complexity score
        """
        base_score = {
            SkillLevel.BEGINNER: 1.0,
            SkillLevel.INTERMEDIATE: 2.0,
            SkillLevel.ADVANCED: 3.0,
            SkillLevel.EXPERT: 4.0
        }[self.skill_level]

        # Add component complexity
        component_score = sum(component.complexity_factor for component in self.components)

        # Calculate final score
        self.complexity_score = base_score * (1 + component_score)
        return self.complexity_score

    def update_quality_metrics(self, quality_rating: int, customer_satisfaction: Optional[int] = None) -> None:
        """
        Update the project's quality metrics.

        Args:
            quality_rating (int): Internal quality assessment (1-10)
            customer_satisfaction (int, optional): Customer satisfaction rating (1-10)
        """
        if not 1 <= quality_rating <= 10:
            raise ValueError("Quality rating must be between 1 and 10")

        if customer_satisfaction is not None and not 1 <= customer_satisfaction <= 10:
            raise ValueError("Customer satisfaction must be between 1 and 10")

        self.quality_rating = quality_rating
        if customer_satisfaction is not None:
            self.customer_satisfaction = customer_satisfaction