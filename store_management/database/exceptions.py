# database/exceptions.py
from typing import Any, Dict, Optional


class DatabaseError(Exception):
    """Base class for database-related exceptions."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(message)


class ModelNotFoundError(DatabaseError):
    """Exception raised when a model instance is not found."""
    pass


class ModelValidationError(DatabaseError):
    """Exception raised when model validation fails."""
    pass


class RepositoryError(DatabaseError):
    """Exception raised when a repository operation fails."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass


class TransactionError(DatabaseError):
    """Exception raised when a database transaction fails."""
    pass