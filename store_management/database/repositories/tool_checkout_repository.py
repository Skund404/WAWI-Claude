# database/repositories/tool_checkout_repository.py
"""
Repository for tool checkout operations in the leatherworking ERP system.

This module provides data access methods for the ToolCheckout model,
including CRUD operations and specialized queries.
"""

import datetime
import logging
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, List, Optional, Tuple, Type

from database.models.tool_checkout import ToolCheckout
from database.models.tool import Tool
from database.models.project import Project
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, RepositoryError, ValidationError


class ToolCheckoutRepository(BaseRepository[ToolCheckout]):
    """Repository for tool checkout operations."""

    def __init__(self, session: Session):
        """Initialize the tool checkout repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session)
        self.logger = logging.getLogger(__name__)

    def _get_model_class(self) -> Type[ToolCheckout]:
        """Get the model class for this repository.

        Returns:
            ToolCheckout model class
        """
        return ToolCheckout

    def get_by_tool_id(self, tool_id: int) -> List[ToolCheckout]:
        """Get all checkout records for a specific tool.

        Args:
            tool_id: The ID of the tool

        Returns:
            List of checkout records
        """
        try:
            records = self.session.query(ToolCheckout).filter(
                ToolCheckout.tool_id == tool_id
            ).order_by(
                ToolCheckout.checked_out_date.desc()
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting checkout records for tool {tool_id}: {e}")
            raise RepositoryError(f"Failed to get checkout records: {str(e)}")

    def get_active_checkout(self, tool_id: int) -> Optional[ToolCheckout]:
        """Get the active checkout record for a tool.

        Args:
            tool_id: The ID of the tool

        Returns:
            Active checkout record or None if not checked out
        """
        try:
            checkout = self.session.query(ToolCheckout).filter(
                and_(
                    ToolCheckout.tool_id == tool_id,
                    ToolCheckout.status.in_(["checked_out", "overdue"])
                )
            ).first()

            return checkout
        except Exception as e:
            self.logger.error(f"Error getting active checkout for tool {tool_id}: {e}")
            raise RepositoryError(f"Failed to get active checkout: {str(e)}")

    def get_overdue_checkouts(self) -> List[ToolCheckout]:
        """Get overdue tool checkouts.

        Returns:
            List of overdue checkout records
        """
        try:
            now = datetime.datetime.now()

            # First, update any checkouts that are overdue but not marked as such
            overdue_query = self.session.query(ToolCheckout).filter(
                and_(
                    ToolCheckout.due_date < now,
                    ToolCheckout.status == "checked_out",
                    ToolCheckout.returned_date == None
                )
            )

            for checkout in overdue_query.all():
                checkout.status = "overdue"

            self.session.commit()

            # Then get all records marked as overdue
            records = self.session.query(ToolCheckout).filter(
                ToolCheckout.status == "overdue"
            ).order_by(
                ToolCheckout.due_date
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting overdue checkouts: {e}")
            raise RepositoryError(f"Failed to get overdue checkouts: {str(e)}")

    def get_by_project_id(self, project_id: int) -> List[ToolCheckout]:
        """Get all checkout records for a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            List of checkout records
        """
        try:
            records = self.session.query(ToolCheckout).filter(
                ToolCheckout.project_id == project_id
            ).order_by(
                ToolCheckout.checked_out_date.desc()
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting checkout records for project {project_id}: {e}")
            raise RepositoryError(f"Failed to get checkout records: {str(e)}")

    def get_by_user(self, username: str) -> List[ToolCheckout]:
        """Get all checkout records for a specific user.

        Args:
            username: The name of the user

        Returns:
            List of checkout records
        """
        try:
            records = self.session.query(ToolCheckout).filter(
                ToolCheckout.checked_out_by == username
            ).order_by(
                ToolCheckout.checked_out_date.desc()
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting checkout records for user {username}: {e}")
            raise RepositoryError(f"Failed to get checkout records: {str(e)}")

    def get_active_checkouts(self) -> List[ToolCheckout]:
        """Get all active (checked out or overdue) tool checkouts.

        Returns:
            List of active checkout records
        """
        try:
            records = self.session.query(ToolCheckout).filter(
                ToolCheckout.status.in_(["checked_out", "overdue"])
            ).order_by(
                ToolCheckout.due_date
            ).all()

            return records
        except Exception as e:
            self.logger.error(f"Error getting active checkouts: {e}")
            raise RepositoryError(f"Failed to get active checkouts: {str(e)}")

    def find(self, criteria: Dict[str, Any] = None, offset: int = 0, limit: int = 50,
             sort_by: str = "checked_out_date", sort_dir: str = "desc",
             include_tool: bool = False, include_project: bool = False) -> List[ToolCheckout]:
        """Find checkout records based on criteria.

        Args:
            criteria: Dictionary of search criteria
            offset: Pagination offset
            limit: Page size
            sort_by: Field to sort by
            sort_dir: Sort direction ("asc" or "desc")
            include_tool: Whether to include the tool relationship
            include_project: Whether to include the project relationship

        Returns:
            List of matching checkout records
        """
        query = self.session.query(ToolCheckout)

        # Include relationships if requested
        if include_tool:
            query = query.options(joinedload(ToolCheckout.tool))

        if include_project:
            query = query.options(joinedload(ToolCheckout.project))

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
            self.logger.error(f"Error finding checkout records: {e}")
            raise RepositoryError(f"Failed to find checkout records: {str(e)}")

    def count(self, criteria: Dict[str, Any] = None) -> int:
        """Count checkout records based on criteria.

        Args:
            criteria: Dictionary of search criteria

        Returns:
            Count of matching checkout records
        """
        query = self.session.query(func.count(ToolCheckout.id))

        # Apply criteria if provided
        if criteria:
            query = self._apply_criteria(query, criteria)

        try:
            return query.scalar()
        except Exception as e:
            self.logger.error(f"Error counting checkout records: {e}")
            raise RepositoryError(f"Failed to count checkout records: {str(e)}")

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
                elif field == "project.name":
                    query = query.join(Project)
                    field = "Project.name"

                if operator == "eq":
                    query = query.filter(getattr(ToolCheckout, field) == value)
                elif operator == "like":
                    query = query.filter(getattr(ToolCheckout, field).like(f"%{value}%"))
                elif operator == "gt":
                    query = query.filter(getattr(ToolCheckout, field) > value)
                elif operator == "gte":
                    query = query.filter(getattr(ToolCheckout, field) >= value)
                elif operator == "lt":
                    query = query.filter(getattr(ToolCheckout, field) < value)
                elif operator == "lte":
                    query = query.filter(getattr(ToolCheckout, field) <= value)
                elif operator == "in":
                    query = query.filter(getattr(ToolCheckout, field).in_(value))
                elif operator == "not":
                    query = query.filter(getattr(ToolCheckout, field) != value)
                elif operator == "not_in":
                    query = query.filter(~getattr(ToolCheckout, field).in_(value))
            else:
                # Handle special cases for related fields
                if key == "tool_name":
                    query = query.join(Tool)
                    query = query.filter(Tool.name.like(f"%{value}%"))
                elif key == "project_name":
                    query = query.join(Project)
                    query = query.filter(Project.name.like(f"%{value}%"))
                # Handle regular equality
                else:
                    query = query.filter(getattr(ToolCheckout, key) == value)

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
        # Handle special cases for related fields
        if sort_by == "tool_name":
            query = query.join(Tool)
            sort_attr = Tool.name
        elif sort_by == "project_name":
            query = query.join(Project)
            sort_attr = Project.name
        else:
            # Get the attribute to sort by
            sort_attr = getattr(ToolCheckout, sort_by, None)

        # If invalid attribute, default to checked_out_date
        if sort_attr is None:
            sort_attr = ToolCheckout.checked_out_date

        # Apply sorting direction
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_attr.asc())
        else:
            query = query.order_by(sort_attr.desc())

        return query