# services/implementations/storage_service.py
from typing import Dict, List, Optional, Any
from services.interfaces.storage_service import IStorageService
from database.repositories.storage_repository import StorageRepository
from di.service import Service
from utils.logger import get_logger


class StorageService(Service, IStorageService):
    """
    Concrete implementation of the IStorageService interface.

    This service provides methods for managing storage locations
    with dependency injection and error handling.
    """

    def __init__(self, container):
        """
        Initialize the StorageService with a dependency injection container.

        Args:
            container: Dependency injection container
        """
        self.container = container
        self.logger = get_logger(self.__class__.__name__)

    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all storage locations.

        Returns:
            List of storage locations as dictionaries.

        Raises:
            Exception: If there's an error retrieving storage locations.
        """
        try:
            repository: StorageRepository = self.container.resolve(StorageRepository)
            storage_locations = repository.get_all()
            return [self._to_dict(storage) for storage in storage_locations]
        except Exception as e:
            self.logger.error(f"Error retrieving storage locations: {e}")
            raise

    def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific storage location by its ID.

        Args:
            storage_id (int): Unique identifier for the storage location.

        Returns:
            Dictionary representation of the storage location or None if not found.

        Raises:
            ValueError: If storage_id is invalid.
        """
        if not isinstance(storage_id, int) or storage_id <= 0:
            raise ValueError("Invalid storage ID")

        try:
            repository: StorageRepository = self.container.resolve(StorageRepository)
            storage = repository.get(storage_id)
            return self._to_dict(storage) if storage else None
        except Exception as e:
            self.logger.error(f"Error retrieving storage location {storage_id}: {e}")
            raise

    def create_storage_location(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new storage location.

        Args:
            storage_data (dict): Data for the new storage location.

        Returns:
            Dictionary of the newly created storage location.

        Raises:
            ValueError: If storage_data is invalid.
        """
        if not storage_data:
            raise ValueError("Storage data cannot be empty")

        try:
            repository: StorageRepository = self.container.resolve(StorageRepository)
            new_storage = repository.create(storage_data)
            created_storage = self._to_dict(new_storage)
            self.logger.info(f"Created new storage location: {created_storage}")
            return created_storage
        except Exception as e:
            self.logger.error(f"Error creating storage location: {e}")
            raise

    def update_storage_location(self, storage_id: int, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing storage location.

        Args:
            storage_id (int): Unique identifier of the storage location to update.
            storage_data (dict): Updated data for the storage location.

        Returns:
            Dictionary of the updated storage location.

        Raises:
            ValueError: If storage_id is invalid or storage_data is empty.
        """
        if not isinstance(storage_id, int) or storage_id <= 0:
            raise ValueError("Invalid storage ID")
        if not storage_data:
            raise ValueError("Storage update data cannot be empty")

        try:
            repository: StorageRepository = self.container.resolve(StorageRepository)
            updated_storage = repository.update(storage_id, storage_data)
            updated_dict = self._to_dict(updated_storage)
            self.logger.info(f"Updated storage location {storage_id}: {updated_dict}")
            return updated_dict
        except Exception as e:
            self.logger.error(f"Error updating storage location {storage_id}: {e}")
            raise

    def delete_storage_location(self, storage_id: int) -> None:
        """
        Delete a storage location.

        Args:
            storage_id (int): Unique identifier of the storage location to delete.

        Raises:
            ValueError: If storage_id is invalid.
        """
        if not isinstance(storage_id, int) or storage_id <= 0:
            raise ValueError("Invalid storage ID")

        try:
            repository: StorageRepository = self.container.resolve(StorageRepository)
            repository.delete(storage_id)
            self.logger.info(f"Deleted storage location {storage_id}")
        except Exception as e:
            self.logger.error(f"Error deleting storage location {storage_id}: {e}")
            raise

    def search_storage_locations(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search storage locations based on a search term.

        Args:
            search_term (str): Term to search for in storage locations.

        Returns:
            List of matching storage locations as dictionaries.

        Raises:
            ValueError: If search term is empty.
        """
        if not search_term or not isinstance(search_term, str):
            raise ValueError("Search term must be a non-empty string")

        try:
            repository: StorageRepository = self.container.resolve(StorageRepository)
            storage_locations = repository.search_storage(search_term)
            return [self._to_dict(storage) for storage in storage_locations]
        except Exception as e:
            self.logger.error(f"Error searching storage locations: {e}")
            raise

    def get_storage_status(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific storage location.

        Args:
            storage_id (int): Unique identifier of the storage location.

        Returns:
            Dictionary with storage status information or None if not found.

        Raises:
            ValueError: If storage_id is invalid.
        """
        if not isinstance(storage_id, int) or storage_id <= 0:
            raise ValueError("Invalid storage ID")

        try:
            repository: StorageRepository = self.container.resolve(StorageRepository)
            storage = repository.get(storage_id)

            if not storage:
                return None

            return {
                'storage_id': storage_id,
                'name': storage.name,
                'location': storage.location,
                'type': storage.type,
                'status': storage.status,
                'occupancy_percentage': storage.occupancy_percentage(),
                'total_capacity': storage.capacity,
                'current_usage': storage.current_occupancy
            }
        except Exception as e:
            self.logger.error(f"Error retrieving storage status for {storage_id}: {e}")
            raise

    def _to_dict(self, storage: Any) -> Dict[str, Any]:
        """
        Convert a storage model to a dictionary.

        Args:
            storage: Storage model instance.

        Returns:
            Dictionary representation of the storage.
        """
        try:
            return {
                'id': storage.id,
                'name': storage.name,
                'description': storage.description or '',
                'capacity': storage.capacity,
                'current_occupancy': storage.current_occupancy,
                'location': storage.location,
                'type': storage.type,
                'status': storage.status,
                'created_at': storage.created_at,
                'updated_at': storage.updated_at,
                'occupancy_percentage': storage.occupancy_percentage()
            }
        except Exception as e:
            self.logger.error(f"Error converting storage to dict: {e}")
            raise