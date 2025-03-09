# database/repositories/tool_repository.py
"""
Tool Repository for managing tool-related database operations.

Provides CRUD and search functionality for tools.
"""

from typing import Optional, List, Dict, Any, Union
import logging

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from database.models.tool import Tool
from database.models.enums import ToolCategory
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class ToolRepository(BaseRepository[Tool]):
    """
    Repository for managing tools in the database.

    Provides methods for creating, retrieving, updating, and deleting
    tools with flexible search capabilities.
    """

    def __init__(self, session: Session):
        """
        Initialize the Tool Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Tool)
        self._logger = logging.getLogger(__name__)

    def get_by_category(self, category: ToolCategory) -> List[Tool]:
        """
        Get tools by their category.

        Args:
            category: Tool category to filter by

        Returns:
            List of tools matching the category
        """
        try:
            stmt = select(Tool).where(Tool.tool_type == category)
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting tools by category: {e}")
            raise DatabaseError(f"Error getting tools by category: {e}")
        except Exception as e:
            self._logger.error(f"Error getting tools by category: {e}")
            raise

    def get_by_supplier(self, supplier_id: int) -> List[Tool]:
        """
        Get tools provided by a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of tools from the supplier
        """
        try:
            stmt = select(Tool).where(Tool.supplier_id == supplier_id)
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting tools by supplier: {e}")
            raise DatabaseError(f"Error getting tools by supplier: {e}")
        except Exception as e:
            self._logger.error(f"Error getting tools by supplier: {e}")
            raise

    def search_tools(
            self,
            name: Optional[str] = None,
            category: Optional[ToolCategory] = None,
            supplier_id: Optional[int] = None,
            sort_by: Optional[str] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[Tool]:
        """
        Search for tools with flexible filtering and pagination.

        Args:
            name: Optional tool name to search for (partial match)
            category: Optional tool category to filter by
            supplier_id: Optional supplier ID to filter by
            sort_by: Field to sort by (prefix with '-' for descending)
            limit: Maximum number of results
            offset: Number of items to skip

        Returns:
            List of matching tools
        """
        try:
            # Build the select statement
            stmt = select(Tool)

            # Apply filters
            conditions = []
            if name:
                conditions.append(Tool.name.ilike(f"%{name}%"))
            if category:
                conditions.append(Tool.tool_type == category)
            if supplier_id:
                conditions.append(Tool.supplier_id == supplier_id)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Apply sorting
            if sort_by:
                # Check if sort is descending
                if sort_by.startswith('-'):
                    sort_field = sort_by[1:]
                    stmt = stmt.order_by(desc(getattr(Tool, sort_field)))
                else:
                    stmt = stmt.order_by(getattr(Tool, sort_by))

            # Apply pagination
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            # Execute query and return results
            results = self.session.execute(stmt).scalars().all()

            self._logger.info(f"Search returned {len(results)} tools")
            return list(results)

        except SQLAlchemyError as e:
            self._logger.error(f"Database error searching tools: {e}")
            raise DatabaseError(f"Error searching tools: {e}")
        except Exception as e:
            self._logger.error(f"Error searching tools: {e}")
            raise

    def get_with_inventory(self, tool_id: int) -> Optional[Tool]:
        """
        Get a tool with its inventory information eagerly loaded.

        Args:
            tool_id: ID of the tool to retrieve

        Returns:
            Tool with inventory information or None if not found
        """
        try:
            stmt = (
                select(Tool)
                .options(selectinload(Tool.inventory))
                .where(Tool.id == tool_id)
            )
            result = self.session.execute(stmt).scalars().first()
            return result
        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting tool with inventory: {e}")
            raise DatabaseError(f"Error getting tool with inventory: {e}")
        except Exception as e:
            self._logger.error(f"Error getting tool with inventory: {e}")
            raise

    def create_tool(self, **tool_data) -> Tool:
        """
        Create a new tool with validation.

        Args:
            **tool_data: Keyword arguments for creating the tool

        Returns:
            Created Tool instance
        """
        try:
            # Validate required fields
            required_fields = ['name', 'tool_type']
            for field in required_fields:
                if field not in tool_data:
                    raise ValueError(f"Missing required field: {field}")

            # Create and add tool to session
            return self.create(**tool_data)

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error creating tool: {e}")
            raise DatabaseError(f"Error creating tool: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error creating tool: {e}")
            raise

    def update_tool(self, tool_id: int, **update_data) -> Tool:
        """
        Update a tool with new data.

        Args:
            tool_id: ID of the tool to update
            **update_data: New data for the tool

        Returns:
            Updated Tool instance

        Raises:
            ModelNotFoundError: If tool with given ID is not found
        """
        try:
            # Get the tool
            tool = self.get_by_id(tool_id)
            if not tool:
                raise ModelNotFoundError(f"Tool with ID {tool_id} not found")

            # Update tool attributes
            for key, value in update_data.items():
                setattr(tool, key, value)

            # Validate and commit
            tool.validate()
            self.session.commit()

            self._logger.info(f"Updated tool {tool_id}")
            return tool

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error updating tool: {e}")
            raise DatabaseError(f"Error updating tool: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error updating tool: {e}")
            raise

    def delete_tool(self, tool_id: int) -> bool:
        """
        Delete a tool by ID.

        Args:
            tool_id: ID of the tool to delete

        Returns:
            True if successful, False if tool not found
        """
        try:
            # Verify tool exists
            tool = self.get_by_id(tool_id)
            if not tool:
                return False

            # Delete the tool
            self.session.delete(tool)
            self.session.commit()

            self._logger.info(f"Deleted tool {tool_id}")
            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            self._logger.error(f"Database error deleting tool: {e}")
            raise DatabaseError(f"Error deleting tool: {e}")
        except Exception as e:
            self.session.rollback()
            self._logger.error(f"Error deleting tool: {e}")
            raise

    def get_used_categories(self) -> List[ToolCategory]:
        """
        Get a list of all tool categories currently in use.

        Returns:
            List of unique tool categories
        """
        try:
            stmt = select(Tool.tool_type).distinct()
            result = self.session.execute(stmt).scalars().all()

            self._logger.info(f"Found {len(result)} tool categories in use")
            return list(result)

        except SQLAlchemyError as e:
            self._logger.error(f"Database error getting tool categories: {e}")
            raise DatabaseError(f"Error getting tool categories: {e}")
        except Exception as e:
            self._logger.error(f"Error getting tool categories: {e}")
            raise