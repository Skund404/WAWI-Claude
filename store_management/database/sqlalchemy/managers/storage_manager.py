"""
Storage Manager for handling storage location operations.
Provides comprehensive management of storage locations and their relationships.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from store_management.database.sqlalchemy.base_manager import BaseManager
from store_management.database.sqlalchemy.models import Storage, Product, Leather, Part
from store_management.utils.error_handler import DatabaseError
from store_management.utils.logger import logger


class StorageManager(BaseManager):
    """Enhanced storage manager implementing specialized storage operations."""

    def __init__(self, session_factory):
        """Initialize storage manager with session factory.

        Args:
            session_factory: Function to create database sessions
        """
        super().__init__(session_factory, Storage)

    def get_all_storage_locations(self) -> List[Storage]:
        """Retrieve all storage locations.

        Returns:
            List[Storage]: List of all storage locations
        """
        try:
            with self.session_scope() as session:
                return session.query(Storage).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving storage locations: {e}")
            raise DatabaseError("Failed to retrieve storage locations")

    def add_storage_location(self, data: Dict[str, Any]) -> Optional[Storage]:
        """Add a new storage location.

        Args:
            data: Dictionary containing storage location data
                Required keys:
                - location: str
                - capacity: float
                Optional keys:
                - description: str
                - status: str

        Returns:
            Optional[Storage]: Added storage location or None if failed

        Raises:
            DatabaseError: If validation fails or database operation fails
        """
        try:
            # Validate location doesn't already exist
            with self.session_scope() as session:
                existing = session.query(Storage).filter(
                    Storage.location == data['location']
                ).first()
                if existing:
                    raise DatabaseError(f"Storage location {data['location']} already exists")

                # Create new storage location
                storage = Storage(**data)
                session.add(storage)
                session.commit()
                return storage
        except SQLAlchemyError as e:
            logger.error(f"Error adding storage location: {e}")
            raise DatabaseError("Failed to add storage location")

    def update_storage_location(self, location_id: int, data: Dict[str, Any]) -> Optional[Storage]:
        """Update a storage location.

        Args:
            location_id: ID of storage location to update
            data: Dictionary containing update data

        Returns:
            Optional[Storage]: Updated storage location or None if not found

        Raises:
            DatabaseError: If validation fails or database operation fails
        """
        try:
            with self.session_scope() as session:
                storage = session.query(Storage).get(location_id)
                if not storage:
                    return None

                # Update attributes
                for key, value in data.items():
                    setattr(storage, key, value)

                session.commit()
                return storage
        except SQLAlchemyError as e:
            logger.error(f"Error updating storage location {location_id}: {e}")
            raise DatabaseError(f"Failed to update storage location {location_id}")

    def delete_storage_location(self, location_id: int) -> bool:
        """Delete a storage location.

        Args:
            location_id: ID of storage location to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            DatabaseError: If deletion fails or has dependent records
        """
        try:
            with self.session_scope() as session:
                storage = session.query(Storage).get(location_id)
                if not storage:
                    return False

                # Check for items in storage
                if storage.items:
                    raise DatabaseError(
                        f"Cannot delete storage location {location_id} - contains items"
                    )

                session.delete(storage)
                session.commit()
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting storage location {location_id}: {e}")
            raise DatabaseError(f"Failed to delete storage location {location_id}")

    def get_storage_with_items(self, storage_id: int) -> Optional[Storage]:
        """Get storage location with all associated items.

        Args:
            storage_id: ID of storage location

        Returns:
            Optional[Storage]: Storage with items loaded or None if not found
        """
        try:
            with self.session_scope() as session:
                return session.query(Storage) \
                    .options(joinedload(Storage.items)) \
                    .filter(Storage.id == storage_id) \
                    .first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving storage location {storage_id} with items: {e}")
            raise DatabaseError(f"Failed to retrieve storage location {storage_id}")

    def get_available_storage(self) -> List[Storage]:
        """Get storage locations with available capacity.

        Returns:
            List[Storage]: List of storage locations with space available
        """
        try:
            with self.session_scope() as session:
                return session.query(Storage) \
                    .filter(Storage.available_capacity > 0) \
                    .all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving available storage: {e}")
            raise DatabaseError("Failed to retrieve available storage")

    def search_storage(self, term: str) -> List[Storage]:
        """Search storage locations by location or description.

        Args:
            term: Search term

        Returns:
            List[Storage]: List of matching storage locations
        """
        try:
            with self.session_scope() as session:
                search = f"%{term}%"
                return session.query(Storage) \
                    .filter(
                    or_(
                        Storage.location.ilike(search),
                        Storage.description.ilike(search)
                    )
                ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching storage locations: {e}")
            raise DatabaseError("Failed to search storage locations")

    def get_storage_status(self, storage_id: int) -> Dict[str, Any]:
        """Get detailed status of a storage location.

        Args:
            storage_id: ID of storage location

        Returns:
            Dict containing:
            - total_capacity: float
            - used_capacity: float
            - available_capacity: float
            - item_count: int
            - last_modified: datetime
        """
        try:
            with self.session_scope() as session:
                storage = session.query(Storage) \
                    .options(joinedload(Storage.items)) \
                    .filter(Storage.id == storage_id) \
                    .first()

                if not storage:
                    raise DatabaseError(f"Storage location {storage_id} not found")

                return {
                    'total_capacity': storage.capacity,
                    'used_capacity': storage.used_capacity,
                    'available_capacity': storage.available_capacity,
                    'item_count': len(storage.items),
                    'last_modified': storage.updated_at
                }
        except SQLAlchemyError as e:
            logger.error(f"Error getting storage status for {storage_id}: {e}")
            raise DatabaseError(f"Failed to get storage status for {storage_id}")

    def get_storage_utilization(self) -> List[Dict[str, Any]]:
        """Get utilization metrics for all storage locations.

        Returns:
            List of dictionaries containing utilization metrics for each location
        """
        try:
            with self.session_scope() as session:
                storages = session.query(Storage) \
                    .options(joinedload(Storage.items)) \
                    .all()

                return [{
                    'location': s.location,
                    'capacity': s.capacity,
                    'utilization': (s.used_capacity / s.capacity * 100) if s.capacity else 0,
                    'item_count': len(s.items)
                } for s in storages]
        except SQLAlchemyError as e:
            logger.error(f"Error getting storage utilization: {e}")
            raise DatabaseError("Failed to get storage utilization")

    def bulk_update_storage(self, updates: List[Dict[str, Any]]) -> int:
        """Update multiple storage locations in bulk.

        Args:
            updates: List of dictionaries containing:
                - id: Storage location ID
                - updates: Dictionary of fields to update

        Returns:
            int: Number of storage locations updated
        """
        try:
            updated = 0
            with self.session_scope() as session:
                for update in updates:
                    storage = session.query(Storage).get(update['id'])
                    if storage:
                        for key, value in update['updates'].items():
                            setattr(storage, key, value)
                        updated += 1
                session.commit()
                return updated
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk storage update: {e}")
            raise DatabaseError("Failed to perform bulk storage update")