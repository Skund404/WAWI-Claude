# utils/error_handling.py

from typing import Optional, Dict, Any
import traceback
import logging


class DatabaseError(Exception):
    """Custom exception for database-related errors.

    Provides detailed context about database operation failures.
    """

    def __init__(self, message: str, details: Optional[str] = None, error_code: Optional[str] = None):
        """Initialize a database error with detailed information.

        Args:
            message: Primary error message
            details: Additional error details or stack trace
            error_code: Optional error code for identification
        """
        self.message = message
        self.details = details
        self.error_code = error_code
        super().__init__(message)

    def __str__(self) -> str:
        """Provide a comprehensive string representation of the error.

        Returns:
            Formatted error message with details
        """
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


def handle_database_error(operation: str, error: Exception,
                          context: Optional[Dict[str, Any]] = None) -> DatabaseError:
    """Standardized handler for database-related errors.

    Args:
        operation: Description of the operation that failed
        error: The original exception
        context: Optional context dictionary with additional information

    Returns:
        A standardized DatabaseError instance
    """
    logger = logging.getLogger(__name__)

    # Get full stack trace
    tb = traceback.format_exc()

    # Create error message
    error_message = f"Database error during {operation}: {str(error)}"

    # Log the error with context and stack trace
    logger.error(error_message)
    if context:
        logger.error(f"Context: {context}")
    logger.debug(f"Stack trace: {tb}")

    # Create and return standardized error
    return DatabaseError(error_message, tb)


def log_database_action(action: str, details: Optional[Dict[str, Any]] = None,
                        level: str = 'info'):
    """Log database-related actions with optional details.

    Args:
        action: Description of the database action
        details: Optional dictionary of additional details
        level: Logging level (info, warning, error)
    """
    logger = logging.getLogger(__name__)

    # Create log message
    message = f"Database action: {action}"
    if details:
        message += f" - Details: {details}"

    # Log at appropriate level
    if level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    else:
        logger.info(message)