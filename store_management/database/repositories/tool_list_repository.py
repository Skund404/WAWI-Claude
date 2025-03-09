# database/repositories/tool_list_repository.py
from database.models.tool_list import ToolList

from database.models.enums import ToolListStatus
from database.models.tool_list_item import ToolListItem
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, select
from typing import Optional, List, Dict, Any
import logging


class ToolListRepository(BaseRepository):
    def __init__(self, session: Session):
        """
        Initialize the ToolList Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, ToolList)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_tool_list(self, tool_list_data: Dict[str, Any],
                         items: Optional[List[Dict[str, Any]]] = None) -> ToolList:
        """
        Create a new tool list with optional tool list items.

        Args:
            tool_list_data (Dict[str, Any]): Data for creating a new tool list
            items (Optional[List[Dict[str, Any]]]): List of tool list items to associate with the tool list

        Returns:
            Created ToolList instance
        """
        try:
            # Create tool list
            tool_list = ToolList(**tool_list_data)
            self.session.add(tool_list)

            # Add tool list items if provided
            if items:
                for item_data in items:
                    item_data['tool_list_id'] = tool_list.id
                    tool_list_item = ToolListItem(**item_data)
                    self.session.add(tool_list_item)

            self.session.commit()
            return tool_list
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error creating tool list: {e}")
            raise

    def find_by_status(self, status: ToolListStatus) -> List[ToolList]:
        """
        Find tool lists by their status.

        Args:
            status (ToolListStatus): Tool list status to filter by

        Returns:
            List of tool lists matching the status
        """
        try:
            return self.session.execute(select(ToolList).filter(ToolList.status == status)).scalars().all()
        except Exception as e:
            self.logger.error(f"Error finding tool lists by status: {e}")
            raise

    def get_tool_list_with_items(self,
                                 project_id: Optional[int] = None,
                                 status: Optional[ToolListStatus] = None) -> List[ToolList]:
        """
        Retrieve tool lists with their associated items, with optional filtering.

        Args:
            project_id (Optional[int]): Project ID to filter tool lists
            status (Optional[ToolListStatus]): Tool list status to filter

        Returns:
            List of tool lists with their items
        """
        try:
            query = select(ToolList).options(joinedload(ToolList.items))

            # Build filter conditions
            conditions = []
            if project_id:
                conditions.append(ToolList.project_id == project_id)
            if status:
                conditions.append(ToolList.status == status)

            # Apply filters if any
            if conditions:
                query = query.filter(and_(*conditions))

            return query.all()
        except Exception as e:
            self.logger.error(f"Error retrieving tool lists with items: {e}")
            raise

    def update_tool_list_status(self, tool_list_id: int, new_status: ToolListStatus) -> ToolList:
        """
        Update the status of a specific tool list.

        Args:
            tool_list_id (int): ID of the tool list to update
            new_status (ToolListStatus): New status for the tool list

        Returns:
            Updated ToolList instance
        """
        try:
            tool_list = self.session.execute(select(ToolList).filter(ToolList.id == tool_list_id)).scalar_one_or_none()

            if not tool_list:
                raise ValueError(f"Tool list with ID {tool_list_id} not found")

            tool_list.status = new_status
            self.session.commit()
            return tool_list
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error updating tool list status: {e}")
            raise