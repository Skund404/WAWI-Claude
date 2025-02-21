# File: utils/error_handling.py
# Purpose: Provide centralized error handling for database operations

from typing import Optional, Dict, Any
import traceback
import logging


class DatabaseError(Exception):
    """
    Custom exception for database-related errors.

    Provides detailed context about database operation failures.
    """

    def __init__(
            self,
            message: str,
            details: Optional[str] = None,
            error_code: Optional[str] = None
    ):
        """
        Initialize a database error with detailed information.

        Args:
            message: Primary error message
            details: Additional error details or stack trace
            error_code: Optional error code for identification
        """
        super().__init__(message)
        self.message = message
        self.details = details or traceback.format_exc()
        self.error_code = error_code or "UNKNOWN_DB_ERROR"

    def __str__(self) -> str:
        """
        Provide a comprehensive string representation of the error.

        Returns:
            Formatted error message with details
        """
        error_str = f"[{self.error_code}] {self.message}"
        if self.details:
            error_str += f"\nDetails: {self.details}"
        return error_str


def handle_database_error(
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
) -> DatabaseError:
    """
    Standardized handler for database-related errors.

    Args:
        operation: Description of the operation that failed
        error: The original exception
        context: Optional context dictionary with additional information

    Returns:
        A standardized DatabaseError instance
    """
    # Log the error
    logging.error(
        f"Database operation failed: {operation}\n"
        f"Error: {str(error)}\n"
        f"Context: {context or 'None'}"
    )

    # Create detailed error message
    details = f"Original Error: {str(error)}\n{traceback.format_exc()}"

    # Create and return DatabaseError
    return DatabaseError(
        message=f"Failed to perform {operation}",
        details=details,
        error_code="DB_OPERATION_FAILED"
    )


def log_database_action(
        action: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = 'info'
) -> None:
    """
    Log database-related actions with optional details.

    Args:
        action: Description of the database action
        details: Optional dictionary of additional details
        level: Logging level (info, warning, error)
    """
    log_func = {
        'info': logging.info,
        'warning': logging.warning,
        'error': logging.error
    }.get(level.lower(), logging.info)

    log_message = f"Database Action: {action}"
    if details:
        log_message += f"\nDetails: {details}"

    log_func(log_message)