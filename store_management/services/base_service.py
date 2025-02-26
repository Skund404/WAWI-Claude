# services/base_service.py
"""
Base service module providing common functionality for all services.

This module defines abstract base classes and common utility methods
for service implementations across the application.
"""

import abc
import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Fix imports by using the correct paths based on project structure
# The exceptions are likely in utils.error_handler or database.exceptions
try:
    # Try to import from database.exceptions first
    from database.exceptions import ApplicationError, NotFoundError, ValidationError
except ImportError:
    try:
        # Try to import from utils.error_handler next
        from utils.error_handler import ApplicationError, NotFoundError, ValidationError
    except ImportError:
        # Define minimal fallback exception classes if imports fail
        class BaseApplicationException(Exception):
            """Base exception class for application errors."""

            def __init__(self, message: str, context: Dict[str, Any] = None):
                self.context = context or {}
                super().__init__(message)


        class ApplicationError(BaseApplicationException):
            """Exception raised for general application errors."""
            pass


        class NotFoundError(BaseApplicationException):
            """Exception raised when a requested resource is not found."""
            pass


        class ValidationError(BaseApplicationException):
            """Exception raised when data validation fails."""
            pass

# Try to import IBaseRepository from the correct location
try:
    # Try database.repositories.interfaces
    from database.repositories.interfaces import IBaseRepository
except ImportError:
    try:
        # Try database.interfaces
        from database.interfaces import IBaseRepository
    except ImportError:
        # Define a minimal interface if import fails
        class IBaseRepository(abc.ABC, Generic[TypeVar('E')]):
            """Interface for repository pattern implementations."""

            @abc.abstractmethod
            def get_by_id(self, id_value: Any): pass

            @abc.abstractmethod
            def get_all(self): pass

            @abc.abstractmethod
            def create(self, data: Dict[str, Any]): pass

            @abc.abstractmethod
            def update(self, id_value: Any, data: Dict[str, Any]): pass

            @abc.abstractmethod
            def delete(self, id_value: Any): pass

# Try to import IUnitOfWork from the correct location
try:
    from database.unit_of_work import IUnitOfWork
except ImportError:
    try:
        from infrastructure.unit_of_work import IUnitOfWork
    except ImportError:
        # Define a minimal interface if import fails
        class IUnitOfWork(abc.ABC):
            """Interface for transaction management."""

            @abc.abstractmethod
            def __enter__(self): pass

            @abc.abstractmethod
            def __exit__(self, exc_type, exc_val, exc_tb): pass

            @abc.abstractmethod
            def commit(self): pass

            @abc.abstractmethod
            def rollback(self): pass

# Import service interfaces - these should be stable
from services.interfaces import (
    InventoryService,
    MaterialService,
    OrderService,
    ProjectService
)

# Logger for this module
logger = logging.getLogger(__name__)

# Type variable for generic typing
T = TypeVar('T')


class Service(abc.ABC, Generic[T]):
    """
    Abstract base class for all services.

    Provides common functionality for CRUD operations and transaction management.
    """

    def __init__(
            self,
            repository: IBaseRepository[T],
            unit_of_work: Optional[IUnitOfWork] = None
    ):
        """
        Initialize the base service with a repository and optional unit of work.

        Args:
            repository (IBaseRepository[T]): Repository for data access
            unit_of_work (Optional[IUnitOfWork], optional): Unit of work for transactions
        """
        self.repository = repository
        self.unit_of_work = unit_of_work
        logger.debug(f"Initialized {self.__class__.__name__} with {repository.__class__.__name__}")

    def get_by_id(self, id_value: Any) -> T:
        """
        Get an entity by its ID.

        Args:
            id_value: The ID of the entity to retrieve

        Returns:
            The entity with the specified ID

        Raises:
            NotFoundError: If the entity does not exist
        """
        try:
            entity = self.repository.get_by_id(id_value)
            if entity is None:
                raise NotFoundError(f"Entity with ID {id_value} not found")
            return entity
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"Error retrieving entity with ID {id_value}: {str(e)}")
            raise ApplicationError(f"Failed to retrieve entity: {str(e)}")

    def get_all(self) -> List[T]:
        """
        Get all entities.

        Returns:
            List of all entities

        Raises:
            ApplicationError: If the operation fails
        """
        try:
            return self.repository.get_all()
        except Exception as e:
            logger.error(f"Error retrieving all entities: {str(e)}")
            raise ApplicationError(f"Failed to retrieve entities: {str(e)}")

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            data: Dictionary with entity data

        Returns:
            The created entity

        Raises:
            ValidationError: If the data is invalid
            ApplicationError: If the operation fails
        """
        try:
            # Validate the data before creating
            self._validate_create_data(data)

            # Use unit of work if available
            if self.unit_of_work:
                with self.unit_of_work:
                    entity = self.repository.create(data)
                    self.unit_of_work.commit()
                    return entity
            else:
                return self.repository.create(data)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating entity: {str(e)}")
            raise ApplicationError(f"Failed to create entity: {str(e)}")

    def update(self, id_value: Any, data: Dict[str, Any]) -> T:
        """
        Update an existing entity.

        Args:
            id_value: ID of the entity to update
            data: Dictionary with updated data

        Returns:
            The updated entity

        Raises:
            NotFoundError: If the entity does not exist
            ValidationError: If the data is invalid
            ApplicationError: If the operation fails
        """
        try:
            # Check if entity exists
            entity = self.get_by_id(id_value)

            # Validate the update data
            self._validate_update_data(id_value, data)

            # Use unit of work if available
            if self.unit_of_work:
                with self.unit_of_work:
                    updated_entity = self.repository.update(id_value, data)
                    self.unit_of_work.commit()
                    return updated_entity
            else:
                return self.repository.update(id_value, data)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error updating entity with ID {id_value}: {str(e)}")
            raise ApplicationError(f"Failed to update entity: {str(e)}")

    def delete(self, id_value: Any) -> bool:
        """
        Delete an entity.

        Args:
            id_value: ID of the entity to delete

        Returns:
            True if the entity was deleted, False otherwise

        Raises:
            NotFoundError: If the entity does not exist
            ApplicationError: If the operation fails
        """
        try:
            # Check if entity exists
            self.get_by_id(id_value)

            # Use unit of work if available
            if self.unit_of_work:
                with self.unit_of_work:
                    result = self.repository.delete(id_value)
                    self.unit_of_work.commit()
                    return result
            else:
                return self.repository.delete(id_value)
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting entity with ID {id_value}: {str(e)}")
            raise ApplicationError(f"Failed to delete entity: {str(e)}")

    def _validate_create_data(self, data: Dict[str, Any]) -> None:
        """
        Validate data for entity creation.

        Args:
            data: Dictionary with entity data

        Raises:
            ValidationError: If the data is invalid
        """
        # Base implementation does nothing - subclasses should override
        pass

    def _validate_update_data(self, id_value: Any, data: Dict[str, Any]) -> None:
        """
        Validate data for entity update.

        Args:
            id_value: ID of the entity to update
            data: Dictionary with updated data

        Raises:
            ValidationError: If the data is invalid
        """
        # Base implementation does nothing - subclasses should override
        pass