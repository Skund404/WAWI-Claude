from typing import Dict, Any, List, Optional, Tuple, Callable


class ValidationMixin:
    """Mixin providing validation functionality for managers.

    This mixin provides methods to validate data before saving to the database.
    """

    def _validators:
        Dict[str, List[Callable]] = {}

    def add_validator(self, field: str, validator: Callable):
        """Add a validator function for a specific field.

        Args:
            field: Field name to validate
            validator: Validation function that returns (bool, str)
        """
        if field not in self._validators:
            self._validators[field] = []

        self._validators[field].append(validator)

    def validate(self, data: Dict[str, Any], partial: bool = False) -> Tuple[bool, Optional[Dict[str, List[str]]]]:
        """Validate data against registered validators.

        Args:
            data: Data to validate
            partial: Whether this is a partial update (only validate provided fields)

        Returns:
            Tuple of (is_valid, error_dict)
        """
        errors = {}

        for field, validators in self._validators.items():
            # Skip validation for missing fields in partial updates
            if partial and field not in data:
                continue

            value = data.get(field)

            field_errors = []
            for validator in validators:
                valid, error = validator(value)
                if not valid:
                    field_errors.append(error)

            if field_errors:
                errors[field] = field_errors

        return len(errors) == 0, errors if errors else None

    # Common validators
    @staticmethod
    def required(value):
        """Validate that a value is not None."""
        if value is None:
            return False, "This field is required"
        return True, None

    @staticmethod
    def min_length(min_length):
        """Validate minimum string length."""

        def validator(value):
            if value is not None and len(str(value)) < min_length:
                return False, f"Must be at least {min_length} characters"
            return True, None

        return validator

    @staticmethod
    def max_length(max_length):
        """Validate maximum string length."""

        def validator(value):
            if value is not None and len(str(value)) > max_length:
                return False, f"Must be at most {max_length} characters"
            return True, None

        return validator

    @staticmethod
    def min_value(min_value):
        """Validate minimum numeric value."""

        def validator(value):
            if value is not None and value < min_value:
                return False, f"Must be at least {min_value}"
            return True, None

        return validator

    @staticmethod
    def max_value(max_value):
        """Validate maximum numeric value."""

        def validator(value):
            if value is not None and value > max_value:
                return False, f"Must be at most {max_value}"
            return True, None

        return validator