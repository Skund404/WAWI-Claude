# services/base_service.py
import logging
from typing import TypeVar, Generic, Dict, Any, Optional, List
from abc import ABC, abstractmethod


# Define custom exceptions
class NotFoundError(Exception):
    """Exception raised when an entity isn't found."""

    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.context = context or {}
        super().__init__(message)


class ValidationError(Exception):
    """Exception raised when data validation fails."""

    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.context = context or {}
        super().__init__(message)


class ApplicationError(Exception):
    """General application error with context information."""

    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.context = context or {}
        super().__init__(message)


# Type variable for generic entity
T = TypeVar('T')


# Repository interface
class IBaseRepository(Generic[T], ABC):
    """Base repository interface for data access operations."""

    @abstractmethod
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Get all entities with optional pagination."""
        pass

    @abstractmethod
    def add(self, data: Dict[str, Any]) -> T:
        """Add a new entity."""
        pass

    @abstractmethod
    def update(self, id: Any, data: Dict[str, Any]) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    def delete(self, id: Any) -> bool:
        """Delete an entity."""
        pass


# Unit of work interface
class IUnitOfWork(ABC):
    """Interface for transaction management."""

    def __enter__(self):
        """Start a transaction."""
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End a transaction."""
        pass

    @abstractmethod
    def commit(self):
        """Commit changes."""
        pass

    @abstractmethod
    def rollback(self):
        """Rollback changes."""
        pass


class BaseService(ABC, Generic[T]):
    """
    Abstract base service providing a generic implementation of CRUD operations.

    This service acts as an intermediate layer between the repository
    and the application logic, adding additional validation, error handling,
    and business logic capabilities.

    Attributes:
        _repository (IBaseRepository): The repository for data access
        _unit_of_work (IUnitOfWork): Unit of work for transaction management
        _logger (logging.Logger): Logger for the service
    """

    def __init__(self, repository: IBaseRepository[T], unit_of_work: Optional[IUnitOfWork] = None):
        """
        Initialize the base service with a repository and optional unit of work.

        Args:
            repository: Repository for data access
            unit_of_work: Optional unit of work for transactions
        """
        self._repository = repository
        self._unit_of_work = unit_of_work
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_by_id(self, id: Any) -> Optional[T]:
        """
        Retrieve an entity by its unique identifier.

        Args:
            id (Any): The unique identifier of the entity

        Returns:
            Optional[T]: The retrieved entity

        Raises:
            NotFoundError: If no entity is found with the given ID
            ApplicationError: If an unexpected error occurs
        """
        try:
            entity = self._repository.get_by_id(id)
            if not entity:
                raise NotFoundError(f'Entity with ID {id} not found', {'id': id})
            return entity
        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(f'Error retrieving entity by ID {id}: {e}')
            raise ApplicationError(f'Failed to retrieve entity: {str(e)}', {'id': id})

    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        Retrieve all entities with optional pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List[T]: A list of entities

        Raises:
            ApplicationError: If an unexpected error occurs
        """
        try:
            return self._repository.get_all(limit=limit, offset=offset)
        except Exception as e:
            self._logger.error(f'Error retrieving all entities: {e}')
            raise ApplicationError('Failed to retrieve entities', {})

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            data: Data to create the entity

        Returns:
            T: The created entity

        Raises:
            ValidationError: If the data fails validation
            ApplicationError: If an unexpected error occurs
        """
        try:
            self._validate_create_data(data)

            if self._unit_of_work:
                with self._unit_of_work:
                    entity = self._repository.add(data)
                    self._unit_of_work.commit()
                    return entity
            else:
                return self._repository.add(data)

        except ValidationError as ve:
            self._logger.warning(f'Validation error creating entity: {ve}')
            raise
        except Exception as e:
            self._logger.error(f'Error creating entity: {e}')
            raise ApplicationError(f'Failed to create entity: {str(e)}', {'input_data': data})

    def update(self, id: Any, data: Dict[str, Any]) -> T:
        """
        Update an existing entity.

        Args:
            id: The unique identifier of the entity to update
            data: Updated data for the entity

        Returns:
            T: The updated entity

        Raises:
            NotFoundError: If the entity doesn't exist
            ValidationError: If the update data is invalid
            ApplicationError: If an unexpected error occurs
        """
        try:
            existing_entity = self.get_by_id(id)
            self._validate_update_data(existing_entity, data)

            if self._unit_of_work:
                with self._unit_of_work:
                    updated_entity = self._repository.update(id, data)
                    self._unit_of_work.commit()
                    return updated_entity
            else:
                return self._repository.update(id, data)

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self._logger.error(f'Error updating entity {id}: {e}')
            raise ApplicationError(f'Failed to update entity: {str(e)}', {'id': id, 'input_data': data})

    def delete(self, id: Any) -> bool:
        """
        Delete an entity by its identifier.

        Args:
            id: The unique identifier of the entity to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the entity doesn't exist
            ApplicationError: If an unexpected error occurs
        """
        try:
            self.get_by_id(id)  # Check if entity exists

            if self._unit_of_work:
                with self._unit_of_work:
                    result = self._repository.delete(id)
                    self._unit_of_work.commit()
                    return result
            else:
                return self._repository.delete(id)

        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(f'Error deleting entity {id}: {e}')
            raise ApplicationError(f'Failed to delete entity: {str(e)}', {'id': id})

    @abstractmethod
    def _validate_create_data(self, data: Dict[str, Any]) -> None:
        """
        Abstract method to validate data before entity creation.

        Subclasses must implement specific validation logic.

        Args:
            data: Data to be validated

        Raises:
            ValidationError: If data is invalid
        """
        pass

    @abstractmethod
    def _validate_update_data(self, existing_entity: T, update_data: Dict[str, Any]) -> None:
        """
        Abstract method to validate data before entity update.

        Subclasses must implement specific validation logic.

        Args:
            existing_entity: The existing entity
            update_data: Data to be validated

        Raises:
            ValidationError: If data is invalid
        """
        pass

    def search(self, search_term: str, fields: Optional[List[str]] = None) -> List[T]:
        """
        Search for entities based on a search term.

        Args:
            search_term: Term to search for
            fields: Fields to search in

        Returns:
            List[T]: List of matching entities

        Raises:
            ApplicationError: If an unexpected error occurs
        """
        try:
            if hasattr(self._repository, 'search'):
                return self._repository.search(search_term, fields)
            else:
                self._logger.warning('Search not supported by repository')
                return []
        except Exception as e:
            self._logger.error(f'Error searching entities: {e}')
            raise ApplicationError(f'Failed to search entities: {str(e)}',
                                   {'search_term': search_term, 'fields': fields})