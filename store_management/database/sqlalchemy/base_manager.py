# File: database/sqlalchemy/base_manager.py
# Purpose: Provide a generic base manager for database operations

from typing import (
    TypeVar, Generic, Type, List, Dict, Any, Optional,
    Callable, Union, Type as PyType
)
from sqlalchemy.orm import Session
from sqlalchemy import select, inspect
from sqlalchemy.exc import SQLAlchemyError

from .mixins.base_mixins import (
    SearchMixin,
    FilterMixin,
    PaginationMixin,
    TransactionMixin
)
from ..utils.error_handling import DatabaseError

T = TypeVar('T')


class BaseManager(Generic[T], SearchMixin, FilterMixin, PaginationMixin, TransactionMixin):
    """
    Comprehensive base manager for database operations.

    Provides a generic, type-safe implementation of common database 
    operations with support for mixins and extensive error handling.
    """

    def __init__(
            self,
            model_class: Type[T],
            session_factory: Callable[[], Session],
            mixins: Optional[List[Type]] = None
    ):
        """
        Initialize the base manager with a model class and session factory.

        Args:
            model_class: The SQLAlchemy model class this manager operates on
            session_factory: A callable that returns a database session
            mixins: Optional list of additional mixin classes to apply
        """
        # Initialize base mixins
        SearchMixin.__init__(self, model_class, session_factory)
        FilterMixin.__init__(self, model_class, session_factory)
        PaginationMixin.__init__(self, model_class, session_factory)
        TransactionMixin.__init__(self, model_class, session_factory)

        # Apply additional mixins if provided
        self._apply_mixins(mixins or [])

    def _apply_mixins(self, mixins: List[Type]):
        """
        Dynamically apply additional mixins to the manager.

        Args:
            mixins: List of mixin classes to apply
        """
        for mixin in mixins:
            if hasattr(mixin, '__init__'):
                mixin.__init__(self, self.model_class, self.session_factory)

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record in the database.

        Args:
            data: Dictionary of attributes for the new record

        Returns:
            The created record

        Raises:
            DatabaseError: If creation fails
        """

        def _create(session: Session) -> T:
            try:
                # Validate data against model columns
                columns = [col.name for col in inspect(self.model_class).columns]
                filtered_data = {k: v for k, v in data.items() if k in columns}

                # Create and add the new instance
                new_instance = self.model_class(**filtered_data)
                session.add(new_instance)
                session.flush()  # Ensures ID is generated
                return new_instance
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to create {self.model_class.__name__}", str(e))

        return self.run_in_transaction(_create)

    def get(self, id: Any) -> Optional[T]:
        """
        Retrieve a record by its primary key.

        Args:
            id: Primary key value

        Returns:
            The record if found, None otherwise

        Raises:
            DatabaseError: If retrieval fails
        """
        with self.session_factory() as session:
            try:
                return session.get(self.model_class, id)
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to retrieve {self.model_class.__name__}", str(e))

    def get_all(
            self,
            order_by: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[T]:
        """
        Retrieve all records, with optional ordering and limit.

        Args:
            order_by: Optional column to order by
            limit: Optional maximum number of records to return

        Returns:
            List of records

        Raises:
            DatabaseError: If retrieval fails
        """
        with self.session_factory() as session:
            try:
                # Start with base select
                query = select(self.model_class)

                # Apply ordering if specified
                if order_by:
                    query = query.order_by(getattr(self.model_class, order_by))

                # Apply limit if specified
                if limit:
                    query = query.limit(limit)

                return session.execute(query).scalars().all()
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to retrieve {self.model_class.__name__} records", str(e))

    def update(self, id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing record.

        Args:
            id: Primary key of the record to update
            data: Dictionary of attributes to update

        Returns:
            The updated record, or None if not found

        Raises:
            DatabaseError: If update fails
        """

        def _update(session: Session) -> Optional[T]:
            try:
                # Retrieve the existing instance
                instance = session.get(self.model_class, id)
                if not instance:
                    return None

                # Validate data against model columns
                columns = [col.name for col in inspect(self.model_class).columns]
                filtered_data = {k: v for k, v in data.items() if k in columns}

                # Update instance attributes
                for key, value in filtered_data.items():
                    setattr(instance, key, value)

                session.flush()
                return instance
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to update {self.model_class.__name__}", str(e))

        return self.run_in_transaction(_update)

    def delete(self, id: Any) -> bool:
        """
        Delete a record by its primary key.

        Args:
            id: Primary key of the record to delete

        Returns:
            True if deletion was successful, False if record not found

        Raises:
            DatabaseError: If deletion fails
        """

        def _delete(session: Session) -> bool:
            try:
                # Retrieve and delete the instance
                instance = session.get(self.model_class, id)
                if not instance:
                    return False

                session.delete(instance)
                session.flush()
                return True
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to delete {self.model_class.__name__}", str(e))

        return self.run_in_transaction(_delete)

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        Bulk create multiple records in a single transaction.

        Args:
            items: List of dictionaries with record data

        Returns:
            List of created records

        Raises:
            DatabaseError: If bulk creation fails
        """

        def _bulk_create(session: Session) -> List[T]:
            try:
                # Validate data against model columns
                columns = [col.name for col in inspect(self.model_class).columns]
                filtered_items = [
                    {k: v for k, v in item.items() if k in columns}
                    for item in items
                ]

                # Create instances
                instances = [self.model_class(**item) for item in filtered_items]

                # Add and flush instances
                session.add_all(instances)
                session.flush()

                return instances
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to bulk create {self.model_class.__name__}", str(e))

            return self.run_in_transaction(_bulk_create)

            def bulk_update(self, updates: List[Dict[str, Any]], key_field: str = 'id') -> int:
                """
                Bulk update multiple records in a single transaction.

                Args:
                    updates: List of dictionaries with update information
                    key_field: Field to use as the primary key for identifying records

                Returns:
                    Number of records updated

                Raises:
                    DatabaseError: If bulk update fails
                """

                def _bulk_update(session: Session) -> int:
                    try:
                        # Validate data against model columns
                        columns = [col.name for col in inspect(self.model_class).columns]
                        updated_count = 0

                        for update in updates:
                            # Ensure update has the key field
                            if key_field not in update:
                                continue

                            # Retrieve the instance
                            instance = session.get(self.model_class, update[key_field])
                            if not instance:
                                continue

                            # Update only valid columns
                            filtered_update = {
                                k: v for k, v in update.items()
                                if k in columns and k != key_field
                            }

                            # Apply updates
                            for key, value in filtered_update.items():
                                setattr(instance, key, value)

                            updated_count += 1

                        session.flush()
                        return updated_count
                    except SQLAlchemyError as e:
                        raise DatabaseError(f"Failed to bulk update {self.model_class.__name__}", str(e))

                return self.run_in_transaction(_bulk_update)

            def exists(self, **kwargs) -> bool:
                """
                Check if a record exists matching the given criteria.

                Args:
                    **kwargs: Field-value pairs to check for existence

                Returns:
                    True if at least one record exists, False otherwise

                Raises:
                    DatabaseError: If existence check fails
                """
                with self.session_factory() as session:
                    try:
                        # Build conditions based on kwargs
                        conditions = [
                            getattr(self.model_class, field) == value
                            for field, value in kwargs.items()
                        ]

                        # Create and execute query
                        query = select(self.model_class).where(and_(*conditions))
                        result = session.execute(query).first()

                        return result is not None
                    except SQLAlchemyError as e:
                        raise DatabaseError(f"Failed to check existence of {self.model_class.__name__}", str(e))

            def count(self, **kwargs) -> int:
                """
                Count records matching the given criteria.

                Args:
                    **kwargs: Optional filtering criteria

                Returns:
                    Number of matching records

                Raises:
                    DatabaseError: If count operation fails
                """
                with self.session_factory() as session:
                    try:
                        # Start with base count query
                        query = select(func.count()).select_from(self.model_class)

                        # Apply filters if provided
                        if kwargs:
                            conditions = [
                                getattr(self.model_class, field) == value
                                for field, value in kwargs.items()
                            ]
                            query = query.where(and_(*conditions))

                        # Execute and return count
                        return session.execute(query).scalar() or 0
                    except SQLAlchemyError as e:
                        raise DatabaseError(f"Failed to count {self.model_class.__name__} records", str(e))