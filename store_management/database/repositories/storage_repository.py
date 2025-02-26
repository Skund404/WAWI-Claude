# Path: database/repositories/storage_repository.py

"""
Storage Repository for managing storage-related database operations.

Provides data access layer for storage entities in the leatherworking
store management application.
"""

import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.storage import Storage
from database.repositories.base_repository import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)


class StorageRepository(BaseRepository):
    """
    Repository for handling storage-related database operations.

    Extends the base repository with storage-specific methods.
    """

    def __init__(self, session: Session):
        """
        Initialize the storage repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Storage)

    def find_by_location(self, location: str) -> List[Storage]:
        """
        Find storage locations by specific location type.

        Args:
            location (str): Location type to search for

        Returns:
            List[Storage]: List of storage locations matching the criteria
        """
        try:
            return self.session.query(Storage).filter(
                Storage.location == location
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error finding storage by location {location}: {e}")
            raise

    def get_storage_utilization(self) -> List[Dict[str, Any]]:
        """
        Get storage utilization statistics.

        Returns:
            List[Dict[str, Any]]: Storage utilization details
        """
        try:
            # Example query to get storage utilization
            storage_query = self.session.query(
                Storage.location,
                Storage.capacity,
                Storage.current_usage
            ).all()

            return [
                {
                    "location": result[0],
                    "capacity": result[1],
                    "current_usage": result[2],
                    "utilization_percentage": (result[2] / result[1]) * 100
                    if result[1] > 0 else 0
                }
                for result in storage_query
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving storage utilization: {e}")
            raise

    def create_storage_location(self,
                                location_data: Dict[str, Any]) -> Storage:
        """
        Create a new storage location.

        Args:
            location_data (Dict[str, Any]): Data for the new storage location

        Returns:
            Storage: The newly created storage location

        Raises:
            ValueError: If required data is missing
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate required fields
            required_fields = ['location', 'capacity']
            for field in required_fields:
                if field not in location_data:
                    raise ValueError(f"Missing required field: {field}")

            # Create new storage location
            new_storage = Storage(**location_data)

            # Add and commit
            self.session.add(new_storage)
            self.session.commit()

            logger.info(f"Created new storage location: {new_storage}")
            return new_storage

        except (ValueError, SQLAlchemyError) as e:
            self.session.rollback()
            logger.error(f"Failed to create storage location: {e}")
            raise