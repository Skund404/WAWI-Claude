from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/repositories/interfaces/base_repository.py

Interface for repository implementations.
"""
T = TypeVar('T')


class IBaseRepository(Generic[T], ABC):
    """
    Interface for repository implementations.

    This interface defines the methods that all repositories must implement.
    """

    @abstractmethod
    @inject(MaterialService)
        def get_by_id(self, id: int) -> Optional[T]:
        """
        Get an entity by ID.

        Args:
            id: The ID of the entity.

        Returns:
            The entity, or None if not found.
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None
                ) -> List[T]:
        """
        Get all entities.

        Args:
            limit: Maximum number of entities to return.
            offset: Number of entities to skip.

        Returns:
            List of entities.
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def create(self, data: Dict[str, Any]) -> Optional[T]:
        """
        Create a new entity.

        Args:
            data: Dictionary of entity data.

        Returns:
            The created entity, or None if creation failed.
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity.

        Args:
            id: The ID of the entity.
            data: Dictionary of entity data to update.

        Returns:
            The updated entity, or None if update failed.
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def delete(self, id: int) -> bool:
        """
        Delete an entity.

        Args:
            id: The ID of the entity.

        Returns:
            True if deletion was successful, False otherwise.
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def exists(self, id: int) -> bool:
        """
        Check if an entity exists.

        Args:
            id: The ID of the entity.

        Returns:
            True if the entity exists, False otherwise.
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def count(self) -> int:
        """
        Count the number of entities.

        Returns:
            The number of entities.
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def filter_by(self, **kwargs) -> List[T]:
        """
        Filter entities by attribute values.

        Args:
            **kwargs: Filter criteria as field=value pairs.

        Returns:
            List of entities that match the criteria.
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def search(self, search_term: str, fields: List[str]) -> List[T]:
        """
        Search for entities by a search term in specified fields.

        Args:
            search_term: The search term.
            fields: List of field names to search in.

        Returns:
            List of entities that match the search criteria.
        """
        pass
