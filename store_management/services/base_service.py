# services/base_service.py
"""
Base service implementation with core abstractions and error handling.

This module provides foundational classes and interfaces for service implementations,
resolving circular import issues and providing a consistent base for services.
"""

import abc
import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar('T')


class BaseApplicationException(Exception):
    """
    Base exception for application-level errors with contextual information.

    Attributes:
        message (str): Primary error message
        context (Optional[Dict[str, Any]]): Additional context for the error
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}
        self.message = message
        logging.error(f"Application Error: {message}, Context: {self.context}")


class NotFoundError(BaseApplicationException):
    """
    Exception raised when an entity or resource is not found.

    Inherits contextual error handling from BaseApplicationException.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Not Found: {message}", context)


class ValidationError(BaseApplicationException):
    """
    Exception raised when data validation fails.

    Inherits contextual error handling from BaseApplicationException.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Validation Error: {message}", context)


class IBaseService(abc.ABC):
    """
    Interface for base service operations with generic type support.

    Provides a standardized interface for core service methods.
    """

    @abc.abstractmethod
    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            data (Dict[str, Any]): Data for creating the entity

        Returns:
            T: Created entity

        Raises:
            ValidationError: If data is invalid
        """
        pass

    @abc.abstractmethod
    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Retrieve an entity by its identifier.

        Args:
            entity_id (Any): Unique identifier for the entity

        Returns:
            Optional[T]: Retrieved entity or None if not found
        """
        pass

    @abc.abstractmethod
    def update(self, entity_id: Any, data: Dict[str, Any]) -> T:
        """
        Update an existing entity.

        Args:
            entity_id (Any): Unique identifier for the entity
            data (Dict[str, Any]): Updated data for the entity

        Returns:
            T: Updated entity

        Raises:
            NotFoundError: If entity doesn't exist
            ValidationError: If update data is invalid
        """
        pass

    @abc.abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """
        Delete an entity by its identifier.

        Args:
            entity_id (Any): Unique identifier for the entity

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If entity doesn't exist
        """
        pass


class BaseService(Generic[T], IBaseService):
    """
    Abstract base implementation of IBaseService with default method implementations.

    Provides a basic implementation that can be extended by specific service classes.
    """

    def __init__(self):
        """
        Initialize the base service with logging.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

    def create(self, data: Dict[str, Any]) -> T:
        """
        Default implementation for creating an entity.

        Args:
            data (Dict[str, Any]): Data for creating the entity

        Returns:
            T: Created entity

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        self.logger.info(f"Creating entity with data: {data}")
        raise NotImplementedError("Subclasses must implement create method")

    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        Default implementation for retrieving an entity by ID.

        Args:
            entity_id (Any): Unique identifier for the entity

        Returns:
            Optional[T]: Retrieved entity or None

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        self.logger.info(f"Retrieving entity with ID: {entity_id}")
        raise NotImplementedError("Subclasses must implement get_by_id method")

    def update(self, entity_id: Any, data: Dict[str, Any]) -> T:
        """
        Default implementation for updating an entity.

        Args:
            entity_id (Any): Unique identifier for the entity
            data (Dict[str, Any]): Updated data for the entity

        Returns:
            T: Updated entity

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        self.logger.info(f"Updating entity {entity_id} with data: {data}")
        raise NotImplementedError("Subclasses must implement update method")

    def delete(self, entity_id: Any) -> bool:
        """
        Default implementation for deleting an entity.

        Args:
            entity_id (Any): Unique identifier for the entity

        Returns:
            bool: True if deletion was successful

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        self.logger.info(f"Deleting entity with ID: {entity_id}")
        raise NotImplementedError("Subclasses must implement delete method")