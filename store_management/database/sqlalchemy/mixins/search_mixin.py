# database/sqlalchemy/mixins/search_mixin.py

from typing import List, Optional, Type, Any, Dict
from sqlalchemy import select, or_, func
from store_management.database.sqlalchemy.models.base import Base
from store_management.database.sqlalchemy.session import get_db_session


class SearchMixin:
    """Mixin providing advanced search functionality for managers.

    This mixin expects the class to have:
    - model_class attribute (SQLAlchemy model class)
    """

    def search(self, search_term: str, fields: List[str] = None) -> List[Any]:
        """Search for records across multiple fields.

        Args:
            search_term: Term to search for
            fields: Optional list of fields to search in (defaults to all string fields)

        Returns:
            List of matching records
        """
        model_class = self.model_class

        with get_db_session() as session:
            # If fields not specified, search all string fields
            if not fields:
                fields = [column.name for column in model_class.__table__.columns
                          if str(column.type).startswith(('VARCHAR', 'TEXT', 'String'))]

            # Build search query with OR conditions
            conditions = []
            for field in fields:
                column = getattr(model_class, field)
                conditions.append(column.ilike(f'%{search_term}%'))

            query = select(model_class).where(or_(*conditions))

            return list(session.execute(query).scalars().all())

    def advanced_search(self, criteria: Dict[str, Any]) -> List[Any]:
        """Perform an advanced search with multiple criteria.

        Args:
            criteria: Dictionary of field-operator-value criteria
                Example: {'name': {'op': 'like', 'value': '%Widget%'},
                          'stock_level': {'op': 'gt', 'value': 10}}

        Returns:
            List of matching records
        """
        model_class = self.model_class

        with get_db_session() as session:
            query = select(model_class)

            for field, condition in criteria.items():
                column = getattr(model_class, field)
                op = condition.get('op', 'eq')
                value = condition.get('value')

                if op == 'eq':
                    query = query.where(column == value)
                elif op == 'neq':
                    query = query.where(column != value)
                elif op == 'gt':
                    query = query.where(column > value)
                elif op == 'lt':
                    query = query.where(column < value)
                elif op == 'gte':
                    query = query.where(column >= value)
                elif op == 'lte':
                    query = query.where(column <= value)
                elif op == 'like':
                    query = query.where(column.like(value))
                elif op == 'ilike':
                    query = query.where(column.ilike(value))
                elif op == 'in':
                    query = query.where(column.in_(value))
                elif op == 'notin':
                    query = query.where(~column.in_(value))

            return list(session.execute(query).scalars().all())