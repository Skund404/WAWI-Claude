# relative path: store_management/services/base_service.py
"""
Base Service Implementation for Leatherworking Store Management.

Provides a foundational abstract base class for service implementations.
"""

import abc
import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar('T')

class BaseApplicationException(Exception):
    """
    Base exception for application-specific errors.

    Provides a standard structure for application-level exceptions.
    """

    def __init__(
            self,
            message: str,
            context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the application exception.

        Args:
            message (str): Error message
            context (Optional[Dict[str, Any]], optional): Additional context about the error
        """
        super().__init__(message)
        self.context = context or {}
        logging.error(f"{self.__class__.__name__}: {message}")


class NotFoundError(BaseApplicationException):
    """
    Exception raised when a requested resource is not found.
    """
    pass


class ValidationError(BaseApplicationException):
    """
    Exception raised when data validation fails.
    """
    pass


class BaseService(abc.ABC, Generic[T]):
    """
    Abstract base class for service implementations.

    Provides a generic interface for basic CRUD operations.
    """

    def __init__(self):
        """
        Initialize the base service with logging.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def get_by_id(
            self,
            id_value: Any
    ) -> Optional[T]:
        """
        Retrieve an item by its unique identifier.

        Args:
            id_value (Any): Unique identifier for the item

        Returns:
            Optional[T]: Retrieved item or None if not found
        """
        pass

    @abc.abstractmethod
    def get_all(
            self,
            filters: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[T]:
        """
        Retrieve all items, with optional filtering and pagination.

        Args:
            filters (Optional[Dict[str, Any]], optional): Filtering criteria
            limit (Optional[int], optional): Maximum number of items to retrieve
            offset (Optional[int], optional): Number of items to skip

        Returns:
            List[T]: List of retrieved items
        """
        pass

    @abc.abstractmethod
    def create(
            self,
            data: Dict[str, Any]
    ) -> T:
        """
        Create a new item.

        Args:
            data (Dict[str, Any]): Data for creating the item

        Returns:
            T: Created item
        """
        pass

    @abc.abstractmethod
    def update(
            self,
            id_value: Any,
            data: Dict[str, Any]
    ) -> T:
        """
        Update an existing item.

        Args:
            id_value (Any): Unique identifier of the item to update
            data (Dict[str, Any]): Updated data

        Returns:
            T: Updated item
        """
        pass

    @abc.abstractmethod
    def delete(
            self,
            id_value: Any
    ) -> bool:
        """
        Delete an item.

        Args:
            id_value (Any): Unique identifier of the item to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    def validate_data(
            self,
            data: Dict[str, Any],
            required_fields: Optional[List[str]] = None
    ) -> None:
        """
        Validate input data.

        Args:
            data (Dict[str, Any]): Data to validate
            required_fields (Optional[List[str]], optional): List of required field names

        Raises:
            ValidationError: If validation fails
        """
        if not data:
            raise ValidationError("No data provided")

        if required_fields:
            missing_fields = [
                field for field in required_fields
                if field not in data or data[field] is None
            ]

            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    {"missing_fields": missing_fields}
                )

    def log_operation(
            self,
            operation: str,
            details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log service operations.

        Args:
            operation (str): Description of the operation
            details (Optional[Dict[str, Any]], optional): Additional operation details
        """
        self.logger.info(f"{operation}: {details or {}}")