# database/models/pattern.py
"""
Pattern models for leatherworking project management.

Defines the data model for patterns used in creating
leatherworking projects and tracking design specifications.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase

from .base import BaseModel, Base
from .enums import ProjectType, SkillLevel, StitchType, EdgeFinishType
from .components import PatternComponent

class Pattern(Base):
    """
    Represents a leatherworking pattern with comprehensive design specifications.

    A pattern serves as a detailed blueprint for creating leather items,
    including technical specifications, material requirements, and
    construction details.

    Attributes:
        id (int): Unique identifier for the pattern
        name (str): Name of the pattern
        description (str, optional): Detailed description of the pattern
        skill_level (SkillLevel): Skill level required for the pattern
        project_type (ProjectType): Type of leatherworking project
        stitch_type (StitchType): Primary stitching technique
        edge_finish_type (EdgeFinishType): Edge finishing method
        pattern_pieces (JSON): Detailed information about pattern pieces
        leather_specifications (JSON): Leather type and quality requirements
        hardware_requirements (JSON): Required hardware and fixtures
        estimated_labor_hours (float): Estimated time to complete
        is_template (bool): Whether this pattern can be used as a template
        version (str): Version of the pattern design
        complexity_score (float): Calculated complexity of the pattern
        pattern_files (relationship): Associated pattern file references
        components (relationship): Components associated with this pattern
    """
    __tablename__ = 'patterns'

    # Timestamp columns
    created_at = Column(DateTime, default=sa.func.now(), nullable=False)
    updated_at = Column(DateTime, default=sa.func.now(), onupdate=sa.func.now(), nullable=False)

    # Primary key
    id = Column(Integer, primary_key=True)

    # Basic pattern information
    name = Column(String, nullable=False)
    description = Column(String)

    # Categorization and skill attributes
    skill_level = Column(Enum(SkillLevel), nullable=False)
    project_type = Column(Enum(ProjectType), nullable=False)
    stitch_type = Column(Enum(StitchType), nullable=True)
    edge_finish_type = Column(Enum(EdgeFinishType), nullable=True)

    # Detailed specifications (using JSON for flexible storage)
    pattern_pieces = Column(JSON)
    leather_specifications = Column(JSON)
    hardware_requirements = Column(JSON)

    # Project attributes
    estimated_labor_hours = Column(Float, default=0.0)
    is_template = Column(Boolean, default=False)
    version = Column(String, default='1.0')
    complexity_score = Column(Float, default=0.0)

    # Relationships
    pattern_files = relationship(
        "PatternFile",
        back_populates="pattern",
        cascade="all, delete-orphan"
    )
    components = relationship(
        "ProjectComponent",
        back_populates="pattern",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        String representation of the pattern.

        Returns:
            str: Readable representation of the pattern
        """
        return (f"<Pattern(id={self.id}, name='{self.name}', "
                f"type={self.project_type}, skill_level={self.skill_level})>")

    def calculate_complexity(self) -> float:
        """
        Calculate the complexity of the pattern.

        Considers multiple factors to determine overall complexity.

        Returns:
            float: Calculated complexity score
        """
        # Base complexity calculation
        complexity = 0.0

        # Component complexity
        complexity += len(self.components) * 0.5

        # Skill level impact
        skill_level_multipliers = {
            SkillLevel.BEGINNER: 1.0,
            SkillLevel.INTERMEDIATE: 1.5,
            SkillLevel.ADVANCED: 2.0,
            SkillLevel.EXPERT: 2.5
        }
        complexity *= skill_level_multipliers.get(self.skill_level, 1.0)

        # Stitch and edge finish complexity
        if self.stitch_type:
            complexity += 0.5
        if self.edge_finish_type:
            complexity += 0.5

        # Labor hours impact
        complexity += self.estimated_labor_hours * 0.1

        # Ensure a reasonable complexity range
        return max(0.1, min(complexity, 10.0))

    def validate_pattern(self) -> bool:
        """
        Validate the pattern's data integrity.

        Returns:
            bool: True if pattern data is valid, False otherwise
        """
        # Validate required fields
        required_fields = ['name', 'skill_level', 'project_type']
        for field in required_fields:
            if not getattr(self, field):
                return False

        # Validate numeric fields
        try:
            if (self.estimated_labor_hours < 0 or
                    self.complexity_score < 0 or
                    self.complexity_score > 10):
                return False
        except (TypeError, ValueError):
            return False

        # Validate components if present
        if self.components:
            for component in self.components:
                try:
                    if not component.validate_component():
                        return False
                except Exception:
                    return False

        return True

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert the pattern to a comprehensive dictionary representation.

        Args:
            exclude_fields (Optional[List[str]], optional): Fields to exclude

        Returns:
            Dict[str, Any]: Dictionary representation of the pattern
        """
        exclude_fields = exclude_fields or []

        # Prepare base dictionary
        pattern_dict = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'skill_level': self.skill_level.name if self.skill_level else None,
            'project_type': self.project_type.name if self.project_type else None,
            'stitch_type': self.stitch_type.name if self.stitch_type else None,
            'edge_finish_type': self.edge_finish_type.name if self.edge_finish_type else None,
            'pattern_pieces': self.pattern_pieces,
            'leather_specifications': self.leather_specifications,
            'hardware_requirements': self.hardware_requirements,
            'estimated_labor_hours': self.estimated_labor_hours,
            'is_template': self.is_template,
            'version': self.version,
            'complexity_score': self.calculate_complexity(),
            'components': [component.to_dict() for component in self.components],
            'pattern_files': [pf.to_dict() for pf in self.pattern_files]
        }

        # Remove any excluded fields
        for field in exclude_fields:
            pattern_dict.pop(field, None)

        return pattern_dict

    @classmethod
    def create_template(
            cls,
            name: str,
            project_type: ProjectType,
            skill_level: SkillLevel,
            estimated_labor_hours: float = 0.0,
            description: Optional[str] = None,
            stitch_type: Optional[StitchType] = None,
            edge_finish_type: Optional[EdgeFinishType] = None
    ) -> 'Pattern':
        """
        Create a pattern template with comprehensive specifications.

        Args:
            name (str): Name of the pattern template
            project_type (ProjectType): Type of leatherworking project
            skill_level (SkillLevel): Required skill level
            estimated_labor_hours (float, optional): Estimated labor hours
            description (Optional[str], optional): Description of the template
            stitch_type (Optional[StitchType], optional): Stitching technique
            edge_finish_type (Optional[EdgeFinishType], optional): Edge finishing method

        Returns:
            Pattern: Created pattern template
        """
        return cls(
            name=name,
            project_type=project_type,
            skill_level=skill_level,
            estimated_labor_hours=estimated_labor_hours,
            description=description,
            is_template=True,
            stitch_type=stitch_type,
            edge_finish_type=edge_finish_type,
            pattern_pieces={},
            leather_specifications={},
            hardware_requirements={}
        )


class PatternFile(Base):
    """
    Represents files associated with a specific pattern.

    Allows tracking of design files, sketches, and other
    pattern-related documents.

    Attributes:
        id (int): Unique identifier for the pattern file
        pattern_id (int): Foreign key to the associated pattern
        pattern (Pattern): Relationship to the parent pattern
        filename (str): Name of the file
        file_path (str): Path to the file
        file_type (str): Type of file (e.g., 'sketch', 'design', 'technical_drawing')
        description (str, optional): Description of the file
    """
    __tablename__ = 'pattern_files'

    # Timestamp columns
    created_at = Column(DateTime, default=sa.func.now(), nullable=False)
    updated_at = Column(DateTime, default=sa.func.now(), onupdate=sa.func.now(), nullable=False)

    id = Column(Integer, primary_key=True)
    pattern_id = Column(Integer, sa.ForeignKey('patterns.id'), nullable=False)
    pattern = relationship("Pattern", back_populates="pattern_files")

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)
    description = Column(String)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the pattern file to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary of pattern file attributes
        """
        return {
            'id': self.id,
            'pattern_id': self.pattern_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'description': self.description
        }