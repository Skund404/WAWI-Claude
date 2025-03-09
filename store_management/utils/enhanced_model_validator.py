# utils/enhanced_model_validator.py
"""
Enhanced validation utilities for model data validation.
"""

import re
from typing import Any, Dict, List, Optional, Union


class ValidationError(Exception):
    """Exception raised for validation errors"""
    pass


def validate_email(email: str) -> bool:
    """
    Validate an email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    # Basic email validation pattern
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))


def validate_phone(phone: str) -> bool:
    """
    Validate a phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    # Basic phone validation pattern
    # Accepts: +1-123-456-7890, (123) 456-7890, 123.456.7890, etc.
    phone_pattern = re.compile(r'^\+?[0-9\(\)\-\.\s]{8,20}$')
    return bool(phone_pattern.match(phone))


def validate_url(url: str) -> bool:
    """
    Validate a URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    # Basic URL validation pattern
    url_pattern = re.compile(
        r'^(https?|ftp)://'  # Protocol
        r'([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+'  # Domain
        r'[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?'  # Domain name
        r'(/[a-zA-Z0-9_\-\.~!*\'();:@&=+$,/?%#]*)?'  # Path
    )
    return bool(url_pattern.match(url))


def validate_length(value: str, min_length: int = 0, max_length: Optional[int] = None) -> bool:
    """
    Validate string length.

    Args:
        value: String to validate
        min_length: Minimum allowed length (default 0)
        max_length: Maximum allowed length (default None)

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(value, str):
        return False

    if len(value) < min_length:
        return False

    if max_length is not None and len(value) > max_length:
        return False

    return True


def validate_range(value: Union[int, float], min_value: Optional[Union[int, float]] = None,
                   max_value: Optional[Union[int, float]] = None) -> bool:
    """
    Validate numeric range.

    Args:
        value: Number to validate
        min_value: Minimum allowed value (default None)
        max_value: Maximum allowed value (default None)

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(value, (int, float)):
        return False

    if min_value is not None and value < min_value:
        return False

    if max_value is not None and value > max_value:
        return False

    return True