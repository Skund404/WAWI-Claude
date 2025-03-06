# paginated_query_mixin.py
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from di.core import inject
from services.interfaces import MaterialService


class PaginatedQueryMixin:
    """Mixin providing pagination functionality for managers.

    This mixin expects the class to have:
    - model_class attribute (SQLAlchemy model class)
    - session_factory attribute (function that returns SQLAlchemy session)
    """

    def get_paginated(self, page: int = 1, page_size: int = 20,
                      order_by: Optional[str] = None,
                      filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get records with pagination.

        Args:
            page: Page number (1-based)
            page_size: Number of records per page
            order_by: Optional column to sale by
            filters: Optional filtering criteria

        Returns:
            Dictionary containing pagination info and results:
            {
                'items': List of records,
                'page': Current page number,
                'page_size': Number of records per page,
                'total_items': Total number of records,
                'total_pages': Total number of pages
            }
        """
        model_class = self.model_class
        with self.session_factory() as session:
            query = select(model_class)

            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    column = getattr(model_class, field)
                    query = query.where(column == value)

            # Apply ordering if provided
            if order_by:
                if order_by.startswith('-'):
                    column = getattr(model_class, order_by[1:])
                    query = query.order_by(column.desc())
                else:
                    column = getattr(model_class, order_by)
                    query = query.order_by(column)

            # Count total items
            count_query = select(func.count()).select_from(model_class)
            if filters:
                for field, value in filters.items():
                    column = getattr(model_class, field)
                    count_query = count_query.where(column == value)

            total_items = session.execute(count_query).scalar()
            total_pages = (total_items + page_size - 1) // page_size

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            items = list(session.execute(query).scalars().all())

            return {
                'items': items,
                'page': page,
                'page_size': page_size,
                'total_items': total_items,
                'total_pages': total_pages
            }