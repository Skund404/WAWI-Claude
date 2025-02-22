"""
File: database/sqlalchemy/managers/storage_manager.py
Storage manager implementation for managing storage locations.
Extends the BaseManager with storage-specific functionality.
"""
import logging
from typing import List, Dict, Any, Optional, Callable, Union
from sqlalchemy.orm import Session, joinedload

from database.sqlalchemy.core.base_manager import BaseManager
from database.models.storage import Storage
from database.models.product import Product  # Assuming this exists based on your project structure

class StorageManager(BaseManager[Storage]):
    """
    Manager class for storage-related database operations.
    Extends BaseManager with storage-specific queries and operations.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize StorageManager with session factory.

        Args:
            session_factory: Factory function to create database sessions
        """
        super().__init__(Storage, session_factory)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all_storage_locations(self) -> List[Storage]:
        """
        Get all storage locations from the database.

        Returns:
            List of all storage locations

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.session_scope() as session:
                return session.query(Storage).all()
        except Exception as e:
            self.logger.error(f"Failed to retrieve all storage locations - Details: {str(e)}")
            raise

    def add_storage_location(self, data: Dict[str, Any]) -> Storage:
        """
        Add a new storage location.

        Args:
            data: Dictionary with storage location data

        Returns:
            The newly created Storage instance

        Raises:
            Exception: If creation fails
        """
        return self.create(data)

    def update_storage_location(self, location_id: Union[int, str], data: Dict[str, Any]) -> Optional[Storage]:
        """
        Update an existing storage location.

        Args:
            location_id: ID of the storage location to update
            data: Dictionary with updated storage data

        Returns:
            The updated Storage instance or None if not found

        Raises:
            Exception: If update fails
        """
        return self.update(location_id, data)

    def delete_storage_location(self, location_id: Union[int, str]) -> bool:
        """
        Delete a storage location.

        Args:
            location_id: ID of the storage location to delete

        Returns:
            True if deleted successfully, False if not found

        Raises:
            Exception: If deletion fails
        """
        return self.delete(location_id)

    def get_storage_with_items(self, storage_id: Union[int, str]) -> Optional[Storage]:
        """
        Get a storage location with all its associated items.

        Args:
            storage_id: ID of the storage location

        Returns:
            Storage instance with loaded relationships or None if not found

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.session_scope() as session:
                # Use joinedload to eager load products associated with this storage
                return session.query(Storage).options(
                    joinedload(Storage.products)  # Assumes a 'products' relationship exists
                ).filter(Storage.id == storage_id).first()
        except Exception as e:
            self.logger.error(f"Failed to get storage with id {storage_id} and its items - Details: {str(e)}")
            raise

    def get_available_storage(self) -> List[Storage]:
        """
        Get storage locations that have available capacity.

        Returns:
            List of storage locations with available capacity

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.session_scope() as session:
                # This is a placeholder implementation - adjust based on your actual model
                # Assuming Storage has 'capacity' and 'used_capacity' fields
                return session.query(Storage).filter(
                    Storage.capacity > Storage.used_capacity
                ).all()
        except Exception as e:
            self.logger.error(f"Failed to get available storage locations - Details: {str(e)}")
            raise

    def search_storage(self, term: str) -> List[Storage]:
        """
        Search for storage locations by name or description.

        Args:
            term: Search term

        Returns:
            List of matching storage locations

        Raises:
            Exception: If search fails
        """
        try:
            with self.session_scope() as session:
                search_pattern = f"%{term}%"
                return session.query(Storage).filter(
                    (Storage.name.ilike(search_pattern)) |
                    (Storage.description.ilike(search_pattern)) |
                    (Storage.location.ilike(search_pattern))
                ).all()
        except Exception as e:
            self.logger.error(f"Failed to search storage locations - Details: {str(e)}")
            raise

    def get_storage_status(self, storage_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get detailed status information about a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            Dictionary with storage status information

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.session_scope() as session:
                storage = session.query(Storage).get(storage_id)
                if not storage:
                    return {}

                # Count products in this storage
                product_count = session.query(Product).filter(
                    Product.storage_id == storage_id
                ).count()

                # Calculate utilization
                utilization = 0
                if hasattr(storage, 'capacity') and storage.capacity > 0:
                    utilization = (getattr(storage, 'used_capacity', 0) / storage.capacity) * 100

                return {
                    'id': storage.id,
                    'name': storage.name,
                    'location': getattr(storage, 'location', ''),
                    'product_count': product_count,
                    'capacity': getattr(storage, 'capacity', 0),
                    'used': getattr(storage, 'used_capacity', 0),
                    'utilization': utilization,
                    'status': 'active'  # Could be determined by other business logic
                }
        except Exception as e:
            self.logger.error(f"Failed to get storage status for id {storage_id} - Details: {str(e)}")
            raise

    def get_storage_utilization(self) -> List[Dict[str, Any]]:
        """
        Get utilization information for all storage locations.

        Returns:
            List of dictionaries with storage utilization data

        Raises:
            Exception: If database operation fails
        """
        try:
            with self.session_scope() as session:
                storage_list = session.query(Storage).all()
                result = []

                for storage in storage_list:
                    # Calculate utilization if capacity fields exist
                    utilization = 0
                    if hasattr(storage, 'capacity') and storage.capacity > 0:
                        utilization = (getattr(storage, 'used_capacity', 0) / storage.capacity) * 100

                    result.append({
                        'id': storage.id,
                        'name': storage.name,
                        'location': getattr(storage, 'location', ''),
                        'capacity': getattr(storage, 'capacity', 0),
                        'used': getattr(storage, 'used_capacity', 0),
                        'utilization': utilization
                    })

                return result
        except Exception as e:
            self.logger.error(f"Failed to get storage utilization - Details: {str(e)}")
            raise

    def bulk_update_storage(self, updates: List[Dict[str, Any]]) -> List[Storage]:
        """
        Update multiple storage locations at once.

        Args:
            updates: List of dictionaries with storage updates, each containing 'id' field

        Returns:
            List of updated Storage instances

        Raises:
            Exception: If bulk update fails
        """
        return self.bulk_update(updates)