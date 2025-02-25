# Path: database/sqlalchemy/managers/storage_manager.py

import logging
from typing import Dict, Any, Union, List, Optional, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from models import Storage, Product
from core.exceptions import DatabaseError


class StorageManager:
    """
    Manager class for storage-related database operations.

    Provides comprehensive methods for managing storage locations,
    tracking inventory, and performing storage-related queries.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize StorageManager with session factory.

        Args:
            session_factory (Callable[[], Session]): Factory function to create database sessions
        """
        self.session_factory = session_factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: Database session
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all_storage_locations(self) -> List[Storage]:
        """
        Retrieve all storage locations from the database.

        Returns:
            List[Storage]: List of all storage locations

        Raises:
            DatabaseError: If database retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Storage)
                result = session.execute(query).scalars().all()
                return list(result)
        except SQLAlchemyError as e:
            error_msg = f'Failed to retrieve storage locations: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def add_storage_location(self, data: Dict[str, Any]) -> Storage:
        """
        Add a new storage location.

        Args:
            data (Dict[str, Any]): Storage location data to create

        Returns:
            Storage: The newly created Storage instance

        Raises:
            DatabaseError: If storage location creation fails
        """
        try:
            with self.session_scope() as session:
                # Validate required fields
                required_fields = ['name', 'location']
                missing_fields = [field for field in required_fields if field not in data]

                if missing_fields:
                    raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

                # Create storage location
                storage = Storage(**data)
                storage.used_capacity = 0  # Initialize used capacity

                session.add(storage)
                return storage
        except (SQLAlchemyError, ValueError) as e:
            error_msg = f'Failed to add storage location: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def update_storage_location(self, location_id: Union[int, str], data: Dict[str, Any]) -> Optional[Storage]:
        """
        Update an existing storage location.

        Args:
            location_id (Union[int, str]): ID of the storage location to update
            data (Dict[str, Any]): Updated storage data

        Returns:
            Optional[Storage]: The updated Storage instance or None if not found

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                storage = session.get(Storage, location_id)

                if not storage:
                    self.logger.warning(f"Storage location {location_id} not found")
                    return None

                # Update storage attributes
                for key, value in data.items():
                    setattr(storage, key, value)

                # Update modification timestamp if available
                if hasattr(storage, 'modified_at'):
                    storage.modified_at = datetime.now()

                return storage
        except SQLAlchemyError as e:
            error_msg = f'Failed to update storage location {location_id}: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def delete_storage_location(self, location_id: Union[int, str]) -> bool:
        """
        Delete a storage location.

        Args:
            location_id (Union[int, str]): ID of the storage location to delete

        Returns:
            bool: True if deleted successfully, False if not found

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            with self.session_scope() as session:
                storage = session.get(Storage, location_id)

                if not storage:
                    self.logger.warning(f"Storage location {location_id} not found")
                    return False

                # Check if storage location has any products
                product_count = session.query(Product).filter(Product.storage_id == location_id).count()
                if product_count > 0:
                    raise ValueError(f"Cannot delete storage location {location_id} with {product_count} products")

                session.delete(storage)
                return True
        except SQLAlchemyError as e:
            error_msg = f'Failed to delete storage location {location_id}: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_storage_with_items(self, storage_id: Union[int, str]) -> Optional[Storage]:
        """
        Retrieve a storage location with all its associated items.

        Args:
            storage_id (Union[int, str]): ID of the storage location

        Returns:
            Optional[Storage]: Storage instance with loaded relationships or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = (
                    select(Storage)
                    .options(joinedload(Storage.products))
                    .filter(Storage.id == storage_id)
                )
                result = session.execute(query).scalar_one_or_none()
                return result
        except SQLAlchemyError as e:
            error_msg = f'Failed to get storage {storage_id} with items: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_available_storage(self) -> List[Storage]:
        """
        Retrieve storage locations with available capacity.

        Returns:
            List[Storage]: List of storage locations with available space

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Storage).filter(Storage.capacity > Storage.used_capacity)
                result = session.execute(query).scalars().all()
                return list(result)
        except SQLAlchemyError as e:
            error_msg = f'Failed to get available storage locations: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def search_storage(self, term: str) -> List[Storage]:
        """
        Search for storage locations by name, description, or location.

        Args:
            term (str): Search term

        Returns:
            List[Storage]: List of matching storage locations

        Raises:
            DatabaseError: If search fails
        """
        try:
            with self.session_scope() as session:
                search_pattern = f'%{term}%'
                query = select(Storage).filter(
                    or_(
                        Storage.name.ilike(search_pattern),
                        Storage.description.ilike(search_pattern),
                        Storage.location.ilike(search_pattern)
                    )
                )
                result = session.execute(query).scalars().all()
                return list(result)
        except SQLAlchemyError as e:
            error_msg = f'Failed to search storage locations: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_storage_status(self, storage_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieve detailed status information about a storage location.

        Args:
            storage_id (Union[int, str]): ID of the storage location

        Returns:
            Dict[str, Any]: Dictionary with storage status information

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                storage = session.get(Storage, storage_id)

                if not storage:
                    return {}

                # Count products in this storage
                product_count = session.query(Product).filter(Product.storage_id == storage_id).count()

                # Calculate utilization
                utilization = 0
                if hasattr(storage, 'capacity') and storage.capacity > 0:
                    utilization = getattr(storage, 'used_capacity', 0) / storage.capacity * 100

                return {
                    'id': storage.id,
                    'name': storage.name,
                    'location': getattr(storage, 'location', ''),
                    'product_count': product_count,
                    'capacity': getattr(storage, 'capacity', 0),
                    'used': getattr(storage, 'used_capacity', 0),
                    'utilization': utilization,
                    'status': 'active'
                }
        except SQLAlchemyError as e:
            error_msg = f'Failed to get storage status for {storage_id}: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_storage_utilization(self) -> List[Dict[str, Any]]:
        """
        Retrieve utilization information for all storage locations.

        Returns:
            List[Dict[str, Any]]: List of storage utilization data

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                storage_list = session.query(Storage).all()

                result = []
                for storage in storage_list:
                    # Calculate utilization
                    utilization = 0
                    if hasattr(storage, 'capacity') and storage.capacity > 0:
                        utilization = getattr(storage, 'used_capacity', 0) / storage.capacity * 100

                    result.append({
                        'id': storage.id,
                        'name': storage.name,
                        'location': getattr(storage, 'location', ''),
                        'capacity': getattr(storage, 'capacity', 0),
                        'used': getattr(storage, 'used_capacity', 0),
                        'utilization': utilization
                    })

                return result
        except SQLAlchemyError as e:
            error_msg = f'Failed to get storage utilization: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def bulk_update_storage(self, updates: List[Dict[str, Any]]) -> List[Storage]:
        """
        Perform bulk updates on multiple storage locations.

        Args:
            updates (List[Dict[str, Any]]): List of storage updates, each containing 'id' field

        Returns:
            List[Storage]: List of updated Storage instances

        Raises:
            DatabaseError: If bulk update fails
        """
        try:
            with self.session_scope() as session:
                updated_storage = []

                for update_data in updates:
                    # Extract storage ID from update data
                    storage_id = update_data.pop('id')

                    # Find and update storage
                    storage = session.get(Storage, storage_id)
                    if storage:
                        # Update storage attributes
                        for key, value in update_data.items():
                            setattr(storage, key, value)

                        # Update modification timestamp if available
                        if hasattr(storage, 'modified_at'):
                            storage.modified_at = datetime.now()

                        updated_storage.append(storage)

                return updated_storage
        except SQLAlchemyError as e:
            error_msg = f'Failed to bulk update storage locations: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='storage_manager.log'
)

# Additional imports for completeness
import logging
from datetime import datetime
from sqlalchemy import or_
from core.exceptions import DatabaseError
from models import Storage, Product