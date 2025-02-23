# database/models/pattern.py

from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from typing import Dict, List, Optional
from datetime import datetime
from .base import BaseModel
from .mixins import TimestampMixin, ValidationMixin, CostingMixin
from .enums import (
    LeatherType, MaterialQualityGrade, ProjectType, SkillLevel,
    ComponentType
)


class Pattern(BaseModel, TimestampMixin, ValidationMixin, CostingMixin):
    """
    Represents a leather working pattern.

    Contains all information needed to create a leather item, including:
    - Pattern pieces and their dimensions
    - Required leather specifications
    - Hardware and tool requirements
    - Construction steps
    """
    __tablename__ = 'patterns'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    skill_level = Column(Enum(SkillLevel), nullable=False)
    project_type = Column(Enum(ProjectType), nullable=False)

    # Leather specifications
    leather_type = Column(Enum(LeatherType), nullable=False)
    leather_thickness_min = Column(Float)  # in mm
    leather_thickness_max = Column(Float)  # in mm
    leather_grade = Column(Enum(MaterialQualityGrade))
    leather_area_required = Column(Float)  # in square feet/meters

    # Pattern specifications
    pattern_pieces = Column(JSON)  # List of pieces with dimensions
    grain_direction_critical = Column(Boolean, default=False)
    hardware_requirements = Column(JSON)  # Dict of required hardware
    tool_requirements = Column(JSON)  # List of required tools

    # Construction details
    construction_steps = Column(JSON)  # Ordered list of construction steps
    edge_finishing = Column(JSON)  # Edge finishing specifications
    stitching_specifications = Column(JSON)  # Stitching details

    # Additional metadata
    estimated_time = Column(Float)  # in hours
    difficulty_notes = Column(String(500))
    version = Column(String(20))

    # Relationships
    components = relationship("PatternComponent", back_populates="pattern")
    projects = relationship("Project", back_populates="pattern")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pattern_pieces = self.pattern_pieces or []
        self.hardware_requirements = self.hardware_requirements or {}
        self.tool_requirements = self.tool_requirements or []
        self.construction_steps = self.construction_steps or []
        self.edge_finishing = self.edge_finishing or {}
        self.stitching_specifications = self.stitching_specifications or {}

    def calculate_total_leather_area(self) -> float:
        """Calculate total leather area needed including waste factor."""
        base_area = sum(
            piece.get('length', 0) * piece.get('width', 0)
            for piece in self.pattern_pieces
        )

        # Add waste factor based on complexity and grain requirements
        waste_factor = 1.15  # Base 15% waste
        if self.grain_direction_critical:
            waste_factor += 0.1  # Additional 10% for grain matching

        return base_area * waste_factor

    def calculate_thread_requirements(self) -> Dict[str, float]:
        """Calculate thread requirements based on stitching specifications."""
        total_stitch_length = 0
        for spec in self.stitching_specifications.get('stitch_lines', []):
            length = spec.get('length', 0)
            rows = spec.get('rows', 1)
            total_stitch_length += length * rows

        # Calculate thread length (typically 3.5x stitch length for saddle stitch)
        thread_length = total_stitch_length * 3.5

        return {
            'total_stitch_length': total_stitch_length,
            'thread_length_needed': thread_length,
            'recommended_length': thread_length * 1.2  # 20% extra for safety
        }

    def validate_pattern(self) -> List[str]:
        """Validate the pattern for completeness and correctness."""
        issues = []

        # Check required fields
        required_fields = ['name', 'leather_type', 'skill_level', 'project_type']
        for field in required_fields:
            if not getattr(self, field):
                issues.append(f"Missing required field: {field}")

        # Validate leather specifications
        if self.leather_thickness_min and self.leather_thickness_max:
            if self.leather_thickness_min > self.leather_thickness_max:
                issues.append("Invalid leather thickness range")

        # Validate pattern pieces
        if not self.pattern_pieces:
            issues.append("No pattern pieces defined")
        else:
            for i, piece in enumerate(self.pattern_pieces):
                if 'name' not in piece:
                    issues.append(f"Piece {i} missing name")
                if 'length' not in piece or 'width' not in piece:
                    issues.append(f"Piece {piece.get('name', i)} missing dimensions")

        # Validate construction steps
        if not self.construction_steps:
            issues.append("No construction steps defined")

        return issues

    def get_required_tools(self) -> List[str]:
        """Get list of required tools with optional alternatives."""
        base_tools = [
            "Cutting mat",
            "Rotary cutter or sharp knife",
            "Steel ruler",
            "Mallet"
        ]
        return base_tools + self.tool_requirements

    def estimate_completion_time(self, skill_level: SkillLevel) -> float:
        """Estimate completion time based on skill level."""
        base_time = self.estimated_time

        # Adjust time based on skill level
        skill_multipliers = {
            SkillLevel.BEGINNER: 2.0,
            SkillLevel.INTERMEDIATE: 1.5,
            SkillLevel.ADVANCED: 1.0,
            SkillLevel.EXPERT: 0.8
        }

        return base_time * skill_multipliers.get(skill_level, 1.0)

    def to_dict(self) -> Dict:
        """Convert pattern to dictionary with all relevant information."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'skill_level': self.skill_level.name if self.skill_level else None,
            'project_type': self.project_type.name if self.project_type else None,
            'leather_specifications': {
                'type': self.leather_type.name if self.leather_type else None,
                'thickness_range': {
                    'min': self.leather_thickness_min,
                    'max': self.leather_thickness_max
                },
                'grade': self.leather_grade.name if self.leather_grade else None,
                'area_required': self.leather_area_required
            },
            'pattern_pieces': self.pattern_pieces,
            'grain_direction_critical': self.grain_direction_critical,
            'hardware_requirements': self.hardware_requirements,
            'tool_requirements': self.get_required_tools(),
            'construction_steps': self.construction_steps,
            'edge_finishing': self.edge_finishing,
            'stitching_specifications': self.stitching_specifications,
            'estimated_time': self.estimated_time,
            'difficulty_notes': self.difficulty_notes,
            'version': self.version
        }