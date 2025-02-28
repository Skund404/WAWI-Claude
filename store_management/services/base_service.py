# services/base_service.py
import abc
import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar('T')


class BaseApplicationException(Exception):
    """Base exception class for application errors with context support."""

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
    """Exception raised when an entity or resource is not found."""
    pass


class ValidationError(BaseApplicationException):
    """Exception raised when data validation fails."""
    pass


class IBaseService(abc.ABC):
    """Interface for base service operations."""

    def validate_data(self, data: Dict[str, Any], required_fields: Optional[List[str]] = None) -> None:
        """Validate input data against requirements.

        Args:
            data: Data to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    {"missing_fields": missing_fields}
                )

    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log a service operation with details.

        Args:
            operation: Description of the operation
            details: Additional details about the operation
        """
        self.logger.info(f"{operation}: {details or {} }")


class BaseService(Generic[T]):
    """Base service implementation with common functionality."""

    def __init__(self):
        """Initialize the base service with logging."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_data(self, data: Dict[str, Any], required_fields: Optional[List[str]] = None) -> None:
        """Validate input data against requirements.

        Args:
            data: Data to validate
            required_fields: List of required field names

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    {"missing_fields": missing_fields}
                )

    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log a service operation with details.

        Args:
            operation: Description of the operation
            details: Additional details about the operation
        """
        self.logger.info(f"{operation}: {details or {} }")


# Add this for backwards compatibility
Service = BaseService