# database/sqlalchemy/core/specialized/storage_manager.py
import logging
from typing import List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import select
from di.core import inject
from services.interfaces import MaterialService
from models.storage import Storage
from core.exceptions import DatabaseError
from core.base_manager import BaseManager


class StorageManager(BaseManager[Storage]):
    """
    Specialized manager for Storage model operations.

    This class extends BaseManager with storage-specific operations.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize the StorageManager.

        Args:
            session_factory (Callable[[], Session]): A factory function 
            that returns a SQLAlchemy Session.
        """
        super().__init__(Storage, session_factory)
        self._logger = logging.getLogger(self.__class__.__name__)

    @inject(MaterialService)
    def create_storage_location(self, storage_data: Dict[str, Any]) -> Storage:
        """
        Create a new storage location.

        Args:
            storage_data (Dict[str, Any]): Dictionary containing storage location information.

        Returns:
            Storage: The created Storage instance.

        Raises:
            DatabaseError: If storage location creation fails.
        """
        try:
            with self.session_scope() as session:
                # Validate required storage data
                if not storage_data:
                    raise ValueError("Storage data cannot be empty")

                storage = Storage(**storage_data)
                session.add(storage)
                session.commit()
                session.refresh(storage)
                return storage
        except Exception as e:
            self._logger.error(f'Error creating storage location: {e}')
            raise DatabaseError(f'Failed to create storage location: {str(e)}', str(e))

    @inject(MaterialService)
    def get_storage_by_id(self, storage_id: int) -> Optional[Storage]:
        """
        Retrieve a storage location by its ID.

        Args:
            storage_id (int): The ID of the storage location to retrieve.

        Returns:
            Optional[Storage]: The Storage instance if found, None otherwise.

        Raises:
            DatabaseError: If there's an error retrieving the storage location.
        """
        try:
            with self.session_scope() as session:
                return session.query(Storage).filter(Storage.id == storage_id).first()
        except Exception as e:
            self._logger.error(f'Error retrieving storage location with ID {storage_id}: {e}')
            raise DatabaseError(f'Failed to retrieve storage location', str(e))

    @inject(MaterialService)
    def get_all_storage_locations(self) -> List[Storage]:
        """
        Retrieve all storage locations.

        Returns:
            List[Storage]: A list of all Storage instances.

        Raises:
            DatabaseError: If there's an error retrieving storage locations.
        """
        try:
            with self.session_scope() as session:
                return session.query(Storage).all()
        except Exception as e:
            self._logger.error(f'Error retrieving all storage locations: {e}')
            raise DatabaseError('Failed to retrieve storage locations', str(e))

    @inject(MaterialService)
    def update_storage_location(self, storage_id: int, update_data: Dict[str, Any]) -> Optional[Storage]:
        """
        Update an existing storage location.

        Args:
            storage_id (int): The ID of the storage location to update.
            update_data (Dict[str, Any]): Dictionary containing fields to update.

        Returns:
            Optional[Storage]: The updated Storage instance, or None if not found.

        Raises:
            DatabaseError: If there's an error updating the storage location.
        """
        try:
            with self.session_scope() as session:
                storage = session.get(Storage, storage_id)

                if not storage:
                    self._logger.warning(f'Storage location with ID {storage_id} not found.')
                    return None

                # Update storage location attributes
                for key, value in update_data.items():
                    setattr(storage, key, value)

                session.commit()
                session.refresh(storage)
                return storage
        except Exception as e:
            self._logger.error(f'Error updating storage location {storage_id}: {e}')
            raise DatabaseError(f'Failed to update storage location', str(e))

    @inject(MaterialService)
    def delete_storage_location(self, storage_id: int) -> bool:
        """
        Delete a storage location by its ID.

        Args:
            storage_id (int): The ID of the storage location to delete.

        Returns:
            bool: True if the storage location was deleted, False otherwise.

        Raises:
            DatabaseError: If there's an error deleting the storage location.
        """
        try:
            with self.session_scope() as session:
                storage = session.get(Storage, storage_id)

                if not storage:
                    self._logger.warning(f'Storage location with ID {storage_id} not found.')
                    return False

                session.delete(storage)
                session.commit()
                return True
        except Exception as e:
            self._logger.error(f'Error deleting storage location {storage_id}: {e}')
            raise DatabaseError(f'Failed to delete storage location', str(e))

    @inject(MaterialService)
    def search_storage_locations(self, search_term: str) -> List[Storage]:
        """
        Search storage locations by name or description.

        Args:
            search_term (str): Term to search for in storage location names or descriptions.

        Returns:
            List[Storage]: List of matching storage locations.

        Raises:
            DatabaseError: If there's an error searching storage locations.
        """
        try:
            with self.session_scope() as session:
                return session.query(Storage).filter(
                    (Storage.name.ilike(f'%{search_term}%')) |
                    (Storage.description.ilike(f'%{search_term}%'))
                ).all()
        except Exception as e:
            self._logger.error(f'Error searching storage locations: {e}')
            raise DatabaseError('Failed to search storage locations', str(e))