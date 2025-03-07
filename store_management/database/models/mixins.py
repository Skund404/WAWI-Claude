# database/models/mixins.py
"""
Advanced Mixin Classes for SQLAlchemy Models

Provides comprehensive mixin classes to extend model functionality
with reusable, composable behaviors for database entities.
"""

import uuid
from datetime import datetime
from typing import Any, Optional, Dict, List, Union, Type

from sqlalchemy import Column, DateTime, Float, String, Boolean, Enum as SAEnum
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import TEXT  # For SQLite compatibility

# Setup logger
import logging
logger = logging.getLogger(__name__)


class TimestampMixin:
    """
    Enhanced timestamp tracking for database models.
    Provides creation and modification timestamp tracking.
    """
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    @classmethod
    def get_recent_records(cls, session, days: int = 30):
        """
        Retrieve records created within the specified number of days.

        Args:
            session: Database session
            days: Number of days to look back (default 30)

        Returns:
            Query of recent records
        """
        from sqlalchemy import func
        return session.query(cls).filter(
            cls.created_at >= func.date('now', f'-{days} days')
        )


class ValidationMixin:
    """
    Advanced validation mixin with comprehensive validation strategies.
    """

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Comprehensive validation method with detailed error reporting.

        Args:
            data: Dictionary of attributes to validate

        Returns:
            Dictionary of validation errors
        """
        errors = {}

        # Implement base validation logic
        for key, value in data.items():
            # Check for None values
            if value is None:
                errors.setdefault('required_fields', []).append(
                    f"{key} cannot be None"
                )

        return errors

    @classmethod
    def validate_enum(
            cls,
            value: Any,
            enum_class: Type,
            field_name: str
    ) -> Optional[str]:
        """
        Validate that a value is a valid enum member.

        Args:
            value: Value to validate
            enum_class: Enum class to validate against
            field_name: Name of the field being validated

        Returns:
            Error message if validation fails, None otherwise
        """
        try:
            if not isinstance(value, enum_class):
                return f"{field_name} must be a valid {enum_class.__name__}"
            return None
        except Exception:
            return f"Invalid {field_name} value"


class CostingMixin:
    """
    Advanced costing tracking for financial entities.
    """
    # Base costing attributes
    unit_cost = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)

    @declared_attr
    def quality_grade(cls):
        """Adds quality_grade column using declared_attr."""
        # Import inside method to avoid circular imports
        from database.models.enums import QualityGrade
        return Column(
            SAEnum(QualityGrade),
            default=QualityGrade.STANDARD,
            nullable=False
        )

    # Cost calculation methods
    def calculate_total_cost(
            self,
            unit_cost: Optional[float] = None,
            quantity: Optional[float] = 1.0
    ) -> float:
        """
        Calculate total cost with optional overrides.

        Args:
            unit_cost: Optional unit cost override
            quantity: Quantity to calculate cost for

        Returns:
            Calculated total cost
        """
        cost_per_unit = unit_cost or self.unit_cost
        return cost_per_unit * (quantity or 1.0)

    def update_cost(
            self,
            unit_cost: float,
            total_cost: Optional[float] = None
    ) -> None:
        """
        Update costing information.

        Args:
            unit_cost: New unit cost
            total_cost: Optional total cost (will be calculated if not provided)
        """
        self.unit_cost = unit_cost
        self.total_cost = total_cost or self.calculate_total_cost()


class TrackingMixin:
    """
    Advanced tracking capabilities for database entities.
    """
    # Unique tracking identifier
    tracking_id = Column(
        String(255),
        unique=True,
        nullable=True,
        default=lambda: str(uuid.uuid4())
    )

    @declared_attr
    def material_type(cls):
        """Adds material_type column using declared_attr."""
        # Import inside method to avoid circular imports
        from database.models.enums import MaterialType
        return Column(
            SAEnum(MaterialType),
            nullable=True
        )

    @declared_attr
    def inventory_status(cls):
        """Adds inventory_status column using declared_attr."""
        # Import inside method to avoid circular imports
        from database.models.enums import InventoryStatus
        return Column(
            SAEnum(InventoryStatus),
            default=InventoryStatus.IN_STOCK,
            nullable=False
        )

    # Tracking methods
    def generate_tracking_id(self) -> str:
        """
        Generate a new unique tracking identifier.

        Returns:
            Unique tracking ID
        """
        return str(uuid.uuid4())

    def update_tracking_id(self) -> None:
        """
        Update the tracking identifier.
        """
        self.tracking_id = self.generate_tracking_id()

    def update_inventory_status(
            self,
            new_status,  # Type hint removed to avoid circular import
            threshold: Optional[float] = None
    ) -> None:
        """
        Update inventory status with optional threshold logic.

        Args:
            new_status: New inventory status
            threshold: Optional threshold for status determination
        """
        self.inventory_status = new_status


class ComplianceMixin:
    """
    Advanced compliance and audit tracking mixin.
    """
    # Compliance and audit tracking
    is_compliant = Column(Boolean, default=True, nullable=False)
    compliance_notes = Column(TEXT, nullable=True)
    last_compliance_check = Column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow
    )

    def mark_compliance(
            self,
            is_compliant: bool,
            notes: Optional[str] = None
    ) -> None:
        """
        Update compliance status.

        Args:
            is_compliant: Compliance status
            notes: Optional compliance notes
        """
        self.is_compliant = is_compliant
        self.compliance_notes = notes
        self.last_compliance_check = datetime.utcnow()


# Utility function for easy mixin application
def apply_mixins(*mixin_classes):
    """
    Utility to dynamically apply multiple mixins.

    Args:
        *mixin_classes: Mixin classes to apply

    Returns:
        Tuple of mixin classes
    """
    return mixin_classes