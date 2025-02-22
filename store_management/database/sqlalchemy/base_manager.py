"""
File: database/sqlalchemy/core/base_manager.py
Base manager for database operations using SQLAlchemy.
Provides common database operations and session management.
"""
import logging
from contextlib import contextmanager
from typing import TypeVar, Generic, List, Optional, Type, Any, Dict, Callable, Iterator
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import Column, asc, desc

# Type variables for generic typing
T = TypeVar('T')
ModelType = TypeVar('ModelType')


class BaseManager(Generic[ModelType]):
    """
    Base manager class for database operations.
    Provides common CRUD operations and session management.

    Generic over the model class type to provide type-safe operations.
    """

    def __init__(self, model_class: Type[ModelType], session_factory: Callable[[], Session]):
        """
        Initialize the base manager with a model class and session factory.

        Args:
            model_class: The SQLAlchemy model class to manage
            session_factory: Factory function to create new database sessions
        """
        self.model_class = model_class
        self.session_factory = session_factory
        self.logger = logging.getLogger(self.__class__.__name__)

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """
        Provide a transactional scope around a series of operations.
        Handles session creation, commits, rollbacks, and cleanup.

        Yields:
            Session: SQLAlchemy session for database operations

        Raises:
            Exception: Re-raises any exceptions that occur during database operations
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database operation failed: {str(e)}")
            raise
        finally:
            session.close()

    def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create a new record in the database.

        Args:
            data: Dictionary of field names and values for the new record

        Returns:
            The created model instance

        Raises:
            Exception: If creation fails
        """
        try:
            with self.session_scope() as session:
                instance = self.model_class(**data)
                session.add(instance)
                session.flush()  # Flush to get the ID
                return instance
        except Exception as e:
            self.logger.error(f"Failed to create {self.model_class.__name__} - Details: {str(e)}")
            raise

    def get(self, id: Any) -> Optional[ModelType]:
        """
        Get a record by its ID.

        Args:
            id: The ID of the record to retrieve

        Returns:
            The model instance or None if not found
        """
        try:
            with self.session_scope() as session:
                return session.query(self.model_class).get(id)
        except Exception as e:
            self.logger.error(f"Failed to get {self.model_class.__name__} with id {id} - Details: {str(e)}")
            raise

    def get_all(self, order_by: Optional[Column] = None, limit: Optional[int] = None) -> List[ModelType]:
        """
        Get all records of the model type.

        Args:
            order_by: Optional column to order results by
            limit: Optional maximum number of results to return

        Returns:
            List of model instances
        """
        try:
            with self.session_scope() as session:
                query = session.query(self.model_class)
                if order_by:
                    query = query.order_by(order_by)
                if limit:
                    query = query.limit(limit)
                return query.all()
        except Exception as e:
            self.logger.error(f"Failed to retrieve all {self.model_class.__name__} records - Details: {str(e)}")
            raise

    def update(self, id: Any, data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update a record by its ID.

        Args:
            id: The ID of the record to update
            data: Dictionary of field names and values to update

        Returns:
            The updated model instance or None if not found
        """
        try:
            with self.session_scope() as session:
                instance = session.query(self.model_class).get(id)
                if instance:
                    for key, value in data.items():
                        setattr(instance, key, value)
                    return instance
                return None
        except Exception as e:
            self.logger.error(f"Failed to update {self.model_class.__name__} with id {id} - Details: {str(e)}")
            raise

    def delete(self, id: Any) -> bool:
        """
        Delete a record by its ID.

        Args:
            id: The ID of the record to delete

        Returns:
            True if record was deleted, False if not found
        """
        try:
            with self.session_scope() as session:
                instance = session.query(self.model_class).get(id)
                if instance:
                    session.delete(instance)
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete {self.model_class.__name__} with id {id} - Details: {str(e)}")
            raise

    def exists(self, id: Any) -> bool:
        """
        Check if a record with the given ID exists.

        Args:
            id: The ID to check

        Returns:
            True if the record exists, False otherwise
        """
        try:
            with self.session_scope() as session:
                return session.query(self.model_class.exists().where(self.model_class.id == id)).scalar()
        except Exception as e:
            self.logger.error(
                f"Failed to check existence of {self.model_class.__name__} with id {id} - Details: {str(e)}")
            raise

    def count(self) -> int:
        """
        Count all records of the model type.

        Returns:
            The count of records
        """
        try:
            with self.session_scope() as session:
                return session.query(self.model_class).count()
        except Exception as e:
            self.logger.error(f"Failed to count {self.model_class.__name__} records - Details: {str(e)}")
            raise

    def filter_by(self, **kwargs) -> List[ModelType]:
        """
        Filter records by attribute values.

        Args:
            **kwargs: Field names and values to filter by

        Returns:
            List of model instances matching the filter criteria
        """
        try:
            with self.session_scope() as session:
                return session.query(self.model_class).filter_by(**kwargs).all()
        except Exception as e:
            self.logger.error(f"Failed to filter {self.model_class.__name__} records - Details: {str(e)}")
            raise

    def search(self, term: str, fields: List[Column]) -> List[ModelType]:
        """
        Search records for a term across specified fields.

        Args:
            term: The search term
            fields: List of columns to search in

        Returns:
            List of model instances matching the search criteria
        """
        try:
            with self.session_scope() as session:
                query = session.query(self.model_class)
                if term and fields:
                    conditions = []
                    for field in fields:
                        conditions.append(field.ilike(f"%{term}%"))
                    from sqlalchemy import or_
                    query = query.filter(or_(*conditions))
                return query.all()
        except Exception as e:
            self.logger.error(f"Failed to search {self.model_class.__name__} records - Details: {str(e)}")
            raise

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in the database.

        Args:
            items: List of dictionaries containing field names and values

        Returns:
            List of created model instances
        """
        try:
            with self.session_scope() as session:
                instances = [self.model_class(**item) for item in items]
                session.add_all(instances)
                session.flush()
                return instances
        except Exception as e:
            self.logger.error(f"Failed to bulk create {self.model_class.__name__} records - Details: {str(e)}")
            raise

    def bulk_update(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Update multiple records in the database.
        Each dictionary in items must contain an 'id' field.

        Args:
            items: List of dictionaries containing field names and values

        Returns:
            List of updated model instances
        """
        try:
            with self.session_scope() as session:
                updated = []
                for item in items:
                    if 'id' not in item:
                        raise ValueError("Each item must contain an 'id' field")

                    id_value = item.pop('id')
                    instance = session.query(self.model_class).get(id_value)

                    if instance:
                        for key, value in item.items():
                            setattr(instance, key, value)
                        updated.append(instance)

                return updated
        except Exception as e:
            self.logger.error(f"Failed to bulk update {self.model_class.__name__} records - Details: {str(e)}")
            raise