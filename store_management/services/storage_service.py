# File: store_management/services/storage_service.py
from typing import List, Optional, Dict, Any
from database.sqlalchemy.models_file import Storage, Product
from services.interfaces.storage_service import IStorageService

class StorageService(IStorageService):
    """
    Service for managing storage locations.
    """
    def __init__(self, db_manager):
        """
        Initialize StorageService with a database manager.

        Args:
            db_manager: Database manager for storage operations
        """
        self._db_manager = db_manager

    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all storage locations.

        Returns:
            List of storage location dictionaries
        """
        storages = self._db_manager.get_all_records(Storage)
        return [self._to_dict(storage) for storage in storages]

    def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific storage location by ID.

        Args:
            storage_id: ID of the storage location

        Returns:
            Storage location details or None if not found
        """
        storage = self._db_manager.get_record(Storage, storage_id)
        return self._to_dict(storage) if storage else None

    def _to_dict(self, storage: Storage) -> Dict[str, Any]:
        """
        Convert a Storage model to a dictionary.

        Args:
            storage: Storage model instance

        Returns:
            Dictionary representation of the storage location
        """
        return {
            'id': storage.id,
            'location': storage.location,
            'description': storage.description,
            'capacity': storage.capacity,
            'current_usage': storage.current_usage,
            'products': [self._product_to_dict(product) for product in storage.products]
        }

    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """
        Convert a Product model to a dictionary.

        Args:
            product: Product model instance

        Returns:
            Dictionary representation of the product
        """
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category': product.category,
            'unit_price': product.unit_price
        }