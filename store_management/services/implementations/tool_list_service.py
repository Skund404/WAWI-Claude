"""
services/implementations/tool_list_service.py
Implementation of the tool list service for the leatherworking application.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from database.models.tool_list import ToolList, ToolListItem
from database.models.enums import ToolListStatus
from database.repositories.tool_list_repository import ToolListRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError, ServiceError
from services.interfaces.tool_list_service import IToolListService


class ToolListService(BaseService, IToolListService):
    """Service implementation for managing tool lists."""

    def __init__(self, tool_list_repository=None):
        """
        Initialize the Tool List Service with a repository.

        Args:
            tool_list_repository: Repository for tool list data access
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Initialize repository, creating a new one if not provided
        if tool_list_repository is None:
            session = get_db_session()
            self.repository = ToolListRepository(session)
        else:
            self.repository = tool_list_repository

    def create_tool_list(self, project_id: int, **kwargs) -> Dict[str, Any]:
        """
        Create a new tool list for a project.

        Args:
            project_id: ID of the associated project
            **kwargs: Additional tool list attributes

        Returns:
            Dict containing the created tool list data

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Set defaults for new tool list
            data = {
                "project_id": project_id,
                "status": ToolListStatus.ACTIVE,
                "created_at": datetime.now(),
                **kwargs
            }

            self.logger.info(f"Creating tool list for project_id={project_id}")

            # Create the tool list through the repository
            tool_list = self.repository.create(data)

            # Return the serialized tool list
            return self._serialize_tool_list(tool_list)
        except Exception as e:
            self.logger.error(f"Error creating tool list: {str(e)}")
            raise ValidationError(f"Failed to create tool list: {str(e)}")

    def get_tool_list(self, tool_list_id: int) -> Dict[str, Any]:
        """
        Get a tool list by ID.

        Args:
            tool_list_id: ID of the tool list to retrieve

        Returns:
            Dict containing the tool list data

        Raises:
            NotFoundError: If the tool list doesn't exist
        """
        try:
            tool_list = self.repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            return self._serialize_tool_list(tool_list)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve tool list: {str(e)}")

    def get_tool_lists(self,
                       status: Optional[ToolListStatus] = None,
                       project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get tool lists with optional filtering.

        Args:
            status: Filter by tool list status
            project_id: Filter by associated project ID

        Returns:
            List of tool list dictionaries
        """
        try:
            filters = {}
            if status:
                filters["status"] = status
            if project_id:
                filters["project_id"] = project_id

            tool_lists = self.repository.get_all_by_filter(**filters)
            return [self._serialize_tool_list(tl) for tl in tool_lists]
        except Exception as e:
            self.logger.error(f"Error retrieving tool lists: {str(e)}")
            return []

    def update_tool_list(self,
                         tool_list_id: int,
                         **kwargs) -> Dict[str, Any]:
        """
        Update a tool list's attributes.

        Args:
            tool_list_id: ID of the tool list to update
            **kwargs: Attributes to update

        Returns:
            Dict containing the updated tool list

        Raises:
            NotFoundError: If the tool list doesn't exist
            ValidationError: If update validation fails
        """
        try:
            tool_list = self.repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Remove any attributes that shouldn't be directly updated
            for key in ["id", "created_at", "project_id"]:
                if key in kwargs:
                    del kwargs[key]

            self.logger.info(f"Updating tool list {tool_list_id} with {kwargs}")
            updated_tool_list = self.repository.update(tool_list_id, kwargs)
            return self._serialize_tool_list(updated_tool_list)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool list {tool_list_id}: {str(e)}")
            raise ValidationError(f"Failed to update tool list: {str(e)}")

    def update_status(self,
                      tool_list_id: int,
                      status: ToolListStatus) -> Dict[str, Any]:
        """
        Update the status of a tool list.

        Args:
            tool_list_id: ID of the tool list
            status: New status value

        Returns:
            Dict containing the updated tool list

        Raises:
            NotFoundError: If the tool list doesn't exist
            ValidationError: If status transition is invalid
        """
        try:
            tool_list = self.repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Validate status transition
            self._validate_status_transition(tool_list.status, status)

            self.logger.info(f"Updating tool list {tool_list_id} status to {status}")
            updated_tool_list = self.repository.update(tool_list_id, {"status": status})
            return self._serialize_tool_list(updated_tool_list)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool list status: {str(e)}")
            raise ValidationError(f"Failed to update tool list status: {str(e)}")

    def add_item(self,
                 tool_list_id: int,
                 tool_id: int,
                 quantity: int = 1) -> Dict[str, Any]:
        """
        Add a tool item to a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_id: ID of the tool
            quantity: Quantity of the tool needed

        Returns:
            Dict containing the created tool list item

        Raises:
            NotFoundError: If the tool list doesn't exist
            ValidationError: If item validation fails
        """
        try:
            # Verify tool list exists
            tool_list = self.repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Create item data
            item_data = {
                "tool_list_id": tool_list_id,
                "tool_id": tool_id,
                "quantity": quantity
            }

            self.logger.info(f"Adding tool item to tool list {tool_list_id}")
            item = self.repository.add_item(item_data)
            return self._serialize_tool_list_item(item)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding item to tool list: {str(e)}")
            raise ValidationError(f"Failed to add item to tool list: {str(e)}")

    def update_item(self,
                    item_id: int,
                    quantity: Optional[int] = None,
                    **kwargs) -> Dict[str, Any]:
        """
        Update a tool list item.

        Args:
            item_id: ID of the tool list item
            quantity: New quantity needed
            **kwargs: Additional attributes to update

        Returns:
            Dict containing the updated tool list item

        Raises:
            NotFoundError: If the item doesn't exist
            ValidationError: If update validation fails
        """
        try:
            # Verify item exists
            item = self.repository.get_item_by_id(item_id)
            if not item:
                raise NotFoundError(f"Tool list item with ID {item_id} not found")

            # Update data
            update_data = kwargs
            if quantity is not None:
                if quantity <= 0:
                    raise ValidationError("Quantity must be greater than zero")
                update_data["quantity"] = quantity

            # Remove any attributes that shouldn't be directly updated
            for key in ["id", "tool_list_id", "tool_id"]:
                if key in update_data:
                    del update_data[key]

            self.logger.info(f"Updating tool list item {item_id}")
            updated_item = self.repository.update_item(item_id, update_data)
            return self._serialize_tool_list_item(updated_item)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool list item: {str(e)}")
            raise ValidationError(f"Failed to update tool list item: {str(e)}")

    def remove_item(self, item_id: int) -> None:
        """
        Remove an item from a tool list.

        Args:
            item_id: ID of the tool list item to remove

        Raises:
            NotFoundError: If the item doesn't exist
        """
        try:
            # Verify item exists
            item = self.repository.get_item_by_id(item_id)
            if not item:
                raise NotFoundError(f"Tool list item with ID {item_id} not found")

            self.logger.info(f"Removing tool list item {item_id}")
            self.repository.delete_item(item_id)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error removing tool list item: {str(e)}")
            raise ValidationError(f"Failed to remove tool list item: {str(e)}")

    def get_tool_list_for_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the active tool list for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            Dict containing the tool list data, or None if no active tool list exists
        """
        try:
            # Get active tool list for the project
            tool_lists = self.repository.get_all_by_filter(
                project_id=project_id,
                status=ToolListStatus.ACTIVE
            )

            if not tool_lists or len(tool_lists) == 0:
                return None

            # Return the first active tool list
            return self._serialize_tool_list(tool_lists[0])
        except Exception as e:
            self.logger.error(f"Error getting tool list for project {project_id}: {str(e)}")
            return None

    def _validate_status_transition(self, current_status: ToolListStatus,
                                    new_status: ToolListStatus) -> None:
        """
        Validate if a status transition is allowed.

        Args:
            current_status: Current tool list status
            new_status: New tool list status

        Raises:
            ValidationError: If the status transition is not allowed
        """
        # Define allowed status transitions
        allowed_transitions = {
            ToolListStatus.ACTIVE: [ToolListStatus.COMPLETED, ToolListStatus.CANCELLED],
            ToolListStatus.COMPLETED: [],  # No transitions from completed
            ToolListStatus.CANCELLED: []  # No transitions from cancelled
        }

        if new_status not in allowed_transitions.get(current_status, []):
            raise ValidationError(
                f"Cannot transition from {current_status} to {new_status}"
            )

    def _serialize_tool_list(self, tool_list: ToolList) -> Dict[str, Any]:
        """
        Serialize a tool list to a dictionary.

        Args:
            tool_list: ToolList instance to serialize

        Returns:
            Dictionary representation of the tool list
        """
        result = {
            "id": tool_list.id,
            "project_id": tool_list.project_id,
            "status": tool_list.status.name,
            "created_at": tool_list.created_at.isoformat() if tool_list.created_at else None
        }

        # Include items if they are loaded
        if hasattr(tool_list, 'items') and tool_list.items is not None:
            result["items"] = [self._serialize_tool_list_item(item) for item in tool_list.items]

        return result

    def _serialize_tool_list_item(self, item: ToolListItem) -> Dict[str, Any]:
        """
        Serialize a tool list item to a dictionary.

        Args:
            item: ToolListItem instance to serialize

        Returns:
            Dictionary representation of the tool list item
        """
        return {
            "id": item.id,
            "tool_list_id": item.tool_list_id,
            "tool_id": item.tool_id,
            "quantity": item.quantity
        }