from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/exceptions.py

Custom exceptions for database operations.
"""


class DatabaseError(Exception):
    """Base exception for all database errors."""

    @inject(MaterialService)
        def __init__(self, message: str, details: str = None, error_code: int = None):
        """
        Initialize a new DatabaseError.

        Args:
            message: The error message.
            details: Additional error details.
            error_code: Error code.
        """
        self.message = message
        self.details = details
        self.error_code = error_code
        super().__init__(message)

        @inject(MaterialService)
            def __str__(self) -> str:
        """Get string representation of the error."""
        if self.details:
            return f'{self.message} - {self.details}'
        return self.message


class ModelNotFoundError(DatabaseError):
    """Exception raised when a model instance is not found."""

    @inject(MaterialService)
        def __init__(self, model_name: str, model_id: int, message: str = None):
        """
        Initialize a new ModelNotFoundError.

        Args:
            model_name: The name of the model.
            model_id: The ID of the model instance.
            message: Custom error message (optional).
        """
        self.model_name = model_name
        self.model_id = model_id
        message = message or f'{model_name} with ID {model_id} not found'
        super().__init__(message, error_code=404)


class ValidationError(DatabaseError):
    """Exception raised when model validation fails."""

    @inject(MaterialService)
        def __init__(self, model_name: str, errors: dict, message: str = None):
        """
        Initialize a new ValidationError.

        Args:
            model_name: The name of the model.
            errors: Dictionary of validation errors.
            message: Custom error message (optional).
        """
        self.model_name = model_name
        self.errors = errors
        message = message or f'Validation failed for {model_name}'
        super().__init__(message, details=str(errors), error_code=400)


class RepositoryError(DatabaseError):
    """Exception raised for repository operations errors."""

    @inject(MaterialService)
        def __init__(self, repository_name: str, operation: str, details: str = None
                 ):
        """
        Initialize a new RepositoryError.

        Args:
            repository_name: The name of the repository.
            operation: The operation that failed.
            details: Error details.
        """
        self.repository_name = repository_name
        self.operation = operation
        message = (
            f"Repository operation '{operation}' failed for {repository_name}")
        super().__init__(message, details=details, error_code=500)


class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails."""

    @inject(MaterialService)
        def __init__(self, message: str = 'Failed to connect to the database',
                 details: str = None):
        """
        Initialize a new DatabaseConnectionError.

        Args:
            message: The error message.
            details: Error details.
        """
        super().__init__(message, details=details, error_code=503)


class TransactionError(DatabaseError):
    """Exception raised when a database transaction fails."""

    @inject(MaterialService)
        def __init__(self, operation: str, details: str = None):
        """
        Initialize a new TransactionError.

        Args:
            operation: The transaction operation that failed.
            details: Error details.
        """
        message = f"Transaction operation '{operation}' failed"
        super().__init__(message, details=details, error_code=500)
