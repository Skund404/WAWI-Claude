# utils/validators/__init__.py
"""
Validation utility functions for the leatherworking store management system.
"""

import re
from typing import Any, Optional, Union
from datetime import datetime


def validate_string(value: str, field_name: str,
                    min_length: Optional[int] = None,
                    max_length: Optional[int] = None) -> str:
    """
    Validate a string field.

    Args:
        value (str): The string to validate
        field_name (str): Name of the field for error messaging
        min_length (Optional[int]): Minimum allowed length
        max_length (Optional[int]): Maximum allowed length

    Returns:
        str: The validated string

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    # Strip whitespace
    value = value.strip()

    # Check minimum length
    if min_length is not None and len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters long")

    # Check maximum length
    if max_length is not None and len(value) > max_length:
        raise ValueError(f"{field_name} must be no more than {max_length} characters long")

    return value


def validate_not_empty(value: Any, field_name: str) -> Any:
    """
    Ensure a value is not None or empty.

    Args:
        value (Any): The value to validate
        field_name (str): Name of the field for error messaging

    Returns:
        Any: The validated value

    Raises:
        ValueError: If validation fails
    """
    if value is None:
        raise ValueError(f"{field_name} cannot be None")

    if isinstance(value, (str, list, dict, set)) and len(value) == 0:
        raise ValueError(f"{field_name} cannot be empty")

    return value


def validate_positive_number(value: Union[int, float], field_name: str) -> Union[int, float]:
    """
    Validate that a number is positive.

    Args:
        value (Union[int, float]): The number to validate
        field_name (str): Name of the field for error messaging

    Returns:
        Union[int, float]: The validated positive number

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")

    if value < 0:
        raise ValueError(f"{field_name} must be a positive number")

    return value


def validate_email(email: str, field_name: str = "email") -> str:
    """
    Validate an email address.

    Args:
        email (str): The email address to validate
        field_name (str, optional): Name of the field for error messaging

    Returns:
        str: The validated email address

    Raises:
        ValueError: If validation fails
    """
    # Validate string first
    email = validate_string(email, field_name, max_length=100)

    # Simple email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        raise ValueError(f"Invalid {field_name} format")

    return email


def validate_phone(phone: str, field_name: str = "phone") -> str:
    """
    Validate a phone number.

    Args:
        phone (str): The phone number to validate
        field_name (str, optional): Name of the field for error messaging

    Returns:
        str: The validated phone number

    Raises:
        ValueError: If validation fails
    """
    # Validate string first
    phone = validate_string(phone, field_name, max_length=20)

    # Remove non-digit characters
    phone_digits = re.sub(r'\D', '', phone)

    # Basic phone number validation (adjust as needed)
    if len(phone_digits) < 10 or len(phone_digits) > 15:
        raise ValueError(f"Invalid {field_name} number")

    return phone


def validate_date(date: Union[datetime, str], field_name: str = "date") -> datetime:
    """
    Validate a date.

    Args:
        date (Union[datetime, str]): The date to validate
        field_name (str, optional): Name of the field for error messaging

    Returns:
        datetime: The validated date

    Raises:
        ValueError: If validation fails
    """
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            raise ValueError(f"Invalid {field_name} format. Use ISO format (YYYY-MM-DD)")

    if not isinstance(date, datetime):
        raise ValueError(f"{field_name} must be a datetime object or ISO format string")

    # Optional: Add additional date validation if needed
    if date > datetime.now():
        raise ValueError(f"{field_name} cannot be in the future")

    return date


# Export all validation functions
__all__ = [
    'validate_string',
    'validate_not_empty',
    'validate_positive_number',
    'validate_email',
    'validate_phone',
    'validate_date'
]