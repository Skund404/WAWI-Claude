from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/database_service.py

Database service for high-level database operations.
"""
logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for high-level database operations.

    This class provides methods for common database operations across models.
    """

    @inject(MaterialService)
        def __init__(self):
        """Initialize a new DatabaseService instance."""
        self._session_factory = get_db_session

        @contextmanager
    @inject(MaterialService)
        def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Yields:
            SQLAlchemy session.
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f'Database transaction error: {str(e)}')
            raise
        finally:
            session.close()

        @inject(MaterialService)
            def get_repository(self, model_name: str, session: Session
                           ) -> BaseRepository:
        """
        Get a repository for a model.

        Args:
            model_name: The name of the model.
            session: SQLAlchemy session.

        Returns:
            A repository for the model.
        """
        return RepositoryFactory.get_repository(model_name, session)

        @inject(MaterialService)
            def create(self, model_name: str, data: Dict[str, Any]) -> Optional[Any]:
        """
        Create a new model instance.

        Args:
            model_name: The name of the model.
            data: Dictionary of data for the model.

        Returns:
            The created model instance, or None if creation failed.
        """
        try:
            with self.session_scope() as session:
                repository = self.get_repository(model_name, session)
                return repository.create(data)
        except Exception as e:
            logger.error(f'Error creating {model_name}: {str(e)}')
            return None

        @inject(MaterialService)
            def get_by_id(self, model_name: str, id: int) -> Optional[Any]:
        """
        Get a model instance by ID.

        Args:
            model_name: The name of the model.
            id: The ID of the model instance.

        Returns:
            The model instance, or None if not found.
        """
        try:
            with self.session_scope() as session:
                repository = self.get_repository(model_name, session)
                return repository.get_by_id(id)
        except Exception as e:
            logger.error(f'Error getting {model_name} with ID {id}: {str(e)}')
            return None

        @inject(MaterialService)
            def get_all(self, model_name: str, limit: Optional[int] = None, offset:
                    Optional[int] = None) -> List[Any]:
        """
        Get all instances of a model.

        Args:
            model_name: The name of the model.
            limit: Maximum number of instances to return.
            offset: Number of instances to skip.

        Returns:
            List of model instances.
        """
        try:
            with self.session_scope() as session:
                repository = self.get_repository(model_name, session)
                return repository.get_all(limit, offset)
        except Exception as e:
            logger.error(f'Error getting all {model_name} instances: {str(e)}')
            return []

        @inject(MaterialService)
            def update(self, model_name: str, id: int, data: Dict[str, Any]
                   ) -> Optional[Any]:
        """
        Update a model instance.

        Args:
            model_name: The name of the model.
            id: The ID of the model instance.
            data: Dictionary of data to update.

        Returns:
            The updated model instance, or None if update failed.
        """
        try:
            with self.session_scope() as session:
                repository = self.get_repository(model_name, session)
                return repository.update(id, data)
        except Exception as e:
            logger.error(f'Error updating {model_name} with ID {id}: {str(e)}')
            return None

        @inject(MaterialService)
            def delete(self, model_name: str, id: int) -> bool:
        """
        Delete a model instance.

        Args:
            model_name: The name of the model.
            id: The ID of the model instance.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            with self.session_scope() as session:
                repository = self.get_repository(model_name, session)
                return repository.delete(id)
        except Exception as e:
            logger.error(f'Error deleting {model_name} with ID {id}: {str(e)}')
            return False

        @inject(MaterialService)
            def search(self, model_name: str, search_term: str, fields: List[str]
                   ) -> List[Any]:
        """
        Search for model instances.

        Args:
            model_name: The name of the model.
            search_term: The search term.
            fields: List of fields to search in.

        Returns:
            List of model instances that match the search criteria.
        """
        try:
            with self.session_scope() as session:
                repository = self.get_repository(model_name, session)
                return repository.search(search_term, fields)
        except Exception as e:
            logger.error(
                f"Error searching {model_name} for '{search_term}': {str(e)}")
            return []

        @inject(MaterialService)
            def execute_custom_query(self, callback, *args, **kwargs) -> Any:
        """
        Execute a custom database query.

        Args:
            callback: Function that takes a session and executes a query.
            *args: Arguments to pass to the callback.
            **kwargs: Keyword arguments to pass to the callback.

        Returns:
            The result of the callback.
        """
        try:
            with self.session_scope() as session:
                return callback(session, *args, **kwargs)
        except Exception as e:
            logger.error(f'Error executing custom query: {str(e)}')
            raise


db_service = DatabaseService()
