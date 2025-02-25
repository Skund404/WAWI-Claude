# filter_mixin.py
from typing import Any, Dict, List, TypeVar
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from di.core import inject
from services.interfaces import MaterialService

T = TypeVar('T')


class FilterMixin:
    """Mixin providing advanced filtering functionality for managers.

    This mixin expects the class to have:
    - model_class attribute (SQLAlchemy model class)
    - session_factory attribute (function that returns SQLAlchemy session)
    """

    def filter_by_multiple(self, filters: Dict[str, Any]) -> List[Any]:
        """Filter records by multiple criteria (AND condition).

        Args:
            filters: Dictionary of field-value pairs

        Returns:
            List of matching records
        """
        model_class = self.model_class
        with self.session_factory() as session:
            query = select(model_class)
            for field, value in filters.items():
                column = getattr(model_class, field)
                query = query.where(column == value)
            return list(session.execute(query).scalars().all())

    def filter_with_or(self, filters: Dict[str, List[Any]]) -> List[Any]:
        """Filter records with OR conditions for each field.

        Args:
            filters: Dictionary of field-values pairs where values is a list
                     Example: {'status': ['NEW', 'PENDING']}

        Returns:
            List of matching records
        """
        model_class = self.model_class
        with self.session_factory() as session:
            query = select(model_class)
            for field, values in filters.items():
                column = getattr(model_class, field)
                query = query.where(column.in_(values))
            return list(session.execute(query).scalars().all())

    def filter_complex(self, conditions: List[Dict[str, Any]], join_type: str = 'and') -> List[Any]:
        """Execute a complex filter with custom conditions.

        Args:
            conditions: List of condition dictionaries
                        Example: [
                            {'field': 'status', 'op': 'eq', 'value': 'NEW'},
                            {'field': 'price', 'op': 'gt', 'value': 100}
                        ]
            join_type: How to join conditions ('and' or 'or')

        Returns:
            List of matching records
        """
        model_class = self.model_class
        with self.session_factory() as session:
            query = select(model_class)
            filter_conditions = []

            for condition in conditions:
                field = condition.get('field')
                op = condition.get('op', 'eq')
                value = condition.get('value')
                column = getattr(model_class, field)

                if op == 'eq':
                    filter_conditions.append(column == value)
                elif op == 'neq':
                    filter_conditions.append(column != value)
                elif op == 'gt':
                    filter_conditions.append(column > value)
                elif op == 'lt':
                    filter_conditions.append(column < value)
                elif op == 'gte':
                    filter_conditions.append(column >= value)
                elif op == 'lte':
                    filter_conditions.append(column <= value)
                elif op == 'like':
                    filter_conditions.append(column.like(value))
                elif op == 'ilike':
                    filter_conditions.append(column.ilike(value))
                elif op == 'in':
                    filter_conditions.append(column.in_(value))
                elif op == 'notin':
                    filter_conditions.append(~column.in_(value))

            if join_type.lower() == 'and':
                query = query.where(and_(*filter_conditions))
            else:
                query = query.where(or_(*filter_conditions))

            return list(session.execute(query).scalars().all())