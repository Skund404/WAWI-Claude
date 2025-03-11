# database/repositories/tool_maintenance_repository.py
"""
Repository for tool maintenance operations in the leatherworking ERP system.

This module provides data access methods for the ToolMaintenance model,
including CRUD operations and specialized queries.
"""

import datetime
import logging
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, List, Optional, Tuple, Type

from database.models.tool_maintenance import ToolMaintenance
from database.models.tool import Tool
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, RepositoryError, ValidationError


class ToolMaintenanceRepository(BaseRepository[ToolMaintenance]):
    """Repository for tool maintenance operations."""

    def __init__(self, session: Session):
        """Initialize the tool maintenance repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session)
        self.logger = logging.getLogger(__name__)

    def _get_model_class(self) -> Type[ToolMaintenance]:
        """Get the model class for this repository.

        Returns:
            ToolMaintenance model class
        """
        return ToolMaintenance

    def get_by_tool_id(self, tool_id: int) -> List[ToolMaintenance]:
        """Get all maintenance records for a specific tool.

        Args:
            tool_id: The ID of the tool

        Returns:
            List of maintenance records
        """
        try:
            records = self.session.query(ToolMaintenance).filter(
                ToolMaintenance.tool_id == tool_id
            ).order_by(
                ToolMaintenance.maintenance_date.desc()
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting maintenance records for tool {tool_id}: {e}")
            raise RepositoryError(f"Failed to get maintenance records: {str(e)}")

    def get_upcoming_maintenance(self, days: int = 30) -> List[ToolMaintenance]:
        """Get maintenance records due within the specified number of days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of upcoming maintenance records
        """
        try:
            cutoff_date = datetime.datetime.now() + datetime.timedelta(days=days)

            records = self.session.query(ToolMaintenance).filter(
                and_(
                    ToolMaintenance.next_maintenance_date <= cutoff_date,
                    ToolMaintenance.next_maintenance_date > datetime.datetime.now(),
                    ToolMaintenance.status != "Completed"
                )
            ).order_by(
                ToolMaintenance.next_maintenance_date
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting upcoming maintenance: {e}")
            raise RepositoryError(f"Failed to get upcoming maintenance: {str(e)}")

    def get_overdue_maintenance(self) -> List[ToolMaintenance]:
        """Get overdue maintenance records.

        Returns:
            List of overdue maintenance records
        """
        try:
            now = datetime.datetime.now()

            records = self.session.query(ToolMaintenance).filter(
                and_(
                    ToolMaintenance.next_maintenance_date < now,
                    ToolMaintenance.status != "Completed"
                )
            ).order_by(
                ToolMaintenance.next_maintenance_date
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting overdue maintenance: {e}")
            raise RepositoryError(f"Failed to get overdue maintenance: {str(e)}")

    def get_recent_maintenance(self, days: int = 30) -> List[ToolMaintenance]:
        """Get maintenance records completed within the specified number of days.

        Args:
            days: Number of days to look back

        Returns:
            List of recent maintenance records
        """
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

            records = self.session.query(ToolMaintenance).filter(
                and_(
                    ToolMaintenance.maintenance_date >= cutoff_date,
                    ToolMaintenance.status == "Completed"
                )
            ).order_by(
                ToolMaintenance.maintenance_date.desc()
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting recent maintenance: {e}")
            raise RepositoryError(f"Failed to get recent maintenance: {str(e)}")

    def find(self, criteria: Dict[str, Any] = None, offset: int = 0, limit: int = 50,
             sort_by: str = "maintenance_date", sort_dir: str = "desc",
             include_tool: bool = False) -> List[ToolMaintenance]:
        """Find maintenance records based on criteria.

        Args:
            criteria: Dictionary of search criteria
            offset: Pagination offset
            limit: Page size
            sort_by: Field to sort by
            sort_dir: Sort direction ("asc" or "desc")
            include_tool: Whether to include the tool relationship

        Returns:
            List of matching maintenance records
        """
        query = self.session.query(ToolMaintenance)

        # Include tool relationship if requested
        if include_tool:
            query = query.options(joinedload(ToolMaintenance.tool))

        # Apply criteria if provided
        if criteria:
            query = self._apply_criteria(query, criteria)

        # Apply sorting
        query = self._apply_sorting(query, sort_by, sort_dir)

        # Apply pagination
        if limit > 0:
            query = query.offset(offset).limit(limit)

        try:
            return query.all()
        except Exception as e:
            self.logger.error(f"Error finding maintenance records: {e}")
            raise RepositoryError(f"Failed to find maintenance records: {str(e)}")

    def count(self, criteria: Dict[str, Any] = None) -> int:
        """Count maintenance records based on criteria.

        Args:
            criteria: Dictionary of search criteria

        Returns:
            Count of matching maintenance records
        """
        query = self.session.query(func.count(ToolMaintenance.id))

        # Apply criteria if provided
        if criteria:
            query = self._apply_criteria(query, criteria)

        try:
            return query.scalar()
        except Exception as e:
            self.logger.error(f"Error counting maintenance records: {e}")
            raise RepositoryError(f"Failed to count maintenance records: {str(e)}")

    def _apply_criteria(self, query, criteria: Dict[str, Any]):
        """Apply search criteria to the query.

        Args:
            query: The SQLAlchemy query
            criteria: Dictionary of search criteria

        Returns:
            Updated query with criteria applied
        """
        for key, value in criteria.items():
            # Check for special keys with operators
            if "__" in key:
                field, operator = key.split("__")

                # Handle field name mappings (for relationships)
                if field == "tool.name":
                    query = query.join(Tool)
                    field = "Tool.name"

                if operator == "eq":
                    query = query.filter(getattr(ToolMaintenance, field) == value)
                elif operator == "like":
                    query = query.filter(getattr(ToolMaintenance, field).like(f"%{value}%"))
                elif operator == "gt":
                    query = query.filter(getattr(ToolMaintenance, field) > value)
                elif operator == "gte":
                    query = query.filter(getattr(ToolMaintenance, field) >= value)
                elif operator == "lt":
                    query = query.filter(getattr(ToolMaintenance, field) < value)
                elif operator == "lte":
                    query = query.filter(getattr(ToolMaintenance, field) <= value)
                elif operator == "in":
                    query = query.filter(getattr(ToolMaintenance, field).in_(value))
                elif operator == "not":
                    query = query.filter(getattr(ToolMaintenance, field) != value)
                elif operator == "not_in":
                    query = query.filter(~getattr(ToolMaintenance, field).in_(value))
            else:
                # Handle special case for tool name
                if key == "tool_name":
                    query = query.join(Tool)
                    query = query.filter(Tool.name.like(f"%{value}%"))
                # Handle regular equality
                else:
                    query = query.filter(getattr(ToolMaintenance, key) == value)

        return query

    def _apply_sorting(self, query, sort_by: str, sort_dir: str):
        """Apply sorting to the query.

        Args:
            query: The SQLAlchemy query
            sort_by: Field to sort by
            sort_dir: Sort direction ("asc" or "desc")

        Returns:
            Updated query with sorting applied
        """
        # Handle special case for tool name
        if sort_by == "tool_name":
            query = query.join(Tool)
            sort_attr = Tool.name
        else:
            # Get the attribute to sort by
            sort_attr = getattr(ToolMaintenance, sort_by, None)

        # If invalid attribute, default to maintenance_date
        if sort_attr is None:
            sort_attr = ToolMaintenance.maintenance_date

        # Apply sorting direction
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_attr.asc())
        else:
            query = query.order_by(sort_attr.desc())

        return query