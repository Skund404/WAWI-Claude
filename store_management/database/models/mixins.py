# database/models/mixins.py
"""
Mixin classes for SQLAlchemy models providing additional functionality.
"""

import abc
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import TEXT  # For SQLite compatibility

class TimestampMixin:
    """
    Mixin to automatically track creation and update timestamps.
    """
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class ValidationMixin(abc.ABC):
    """
    Mixin providing validation methods for model instances.
    """
    @classmethod
    def validate(cls, data: dict) -> bool:
        """
        Validate input data for the model.

        Args:
            data (dict): Data to validate

        Returns:
            bool: Whether the data is valid
        """
        # Implement basic validation logic
        # This is a placeholder and should be overridden in specific models
        return all(value is not None for value in data.values())

class CostingMixin:
    """
    Mixin to provide costing-related calculations.
    """
    unit_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    def calculate_total_cost(self) -> float:
        """
        Calculate the total cost of the item.

        Returns:
            float: Total cost
        """
        # Placeholder implementation
        # Should be overridden in specific models
        return self.total_cost

    def update_total_cost(self, new_cost: float) -> None:
        """
        Update the total cost of the item.

        Args:
            new_cost (float): New total cost value
        """
        self.total_cost = new_cost

class TrackingMixin:
    """
    Mixin to provide tracking capabilities for model instances.
    """
    @declared_attr
    def tracking_id(cls):
        """
        Generate a tracking ID column.

        Returns:
            Column: A unique tracking identifier column
        """
        return Column(String(255), unique=True, nullable=True)  # Specify the type and max length

    def generate_tracking_id(self) -> Optional[str]:
        """
        Generate a unique tracking identifier.

        Returns:
            Optional[str]: A unique tracking identifier
        """
        # Placeholder implementation
        # Should be implemented with proper logic in specific models
        return None

def comparison_func(x: Any, y: Any) -> bool:
    """
    Generic comparison function for sorting or comparing objects.

    Args:
        x (Any): First object to compare
        y (Any): Second object to compare

    Returns:
        bool: Result of the comparison
    """
    # Default implementation - can be customized as needed
    return x < y