# File: database/repositories/storage_repository.py
# Purpose: Storage repository refactored to use new manager pattern

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from database.sqlalchemy.base_manager import BaseManager
from database.models.storage import Storage
from database.sqlalchemy.manager_factory import register_specialized_manager


class StorageRepository(BaseManager[Storage]):
    """
    Specialized repository for Storage model with additional methods.

    Provides storage-specific operations beyond standard CRUD methods.
    """

    def get_by_location(self, location: str) -> Optional[Storage]:
        """
        Retrieve a storage location by its specific location.

        Args:
            location: The location identifier

        Returns:
            Storage instance if found, None otherwise
        """
        results = self.filter_by_multiple({'location': location})
        return results[0] if results else None

    def get_available_storage(self) -> List[Storage]:
        """
        Retrieve all available storage locations.

        Returns:
            List of available storage locations
        """
        return self.filter_by_multiple({'status': 'available'})

    def get_storage_with_details(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            Dictionary with storage details, or None if not found
        """
        with self.session_factory() as session:
            try:
                # Retrieve storage with additional details
                query = select(Storage).where(Storage.id == storage_id)
                storage = session.execute(query).scalar_one_or_none()

                if not storage:
                    return None

                # You can add more complex logic here to fetch related data
                return {
                    'id': storage.id,
                    'location': storage.location,
                    'capacity': storage.capacity,
                    'current_usage': storage.current_usage,
                    'status': storage.status
                }
            except Exception as e:
                # Use error handling from previous implementation
                from store_management.utils.error_handling import handle_database_error
                raise handle_database_error("get_storage_with_details", e)

    def search_storage(self, search_term: str) -> List[Storage]:
        """
        Search storage locations by location or description.

        Args:
            search_term: Term to search for

        Returns:
            List of matching storage locations
        """
        return self.search(search_term, fields=['location', 'description'])


# Register the specialized manager
register_specialized_manager(Storage, StorageRepository)


# Optional: Create a function for backward compatibility
def get_storage_repository(session: Optional[Session] = None) -> StorageRepository:
    """
    Backward-compatible method to get a storage repository.

    Args:
        session: Optional SQLAlchemy session (for backward compatibility)

    Returns:
        StorageRepository instance
    """
    from store_management.database.sqlalchemy.session import get_db_session

    # If a session is provided, create a custom session factory
    if session:
        def session_factory():
            return session
    else:
        session_factory = get_db_session

    return StorageRepository(
        model_class=Storage,
        session_factory=session_factory
    )