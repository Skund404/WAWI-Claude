# File: store_management/utils/error_handling.py

from typing import Optional, Any, Dict
import functools
from store_management.utils.logging_config import error_tracker


class ApplicationError(Exception):
    """
    Base class for application-specific errors

    Provides consistent error handling and logging
    """

    def __init__(
            self,
            message: str,
            error_code: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ApplicationError

        Args:
            message (str): Error message
            error_code (Optional[str]): Unique error identifier
            context (Optional[Dict]): Additional error context
        """
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}

        # Log the error automatically
        error_tracker.log_error(
            self,
            context=self.context,
            additional_info=f"Error Code: {self.error_code}"
        )


class DatabaseError(ApplicationError):
    """Specific error for database-related exceptions"""
    pass


class ValidationError(ApplicationError):
    """Error for data validation failures"""
    pass


def handle_errors(
        error_mapping: Optional[Dict[type, type]] = None,
        default_error: type = ApplicationError
):
    """
    Decorator for global error handling and transformation

    Args:
        error_mapping (Optional[Dict]): Mapping of exception types to custom errors
        default_error (type): Default error type if no mapping exists
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if error should be mapped
                error_type = type(e)
                mapped_error = (error_mapping or {}).get(error_type, default_error)

                # Raise mapped or default error
                raise mapped_error(
                    str(e),
                    context={
                        'original_error': error_type.__name__,
                        'function': func.__name__
                    }
                ) from e

        return wrapper

    return decorator