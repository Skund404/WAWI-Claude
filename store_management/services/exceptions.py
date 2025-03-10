# services/exceptions.py
# Service-specific exceptions

class ServiceError(Exception):
    """Base exception for service-related errors."""

    def __init__(self, message: str = "An error occurred in the service"):
        self.message = message
        super().__init__(self.message)


class ValidationError(ServiceError):
    """Exception raised for business rule violations."""

    def __init__(self, message: str = "Validation error"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(ServiceError):
    """Exception raised when requested entities don't exist."""

    def __init__(self, message: str = "Entity not found"):
        self.message = message
        super().__init__(self.message)


class ConcurrencyError(ServiceError):
    """Exception raised for handling concurrent modifications."""

    def __init__(self, message: str = "Concurrent modification detected"):
        self.message = message
        super().__init__(self.message)


class AuthorizationError(ServiceError):
    """Exception raised when user is not authorized to perform an action."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        self.message = message
        super().__init__(self.message)


class BusinessRuleError(ServiceError):
    """Exception raised when a business rule is violated."""

    def __init__(self, message: str = "Business rule violation"):
        self.message = message
        super().__init__(self.message)