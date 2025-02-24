from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Base Manager for creating specialized database managers with generic operations.
"""
T = TypeVar('T')


class BaseManager(Generic[T]):
    """
    A generic base manager for database operations.

    Provides common CRUD (Create, Read, Update, Delete) operations 
    for different model types.

    Attributes:
        _session_factory (callable): Factory function to create database sessions
        _model_class (Type[T]): The SQLAlchemy model class managed by this manager
    """

    @inject(MaterialService)
        def __init__(self, model_class: Type[T], session_factory: Any):
        """
        Initialize the BaseManager.

        Args:
            model_class (Type[T]): The SQLAlchemy model class to manage
            session_factory (Any): A factory function to create database sessions
        """
        self._model_class = model_class
        self._session_factory = session_factory

        @inject(MaterialService)
            def _get_session(self) -> Session:
        """
        Retrieve a database session.

        Returns:
            Session: A database session
        """
        return self._session_factory()

        @inject(MaterialService)
            def create(self, data: dict) -> T:
        """
        Create a new record.

        Args:
            data (dict): Dictionary of attributes for the new record

        Returns:
            T: The created model instance
        """
        session = self._get_session()
        try:
            model_instance = self._model_class(**data)
            session.add(model_instance)
            session.commit()
            return model_instance
        except SQLAlchemyError as e:
            session.rollback()
            raise ValueError(
                f'Error creating {self._model_class.__name__}: {str(e)}')
        finally:
            session.close()

        @inject(MaterialService)
            def get(self, id: int) -> Optional[T]:
        """
        Retrieve a record by its ID.

        Args:
            id (int): The unique identifier of the record

        Returns:
            Optional[T]: The retrieved model instance or None
        """
        session = self._get_session()
        try:
            return session.query(self._model_class).get(id)
        except SQLAlchemyError as e:
            raise ValueError(
                f'Error retrieving {self._model_class.__name__}: {str(e)}')
        finally:
            session.close()

        @inject(MaterialService)
            def get_all(self, order_by: Optional[str] = None, limit: Optional[int] = None
                    ) -> List[T]:
        """
        Retrieve all records, with optional ordering and limiting.

        Args:
            order_by (Optional[str], optional): Column to order by
            limit (Optional[int], optional): Maximum number of records to return

        Returns:
            List[T]: List of model instances
        """
        session = self._get_session()
        try:
            query = session.query(self._model_class)
            if order_by:
                query = query.order_by(getattr(self._model_class, order_by))
            if limit:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            raise ValueError(
                f'Error retrieving {self._model_class.__name__} records: {str(e)}'
            )
        finally:
            session.close()

        @inject(MaterialService)
            def update(self, id: int, data: dict) -> Optional[T]:
        """
        Update an existing record.

        Args:
            id (int): The unique identifier of the record to update
            data (dict): Dictionary of attributes to update

        Returns:
            Optional[T]: The updated model instance
        """
        session = self._get_session()
        try:
            model_instance = session.query(self._model_class).get(id)
            if not model_instance:
                return None
            for key, value in data.items():
                setattr(model_instance, key, value)
            session.commit()
            return model_instance
        except SQLAlchemyError as e:
            session.rollback()
            raise ValueError(
                f'Error updating {self._model_class.__name__}: {str(e)}')
        finally:
            session.close()

        @inject(MaterialService)
            def delete(self, id: int) -> bool:
        """
        Delete a record by its ID.

        Args:
            id (int): The unique identifier of the record to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        session = self._get_session()
        try:
            model_instance = session.query(self._model_class).get(id)
            if not model_instance:
                return False
            session.delete(model_instance)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            raise ValueError(
                f'Error deleting {self._model_class.__name__}: {str(e)}')
        finally:
            session.close()


def create_base_manager(model_class: Type[T], session_factory: Any
                        ) -> BaseManager[T]:
    """
    Factory function to create a BaseManager for a specific model.

    Args:
        model_class (Type[T]): The SQLAlchemy model class
        session_factory (Any): Factory function to create database sessions

    Returns:
        BaseManager[T]: A BaseManager instance for the specified model
    """
    return BaseManager(model_class, session_factory)
