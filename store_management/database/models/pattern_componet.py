# database/models/pattern_component.py

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Enum,
    ForeignKey, JSON, CheckConstraint
)
from sqlalchemy.orm import relationship
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from math import pi, cos, sin, radians
from decimal import Decimal
from .base import BaseModel
from .mixins import TimestampMixin, ValidationMixin
from .enums import (
    ComponentType, LeatherType, MaterialQualityGrade,
    StitchType, EdgeFinishType
)


@dataclass
class EdgeFinishRequirements:
    """Calculate requirements for different edge finishing techniques."""
    length_mm: float
    edge_type: EdgeFinishType
    layers: int = 1

    def calculate_requirements(self) -> Dict[str, float]:
        """Calculate materials needed for edge finishing."""
        # Base requirements per meter
        base_reqs = {
            EdgeFinishType.BURNISHED: {
                'gum_tragacanth_ml': 0.8,
                'time_minutes': 3.0
            },
            EdgeFinishType.PAINTED: {
                'edge_paint_ml': 1.0,
                'time_minutes': 2.0
            },
            EdgeFinishType.CREASED: {
                'time_minutes': 2.5
            },
            EdgeFinishType.WAX_FINISHED: {
                'wax_grams': 0.5,
                'time_minutes': 4.0
            }
        }

        # Get base requirements for this edge type
        reqs = base_reqs.get(self.edge_type, {}).copy()

        # Adjust for length and layers
        length_meters = self.length_mm / 1000
        for key, value in reqs.items():
            reqs[key] = value * length_meters * (1 + (self.layers - 1) * 0.5)

        return reqs


class PatternComponent(BaseModel, TimestampMixin, ValidationMixin):
    """Represents a component in a leather pattern."""
    __tablename__ = 'pattern_components'

    id = Column(Integer, primary_key=True)
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=False)
    name = Column(String(100), nullable=False)
    component_type = Column(Enum(ComponentType), nullable=False)

    # Dimensions
    length_mm = Column(Float, CheckConstraint('length_mm > 0'))
    width_mm = Column(Float, CheckConstraint('width_mm > 0'))
    thickness_mm = Column(Float)  # Optional for non-leather components

    # Leather-specific attributes
    leather_type = Column(Enum(LeatherType))
    leather_grade = Column(Enum(MaterialQualityGrade))
    grain_direction_degrees = Column(Float)  # 0-360 degrees
    stretch_direction_critical = Column(Boolean, default=False)
    skiving_required = Column(Boolean, default=False)
    skiving_details = Column(JSON)  # Details about where/how to skive

    # Construction details
    edge_finish_type = Column(Enum(EdgeFinishType))
    stitch_type = Column(Enum(StitchType))
    stitch_spacing_mm = Column(Float)
    number_of_stitching_rows = Column(Integer, default=1)
    stitching_margin_mm = Column(Float)
    requires_reinforcement = Column(Boolean, default=False)
    reinforcement_details = Column(JSON)

    # Notes and instructions
    construction_notes = Column(String(500))
    grain_pattern_notes = Column(String(200))
    special_instructions = Column(String(500))

    # Relationships
    pattern = relationship("Pattern", back_populates="components")
    adjacent_components = Column(JSON)  # List of component IDs this connects to

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.skiving_details = self.skiving_details or {}
        self.reinforcement_details = self.reinforcement_details or {}
        self.adjacent_components = self.adjacent_components or []

    def calculate_area(self) -> Dict[str, float]:
        """Calculate area in different units with waste factor."""
        base_area_mm2 = self.length_mm * self.width_mm

        # Calculate waste factor based on component characteristics
        waste_factor = 1.15  # Base 15% waste
        if self.grain_direction_degrees is not None:
            waste_factor += 0.1  # Additional 10% for grain matching
        if self.stretch_direction_critical:
            waste_factor += 0.05  # Additional 5% for stretch consideration

        total_area_mm2 = base_area_mm2 * waste_factor

        return {
            'base_area_mm2': base_area_mm2,
            'total_area_mm2': total_area_mm2,
            'base_area_sqft': base_area_mm2 / 92903,  # Convert to square feet
            'total_area_sqft': total_area_mm2 / 92903,
            'waste_factor': waste_factor
        }

    def calculate_stitching_requirements(self) -> Dict[str, float]:
        """Calculate stitching requirements including thread length."""
        if not self.stitch_spacing_mm or not self.stitch_type:
            return {}

        # Calculate perimeter
        perimeter_mm = 2 * (self.length_mm + self.width_mm)

        # Calculate number of stitches
        stitches_per_row = perimeter_mm / self.stitch_spacing_mm
        total_stitches = stitches_per_row * self.number_of_stitching_rows

        # Calculate thread length (3.5x stitch length for saddle stitch)
        thread_multiplier = 3.5 if self.stitch_type == StitchType.SADDLE else 2.0
        thread_length_mm = perimeter_mm * thread_multiplier * self.number_of_stitching_rows

        return {
            'perimeter_mm': perimeter_mm,
            'total_stitches': total_stitches,
            'thread_length_mm': thread_length_mm,
            'recommended_thread_length_mm': thread_length_mm * 1.2  # 20% extra
        }

    def calculate_edge_finishing_requirements(self) -> Dict[str, float]:
        """Calculate edge finishing requirements."""
        if not self.edge_finish_type:
            return {}

        perimeter_mm = 2 * (self.length_mm + self.width_mm)

        edge_calc = EdgeFinishRequirements(
            length_mm=perimeter_mm,
            edge_type=self.edge_finish_type,
            layers=self.get_layer_count()
        )

        return edge_calc.calculate_requirements()

    def calculate_skiving_requirements(self) -> Dict[str, float]:
        """Calculate skiving areas and specifications."""
        if not self.skiving_required:
            return {}

        skiving_length_mm = 0
        total_skived_area_mm2 = 0

        for detail in self.skiving_details.get('areas', []):
            length = detail.get('length_mm', 0)
            width = detail.get('width_mm', 0)
            skiving_length_mm += length
            total_skived_area_mm2 += length * width

        return {
            'total_skiving_length_mm': skiving_length_mm,
            'total_skived_area_mm2': total_skived_area_mm2,
            'estimated_time_minutes': skiving_length_mm * 0.05  # 0.05 min per mm
        }

    def get_layer_count(self) -> int:
        """Get number of leather layers at edges."""
        base_layers = 1
        if self.reinforcement_details.get('edges', False):
            base_layers += 1
        return base_layers

    def validate_component(self) -> List[str]:
        """Validate component specifications."""
        issues = []

        # Basic dimension checks
        if not (self.length_mm and self.width_mm):
            issues.append("Missing dimensions")
        elif self.length_mm <= 0 or self.width_mm <= 0:
            issues.append("Invalid dimensions")

        # Leather-specific validation
        if self.component_type == ComponentType.LEATHER:
            if not self.leather_type:
                issues.append("Leather type not specified")
            if not self.leather_grade:
                issues.append("Leather grade not specified")

        # Stitching validation
        if self.stitch_type and not self.stitch_spacing_mm:
            issues.append("Stitch spacing not specified")

        # Skiving validation
        if self.skiving_required and not self.skiving_details:
            issues.append("Skiving details not provided")

        return issues

    def to_dict(self) -> Dict:
        """Convert component to dictionary with all specifications."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.component_type.name if self.component_type else None,
            'dimensions': {
                'length_mm': self.length_mm,
                'width_mm': self.width_mm,
                'thickness_mm': self.thickness_mm
            },
            'leather_specs': {
                'type': self.leather_type.name if self.leather_type else None,
                'grade': self.leather_grade.name if self.leather_grade else None,
                'grain_direction': self.grain_direction_degrees,
                'stretch_critical': self.stretch_direction_critical
            },
            'construction': {
                'edge_finish': self.edge_finish_type.name if self.edge_finish_type else None,
                'stitch_type': self.stitch_type.name if self.stitch_type else None,
                'stitch_spacing': self.stitch_spacing_mm,
                'stitching_rows': self.number_of_stitching_rows,
                'skiving': self.skiving_details if self.skiving_required else None,
                'reinforcement': self.reinforcement_details if self.requires_reinforcement else None
            },
            'notes': {
                'construction': self.construction_notes,
                'grain_pattern': self.grain_pattern_notes,
                'special': self.special_instructions
            },
            'adjacent_components': self.adjacent_components
        }