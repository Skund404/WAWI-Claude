# database/models/pattern.py
from database.models.base import Base
from database.models.enums import SkillLevel
from sqlalchemy import Column, Enum, String, Text, Integer, Float, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class Pattern(Base):
    """
    Model representing leatherworking patterns.
    """
    # Pattern specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    skill_level = Column(Enum(SkillLevel), nullable=False, default=SkillLevel.BEGINNER)
    version = Column(String(20), nullable=True)

    width_mm = Column(Float, nullable=True)
    height_mm = Column(Float, nullable=True)

    estimated_time_hours = Column(Float, nullable=True)
    estimated_leather_sqft = Column(Float, nullable=True)

    instructions = Column(Text, nullable=True)
    tools_required = Column(Text, nullable=True)
    materials_required = Column(Text, nullable=True)

    is_published = Column(Boolean, default=False, nullable=False)
    publication_date = Column(DateTime, nullable=True)

    file_path = Column(String(255), nullable=True)
    pattern_metadata  = Column(JSON, nullable=True)

    # Relationships
    components = relationship("PatternComponent", back_populates="pattern", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="pattern")

    def __init__(self, **kwargs):
        """Initialize a Pattern instance with validation.

        Args:
            **kwargs: Keyword arguments with pattern attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate pattern data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        if 'name' not in data or not data['name']:
            raise ValueError("Pattern name is required")

        if 'skill_level' not in data:
            data['skill_level'] = SkillLevel.BEGINNER

    def publish(self):
        """Mark the pattern as published and set publication date."""
        self.is_published = True
        self.publication_date = datetime.utcnow()

    def unpublish(self):
        """Mark the pattern as unpublished."""
        self.is_published = False

    def calculate_leather_requirement(self):
        """Calculate total leather requirement based on components.

        Returns:
            float: Total estimated leather requirement in square feet
        """
        total = self.estimated_leather_sqft or 0

        # If component relationships are loaded, add their requirements
        if self.components:
            for component in self.components:
                if hasattr(component, 'area_sqft') and component.area_sqft:
                    total += component.area_sqft

        return total

    def __repr__(self):
        """String representation of the pattern.

        Returns:
            str: String representation
        """
        return f"<Pattern(id={self.id}, name='{self.name}', skill_level={self.skill_level})>"