# base_mixins.py
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Type
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from di.core import inject
from services.interfaces import MaterialService

T = TypeVar('T')


class BaseMixin(Generic[T]):
    """Base mixin providing core functionality for database managers.

    This mixin serves as a foundational class for other database-related mixins,
    providing common initialization and type safety.
    """

    def __init__(self, model_class: Type[T], session_factory: Callable[[], Session]):
        """Initialize the base mixin with a model class and session factory.

        Args:
            model_class: The SQLAlchemy model class this mixin operates on
            session_factory: A callable that returns a database session
        """
        self.model_class = model_class
        self.session_factory = session_factory


class SearchMixin(BaseMixin[T]):
    """Advanced search functionality for database managers.

    Provides comprehensive search capabilities across multiple fields
    with flexible configuration.
    """

    def search(self, search_term: str, fields: Optional[List[str]] = None) -> List[T]:
        """Perform a comprehensive search across multiple fields.

        Args:
            search_term: The term to search for
            fields: Optional list of fields to search.
                   If None, uses all string columns.

        Returns:
            List of matching records
        """
        with self.session_factory() as session:
            if not fields:
                fields = [
                    col.name for col in self.model_class.__table__.columns
                    if hasattr(col.type, 'length')
                ]

            search_conditions = [
                func.lower(getattr(self.model_class, field)).like(f'%{search_term.lower()}%')
                for field in fields
            ]

            query = select(self.model_class).where(or_(*search_conditions))
            return session.execute(query).scalars().all()

    def advanced_search(self, criteria: Dict[str, Dict[str, Any]]) -> List[T]:
        """Perform an advanced search with multiple criteria.

        Args:
            criteria: Dictionary of field-operator-value criteria
                     Example: {
                         'name': {'op': 'like', 'value': '%Widget%'},
                         'stock_level': {'op': 'gt', 'value': 10}
                     }

        Returns:
            List of matching records
        """
        with self.session_factory() as session:
            conditions = []

            for field, condition in criteria.items():
                column = getattr(self.model_class, field)
                op = condition.get('op', '==')
                value = condition['value']

                ops = {
                    '==': column == value,
                    '!=': column != value,
                    '>': column > value,
                    '<': column < value,
                    '>=': column >= value,
                    '<=': column <= value,
                    'like': column.like(value),
                    'in': column.in_(value)
                }

                conditions.append(ops.get(op, column == value))

            query = select(self.model_class).where(and_(*conditions))
            return session.execute(query).scalars().all()


class FilterMixin(BaseMixin[T]):
    """Advanced filtering capabilities for database managers.

    Provides methods for complex, flexible filtering of database records.
    """

    def filter_by_multiple(self, filters: Dict[str, Any]) -> List[T]:
        """Filter records by multiple exact match criteria.

        Args:
            filters: Dictionary of field-value pairs

        Returns:
            List of matching records
        """
        with self.session_factory() as session:
            conditions = [
                (getattr(self.model_class, field) == value)
                for field, value in filters.items()
            ]

            query = select(self.model_class).where(and_(*conditions))
            return session.execute(query).scalars().all()

    def filter_with_or(self, filters: Dict[str, List[Any]]) -> List[T]:
        """Filter records with OR conditions for each field.

        Args:
            filters: Dictionary of field-values pairs where values is a list
                    Example: {'status': ['NEW', 'PENDING']}

        Returns:
            List of matching records
        """
        with self.session_factory() as session:
            conditions = [
                getattr(self.model_class, field).in_(values)
                for field, values in filters.items()
            ]

            query = select(self.model_class).where(or_(*conditions))
            return session.execute(query).scalars().all()

    def filter_complex(self, conditions: List[Dict[str, Any]], join_type: str = 'and') -> List[T]:
        """Execute a complex filter with custom conditions.

        Args:
            conditions: List of condition dictionaries
            join_type: How to join conditions ('and' or 'or')

        Returns:
            List of matching records
        """

        def build_condition(condition: Dict[str, Any]) -> ColumnElement:
            field = condition['field']
            op = condition.get('op', '==')
            value = condition['value']
            column = getattr(self.model_class, field)

            ops = {
                '==': column == value,
                '!=': column != value,
                '>': column > value,
                '<': column < value,
                '>=': column >= value,
                '<=': column <= value,
                'like': column.like(value),
                'in': column.in_(value)
            }

            return ops.get(op, column == value)

        with self.session_factory() as session:
            mapped_conditions = [build_condition(cond) for cond in conditions]

            if join_type == 'and':
                query = select(self.model_class).where(and_(*mapped_conditions))
            else:
                query = select(self.model_class).where(or_(*mapped_conditions))

            return session.execute(query).scalars().all()


class PaginationMixin(BaseMixin[T]):
    """Pagination support for database managers.

    Provides methods for retrieving paginated results with
    optional filtering and ordering.
    """

    def get_paginated(
            self,
            page: int = 1,
            page_size: int = 20,
            order_by: Optional[str] = None,
            filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get paginated results with optional ordering and filtering.

        Args:
            page: Page number (1-based)
            page_size: Number of records per page
            order_by: Optional column to sale by
            filters: Optional filtering criteria

        Returns:
            Pagination result dictionary
        """
        with self.session_factory() as session:
            query = select(self.model_class)

            # Apply filters if provided
            if filters:
                filter_conditions = [
                    (getattr(self.model_class, field) == value)
                    for field, value in filters.items()
                ]
                query = query.where(and_(*filter_conditions))

            # Apply ordering if provided
            if order_by:
                order_column = getattr(self.model_class, order_by)
                query = query.order_by(order_column)

            # Get total items for pagination
            total_query = select(func.count()).select_from(query.subquery())
            total_items = session.execute(total_query).scalar() or 0
            total_pages = (total_items + page_size - 1) // page_size

            # Apply pagination
            offset = (page - 1) * page_size
            paginated_query = query.offset(offset).limit(page_size)
            items = session.execute(paginated_query).scalars().all()

            return {
                'items': items,
                'page': page,
                'page_size': page_size,
                'total_items': total_items,
                'total_pages': total_pages
            }


class TransactionMixin(BaseMixin[T]):
    """Transaction handling mixin for database managers.

    Provides methods for running operations within database transactions
    with robust error handling.
    """

    def run_in_transaction(self, operation: Callable[[Session], Any], *args, **kwargs) -> Any:
        """Execute an operation within a database transaction.

        Args:
            operation: Function to execute within the transaction
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Result of the operation

        Raises:
            Exception: If the transaction fails
        """
        with self.session_factory() as session:
            try:
                result = operation(session, *args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    def execute_with_result(self, operation: Callable[..., Any], *args, **kwargs) -> Dict[str, Any]:
        """Execute an operation in a transaction and return a standard result.

        Args:
            operation: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Dictionary with operation result
        """
        try:
            result = self.run_in_transaction(operation, *args, **kwargs)
            return {'success': True, 'data': result, 'error': None}
        except Exception as e:
            return {'success': False, 'data': None, 'error': str(e)}