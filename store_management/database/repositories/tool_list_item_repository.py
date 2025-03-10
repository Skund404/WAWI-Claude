# database/repositories/tool_list_item_repository.py
"""
Repository for Tool List Item operations with advanced querying.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from logging import getLogger

from database.repositories.base_repository import BaseRepository
from database.models.tool_list_item import ToolListItem
from database.exceptions import RepositoryError, ModelNotFoundError


class ToolListItemRepository(BaseRepository):
    """
    Repository for managing Tool List Item database operations.
    Supports advanced querying based on ER diagram relationships.
    """

    def __init__(self, session: Session):
        """
        Initialize the Tool List Item Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, ToolListItem)
        self.logger = getLogger(__name__)

    def get_by_tool_list(self, tool_list_id: int) -> List[ToolListItem]:
        """
        Retrieve all tool list items for a specific tool list.

        Args:
            tool_list_id (int): ID of the tool list

        Returns:
            List[ToolListItem]: List of tool list items
        """
        try:
            query = select(ToolListItem).where(
                ToolListItem.tool_list_id == tool_list_id
            )
            return list(self.session.execute(query).scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving tool list items: {str(e)}")
            raise RepositoryError(f"Failed to retrieve tool list items: {str(e)}")

    def get_by_tool(self, tool_id: int) -> List[ToolListItem]:
        """
        Retrieve all tool list items for a specific tool.

        Args:
            tool_id (int): ID of the tool

        Returns:
            List[ToolListItem]: List of tool list items
        """
        try:
            query = select(ToolListItem).where(
                ToolListItem.tool_id == tool_id
            )
            return list(self.session.execute(query).scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving tool list items for tool: {str(e)}")
            raise RepositoryError(f"Failed to retrieve tool list items for tool: {str(e)}")

    def get_items_by_quantity_range(self, min_quantity: int = 0, max_quantity: Optional[int] = None) -> List[
        ToolListItem]:
        """
        Retrieve tool list items within a specific quantity range.

        Args:
            min_quantity (int, optional): Minimum quantity. Defaults to 0.
            max_quantity (Optional[int], optional): Maximum quantity. Defaults to None.

        Returns:
            List[ToolListItem]: List of tool list items matching the quantity criteria
        """
        try:
            query = select(ToolListItem)

            # Add minimum quantity filter
            if min_quantity is not None:
                query = query.where(ToolListItem.quantity >= min_quantity)

            # Add maximum quantity filter if specified
            if max_quantity is not None:
                query = query.where(ToolListItem.quantity <= max_quantity)

            return list(self.session.execute(query).scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving tool list items by quantity: {str(e)}")
            raise RepositoryError(f"Failed to retrieve tool list items by quantity: {str(e)}")