# services/implementations/tool_list_service.py
"""
Implementation of Tool List Service that manages tool lists for projects.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.models.enums import ToolListStatus
from database.models.tool_list import ToolList, ToolListItem
from database.repositories.tool_list_repository import ToolListRepository
from database.sqlalchemy.session import get_db_session
from di.core import inject
from services.base_service import BaseService, NotFoundError, ServiceError, ValidationError
from services.interfaces.tool_list_service import IToolListService


class ToolListService(BaseService, IToolListService):
    """
    Implementation of the Tool List Service interface that handles tool list operations.
    """

    @inject
    def __init__(self, tool_list_repository=None):
        """
        Initialize the Tool List Service with a repository.

        Args:
            tool_list_repository: Repository for tool list data access
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)

        if tool_list_repository:
            self.tool_list_repository = tool_list_repository
        else:
            session = get_db_session()
            self.tool_list_repository = ToolListRepository(session)
            self.session = session

    def get_tool_list(self, tool_list_id: int) -> ToolList:
        """
        Retrieve a tool list by its ID.

        Args:
            tool_list_id: ID of the tool list to retrieve

        Returns:
            ToolList: The retrieved tool list

        Raises:
            NotFoundError: If the tool list does not exist
        """
        try:
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")
            return tool_list
        except Exception as e:
            self.logger.error(f"Error retrieving tool list {tool_list_id}: {str(e)}")
            raise NotFoundError(f"Error retrieving tool list: {str(e)}")

    def get_tool_lists(self, **filters) -> List[ToolList]:
        """
        Retrieve tool lists based on optional filters.

        Args:
            **filters: Optional keyword arguments for filtering tool lists

        Returns:
            List[ToolList]: List of tool lists matching the filters
        """
        try:
            return self.tool_list_repository.find_all(**filters)
        except Exception as e:
            self.logger.error(f"Error retrieving tool lists: {str(e)}")
            return []

    def create_tool_list(self, project_id: int, tool_list_data: Dict[str, Any] = None) -> ToolList:
        """
        Create a new tool list for a project with the provided data.

        Args:
            project_id: ID of the project to create a tool list for
            tool_list_data: Additional data for creating the tool list

        Returns:
            ToolList: The created tool list

        Raises:
            ValidationError: If the tool list data is invalid
            NotFoundError: If the project does not exist
        """
        try:
            # Initialize tool list data if not provided
            if tool_list_data is None:
                tool_list_data = {}

            # Set required fields
            tool_list_data["project_id"] = project_id
            if "status" not in tool_list_data:
                tool_list_data["status"] = ToolListStatus.PENDING
            if "created_at" not in tool_list_data:
                tool_list_data["created_at"] = datetime.now()

            # Create tool list
            tool_list = ToolList(**tool_list_data)
            return self.tool_list_repository.add(tool_list)
        except Exception as e:
            self.logger.error(f"Error creating tool list for project {project_id}: {str(e)}")
            raise ValidationError(f"Error creating tool list: {str(e)}")

    def update_tool_list(self, tool_list_id: int, tool_list_data: Dict[str, Any]) -> ToolList:
        """
        Update a tool list with the provided data.

        Args:
            tool_list_id: ID of the tool list to update
            tool_list_data: Data for updating the tool list

        Returns:
            ToolList: The updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If the tool list data is invalid
        """
        try:
            # Get the tool list
            tool_list = self.get_tool_list(tool_list_id)

            # Update tool list fields
            for key, value in tool_list_data.items():
                if hasattr(tool_list, key):
                    setattr(tool_list, key, value)

            return self.tool_list_repository.update(tool_list)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool list {tool_list_id}: {str(e)}")
            raise ValidationError(f"Error updating tool list: {str(e)}")

    def delete_tool_list(self, tool_list_id: int) -> bool:
        """
        Delete a tool list by its ID.

        Args:
            tool_list_id: ID of the tool list to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the tool list does not exist
        """
        try:
            # Get the tool list
            tool_list = self.get_tool_list(tool_list_id)

            # Delete tool list
            self.tool_list_repository.delete(tool_list)
            return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Error deleting tool list: {str(e)}")

    def update_tool_list_status(self, tool_list_id: int, status: ToolListStatus) -> ToolList:
        """
        Update the status of a tool list.

        Args:
            tool_list_id: ID of the tool list to update
            status: New status for the tool list

        Returns:
            ToolList: The updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If the status transition is invalid
        """
        try:
            # Get the tool list
            tool_list = self.get_tool_list(tool_list_id)

            # Validate status transition
            self._validate_status_transition(tool_list.status, status)

            # Update status
            tool_list.status = status
            return self.tool_list_repository.update(tool_list)
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool list {tool_list_id} status: {str(e)}")
            raise ServiceError(f"Error updating tool list status: {str(e)}")

    def _validate_status_transition(self, current_status: ToolListStatus, new_status: ToolListStatus) -> None:
        """
        Validate if a status transition is allowed.

        Args:
            current_status: Current status of the tool list
            new_status: New status for the tool list

        Raises:
            ValidationError: If the status transition is invalid
        """
        # Define allowed status transitions
        allowed_transitions = {
            ToolListStatus.PENDING: [ToolListStatus.IN_PROGRESS, ToolListStatus.CANCELLED],
            ToolListStatus.IN_PROGRESS: [ToolListStatus.COMPLETED, ToolListStatus.CANCELLED, ToolListStatus.ON_HOLD],
            ToolListStatus.ON_HOLD: [ToolListStatus.IN_PROGRESS, ToolListStatus.CANCELLED],
            ToolListStatus.COMPLETED: [ToolListStatus.IN_PROGRESS],  # Allow reopening if needed
            ToolListStatus.CANCELLED: [ToolListStatus.PENDING]  # Allow reactivating cancelled lists
        }

        if new_status not in allowed_transitions.get(current_status, []):
            raise ValidationError(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )

    def get_tool_list_items(self, tool_list_id: int) -> List[ToolListItem]:
        """
        Retrieve items in a tool list.

        Args:
            tool_list_id: ID of the tool list

        Returns:
            List[ToolListItem]: List of items in the tool list

        Raises:
            NotFoundError: If the tool list does not exist
        """
        try:
            # Get the tool list to ensure it exists
            tool_list = self.get_tool_list(tool_list_id)

            # Return its items
            return tool_list.items
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving items for tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Error retrieving tool list items: {str(e)}")

    def add_tool_to_list(self, tool_list_id: int, tool_id: int, quantity: int = 1) -> ToolListItem:
        """
        Add a tool to a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_id: ID of the tool to add
            quantity: Quantity of the tool to add (default 1)

        Returns:
            ToolListItem: The created tool list item

        Raises:
            NotFoundError: If the tool list or tool does not exist
            ValidationError: If the quantity is invalid
        """
        try:
            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Get the tool list
            tool_list = self.get_tool_list(tool_list_id)

            # Check if the tool exists (would normally use a tool repository)
            # For now, we'll assume the tool_id is valid

            # Check if the tool is already in the list
            for item in tool_list.items:
                if item.tool_id == tool_id:
                    # Update quantity
                    item.quantity += quantity
                    self.tool_list_repository.session.commit()
                    return item

            # Create new tool list item
            item = ToolListItem(
                tool_list_id=tool_list_id,
                tool_id=tool_id,
                quantity=quantity
            )

            # Add item to database
            self.tool_list_repository.session.add(item)
            self.tool_list_repository.session.commit()

            return item
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error adding tool to list {tool_list_id}: {str(e)}")
            self.tool_list_repository.session.rollback()
            raise ServiceError(f"Error adding tool to list: {str(e)}")

    def update_tool_list_item(
            self, tool_list_id: int, item_id: int, item_data: Dict[str, Any]
    ) -> ToolListItem:
        """
        Update a tool list item.

        Args:
            tool_list_id: ID of the tool list
            item_id: ID of the item to update
            item_data: Data for updating the item

        Returns:
            ToolListItem: The updated tool list item

        Raises:
            NotFoundError: If the tool list or item does not exist
            ValidationError: If the item data is invalid
        """
        try:
            # Get the tool list to ensure it exists
            tool_list = self.get_tool_list(tool_list_id)

            # Find the item
            item = None
            for list_item in tool_list.items:
                if list_item.id == item_id:
                    item = list_item
                    break

            if not item:
                raise NotFoundError(f"Tool list item with ID {item_id} not found")

            # Validate quantity if it's being updated
            if "quantity" in item_data and item_data["quantity"] <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Update item fields
            for key, value in item_data.items():
                if hasattr(item, key):
                    setattr(item, key, value)

            # Commit changes
            self.tool_list_repository.session.commit()

            return item
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool list item {item_id}: {str(e)}")
            self.tool_list_repository.session.rollback()
            raise ServiceError(f"Error updating tool list item: {str(e)}")

    def remove_tool_from_list(self, tool_list_id: int, item_id: int) -> bool:
        """
        Remove a tool from a tool list.

        Args:
            tool_list_id: ID of the tool list
            item_id: ID of the item to remove

        Returns:
            bool: True if the item was removed successfully

        Raises:
            NotFoundError: If the tool list or item does not exist
        """
        try:
            # Get the tool list to ensure it exists
            tool_list = self.get_tool_list(tool_list_id)

            # Find the item
            item = None
            for list_item in tool_list.items:
                if list_item.id == item_id:
                    item = list_item
                    break

            if not item:
                raise NotFoundError(f"Tool list item with ID {item_id} not found")

            # Remove the item
            self.tool_list_repository.session.delete(item)
            self.tool_list_repository.session.commit()

            return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error removing tool from list {tool_list_id}: {str(e)}")
            self.tool_list_repository.session.rollback()
            raise ServiceError(f"Error removing tool from list: {str(e)}")

    def get_tool_lists_by_project(self, project_id: int) -> List[ToolList]:
        """
        Retrieve tool lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List[ToolList]: List of tool lists for the project
        """
        try:
            return self.tool_list_repository.find_all(project_id=project_id)
        except Exception as e:
            self.logger.error(f"Error retrieving tool lists for project {project_id}: {str(e)}")
            return []