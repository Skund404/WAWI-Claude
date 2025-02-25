# store_management/database/repositories/storage_repository.py
"""
Repository for Storage model database access.

Provides specialized operations for retrieving, creating, and managing
storage locations with advanced querying capabilities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces import InventoryService
from models.storage import Storage, StorageStatus

# Configure logging
logger = logging.getLogger(__name__)


class StorageRepository:
    """
    Repository for Storage model database operations.

    Provides methods to interact with storage locations, including
    retrieval, filtering, and comprehensive management.
    """

    @inject(InventoryService)
    def __init__(self, session):
        """
        Initialize the StorageRepository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_by_location(self, location: str) -> List[Storage]:
        """
        Retrieve storage locations by location string.

        Args:
            location (str): The location string to search for

        Returns:
            List[Storage]: Storage locations matching the location
        """
        try:
            return (
                self.session.query(Storage)
                .filter(Storage.location.ilike(f'%{location}%'))
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting storage locations by location '{location}': {e}")
            raise

    def get_available_storage(self) -> List[Storage]:
        """
        Retrieve available storage locations (not full and active).

        Returns:
            List[Storage]: Available storage locations
        """
        try:
            return (
                self.session.query(Storage)
                .filter(Storage.current_occupancy < Storage.capacity)
                .filter(Storage.status == StorageStatus.ACTIVE)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error getting available storage locations: {e}')
            raise

    def get_storage_with_details(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve storage details with comprehensive information.

        Args:
            storage_id (int): The ID of the storage location

        Returns:
            Optional[Dict[str, Any]]: Detailed storage information
        """
        try:
            storage = self.session.query(Storage).get(storage_id)

            if not storage:
                return None

            # Convert storage to dictionary
            result = {
                'id': storage.id,
                'name': storage.name,
                'location': storage.location,
                'capacity': storage.capacity,
                'current_occupancy': storage.current_occupancy,
                'type': storage.type,
                'status': storage.status,
                'occupancy_percentage': storage.occupancy_percentage()
            }

            # Add products if available
            if hasattr(storage, 'products') and storage.products:
                product_list = [
                    {
                        'id': product.id,
                        'name': product.name,
                        'sku': product.sku,
                        'quantity': product.stock_quantity
                    }
                    for product in storage.products
                ]
                result['products'] = product_list
                result['product_count'] = len(product_list)

            return result
        except SQLAlchemyError as e:
            logger.error(f'Error getting storage details for ID {storage_id}: {e}')
            raise

    def search_storage(self, search_term: str) -> List[Storage]:
        """
        Search for storage locations across multiple fields.

        Args:
            search_term (str): The search term

        Returns:
            List[Storage]: Storage locations matching the search criteria
        """
        try:
            return (
                self.session.query(Storage)
                .filter(
                    (Storage.name.ilike(f'%{search_term}%')) |
                    (Storage.location.ilike(f'%{search_term}%')) |
                    (Storage.type.ilike(f'%{search_term}%')) |
                    (Storage.description.ilike(f'%{search_term}%'))
                )
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error searching storage locations for '{search_term}': {e}")
            raise

    def create_storage(self, storage_data: Dict[str, Any]) -> Optional[Storage]:
        """
        Create a new storage location.

        Args:
            storage_data (Dict[str, Any]): Data for creating a storage location

        Returns:
            Optional[Storage]: Created storage location
        """
        try:
            # Validate required fields
            if not storage_data.get('name'):
                raise ValueError('Storage name is required')

            # Set default status if not provided
            if 'status' not in storage_data:
                storage_data['status'] = StorageStatus.ACTIVE

            # Create storage instance
            storage = Storage(**storage_data)

            # Add to session and commit
            self.session.add(storage)
            self.session.commit()

            logger.info(f'Created storage location: {storage.name}')
            return storage
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error creating storage location: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error creating storage: {e}')
            raise

    def update_storage(self, storage_id: int, storage_data: Dict[str, Any]) -> Optional[Storage]:
        """
        Update an existing storage location.

        Args:
            storage_id (int): ID of the storage location to update
            storage_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Storage]: Updated storage location
        """
        try:
            # Retrieve existing storage
            storage = self.session.query(Storage).get(storage_id)

            if not storage:
                logger.warning(f'Storage with ID {storage_id} not found for update')
                return None

            # Update attributes
            for key, value in storage_data.items():
                if hasattr(storage, key):
                    setattr(storage, key, value)
                else:
                    logger.warning(f'Attempted to set non-existent attribute {key} on Storage')

            # Commit changes
            self.session.commit()

            logger.info(f'Updated storage location: {storage.name}')
            return storage
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error updating storage location with ID {storage_id}: {e}')
            raise

    def get_storage_inventory_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive storage inventory summary.

        Returns:
            Dict[str, Any]: Storage inventory statistics
        """
        try:
            # Total storage locations
            total_storage = self.session.query(Storage).count()

            # Active storage locations
            active_storage = (
                self.session.query(Storage)
                .filter(Storage.status == StorageStatus.ACTIVE)
                .count()
            )

            # Storage locations by type
            storage_by_type = (
                self.session.query(Storage.type, func.count(Storage.id))
                .group_by(Storage.type)
                .all()
            )

            # Calculate total and average occupancy
            occupancy_stats = (
                self.session.query(
                    func.avg(Storage.current_occupancy / Storage.capacity * 100).label('avg_occupancy'),
                    func.sum(Storage.current_occupancy).label('total_occupancy'),
                    func.sum(Storage.capacity).label('total_capacity')
                )
                .first()
            )

            return {
                'total_storage_locations': total_storage,
                'active_storage_locations': active_storage,
                'storage_by_type': dict(storage_by_type),
                'average_occupancy_percentage': round(occupancy_stats.avg_occupancy,
                                                      2) if occupancy_stats.avg_occupancy else 0,
                'total_occupancy': occupancy_stats.total_occupancy,
                'total_capacity': occupancy_stats.total_capacity
            }
        except SQLAlchemyError as e:
            logger.error(f'Error generating storage inventory summary: {e}')
            raise