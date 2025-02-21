# Path: store_management/services/implementations/storage_service.py
from typing import List, Optional, Dict, Any

from store_management.di.service import Service
from store_management.di.container import DependencyContainer
from store_management.services.interfaces.storage_service import IStorageService
from store_management.database.sqlalchemy.core.specialized.storage_manager import StorageManager


class StorageService(Service, IStorageService):
    """
    Concrete implementation of the IStorageService interface.

    This class provides methods for managing storage locations and their inventory.
    """

    def __init__(self, container: DependencyContainer):
        """
        Initialize StorageService with a dependency container.

        Args:
            container: Dependency injection container
        """
        super().__init__(container)
        self.storage_manager = self.get_dependency(StorageManager)

    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all storage locations.

        Returns:
            A list of dictionaries, each representing a storage location.
        """
        try:
            storage_locations = self.storage_manager.get_all()
            return [self._to_dict(location) for location in storage_locations]
        except Exception as e:
            print(
                f"Error retrieving storage locations: {e}")
            return []

    def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific storage location by its ID.

        Args:
            storage_id: The unique identifier of the storage location.

        Returns:
            A dictionary representing the storage location if found, None otherwise.
        """
        try:
            storage = self.storage_manager.get(storage_id)
            return self._to_dict(storage) if storage else None
        except Exception as e:
            print(f"Error retrieving storage location {storage_id}: {e}")
            return None

    def create_storage_location(self, storage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new storage location.

        Args:
            storage_data: Dictionary containing storage location information

        Returns:
            Created storage location dictionary or None if creation fails
        """
        try:
            new_storage = self.storage_manager.create(storage_data)
            return self._to_dict(new_storage)
        except Exception as e:
            print(f"Error creating storage location: {e}")
            return None

    def update_storage_location(self, storage_id: int, storage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing storage location.

        Args:
            storage_id: ID of the storage location to update
            storage_data: Dictionary with updated storage location information

        Returns:
            Updated storage location dictionary or None if update fails
        """
        try:
            updated_storage = self.storage_manager.update(storage_id, storage_data)
            return self._to_dict(updated_storage)
        except Exception as e:
            print(f"Error updating storage location {storage_id}: {e}")
            return None

    def delete_storage_location(self, storage_id: int) -> bool:
        """
        Delete a storage location.

        Args:
            storage_id: ID of the storage location to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            return self.storage_manager.delete(storage_id)
        except Exception as e:
            print(f"Error deleting storage location {storage_id}: {e}")
            return False

    def search_storage_locations(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search storage locations by location or description.

        Args:
            search_term: Term to search for

        Returns:
            List of matching storage locations
        """
        try:
            search_results = self.storage_manager.search(search_term)
            return [self._to_dict(result) for result in search_results]
        except Exception as e:
            print(f"Error searching storage locations: {e}")
            return []

    def get_storage_status(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed status of a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            Dictionary containing storage status details or None
        """
        try:
            # This might require a specific method in the storage manager
            status = self.storage_manager.get_storage_status(storage_id)
            return {
                'storage_id': storage_id,
                'total_capacity': status.get('total_capacity', 0),
                'used_capacity': status.get('used_capacity', 0),
                'available_capacity': status.get('available_capacity', 0),
                'item_count': status.get('item_count', 0),
                'utilization_percentage': status.get('utilization_percentage', 0)
            }
        except Exception as e:
            print(f"Error retrieving storage status for {storage_id}: {e}")
            return None

    def _to_dict(self, storage):
        """
        Convert storage model to dictionary.

        Args:
            storage: Storage model instance

        Returns:
            Dictionary representation of the storage location
        """
        if not storage:
            return {}

        # Basic storage location information
        storage_dict = {
            'id': storage.id,
            'location': getattr(storage, 'location', ''),
            'description': getattr(storage, 'description', ''),
            'capacity': getattr(storage, 'capacity', 0.0),
            'current_usage': getattr(storage, 'current_usage', 0.0)
        }

        # Optional: Add products or other details if available
        try:
            # Attempt to load products in this storage
            # This might require a method from the storage manager
            products = self.storage_manager.get_storage_products(storage.id) if storage.id else []

            storage_dict['products'] = [
                {
                    'id': product.id,
                    'name': getattr(product, 'name', ''),
                    'quantity': getattr(product, 'quantity', 0),
                    'category': getattr(product, 'category', '')
                }
                for product in products
            ]
        except Exception as e:
            print(f"Error loading storage products: {e}")
            storage_dict['products'] = []

        return storage_dict