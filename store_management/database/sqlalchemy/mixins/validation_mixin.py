# validation_mixin.py
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from datetime import datetime

from di.core import inject
from services.interfaces import MaterialService


class ValidationMixin(ABC):
    """Base mixin for validation functionality.

    This mixin provides common validation methods that can be used by any model
    class. It includes methods for validating required fields, numeric ranges,
    string formats, and custom business rules.
    """

    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that all required fields are present and not None.

        Args:
            data: Dictionary of field values to validate
            required_fields: List of field names that must be present and not None

        Returns:
            bool: True if all required fields are present and not None
        """
        return all(field in data and data[field] is not None for field in required_fields)

    def validate_numeric_range(
            self,
            value: Union[int, float],
            min_val: Optional[Union[int, float]] = None,
            max_val: Optional[Union[int, float]] = None
    ) -> bool:
        """Validate that a numeric value is within the specified range.

        Args:
            value: The numeric value to validate
            min_val: Optional minimum value (inclusive)
            max_val: Optional maximum value (inclusive)

        Returns:
            bool: True if value is within range
        """
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True

    def validate_string_format(
            self,
            value: str,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            pattern: Optional[str] = None
    ) -> bool:
        """Validate string format including length and pattern matching.

        Args:
            value: String value to validate
            min_length: Optional minimum length
            max_length: Optional maximum length
            pattern: Optional regex pattern to match

        Returns:
            bool: True if string matches all specified criteria
        """
        if min_length is not None and len(value) < min_length:
            return False
        if max_length is not None and len(value) > max_length:
            return False
        if pattern is not None and not re.match(pattern, value):
            return False
        return True

    def validate_date_range(
            self,
            date: datetime,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> bool:
        """Validate that a date falls within the specified range.

        Args:
            date: The date to validate
            start_date: Optional start of valid range (inclusive)
            end_date: Optional end of valid range (inclusive)

        Returns:
            bool: True if date is within range
        """
        if start_date is not None and date < start_date:
            return False
        if end_date is not None and date > end_date:
            return False
        return True

    def validate_related_fields(
            self,
            data: Dict[str, Any],
            field_pairs: List[Tuple[str, str]],
            comparison_func: Optional[Callable] = None
    ) -> bool:
        """Validate relationships between pairs of fields.

        Args:
            data: Dictionary containing field values
            field_pairs: List of field name tuples to compare
            comparison_func: Optional function to use for comparison
                Default is to check if first value <= second value

        Returns:
            bool: True if all field pairs pass validation
        """
        if comparison_func is None:
            def comparison_func(x, y):
                return x <= y

        for field1, field2 in field_pairs:
            if field1 not in data or field2 not in data:
                return False
            if not comparison_func(data[field1], data[field2]):
                return False

        return True

    @abstractmethod
    def validate(self) -> bool:
        """Validate the entire object.

        This method must be implemented by classes using this mixin to provide
        model-specific validation logic.

        Returns:
            bool: True if all validation checks pass
        """
        pass

    def _validate_type(self, value: Any, expected_type: Type) -> bool:
        """Internal helper to validate type of a value.

        Args:
            value: Value to check
            expected_type: Expected type of the value

        Returns:
            bool: True if value matches expected type
        """
        return isinstance(value, expected_type)

    def _validate_enum(self, value: Any, valid_values: List[Any]) -> bool:
        """Internal helper to validate enum-like values.

        Args:
            value: Value to check
            valid_values: List of valid values

        Returns:
            bool: True if value is in valid_values
        """
        return value in valid_values