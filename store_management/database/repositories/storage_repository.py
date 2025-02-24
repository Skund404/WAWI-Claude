from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/repositories/storage_repository.py

Storage repository for database access.
"""
logger = logging.getLogger(__name__)


class StorageRepository(BaseRepository):
    """
    Repository for Storage model database access.

    This class provides specialized operations for the Storage model.
    """

    @inject(MaterialService)
        def __init__(self, session: Session):
        """
        Initialize a new StorageRepository instance.

        Args:
            session: SQLAlchemy session.
        """
        super().__init__(session, Storage)

        @inject(MaterialService)
            def get_by_location(self, location: str) -> List[Storage]:
        """
        Get storage locations by location string.

        Args:
            location: The location string to search for.

        Returns:
            List of storage locations that match the location.
        """
        try:
            return self.session.query(Storage).filter(Storage.location.
                                                      ilike(f'%{location}%')).all()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting storage locations by location '{location}': {str(e)}"
            )
            return []

        @inject(MaterialService)
            def get_available_storage(self) -> List[Storage]:
        """
        Get available storage locations (not full).

        Returns:
            List of available storage locations.
        """
        try:
            return self.session.query(Storage).filter(Storage.
                                                      current_occupancy < Storage.capacity).filter(Storage.status ==
                                                                                                   'Active').all()
        except SQLAlchemyError as e:
            logger.error(f'Error getting available storage locations: {str(e)}'
                         )
            return []

        @inject(MaterialService)
            def get_storage_with_details(self, storage_id: int) -> Optional[Dict[str,
                                                                             Any]]:
        """
        Get storage with detailed information including products.

        Args:
            storage_id: The ID of the storage location.

        Returns:
            Dictionary with storage details, or None if storage not found.
        """
        try:
            storage = self.get_by_id(storage_id)
            if not storage:
                return None
            result = storage.to_dict() if hasattr(storage, 'to_dict') else {
                'id': storage.id, 'name': storage.name, 'location': storage
                .location, 'capacity': storage.capacity,
                'current_occupancy': storage.current_occupancy, 'type':
                storage.type, 'status': storage.status,
                'occupancy_percentage': storage.occupancy_percentage()}
            if hasattr(storage, 'products') and storage.products:
                product_list = []
                for product in storage.products:
                    product_list.append({'id': product.id, 'name': product.
                                         name, 'sku': product.sku, 'quantity': product.
                                         stock_quantity})
                result['products'] = product_list
                result['product_count'] = len(product_list)
            return result
        except Exception as e:
            logger.error(
                f'Error getting storage details for ID {storage_id}: {str(e)}')
            return None

        @inject(MaterialService)
            def search_storage(self, search_term: str) -> List[Storage]:
        """
        Search for storage locations by name, location, or type.

        Args:
            search_term: The search term.

        Returns:
            List of storage locations that match the search criteria.
        """
        try:
            return self.search(search_term, ['name', 'location', 'type',
                                             'description'])
        except Exception as e:
            logger.error(
                f"Error searching storage locations for '{search_term}': {str(e)}"
            )
            return []

        @inject(MaterialService)
            def create(self, data: Dict[str, Any]) -> Optional[Storage]:
        """
        Create a new storage location.

        Args:
            data: Dictionary of storage data.

        Returns:
            The created storage location, or None if creation failed.
        """
        try:
            if 'name' not in data or not data['name']:
                raise ValueError('Storage name is required')
            storage = Storage(**data)
            self.session.add(storage)
            self.session.flush()
            logger.info(f'Created storage location: {storage.name}')
            return storage
        except Exception as e:
            logger.error(f'Error creating storage location: {str(e)}')
            self.session.rollback()
            return None

        @inject(MaterialService)
            def update(self, storage_id: int, data: Dict[str, Any]) -> Optional[Storage
                                                                            ]:
        """
        Update a storage location.

        Args:
            storage_id: The ID of the storage location to update.
            data: Dictionary of storage data to update.

        Returns:
            The updated storage location, or None if update failed.
        """
        try:
            storage = self.get_by_id(storage_id)
            if not storage:
                logger.warning(
                    f'Storage with ID {storage_id} not found for update')
                return None
            for key, value in data.items():
                if hasattr(storage, key):
                    setattr(storage, key, value)
            self.session.flush()
            logger.info(f'Updated storage location: {storage.name}')
            return storage
        except Exception as e:
            logger.error(
                f'Error updating storage location with ID {storage_id}: {str(e)}'
            )
            self.session.rollback()
            return None
