# database/models/pattern_component.py
"""
Comprehensive Pattern Component Model for Leatherworking Management System

This module defines the PatternComponent model with extensive validation,
relationship management, and circular import resolution.

Implements the Component entity from the ER diagram specifically for
pattern-based components, with all calculations and specifications
needed for leatherworking patterns.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type, Tuple

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    ComponentType,
    QualityGrade,
    MaterialType,
    LeatherType,
    SkillLevel
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    CircularImportResolver
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Define pattern-specific enums
import enum


class EdgeFinishType(enum.Enum):
    """Enumeration of edge finishing techniques."""
    BURNISHED = "burnished"
    PAINTED = "painted"
    CREASED = "creased"
    WAX_FINISHED = "wax_finished"
    RAW = "raw"


class StitchType(enum.Enum):
    """Enumeration of stitching techniques."""
    SADDLE = "saddle"
    MACHINE = "machine"
    HAND = "hand"
    NONE = "none"


# Register lazy imports
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')
register_lazy_import('Component', 'database.models.components', 'Component')
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')


class PatternComponent(Base, TimestampMixin, ValidationMixin):
    """
    PatternComponent model representing a component within a leather pattern.

    This model contains all the specifications and details needed to create
    accurate leatherworking patterns with comprehensive material calculations.
    """
    __tablename__ = 'pattern_components'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_id: Mapped[int] = mapped_column(Integer, ForeignKey('patterns.id'), nullable=False, index=True)
    component_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('components.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Component classifications
    component_type: Mapped[ComponentType] = mapped_column(
        Enum(ComponentType),
        nullable=False
    )

    # Physical dimensions with constraints
    length_mm: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('length_mm > 0'),
        nullable=False
    )
    width_mm: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('width_mm > 0'),
        nullable=False
    )
    thickness_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Leather specific attributes
    leather_type: Mapped[Optional[LeatherType]] = mapped_column(Enum(LeatherType), nullable=True)
    leather_grade: Mapped[Optional[QualityGrade]] = mapped_column(Enum(QualityGrade), nullable=True)
    grain_direction_degrees: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stretch_direction_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Edge and construction details
    skiving_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skiving_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    edge_finish_type: Mapped[Optional[EdgeFinishType]] = mapped_column(Enum(EdgeFinishType), nullable=True)

    # Stitching specifications
    stitch_type: Mapped[Optional[StitchType]] = mapped_column(Enum(StitchType), nullable=True)
    stitch_spacing_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    number_of_stitching_rows: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    stitching_margin_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Additional construction details
    requires_reinforcement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reinforcement_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Instructions and notes
    construction_notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    grain_pattern_notes: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    special_instructions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Component relationships and adjacency
    adjacent_components: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # Relationships
    pattern = relationship("Pattern", back_populates="components")
    component = relationship("Component", back_populates="pattern_components")

    def __init__(self, **kwargs):
        """
        Initialize a PatternComponent instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for pattern component attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Initialize JSON fields with empty values if not provided
            for json_field in ['skiving_details', 'reinforcement_details', 'adjacent_components']:
                if json_field not in kwargs or kwargs[json_field] is None:
                    kwargs[json_field] = {}

            # Validate input data
            self._validate_pattern_component_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PatternComponent initialization failed: {e}")
            raise ModelValidationError(f"Failed to create PatternComponent: {str(e)}") from e

    @classmethod
    def _validate_pattern_component_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of pattern component creation data.

        Args:
            data: Pattern component creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'pattern_id', 'Pattern ID is required')
        validate_not_empty(data, 'name', 'Component name is required')
        validate_not_empty(data, 'component_type', 'Component type is required')

        # Validate dimensions
        for dim in ['length_mm', 'width_mm']:
            if dim in data:
                validate_positive_number(
                    data,
                    dim,
                    allow_zero=False,
                    message=f"{dim.replace('_', ' ').title()} must be a positive number"
                )

        if 'thickness_mm' in data and data['thickness_mm'] is not None:
            validate_positive_number(
                data,
                'thickness_mm',
                allow_zero=False,
                message="Thickness must be a positive number"
            )

        # Validate component type
        if 'component_type' in data:
            ModelValidator.validate_enum(
                data['component_type'],
                ComponentType,
                'component_type'
            )

        # Validate leather-specific fields when component type is LEATHER
        if data.get('component_type') == ComponentType.LEATHER:
            if 'leather_type' in data and data['leather_type'] is not None:
                ModelValidator.validate_enum(
                    data['leather_type'],
                    LeatherType,
                    'leather_type'
                )

            if 'leather_grade' in data and data['leather_grade'] is not None:
                ModelValidator.validate_enum(
                    data['leather_grade'],
                    QualityGrade,
                    'leather_grade'
                )

        # Validate stitching details
        if 'stitch_type' in data and data['stitch_type'] is not None:
            ModelValidator.validate_enum(
                data['stitch_type'],
                StitchType,
                'stitch_type'
            )

            # If stitch type is specified, stitch spacing should be provided
            if data['stitch_type'] != StitchType.NONE and (
                    'stitch_spacing_mm' not in data or data['stitch_spacing_mm'] is None):
                raise ValidationError("Stitch spacing is required when stitch type is specified", "stitch_spacing_mm")

            if 'stitch_spacing_mm' in data and data['stitch_spacing_mm'] is not None:
                validate_positive_number(
                    data,
                    'stitch_spacing_mm',
                    allow_zero=False,
                    message="Stitch spacing must be a positive number"
                )

        # Validate edge finishing
        if 'edge_finish_type' in data and data['edge_finish_type'] is not None:
            ModelValidator.validate_enum(
                data['edge_finish_type'],
                EdgeFinishType,
                'edge_finish_type'
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Ensure JSON fields are properly initialized
        if not hasattr(self, 'skiving_details') or self.skiving_details is None:
            self.skiving_details = {}

        if not hasattr(self, 'reinforcement_details') or self.reinforcement_details is None:
            self.reinforcement_details = {}

        if not hasattr(self, 'adjacent_components') or self.adjacent_components is None:
            self.adjacent_components = []

    def calculate_area(self) -> Dict[str, float]:
        """
        Calculate area in different units with waste factor.

        Returns:
            Dictionary with area calculations in different units
        """
        # Calculate base area
        base_area_mm2 = self.length_mm * self.width_mm

        # Calculate waste factor based on component properties
        waste_factor = 1.15  # Base waste factor of 15%

        if hasattr(self, 'grain_direction_degrees') and self.grain_direction_degrees is not None:
            waste_factor += 0.1  # Add 10% waste for grain direction requirements

        if hasattr(self, 'stretch_direction_critical') and self.stretch_direction_critical:
            waste_factor += 0.05  # Add 5% waste for stretch direction requirements

        # Calculate total area including waste
        total_area_mm2 = base_area_mm2 * waste_factor

        # Convert to different units
        # 1 sq ft = 92,903 sq mm
        return {
            'base_area_mm2': base_area_mm2,
            'total_area_mm2': total_area_mm2,
            'base_area_sqft': base_area_mm2 / 92903,
            'total_area_sqft': total_area_mm2 / 92903,
            'waste_factor': waste_factor
        }

    def calculate_stitching_requirements(self) -> Dict[str, float]:
        """
        Calculate stitching requirements including thread length.

        Returns:
            Dictionary with stitching calculations
        """
        # Check if stitching is specified
        if not hasattr(self, 'stitch_spacing_mm') or not self.stitch_spacing_mm or not self.stitch_type:
            return {}

        # Calculate perimeter
        perimeter_mm = 2 * (self.length_mm + self.width_mm)

        # Calculate number of stitches
        stitches_per_row = perimeter_mm / self.stitch_spacing_mm
        total_stitches = stitches_per_row * self.number_of_stitching_rows

        # Calculate thread length based on stitch type
        thread_multiplier = 3.5 if self.stitch_type == StitchType.SADDLE else 2.0
        thread_length_mm = perimeter_mm * thread_multiplier * self.number_of_stitching_rows

        return {
            'perimeter_mm': perimeter_mm,
            'total_stitches': total_stitches,
            'thread_length_mm': thread_length_mm,
            'recommended_thread_length_mm': thread_length_mm * 1.2  # Add 20% extra for safety
        }

    def calculate_edge_finishing_requirements(self) -> Dict[str, float]:
        """
        Calculate edge finishing requirements.

        Returns:
            Dictionary with edge finishing calculations
        """
        # Check if edge finishing is specified
        if not hasattr(self, 'edge_finish_type') or not self.edge_finish_type:
            return {}

        # Calculate perimeter
        perimeter_mm = 2 * (self.length_mm + self.width_mm)

        # Calculate layer count
        layers = self.get_layer_count()

        # Base requirements for different edge finish types (per meter)
        base_requirements = {
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
            },
            EdgeFinishType.RAW: {
                'time_minutes': 0.5
            }
        }

        # Get requirements for this edge finish type
        requirements = base_requirements.get(self.edge_finish_type, {}).copy()

        # Scale based on perimeter and layer count
        perimeter_meters = perimeter_mm / 1000

        for key, value in requirements.items():
            # Adjust for layers - each additional layer adds 50% more material/time
            layer_factor = 1 + ((layers - 1) * 0.5)
            requirements[key] = value * perimeter_meters * layer_factor

        return requirements

    def calculate_skiving_requirements(self) -> Dict[str, float]:
        """
        Calculate skiving areas and specifications.

        Returns:
            Dictionary with skiving calculations
        """
        # Check if skiving is required
        if not hasattr(self, 'skiving_required') or not self.skiving_required:
            return {}

        # Initialize values
        skiving_length_mm = 0
        total_skived_area_mm2 = 0

        # Process each skiving area
        if hasattr(self, 'skiving_details') and isinstance(self.skiving_details, dict):
            for area in self.skiving_details.get('areas', []):
                length = area.get('length_mm', 0)
                width = area.get('width_mm', 0)
                skiving_length_mm += length
                total_skived_area_mm2 += length * width

        # Calculate estimated time (5 seconds per 100mm of skiving)
        estimated_time_minutes = skiving_length_mm * 0.05 / 60

        return {
            'total_skiving_length_mm': skiving_length_mm,
            'total_skived_area_mm2': total_skived_area_mm2,
            'estimated_time_minutes': estimated_time_minutes
        }

    def get_layer_count(self) -> int:
        """
        Get number of leather layers at edges.

        Returns:
            Layer count for edges
        """
        # Start with base layer
        base_layers = 1

        # Add reinforcement layers if specified
        if hasattr(self, 'reinforcement_details') and isinstance(self.reinforcement_details, dict):
            if self.reinforcement_details.get('edges', False):
                base_layers += 1

            # Count additional specified layers
            additional_layers = self.reinforcement_details.get('layer_count', 0)
            base_layers += additional_layers

        return base_layers

    def validate_component(self) -> List[str]:
        """
        Validate component specifications and identify issues.

        Returns:
            List of validation issues (empty if component is valid)
        """
        issues = []

        # Check dimensions
        if not hasattr(self, 'length_mm') or not self.length_mm or not hasattr(self, 'width_mm') or not self.width_mm:
            issues.append('Missing dimensions')
        elif self.length_mm <= 0 or self.width_mm <= 0:
            issues.append('Invalid dimensions')

        # Check leather-specific attributes for leather components
        if hasattr(self, 'component_type') and self.component_type == ComponentType.LEATHER:
            if not hasattr(self, 'leather_type') or not self.leather_type:
                issues.append('Leather type not specified')
            if not hasattr(self, 'leather_grade') or not self.leather_grade:
                issues.append('Leather grade not specified')

        # Check stitching specifications
        if hasattr(self, 'stitch_type') and self.stitch_type and self.stitch_type != StitchType.NONE:
            if not hasattr(self, 'stitch_spacing_mm') or not self.stitch_spacing_mm:
                issues.append('Stitch spacing not specified')

        # Check skiving details
        if hasattr(self, 'skiving_required') and self.skiving_required:
            if not hasattr(self, 'skiving_details') or not self.skiving_details:
                issues.append('Skiving details not provided')

        # Check reinforcement details
        if hasattr(self, 'requires_reinforcement') and self.requires_reinforcement:
            if not hasattr(self, 'reinforcement_details') or not self.reinforcement_details:
                issues.append('Reinforcement details not provided')

        return issues

    def calculate_material_requirements(self) -> Dict[str, Any]:
        """
        Calculate comprehensive material requirements for this component.

        Returns:
            Dictionary with all material requirements
        """
        requirements = {}

        # Add area calculations
        requirements['area'] = self.calculate_area()

        # Add stitching requirements if applicable
        stitching_reqs = self.calculate_stitching_requirements()
        if stitching_reqs:
            requirements['stitching'] = stitching_reqs

        # Add edge finishing requirements if applicable
        edge_reqs = self.calculate_edge_finishing_requirements()
        if edge_reqs:
            requirements['edge_finishing'] = edge_reqs

        # Add skiving requirements if applicable
        skiving_reqs = self.calculate_skiving_requirements()
        if skiving_reqs:
            requirements['skiving'] = skiving_reqs

        # Calculate estimated time
        total_time = 0

        # Base time for cutting (1 minute per sqft)
        total_time += requirements['area'].get('total_area_sqft', 0) * 1.0

        # Add time for edge finishing
        if 'edge_finishing' in requirements:
            total_time += requirements['edge_finishing'].get('time_minutes', 0)

        # Add time for stitching (1 stitch per 2 seconds)
        if 'stitching' in requirements:
            stitch_count = requirements['stitching'].get('total_stitches', 0)
            total_time += (stitch_count / 30)  # 30 stitches per minute

        # Add time for skiving
        if 'skiving' in requirements:
            total_time += requirements['skiving'].get('estimated_time_minutes', 0)

        requirements['estimated_time_minutes'] = total_time

        return requirements

    def to_dict(self, include_calculations: bool = False) -> Dict[str, Any]:
        """
        Convert component to dictionary with all specifications.

        Args:
            include_calculations: Whether to include calculated values

        Returns:
            Dictionary representation of the component
        """
        # Build basic component data
        component_dict = {
            'id': self.id,
            'name': self.name,
            'type': self.component_type.name if hasattr(self, 'component_type') and self.component_type else None,
            'dimensions': {
                'length_mm': self.length_mm,
                'width_mm': self.width_mm,
                'thickness_mm': self.thickness_mm
            },
            'leather_specs': {
                'type': self.leather_type.name if hasattr(self, 'leather_type') and self.leather_type else None,
                'grade': self.leather_grade.name if hasattr(self, 'leather_grade') and self.leather_grade else None,
                'grain_direction': self.grain_direction_degrees,
                'stretch_critical': self.stretch_direction_critical
            },
            'construction': {
                'edge_finish': self.edge_finish_type.name if hasattr(self,
                                                                     'edge_finish_type') and self.edge_finish_type else None,
                'stitch_type': self.stitch_type.name if hasattr(self, 'stitch_type') and self.stitch_type else None,
                'stitch_spacing': self.stitch_spacing_mm,
                'stitching_rows': self.number_of_stitching_rows,
                'skiving': self.skiving_details if hasattr(self,
                                                           'skiving_required') and self.skiving_required else None,
                'reinforcement': self.reinforcement_details if hasattr(self,
                                                                       'requires_reinforcement') and self.requires_reinforcement else None
            },
            'notes': {
                'construction': self.construction_notes,
                'grain_pattern': self.grain_pattern_notes,
                'special': self.special_instructions
            },
            'adjacent_components': self.adjacent_components
        }

        # Add calculated values if requested
        if include_calculations:
            component_dict['calculations'] = self.calculate_material_requirements()
            component_dict['validation_issues'] = self.validate_component()

        return component_dict

    def __repr__(self) -> str:
        """
        String representation of the PatternComponent.

        Returns:
            Detailed pattern component representation
        """
        return (
            f"<PatternComponent(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.component_type.name if hasattr(self, 'component_type') and self.component_type else 'None'}, "
            f"pattern_id={self.pattern_id})>"
        )


# Register for lazy import resolution
register_lazy_import('PatternComponent', 'database.models.pattern_component', 'PatternComponent')
register_lazy_import('EdgeFinishType', 'database.models.pattern_component', 'EdgeFinishType')
register_lazy_import('StitchType', 'database.models.pattern_component', 'StitchType')