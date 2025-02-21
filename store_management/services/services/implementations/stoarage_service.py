# store_management/services/implementations/storage_service.py
from typing import List, Optional, Dict, Any, Type, cast
from store_management.di.service import Service
from store_management.di.container import DependencyContainer
from store_management.services.interfaces.storage_service import IStorageService
from store_management.database.sqlalchemy.base_manager import BaseManager
from store_management.database.sqlalchemy.models.storage import Storage


class StorageService(Service, IStorageService):
    """Service for managing storage locations and their inventory."""

    def __init__(self, container: DependencyContainer):
        super().__init__(container)
        self._storage_manager = self.get_dependency(BaseManager[Storage])

    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """Get all storage locations."""
        storage_list = self._storage_manager.get_all()
        return [self._to_dict(storage) for storage in storage_list]

    def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """Get a storage location by ID."""
        storage = self._storage_manager.get(storage_id)
        return self._to_dict(storage) if storage else None

    def _to_dict(self, storage: Storage) -> Dict[str, Any]:
        """Convert Storage model to dictionary."""
        return {
            'id': storage.id,
            'location': storage.location,
            'description': storage.description,
            'capacity': storage.capacity,
            'current_usage': storage.current_usage
        }

    # Implement other methods