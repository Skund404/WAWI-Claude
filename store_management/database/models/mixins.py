# Path: database/models/mixins.py
"""
Mixin classes to provide additional functionality to database models.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime
from typing import Any, Dict, Optional
import re

class TimestampMixin:
    """
    Mixin to add timestamp tracking to models.
    """
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def update_timestamp(self) -> None:
        """
        Manually update the updated_at timestamp.
        """
        self.updated_at = datetime.utcnow()

class ValidationMixin:
    """
    Mixin to provide common validation methods for models.
    """
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list[str]) -> bool:
        """
        Validate that all required fields are present and not empty.

        Args:
            data (Dict[str, Any]): Dictionary of data to validate.
            required_fields (list[str]): List of fields that must be present.

        Returns:
            bool: True if all required fields are present and non-empty, False otherwise.
        """
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        return True

    def validate_numeric_range(self,
                                value: float,
                                min_val: Optional[float] = None,
                                max_val: Optional[float] = None) -> bool:
        """
        Validate a numeric value is within a specified range.

        Args:
            value (float): Value to validate.
            min_val (Optional[float], optional): Minimum allowed value. Defaults to None.
            max_val (Optional[float], optional): Maximum allowed value. Defaults to None.

        Returns:
            bool: True if value is within range, False otherwise.
        """
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True

    def validate_string_format(self,
                                value: str,
                                min_length: Optional[int] = None,
                                max_length: Optional[int] = None,
                                pattern: Optional[str] = None) -> bool:
        """
        Validate string based on length and optional regex pattern.

        Args:
            value (str): String to validate.
            min_length (Optional[int], optional): Minimum string length. Defaults to None.
            max_length (Optional[int], optional): Maximum string length. Defaults to None.
            pattern (Optional[str], optional): Regex pattern to match. Defaults to None.

        Returns:
            bool: True if string meets all validation criteria, False otherwise.
        """
        if min_length is not None and len(value) < min_length:
            return False
        if max_length is not None and len(value) > max_length:
            return False
        if pattern is not None and not re.match(pattern, value):
            return False
        return True

class CostingMixin:
    """
    Mixin to provide common costing methods for models.
    """
    def calculate_labor_cost(self, hours: float, rate: float = 50.0) -> float:
        """
        Calculate labor cost based on hours and hourly rate.

        Args:
            hours (float): Number of labor hours.
            rate (float, optional): Hourly rate. Defaults to 50.0.

        Returns:
            float: Total labor cost.
        """
        return hours * rate

    def calculate_overhead_cost(self, base_cost: float, overhead_rate: float = 0.1) -> float:
        """
        Calculate overhead cost as a percentage of base cost.

        Args:
            base_cost (float): Base cost to calculate overhead on.
            overhead_rate (float, optional): Overhead rate. Defaults to 0.1 (10%).

        Returns:
            float: Overhead cost.
        """
        return base_cost * overhead_rate

    def calculate_total_cost(self,
                              materials_cost: float,
                              labor_hours: float,
                              labor_rate: float = 50.0,
                              overhead_rate: float = 0.1) -> float:
        """
        Calculate total cost including materials, labor, and overhead.

        Args:
            materials_cost (float): Cost of materials.
            labor_hours (float): Number of labor hours.
            labor_rate (float, optional): Hourly labor rate. Defaults to 50.0.
            overhead_rate (float, optional): Overhead rate. Defaults to 0.1 (10%).

        Returns:
            float: Total cost.
        """
        labor_cost = self.calculate_labor_cost(labor_hours, labor_rate)
        overhead_cost = self.calculate_overhead_cost(materials_cost + labor_cost, overhead_rate)
        return materials_cost + labor_cost + overhead_cost