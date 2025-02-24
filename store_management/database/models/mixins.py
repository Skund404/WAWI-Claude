# database/models/mixins.py
"""
Mixin classes providing common functionality for database models.

These mixins add reusable methods and attributes to SQLAlchemy models
for timestamp tracking, note management, costing calculations,
and data validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import sqlalchemy as sa
from sqlalchemy import Column, DateTime, String, Float, func


class TimestampMixin:
    """
    Mixin to add automatic timestamp tracking to models.

    Adds created_at and updated_at timestamps that are
    automatically managed by the database.
    """
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def update_timestamp(self):
        """
        Manually update the updated_at timestamp.

        Useful for cases where automatic update might not trigger.
        """
        self.updated_at = datetime.utcnow()


class NoteMixin:
    """
    Mixin to add note-taking capability to models.

    Provides methods to add, retrieve, and manage notes
    associated with a model instance.
    """
    notes = Column(String, nullable=True)

    def add_note(self, note: str) -> None:
        """
        Add a new note to the existing notes.

        Args:
            note (str): The note to add
        """
        if not note:
            return

        if self.notes:
            # Append new note with a timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            self.notes += f"\n[{timestamp}] {note}"
        else:
            # First note
            self.notes = note


class CostingMixin:
    """
    Mixin to add costing-related calculations to models.

    Provides methods for calculating labor, overhead,
    and total project costs.
    """

    def calculate_labor_cost(self, hours: float, rate: float) -> float:
        """
        Calculate labor cost based on hours worked and hourly rate.

        Args:
            hours (float): Number of labor hours
            rate (float): Hourly labor rate

        Returns:
            float: Total labor cost
        """
        return max(0, hours * rate)

    def calculate_overhead_cost(self, base_cost: float, overhead_rate: float) -> float:
        """
        Calculate overhead cost as a percentage of base cost.

        Args:
            base_cost (float): Base cost to calculate overhead on
            overhead_rate (float): Overhead rate as a decimal (e.g., 0.1 for 10%)

        Returns:
            float: Calculated overhead cost
        """
        return max(0, base_cost * overhead_rate)

    def calculate_total_cost(
            self,
            material_cost: float,
            labor_cost: float,
            overhead_rate: float = 0.1
    ) -> float:
        """
        Calculate total project cost including materials, labor, and overhead.

        Args:
            material_cost (float): Cost of materials
            labor_cost (float): Cost of labor
            overhead_rate (float, optional): Overhead rate. Defaults to 0.1 (10%)

        Returns:
            float: Total project cost
        """
        overhead_cost = self.calculate_overhead_cost(material_cost + labor_cost, overhead_rate)
        return material_cost + labor_cost + overhead_cost


class ValidationMixin:
    """
    Mixin to add validation functionality to models.

    Provides methods for validating model data against
    various constraints.
    """

    def validate_required_fields(self, required_fields: List[str]) -> bool:
        """
        Validate that all required fields have non-None, non-empty values.

        Args:
            required_fields (List[str]): List of field names to validate

        Returns:
            bool: True if all required fields are filled, False otherwise
        """
        for field in required_fields:
            value = getattr(self, field, None)

            # Check for None
            if value is None:
                return False

            # Additional checks for different types
            if isinstance(value, str) and not value.strip():
                return False

            # For numeric fields, check for zero or negative values if needed
            if isinstance(value, (int, float)) and value <= 0:
                return False

        return True

    def validate_numeric_range(
            self,
            value: float,
            min_val: Optional[float] = None,
            max_val: Optional[float] = None
    ) -> bool:
        """
        Validate that a numeric value is within specified range.

        Args:
            value (float): Value to validate
            min_val (Optional[float], optional): Minimum allowed value
            max_val (Optional[float], optional): Maximum allowed value

        Returns:
            bool: True if value is within range, False otherwise
        """
        # Validate against minimum if specified
        if min_val is not None and value < min_val:
            return False

        # Validate against maximum if specified
        if max_val is not None and value > max_val:
            return False

        return True

    def validate_email(self, email: str) -> bool:
        """
        Basic email validation.

        Args:
            email (str): Email address to validate

        Returns:
            bool: True if email appears valid, False otherwise
        """
        import re

        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))