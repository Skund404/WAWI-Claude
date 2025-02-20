from contextlib import contextmanager
from typing import TypeVar, Type, Optional, List, Dict, Any, Generic, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, update, delete
from sqlalchemy.sql import Select

from store_management.utils.logger import logger
from store_management.utils.error_handler import DatabaseError
from store_management.database.sqlalchemy.models import Base

T = TypeVar('T', bound=Base)


class BaseManager(Generic[T]):
    """
    Base manager class providing common database operations with proper transaction
    and error handling. Generic type T must be a SQLAlchemy model class.
    """

    def __init__(self, session_factory: Any, model_class: Type[T]):
        """
        Initialize base manager.

        Args:
            session_factory: SQLAlchemy session factory
            model_class: The model class this manager handles
        """
        self.session_factory = session_factory
        self.model_class = model_class

    @contextmanager
    def session_scope(self) -> Session:
        """
        Provide a transactional scope around a series of operations.
        Handles commit/rollback automatically.
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
        finally:
            session.close()

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record.

        Args:
            data: Dictionary of model attributes

        Returns:
            Created model instance
        """
        with self.session_scope() as session:
            try:
                instance = self.model_class(**data)
                session.add(instance)
                session.flush()  # Flush to get the ID
                return instance
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to create {self.model_class.__name__}: {str(e)}")

    def get(self, id: Any) -> Optional[T]:
        """
        Get a single record by ID.

        Args:
            id: Primary key value

        Returns:
            Model instance if found, None otherwise
        """
        with self.session_scope() as session:
            return session.get(self.model_class, id)

    def get_all(self, order_by: Optional[str] = None) -> List[T]:
        """
        Get all records with optional ordering.

        Args:
            order_by: Column name to order by

        Returns:
            List of model instances
        """
        with self.session_scope() as session:
            query = select(self.model_class)
            if order_by:
                query = query.order_by(order_by)
            return list(session.execute(query).scalars())

    def update(self, id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Update a record by ID.

        Args:
            id: Primary key value
            data: Dictionary of attributes to update

        Returns:
            Updated model instance or None if not found
        """
        with self.session_scope() as session:
            instance = session.get(self.model_class, id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                return instance
            return None

    def delete(self, id: Any) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Primary key value

        Returns:
            True if deleted, False if not found
        """
        with self.session_scope() as session:
            instance = session.get(self.model_class, id)
            if instance:
                session.delete(instance)
                return True
            return False

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple records in a single transaction.

        Args:
            items: List of dictionaries containing model attributes

        Returns:
            List of created model instances
        """
        with self.session_scope() as session:
            instances = [self.model_class(**item) for item in items]
            session.add_all(instances)
            session.flush()
            return instances

    def bulk_update(self, updates: List[Dict[str, Any]], key_field: str = 'id') -> int:
        """
        Update multiple records in a single transaction.

        Args:
            updates: List of dictionaries containing updates
            key_field: Field to use as the primary key

        Returns:
            Number of records updated
        """
        with self.session_scope() as session:
            count = 0
            for update_data in updates:
                key_value = update_data.pop(key_field, None)
                if key_value is None:
                    continue
                instance = session.get(self.model_class, key_value)
                if instance:
                    for key, value in update_data.items():
                        setattr(instance, key, value)
                    count += 1
            return count

    def exists(self, **kwargs) -> bool:
        """
        Check if a record exists with given criteria.

        Args:
            **kwargs: Field-value pairs to check

        Returns:
            True if exists, False otherwise
        """
        with self.session_scope() as session:
            query = select(self.model_class)
            for key, value in kwargs.items():
                query = query.filter(getattr(self.model_class, key) == value)
            return session.execute(query.exists()).scalar()

    def count(self, **filters) -> int:
        """
        Count records matching given filters.

        Args:
            **filters: Field-value pairs to filter by

        Returns:
            Number of matching records
        """
        with self.session_scope() as session:
            query = select(self.model_class)
            for key, value in filters.items():
                query = query.filter(getattr(self.model_class, key) == value)
            return len(session.execute(query).all())

    def build_query(self) -> Select:
        """
        Create a base query for the model.
        Useful for complex queries in derived managers.

        Returns:
            SQLAlchemy Select object
        """
        return select(self.model_class)