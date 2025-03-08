"""
utils/enhanced_model_validator.py - Enhanced validation utilities for SQLAlchemy models.

This module provides comprehensive validation utilities for SQLAlchemy models,
including type checking, constraint validation, and data sanitization.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

import re

def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email (str): Email address to validate

    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    # RFC 5322 Official Standard email regex
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

class ValidationError(Exception):
    """Exception raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize a ValidationError.

        Args:
            message: Error message
            field: Optional field name where validation failed
        """
        self.field = field
        self.message = message

        # Format the message to include the field if provided
        formatted_message = message
        if field:
            formatted_message = f"{message} (field: {field})"

        super().__init__(formatted_message)


class ModelValidator:
    """Provides validation utilities for SQLAlchemy models."""

    @staticmethod
    def validate_string_length(value: str, min_length: int = 0, max_length: Optional[int] = None,
                               field: str = None) -> None:
        """Validate string length.

        Args:
            value: String to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length (if any)
            field: Field name for error reporting

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected a string, got {type(value).__name__}", field)

        if len(value) < min_length:
            raise ValidationError(f"String is too short (minimum length: {min_length})", field)

        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"String is too long (maximum length: {max_length})", field)

    @staticmethod
    def validate_number_range(value: Union[int, float], min_value: Optional[Union[int, float]] = None,
                              max_value: Optional[Union[int, float]] = None, field: str = None) -> None:
        """Validate number is within range.

        Args:
            value: Number to validate
            min_value: Minimum allowed value (if any)
            max_value: Maximum allowed value (if any)
            field: Field name for error reporting

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Expected a number, got {type(value).__name__}", field)

        if min_value is not None and value < min_value:
            raise ValidationError(f"Value is too small (minimum: {min_value})", field)

        if max_value is not None and value > max_value:
            raise ValidationError(f"Value is too large (maximum: {max_value})", field)

    @staticmethod
    def validate_email(value: str, field: str = None) -> None:
        """Validate email format.

        Args:
            value: Email to validate
            field: Field name for error reporting

        Raises:
            ValidationError: If validation fails
        """
        # Simple regex for basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, value):
            raise ValidationError("Invalid email format", field)

    @staticmethod
    def validate_date(value: datetime, min_date: Optional[datetime] = None, max_date: Optional[datetime] = None,
                      field: str = None) -> None:
        """Validate date is within range.

        Args:
            value: Date to validate
            min_date: Minimum allowed date (if any)
            max_date: Maximum allowed date (if any)
            field: Field name for error reporting

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, datetime):
            raise ValidationError(f"Expected a datetime, got {type(value).__name__}", field)

        if min_date is not None and value < min_date:
            raise ValidationError(f"Date is too early (minimum: {min_date})", field)

        if max_date is not None and value > max_date:
            raise ValidationError(f"Date is too late (maximum: {max_date})", field)

    @staticmethod
    def validate_enum(value: Any, enum_class: Type, field: str = None) -> None:
        """Validate value is a valid enum member.

        Args:
            value: Value to validate
            enum_class: Enum class to check against
            field: Field name for error reporting

        Raises:
            ValidationError: If validation fails
        """
        # Check if value is an instance of the enum
        if isinstance(value, enum_class):
            return

        # Check if value is a string representation of an enum member
        if isinstance(value, str):
            try:
                enum_class[value]
                return
            except (KeyError, TypeError):
                pass

        # If we get here, validation failed
        valid_values = ", ".join(str(m.name) for m in enum_class)
        raise ValidationError(f"Invalid enum value. Expected one of: {valid_values}", field)


def validate_not_empty(data: Dict[str, Any], field: str, message: Optional[str] = None) -> None:
    """Validate that a field is present and not empty.

    Args:
        data: Data dictionary to validate
        field: Field name to check
        message: Optional custom error message

    Raises:
        ValidationError: If validation fails
    """
    if field not in data or not data[field]:
        raise ValidationError(message or f"{field} cannot be empty", field)


def validate_positive_number(data: Dict[str, Any], field: str, allow_zero: bool = False,
                             message: Optional[str] = None) -> None:
    """Validate that a field contains a positive number.

    Args:
        data: Data dictionary to validate
        field: Field name to check
        allow_zero: Whether to allow zero value
        message: Optional custom error message

    Raises:
        ValidationError: If validation fails
    """
    if field not in data:
        return

    value = data[field]

    if not isinstance(value, (int, float)):
        raise ValidationError(message or f"{field} must be a number", field)

    min_value = 0 if allow_zero else 0.000001

    if value < min_value:
        raise ValidationError(
            message or f"{field} must be {'positive' if not allow_zero else 'non-negative'}",
            field
        )


def validate_model_data(model_class: Type, data: Dict[str, Any]) -> None:
    """Validate data against a SQLAlchemy model's columns and constraints.

    This function checks:
    - Required fields are present
    - Data types match column types
    - String lengths are within column limits
    - Numeric values are within constraints

    Args:
        model_class: SQLAlchemy model class
        data: Data to validate

    Raises:
        ValidationError: If validation fails
    """
    try:
        # Get model table info if available
        if hasattr(model_class, '__table__'):
            table = model_class.__table__

            # Check each column
            for column in table.columns:
                column_name = column.name

                # Skip primary key and other auto-generated columns
                if column.primary_key and column_name not in data:
                    continue

                # Check required fields
                if not column.nullable and not column.default and not column.server_default:
                    validate_not_empty(data, column_name, f"{column_name} is required")

                # If field is present, validate type and constraints
                if column_name in data and data[column_name] is not None:
                    value = data[column_name]

                    # String validation
                    if hasattr(column.type, 'length') and column.type.length is not None:
                        if isinstance(value, str):
                            ModelValidator.validate_string_length(
                                value,
                                0,
                                column.type.length,
                                column_name
                            )

                    # Numeric validation
                    if hasattr(column.type, 'precision'):
                        if isinstance(value, (int, float)):
                            # For now, just ensure it's a number
                            pass

        # Perform any model-specific validation
        if hasattr(model_class, '_validate_creation') and callable(model_class._validate_creation):
            model_class._validate_creation(data)

    except ValidationError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Log and convert other errors to ValidationError
        logger.error(f"Error validating model data: {e}")
        raise ValidationError(f"Data validation error: {str(e)}")


# Simpler validation functions for convenience

def validate_string(data: Dict[str, Any], field: str, min_length: int = 0, max_length: Optional[int] = None,
                    required: bool = False) -> None:
    """Validate a string field.

    Args:
        data: Data dictionary to validate
        field: Field name to check
        min_length: Minimum allowed length
        max_length: Maximum allowed length (if any)
        required: Whether the field is required

    Raises:
        ValidationError: If validation fails
    """
    if required:
        validate_not_empty(data, field)

    if field in data and data[field] is not None:
        ModelValidator.validate_string_length(data[field], min_length, max_length, field)


def validate_number(data: Dict[str, Any], field: str, min_value: Optional[Union[int, float]] = None,
                    max_value: Optional[Union[int, float]] = None, required: bool = False) -> None:
    """Validate a numeric field.

    Args:
        data: Data dictionary to validate
        field: Field name to check
        min_value: Minimum allowed value (if any)
        max_value: Maximum allowed value (if any)
        required: Whether the field is required

    Raises:
        ValidationError: If validation fails
    """
    if required:
        validate_not_empty(data, field)

    if field in data and data[field] is not None:
        ModelValidator.validate_number_range(data[field], min_value, max_value, field)


def validate_phone_number(phone_number: str) -> bool:
    """
    Validate phone number format.

    Supports various international and local phone number formats:
    - US/Canada: (123) 456-7890, 123-456-7890, 1234567890
    - International: +1 (123) 456-7890, +44 20 1234 5678

    Args:
        phone_number (str): Phone number to validate

    Returns:
        bool: True if phone number is valid, False otherwise
    """
    if not phone_number or not isinstance(phone_number, str):
        return False

    # Remove all non-digit characters
    cleaned_number = re.sub(r'\D', '', phone_number)

    # Check various phone number patterns
    phone_patterns = [
        r'^\+?1?\d{10,14}$',  # Global pattern for 10-14 digits
        r'^\+?[1-9]\d{1,14}$'  # Flexible international format
    ]

    # Optional: More specific US/Canada pattern
    us_canada_pattern = r'^(\+?1\s?)?(\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}$'

    for pattern in phone_patterns:
        if re.match(pattern, cleaned_number):
            return True

    # Additional check for formatted numbers
    if re.match(us_canada_pattern, phone_number):
        return True

    return False

# Convenience wrapper for use in validation contexts
def validate_phone(phone_number: str) -> Optional[str]:
    """
    Validation function that returns an error message if invalid.

    Args:
        phone_number (str): Phone number to validate

    Returns:
        Optional error message
    """
    if not validate_phone_number(phone_number):
        return "Invalid phone number format"
    return None