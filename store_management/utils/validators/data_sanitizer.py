# utils/validators/data_sanitizer.py
"""
Data sanitization utilities for cleaning and validating input data.
"""
from typing import Any, Dict, Union
import re


class DataSanitizer:
    """
    Utility class for sanitizing and cleaning input data.
    Provides methods to clean, validate, and transform various types of data.
    """

    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """
        Sanitize a string by stripping whitespace and removing potentially harmful characters.

        Args:
            value (str): Input string to sanitize

        Returns:
            str: Sanitized string
        """
        if not isinstance(value, str):
            return str(value).strip()

        # Remove or escape potentially harmful characters
        sanitized = re.sub(r'[<>&\'\"]', '', value.strip())
        return sanitized

    @classmethod
    def sanitize_numeric(cls, value: Union[int, float, str], default: Union[int, float] = 0) -> Union[int, float]:
        """
        Sanitize numeric values, handling various input types.

        Args:
            value: Input value to sanitize
            default: Default value to return if sanitization fails

        Returns:
            Sanitized numeric value
        """
        try:
            # Handle string inputs
            if isinstance(value, str):
                # Remove any non-numeric characters except decimal point and minus sign
                cleaned = re.sub(r'[^\d.-]', '', value)
                return float(cleaned) if '.' in cleaned else int(cleaned)

            # Handle numeric inputs
            return float(value) if isinstance(value, float) else int(value)
        except (ValueError, TypeError):
            return default

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize an entire dictionary, cleaning each value based on its type.

        Args:
            data (Dict[str, Any]): Input dictionary to sanitize

        Returns:
            Dict[str, Any]: Sanitized dictionary
        """
        if not isinstance(data, dict):
            return {}

        sanitized_data = {}
        for key, value in data.items():
            # Sanitize key
            sanitized_key = cls.sanitize_string(key)

            # Sanitize value based on type
            if isinstance(value, str):
                sanitized_data[sanitized_key] = cls.sanitize_string(value)
            elif isinstance(value, (int, float)) or isinstance(value, str):
                sanitized_data[sanitized_key] = cls.sanitize_numeric(value)
            elif value is None:
                sanitized_data[sanitized_key] = None
            else:
                # For complex types, convert to string
                sanitized_data[sanitized_key] = str(value)

        return sanitized_data

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email (str): Email address to validate

        Returns:
            bool: True if email is valid, False otherwise
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, email))

    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """
        Validate phone number format.

        Args:
            phone (str): Phone number to validate

        Returns:
            bool: True if phone number is valid, False otherwise
        """
        # Basic phone number validation (adjust regex as needed)
        phone_regex = r'^\+?1?\d{10,14}$'
        return bool(re.match(phone_regex, phone.replace(' ', '').replace('-', '')))