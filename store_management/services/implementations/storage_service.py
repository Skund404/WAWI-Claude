from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Concrete implementation of the IStorageService interface.

This module provides a comprehensive implementation of storage-related
operations using the dependency injection pattern and repository pattern.
"""


class StorageService(Service, IStorageService):
    """
    Concrete implementation of the IStorageService interface.

    This service provides methods for managing storage locations with
    dependency injection, error handling, and validation.

    Attributes:
        _storage_repository (StorageRepository): Repository for storage-related database operations
    """

    @inject(MaterialService)
        def __init__(self, container):
        """
        Initialize the StorageService with a dependency injection container.

        Args:
            container: Dependency injection container
        """
        super().__init__(container)
        self._storage_repository = self.get_dependency(StorageRepository)
        self._logger = logging.getLogger(__name__)

        @inject(MaterialService)
            def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Retrieve all storage locations from the system.

        Returns:
            List[Dict[str, Any]]: A list of storage locations with their details.

        Raises:
            ApplicationError: If retrieval fails due to database or system errors.
        """
        try:
            storage_locations = self._storage_repository.get_all()
            return [self._to_dict(location) for location in storage_locations]
        except Exception as e:
            self._logger.error(f'Error retrieving storage locations: {str(e)}')
            raise ApplicationError('Failed to retrieve storage locations'
                                   ) from e

        @inject(MaterialService)
            def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific storage location by its unique identifier.

        Args:
            storage_id (int): The unique identifier of the storage location.

        Returns:
            Optional[Dict[str, Any]]: Details of the storage location if found,
                                      None otherwise.

        Raises:
            ValidationError: If the storage_id is invalid.
            ApplicationError: If retrieval fails due to database or system errors.
        """
        try:
            if not isinstance(storage_id, int) or storage_id <= 0:
                raise ValidationError('Invalid storage ID')
            storage = self._storage_repository.get(storage_id)
            return self._to_dict(storage) if storage else None
        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(
                f'Error retrieving storage location {storage_id}: {str(e)}')
            raise ApplicationError(
                f'Failed to retrieve storage location {storage_id}') from e

        @inject(MaterialService)
            def create_storage_location(self, storage_data: Dict[str, Any]) -> Dict[
                str, Any]:
        """
        Create a new storage location in the system.

        Args:
            storage_data (Dict[str, Any]): Data for the new storage location.

        Returns:
            Dict[str, Any]: Details of the created storage location.

        Raises:
            ValidationError: If the provided storage data is invalid.
            ApplicationError: If creation fails due to database or system errors.
        """
        try:
            self._validate_storage_data(storage_data)
            new_storage = self._storage_repository.create(storage_data)
            self._logger.info(f'Created new storage location: {new_storage.id}'
                              )
            return self._to_dict(new_storage)
        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f'Error creating storage location: {str(e)}')
            raise ApplicationError('Failed to create storage location') from e

        @inject(MaterialService)
            def update_storage_location(self, storage_id: int, storage_data: Dict[
                str, Any]) -> Dict[str, Any]:
        """
        Update an existing storage location.

        Args:
            storage_id (int): Unique identifier of the storage location to update.
            storage_data (Dict[str, Any]): Updated data for the storage location.

        Returns:
            Dict[str, Any]: Updated details of the storage location.

        Raises:
            ValidationError: If the storage_id is invalid or storage data is incomplete.
            ApplicationError: If update fails due to database or system errors.
        """
        try:
            if not isinstance(storage_id, int) or storage_id <= 0:
                raise ValidationError('Invalid storage ID')
            self._validate_storage_data(storage_data, is_update=True)
            updated_storage = self._storage_repository.update(storage_id,
                                                              storage_data)
            if not updated_storage:
                raise ApplicationError(
                    f'Storage location {storage_id} not found')
            self._logger.info(f'Updated storage location: {storage_id}')
            return self._to_dict(updated_storage)
        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(
                f'Error updating storage location {storage_id}: {str(e)}')
            raise ApplicationError(
                f'Failed to update storage location {storage_id}') from e

        @inject(MaterialService)
            def delete_storage_location(self, storage_id: int) -> bool:
        """
        Delete a storage location from the system.

        Args:
            storage_id (int): Unique identifier of the storage location to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.

        Raises:
            ValidationError: If the storage_id is invalid.
            ApplicationError: If deletion fails due to existing dependencies or system errors.
        """
        try:
            if not isinstance(storage_id, int) or storage_id <= 0:
                raise ValidationError('Invalid storage ID')
            deletion_result = self._storage_repository.delete(storage_id)
            if deletion_result:
                self._logger.info(f'Deleted storage location: {storage_id}')
            else:
                self._logger.warning(
                    f'Storage location {storage_id} not found for deletion')
            return deletion_result
        except Exception as e:
            self._logger.error(
                f'Error deleting storage location {storage_id}: {str(e)}')
            raise ApplicationError(
                f'Failed to delete storage location {storage_id}') from e

        @inject(MaterialService)
            def search_storage_locations(self, search_term: str) -> List[Dict[str, Any]
                                                                     ]:
        """
        Search for storage locations based on a search term.

        Args:
            search_term (str): Term to search for in storage locations.

        Returns:
            List[Dict[str, Any]]: List of storage locations matching the search term.

        Raises:
            ValidationError: If the search term is empty or invalid.
            ApplicationError: If search fails due to database or system errors.
        """
        try:
            if not search_term or not isinstance(search_term, str):
                raise ValidationError('Invalid search term')
            search_results = self._storage_repository.search_storage(
                search_term)
            return [self._to_dict(result) for result in search_results]
        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(f'Error searching storage locations: {str(e)}')
            raise ApplicationError('Failed to search storage locations') from e

        @inject(MaterialService)
            def get_storage_status(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a specific storage location.

        Args:
            storage_id (int): Unique identifier of the storage location.

        Returns:
            Optional[Dict[str, Any]]: Dictionary with storage status information
                                      or None if not found.

        Raises:
            ValidationError: If the storage_id is invalid.
            ApplicationError: If status retrieval fails due to database or system errors.
        """
        try:
            if not isinstance(storage_id, int) or storage_id <= 0:
                raise ValidationError('Invalid storage ID')
            storage_status = self._storage_repository.get_storage_with_details(
                storage_id)
            if not storage_status:
                return None
            return self._to_dict(storage_status)
        except ValidationError:
            raise
        except Exception as e:
            self._logger.error(
                f'Error retrieving storage status for {storage_id}: {str(e)}')
            raise ApplicationError(
                f'Failed to retrieve storage status for {storage_id}') from e

        @inject(MaterialService)
            def _to_dict(self, storage) -> Dict[str, Any]:
        """
        Convert a storage model instance to a dictionary.

        Args:
            storage: Storage model instance

        Returns:
            Dict[str, Any]: Dictionary representation of the storage
        """
        return {'id': storage.id, 'name': storage.name, 'location': storage
                .location, 'capacity': storage.capacity, 'current_occupancy':
                storage.current_occupancy, 'type': storage.type, 'description':
                storage.description, 'status': storage.status}

        @inject(MaterialService)
            def _validate_storage_data(self, storage_data: Dict[str, Any],
                                   is_update: bool = False):
        """
        Validate storage location data before creation or update.

        Args:
            storage_data (Dict[str, Any]): Storage location data to validate
            is_update (bool, optional): Whether this is an update operation. Defaults to False.

        Raises:
            ValidationError: If the storage data is invalid
        """
        required_fields = ['name', 'location', 'capacity']
        if not is_update:
            for field in required_fields:
                if field not in storage_data or not storage_data[field]:
                    raise ValidationError(f'Missing required field: {field}')
        if 'capacity' in storage_data:
            try:
                capacity = float(storage_data['capacity'])
                if capacity < 0:
                    raise ValidationError(
                        'Capacity must be a non-negative number')
            except (TypeError, ValueError):
                raise ValidationError('Capacity must be a valid number')
        if 'type' in storage_data and not storage_data['type']:
            raise ValidationError('Storage type cannot be empty')
