from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """
    Abstract base service providing a generic implementation of CRUD operations.

    This service acts as an intermediate layer between the repository
    and the application logic, adding additional validation, error handling,
    and business logic capabilities.

    Attributes:
        _repository (IBaseRepository): The repository for data access
        _unit_of_work (IUnitOfWork): Unit of work for transaction management
        _logger (logging.Logger): Logger for the service
    """

        @inject(MaterialService)
        def __init__(self, repository: IBaseRepository[T], unit_of_work:
        Optional[IUnitOfWork]=None):
        """
        Initialize the base service with a repository and optional unit of work.

        Args:
            repository (IBaseRepository[T]): Repository for data access
            unit_of_work (Optional[IUnitOfWork], optional): Unit of work for transactions
        """
        self._repository = repository
        self._unit_of_work = unit_of_work
        self._logger = logging.getLogger(self.__class__.__name__)

        @inject(MaterialService)
        def get_by_id(self, id: Any) ->Optional[T]:
        """
        Retrieve an entity by its unique identifier.

        Args:
            id (Any): The unique identifier of the entity

        Returns:
            Optional[T]: The retrieved entity

        Raises:
            NotFoundError: If no entity is found with the given ID
        """
        try:
            entity = self._repository.get_by_id(id)
            if not entity:
                raise NotFoundError(f'Entity with ID {id} not found', {'id':
                    id})
            return entity
        except Exception as e:
            self._logger.error(f'Error retrieving entity by ID {id}: {e}')
            raise ApplicationError(f'Failed to retrieve entity: {str(e)}',
                {'id': id})

        @inject(MaterialService)
        def get_all(self, limit: Optional[int]=None, offset: Optional[int]=None
        ) ->List[T]:
        """
        Retrieve all entities with optional pagination.

        Args:
            limit (Optional[int], optional): Maximum number of entities to return
            offset (Optional[int], optional): Number of entities to skip

        Returns:
            List[T]: A list of entities
        """
        try:
            return self._repository.get_all(limit=limit, offset=offset)
        except Exception as e:
            self._logger.error(f'Error retrieving all entities: {e}')
            raise ApplicationError('Failed to retrieve entities', {})

        @inject(MaterialService)
        def create(self, data: Dict[str, Any]) ->T:
        """
        Create a new entity.

        Args:
            data (Dict[str, Any]): Data to create the entity

        Returns:
            T: The created entity

        Raises:
            ValidationError: If the data fails validation
        """
        try:
            self._validate_create_data(data)
            if self._unit_of_work:
                with self._unit_of_work:
                    entity = self._repository.add(data)
                    self._unit_of_work.commit()
                    return entity
            else:
                return self._repository.add(data)
        except ValidationError as ve:
            self._logger.warning(f'Validation error creating entity: {ve}')
            raise
        except Exception as e:
            self._logger.error(f'Error creating entity: {e}')
            raise ApplicationError(f'Failed to create entity: {str(e)}', {
                'input_data': data})

        @inject(MaterialService)
        def update(self, id: Any, data: Dict[str, Any]) ->T:
        """
        Update an existing entity.

        Args:
            id (Any): The unique identifier of the entity to update
            data (Dict[str, Any]): Updated data for the entity

        Returns:
            T: The updated entity

        Raises:
            NotFoundError: If the entity doesn't exist
            ValidationError: If the update data is invalid
        """
        try:
            existing_entity = self.get_by_id(id)
            self._validate_update_data(existing_entity, data)
            if self._unit_of_work:
                with self._unit_of_work:
                    updated_entity = self._repository.update(id, data)
                    self._unit_of_work.commit()
                    return updated_entity
            else:
                return self._repository.update(id, data)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self._logger.error(f'Error updating entity {id}: {e}')
            raise ApplicationError(f'Failed to update entity: {str(e)}', {
                'id': id, 'input_data': data})

        @inject(MaterialService)
        def delete(self, id: Any) ->bool:
        """
        Delete an entity by its identifier.

        Args:
            id (Any): The unique identifier of the entity to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the entity doesn't exist
        """
        try:
            self.get_by_id(id)
            if self._unit_of_work:
                with self._unit_of_work:
                    result = self._repository.delete(id)
                    self._unit_of_work.commit()
                    return result
            else:
                return self._repository.delete(id)
        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(f'Error deleting entity {id}: {e}')
            raise ApplicationError(f'Failed to delete entity: {str(e)}', {
                'id': id})

        @abstractmethod
    @inject(MaterialService)
    def _validate_create_data(self, data: Dict[str, Any]) ->None:
        """
        Abstract method to validate data before entity creation.

        Subclasses must implement specific validation logic.

        Args:
            data (Dict[str, Any]): Data to be validated

        Raises:
            ValidationError: If data is invalid
        """
        pass

        @abstractmethod
    @inject(MaterialService)
    def _validate_update_data(self, existing_entity: T, update_data: Dict[
        str, Any]) ->None:
        """
        Abstract method to validate data before entity update.

        Subclasses must implement specific validation logic.

        Args:
            existing_entity (T): The existing entity
            update_data (Dict[str, Any]): Data to be validated

        Raises:
            ValidationError: If data is invalid
        """
        pass

        @inject(MaterialService)
        def search(self, search_term: str, fields: Optional[List[str]]=None
        ) ->List[T]:
        """
        Search for entities based on a search term.

        Args:
            search_term (str): Term to search for
            fields (Optional[List[str]], optional): Fields to search in

        Returns:
            List[T]: List of matching entities
        """
        try:
            if hasattr(self._repository, 'search'):
                return self._repository.search(search_term, fields)
            else:
                self._logger.warning('Search not supported by repository')
                return []
        except Exception as e:
            self._logger.error(f'Error searching entities: {e}')
            raise ApplicationError(f'Failed to search entities: {str(e)}',
                {'search_term': search_term, 'fields': fields})
