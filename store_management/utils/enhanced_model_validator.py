# utils/enhanced_model_validator.py
"""
Enhanced Model Validation Utility

Provides comprehensive validation mechanisms for database models,
designed to work seamlessly with the CircularImportResolver.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union
from enum import Enum
import re
import logging
from datetime import datetime, date

from utils.circular_import_resolver import lazy_import


class ValidationError(Exception):
    """
    Custom exception for model validation failures with rich context.
    """

    def __init__(
            self,
            message: str,
            field: Optional[str] = None,
            error_type: Optional[str] = None,
            additional_context: Optional[Dict] = None
    ):
        self.message = message
        self.field = field
        self.error_type = error_type
        self.additional_context = additional_context or {}
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """
        Generate a comprehensive error message.

        Returns:
            Formatted error message with context
        """
        base_message = self.message
        if self.field:
            base_message = f"Validation failed for field '{self.field}': {base_message}"

        if self.additional_context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.additional_context.items())
            base_message += f" (Context: {context_str})"

        return base_message


class ModelValidator:
    """
    Advanced validation utility with robust error handling and flexibility.
    """

    @staticmethod
    def validate_not_empty(
            value: Any,
            field_name: str,
            allow_zero: bool = False,
            trim: bool = True
    ) -> None:
        """
        Validate that a value is not empty with configurable options.

        Args:
            value: Value to validate
            field_name: Name of the field being validated
            allow_zero: Whether zero is considered valid
            trim: Whether to strip whitespace for strings

        Raises:
            ValidationError: If value is empty
        """
        if value is None:
            raise ValidationError("Cannot be None", field_name, "null_value")

        # Handle string-specific validation
        if isinstance(value, str):
            cleaned_value = value.strip() if trim else value
            if not cleaned_value:
                raise ValidationError("Cannot be an empty string", field_name, "empty_string")

        # Handle collections
        elif hasattr(value, '__len__'):
            if len(value) == 0:
                raise ValidationError("Cannot be an empty collection", field_name, "empty_collection")

        # Handle numeric values
        elif isinstance(value, (int, float)):
            if not allow_zero and value == 0:
                raise ValidationError("Cannot be zero", field_name, "zero_value")

    @staticmethod
    def validate_type(
            value: Any,
            expected_type: Union[Type, tuple],
            field_name: str,
            allow_none: bool = False
    ) -> None:
        """
        Validate the type of a value with comprehensive type checking.

        Args:
            value: Value to validate
            expected_type: Expected type or tuple of types
            field_name: Name of the field being validated
            allow_none: Whether None is acceptable

        Raises:
            ValidationError: If type is incorrect
        """
        if value is None:
            if not allow_none:
                raise ValidationError("Cannot be None", field_name, "null_value")
            return

        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Must be of type {expected_type}",
                field_name,
                "type_mismatch",
                {"actual_type": type(value)}
            )

    @staticmethod
    def validate_enum(
            value: Any,
            enum_class: Type[Enum],
            field_name: str,
            allow_none: bool = False
    ) -> None:
        """
        Validate that a value is a valid enum member.

        Args:
            value: Value to validate
            enum_class: Enum class to validate against
            field_name: Name of the field being validated
            allow_none: Whether None is acceptable

        Raises:
            ValidationError: If value is not a valid enum
        """
        if value is None:
            if not allow_none:
                raise ValidationError("Cannot be None", field_name, "null_value")
            return

        if not isinstance(value, enum_class):
            raise ValidationError(
                f"Must be a valid {enum_class.__name__} member",
                field_name,
                "invalid_enum",
                {"valid_values": list(enum_class.__members__.keys())}
            )

    @staticmethod
    def validate_regex(
            value: str,
            pattern: str,
            field_name: str,
            error_message: Optional[str] = None
    ) -> None:
        """
        Validate a string against a regex pattern.

        Args:
            value: String to validate
            pattern: Regex pattern
            field_name: Name of the field being validated
            error_message: Optional custom error message

        Raises:
            ValidationError: If value does not match pattern
        """
        if not re.match(pattern, value):
            raise ValidationError(
                error_message or f"Does not match required pattern: {pattern}",
                field_name,
                "pattern_mismatch"
            )

    @staticmethod
    def validate_range(
            value: Union[int, float, date, datetime],
            min_value: Optional[Any] = None,
            max_value: Optional[Any] = None,
            field_name: str = "value"
    ) -> None:
        """
        Validate that a value is within a specified range.

        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            field_name: Name of the field being validated

        Raises:
            ValidationError: If value is outside specified range
        """
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"Must be greater than or equal to {min_value}",
                field_name,
                "below_minimum",
                {"min_value": min_value}
            )

        if max_value is not None and value > max_value:
            raise ValidationError(
                f"Must be less than or equal to {max_value}",
                field_name,
                "above_maximum",
                {"max_value": max_value}
            )

    @classmethod
    def validate_email(cls, email: str) -> None:
        """
        Validate email address format using regex.

        Args:
            email: Email address to validate

        Raises:
            ValidationError: If email is invalid
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        cls.validate_regex(
            email,
            email_pattern,
            'email',
            "Invalid email format"
        )

    @classmethod
    def validate_model(
            cls,
            model_instance: Any,
            validation_rules: Optional[Dict[str, Callable]] = None
    ) -> None:
        """
        Validate an entire model instance with custom validation rules.

        Args:
            model_instance: Model instance to validate
            validation_rules: Optional dictionary of custom validation functions

        Raises:
            ValidationError: If any validation fails
        """
        if validation_rules is None:
            return

        for field, validator in validation_rules.items():
            try:
                value = getattr(model_instance, field, None)
                validator(value)
            except Exception as e:
                raise ValidationError(
                    f"Custom validation failed for {field}",
                    field,
                    "custom_validation_error",
                    {"original_error": str(e)}
                )


# Convenience functions for quick validations
def validate_not_empty(
        data: Dict,
        field: str,
        message: Optional[str] = None,
        allow_zero: bool = False
):
    """
    Quick validation for non-empty values in dictionaries.

    Args:
        data: Dictionary to validate
        field: Field to check
        message: Optional custom error message
        allow_zero: Whether zero is considered valid

    Raises:
        ValidationError: If field is empty
    """
    try:
        ModelValidator.validate_not_empty(
            data.get(field),
            field,
            allow_zero,
            message or f"{field} is required"
        )
    except ValidationError as e:
        raise e


def validate_positive_number(
        data: Dict,
        field: str,
        allow_zero: bool = False,
        message: Optional[str] = None
):
    """
    Quick validation for positive numeric values.

    Args:
        data: Dictionary to validate
        field: Field to check
        allow_zero: Whether zero is considered valid
        message: Optional custom error message

    Raises:
        ValidationError: If value is not a positive number
    """
    value = data.get(field)

    # Check if value exists
    ModelValidator.validate_not_empty(value, field, message)

    # Validate numeric type
    ModelValidator.validate_type(value, (int, float), field)

    # Validate range
    min_value = 0 if not allow_zero else None
    ModelValidator.validate_range(value, min_value, field_name=field)