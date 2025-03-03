# services/base_service.py
import abc
import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Define a generic type variable for models
T = TypeVar('T')


class BaseApplicationException(Exception):
    """Base class for all application exceptions."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Initialize with message and context.

        Args:
            message: The error message
            context: Additional context for the error
        """
        self.message = message
        self.context = context or {}
        super().__init__(message)


class NotFoundError(BaseApplicationException):
    """Exception raised when a requested resource is not found."""
    pass


class ValidationError(BaseApplicationException):
    """Exception raised when input validation fails."""
    pass


class ServiceError(BaseApplicationException):
    """Exception raised when a service operation fails."""
    pass


class IBaseService(abc.ABC):
    """Interface for base service functionality."""
    pass


class BaseService(Generic[T]):
    """
    Base service implementation with common functionality.

    This class provides common service methods and error handling patterns
    to be used across all services.
    """

    def __init__(self):
        """Initialize the base service with logging."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that required fields are present in the input data.

        Args:
            data: Input data to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If any required field is missing
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def to_dict(self, model: T, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert a model instance to a dictionary.

        Args:
            model: The model instance to convert
            include_relationships: Whether to include related models

        Returns:
            Dictionary representation of the model
        """
        # Use the model's to_dict method if available
        if hasattr(model, 'to_dict') and callable(getattr(model, 'to_dict')):
            return model.to_dict(include_relationships=include_relationships)

        # Fallback to manual conversion
        result = {}
        for column in model.__table__.columns:
            result[column.name] = getattr(model, column.name)
        return result