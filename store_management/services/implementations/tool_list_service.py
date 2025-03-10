# services/implementations/tool_list_service.py
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.tool_list import ToolList
from database.models.tool_list_item import ToolListItem
from database.models.enums import ToolListStatus
from database.repositories.tool_list_repository import ToolListRepository
from database.repositories.tool_list_item_repository import ToolListItemRepository
from database.repositories.project_repository import ProjectRepository
from database.repositories.tool_repository import ToolRepository

from services.base_service import BaseService, ValidationError, NotFoundError, ServiceError
from services.interfaces.tool_list_service import IToolListService

from di.core import inject


class ToolListService(BaseService, IToolListService):
    """Implementation of the ToolList Service interface.

    This service provides functionality for managing tool lists for leatherworking
    projects, tracking tool allocation, and handling tool returns.
    """

    @inject
    def __init__(self,
                 session: Session,
                 tool_list_repository: Optional[ToolListRepository] = None,
                 tool_list_item_repository: Optional[ToolListItemRepository] = None,
                 project_repository: Optional[ProjectRepository] = None,
                 tool_repository: Optional[ToolRepository] = None):
        """Initialize the ToolList Service.

        Args:
            session: SQLAlchemy database session
            tool_list_repository: Optional ToolListRepository instance
            tool_list_item_repository: Optional ToolListItemRepository instance
            project_repository: Optional ProjectRepository instance
            tool_repository: Optional ToolRepository instance
        """
        super().__init__(session)
        self.tool_list_repository = tool_list_repository or ToolListRepository(session)
        self.tool_list_item_repository = tool_list_item_repository or ToolListItemRepository(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.tool_repository = tool_repository or ToolRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, tool_list_id: int) -> Dict[str, Any]:
        """Retrieve a tool list by its ID.

        Args:
            tool_list_id: The ID of the tool list to retrieve

        Returns:
            A dictionary representation of the tool list

        Raises:
            NotFoundError: If the tool list does not exist
        """
        try:
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")
            return self._to_dict(tool_list)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve tool list: {str(e)}")

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all tool lists with optional filtering.

        Args:
            filters: Optional filters to apply to the tool list query

        Returns:
            List of dictionaries representing tool lists
        """
        try:
            tool_lists = self.tool_list_repository.get_all(filters)
            return [self._to_dict(tool_list) for tool_list in tool_lists]
        except Exception as e:
            self.logger.error(f"Error retrieving tool lists: {str(e)}")
            raise ServiceError(f"Failed to retrieve tool lists: {str(e)}")

    def create_for_project(self, project_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a new tool list for a project.

        Args:
            project_id: ID of the project
            notes: Optional notes about the tool list

        Returns:
            Dictionary representation of the created tool list

        Raises:
            NotFoundError: If the project does not exist
            ServiceError: If a tool list already exists for the project
        """
        try:
            # Verify project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Check if active tool list already exists
            existing_lists = self.tool_list_repository.get_by_project(
                project_id,
                status=[ToolListStatus.DRAFT.value, ToolListStatus.PENDING.value, ToolListStatus.IN_PROGRESS.value]
            )

            if existing_lists:
                raise ServiceError(f"Active tool list already exists for project {project_id}")

            # Create the tool list within a transaction
            with self.transaction():
                # Create tool list
                tool_list_data = {
                    'project_id': project_id,
                    'status': ToolListStatus.DRAFT.value,
                    'created_at': datetime.now(),
                    'notes': notes
                }

                tool_list = self.tool_list_repository.create(tool_list_data)

                # Get the created tool list
                result = self._to_dict(tool_list)
                result['items'] = []  # Initially empty list of tools

                return result
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating tool list for project {project_id}: {str(e)}")
            raise ServiceError(f"Failed to create tool list: {str(e)}")

    def update(self, tool_list_id: int, tool_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tool list.

        Args:
            tool_list_id: ID of the tool list to update
            tool_list_data: Dictionary containing updated tool list data

        Returns:
            Dictionary representation of the updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If the updated data is invalid
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Validate tool list data
            self._validate_tool_list_data(tool_list_data)

            # Update the tool list within a transaction
            with self.transaction():
                updated_tool_list = self.tool_list_repository.update(tool_list_id, tool_list_data)
                return self._to_dict(updated_tool_list)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to update tool list: {str(e)}")

    def delete(self, tool_list_id: int) -> bool:
        """Delete a tool list by its ID.

        Args:
            tool_list_id: ID of the tool list to delete

        Returns:
            True if the tool list was successfully deleted

        Raises:
            NotFoundError: If the tool list does not exist
            ServiceError: If the tool list cannot be deleted (e.g., in progress)
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Check if tool list can be deleted
            if tool_list.status == ToolListStatus.IN_PROGRESS.value:
                raise ServiceError(f"Cannot delete tool list {tool_list_id} as it is in progress")

            if tool_list.status == ToolListStatus.COMPLETED.value:
                raise ServiceError(f"Cannot delete tool list {tool_list_id} as it is completed")

            # Delete the tool list within a transaction
            with self.transaction():
                # Delete all tool list items first
                items = self.tool_list_item_repository.get_by_tool_list(tool_list_id)
                for item in items:
                    self.tool_list_item_repository.delete(item.id)

                # Then delete the tool list
                self.tool_list_repository.delete(tool_list_id)
                return True
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to delete tool list: {str(e)}")

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get tool lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of dictionaries representing tool lists for the project

        Raises:
            NotFoundError: If the project does not exist
        """
        try:
            # Verify project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            tool_lists = self.tool_list_repository.get_by_project(project_id)
            return [self._to_dict(tool_list) for tool_list in tool_lists]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting tool lists for project {project_id}: {str(e)}")
            raise ServiceError(f"Failed to get tool lists for project: {str(e)}")

    def get_tool_list_items(self, tool_list_id: int) -> List[Dict[str, Any]]:
        """Get all items in a tool list.

        Args:
            tool_list_id: ID of the tool list

        Returns:
            List of dictionaries representing tool list items

        Raises:
            NotFoundError: If the tool list does not exist
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            items = self.tool_list_item_repository.get_by_tool_list(tool_list_id)
            result = []

            for item in items:
                item_dict = self._to_dict(item)

                # Get tool details
                tool = self.tool_repository.get_by_id(item.tool_id)
                if tool:
                    item_dict['tool'] = {
                        'id': tool.id,
                        'name': tool.name,
                        'tool_category': tool.tool_category.name if hasattr(tool.tool_category, 'name') else str(
                            tool.tool_category)
                    }

                result.append(item_dict)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting items for tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to get tool list items: {str(e)}")

    def add_tool(self, tool_list_id: int, tool_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Add a tool to a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_id: ID of the tool
            quantity: Quantity of the tool needed

        Returns:
            Dictionary representing the added tool list item

        Raises:
            NotFoundError: If the tool list or tool does not exist
            ValidationError: If the quantity is invalid
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Check if tool already exists in the list
            existing_items = self.tool_list_item_repository.get_by_tool_list_and_tool(tool_list_id, tool_id)

            # Add or update item within a transaction
            with self.transaction():
                if existing_items:
                    # Update existing item
                    existing_item = existing_items[0]
                    updated_data = {
                        'quantity': existing_item.quantity + quantity
                    }
                    updated_item = self.tool_list_item_repository.update(existing_item.id, updated_data)
                    return self._to_dict(updated_item)
                else:
                    # Create new item
                    item_data = {
                        'tool_list_id': tool_list_id,
                        'tool_id': tool_id,
                        'quantity': quantity,
                        'allocated': False
                    }

                    new_item = self.tool_list_item_repository.create(item_data)
                    return self._to_dict(new_item)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding tool to tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to add tool to tool list: {str(e)}")

    def remove_tool(self, tool_list_id: int, tool_item_id: int) -> bool:
        """Remove a tool from a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_item_id: ID of the tool list item

        Returns:
            True if the tool was successfully removed

        Raises:
            NotFoundError: If the tool list or item does not exist
            ServiceError: If the tool cannot be removed (e.g., already allocated)
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Verify item exists and belongs to the tool list
            item = self.tool_list_item_repository.get_by_id(tool_item_id)
            if not item:
                raise NotFoundError(f"Tool list item with ID {tool_item_id} not found")

            if item.tool_list_id != tool_list_id:
                raise ValidationError(f"Item {tool_item_id} does not belong to tool list {tool_list_id}")

            # Check if tool is allocated
            if getattr(item, 'allocated', False):
                raise ServiceError(f"Cannot remove item {tool_item_id} as it is already allocated")

            # Remove item within a transaction
            with self.transaction():
                self.tool_list_item_repository.delete(tool_item_id)
                return True
        except (NotFoundError, ValidationError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error removing item {tool_item_id} from tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to remove tool from tool list: {str(e)}")

    def update_tool_quantity(self, tool_list_id: int,
                             tool_item_id: int,
                             quantity: int) -> Dict[str, Any]:
        """Update the quantity of a tool in a tool list.

        Args:
            tool_list_id: ID of the tool list
            tool_item_id: ID of the tool list item
            quantity: New quantity of the tool needed

        Returns:
            Dictionary representing the updated tool list item

        Raises:
            NotFoundError: If the tool list or item does not exist
            ValidationError: If the quantity is invalid
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Verify item exists and belongs to the tool list
            item = self.tool_list_item_repository.get_by_id(tool_item_id)
            if not item:
                raise NotFoundError(f"Tool list item with ID {tool_item_id} not found")

            if item.tool_list_id != tool_list_id:
                raise ValidationError(f"Item {tool_item_id} does not belong to tool list {tool_list_id}")

            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Check if tool is allocated
            if getattr(item, 'allocated', False):
                raise ValidationError(f"Cannot update quantity for item {tool_item_id} as it is already allocated")

            # Update item quantity within a transaction
            with self.transaction():
                updated_data = {
                    'quantity': quantity
                }

                updated_item = self.tool_list_item_repository.update(tool_item_id, updated_data)
                return self._to_dict(updated_item)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating item {tool_item_id} quantity in tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to update tool quantity: {str(e)}")

    def allocate_tools(self, tool_list_id: int,
                       allocate_all: bool = False,
                       tool_item_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Allocate tools from inventory to a tool list.

        Args:
            tool_list_id: ID of the tool list
            allocate_all: Whether to allocate all tools in the list
            tool_item_ids: Optional list of specific tool items to allocate

        Returns:
            Dictionary with allocation results

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If both allocate_all and tool_item_ids are specified
            ServiceError: If insufficient tools are available
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Validate allocation parameters
            if allocate_all and tool_item_ids:
                raise ValidationError("Cannot specify both allocate_all and tool_item_ids")

            # Validate tool list status
            valid_statuses = [ToolListStatus.DRAFT.value, ToolListStatus.PENDING.value]
            if tool_list.status not in valid_statuses:
                raise ValidationError(
                    f"Tool list {tool_list_id} status must be DRAFT or PENDING, current status: {tool_list.status}")

            # Get items to allocate
            if allocate_all:
                items = self.tool_list_item_repository.get_by_tool_list(tool_list_id)
            elif tool_item_ids:
                items = []
                for item_id in tool_item_ids:
                    item = self.tool_list_item_repository.get_by_id(item_id)
                    if not item:
                        raise NotFoundError(f"Tool list item with ID {item_id} not found")
                    if item.tool_list_id != tool_list_id:
                        raise ValidationError(f"Item {item_id} does not belong to tool list {tool_list_id}")
                    items.append(item)
            else:
                raise ValidationError("Must specify either allocate_all or tool_item_ids")

            # Initialize result
            result = {
                'success': True,
                'allocated_tools': [],
                'failed_allocations': []
            }

            # Allocate tools within a transaction
            with self.transaction():
                # Update tool list status if not already in progress
                if tool_list.status != ToolListStatus.IN_PROGRESS.value:
                    self.tool_list_repository.update(tool_list_id, {'status': ToolListStatus.IN_PROGRESS.value})

                for item in items:
                    # Skip already allocated items
                    if getattr(item, 'allocated', False):
                        continue

                    # Try to allocate the tool
                    try:
                        # Check tool availability (if you have a ToolService)
                        if hasattr(self, 'tool_service'):
                            # Use tool service to check out the tool
                            checkout_result = self.tool_service.check_out_tool(
                                item.tool_id,
                                project_id=tool_list.project_id,
                                quantity=item.quantity,
                                notes=f"Allocated for tool list {tool_list_id}"
                            )

                            # Update tool list item
                            self.tool_list_item_repository.update(item.id, {
                                'allocated': True,
                                'checkout_id': checkout_result.get('id')
                            })
                        else:
                            # Simple allocation without tool service
                            self.tool_list_item_repository.update(item.id, {'allocated': True})

                        # Add to successful allocations
                        result['allocated_tools'].append({
                            'item_id': item.id,
                            'tool_id': item.tool_id,
                            'quantity': item.quantity
                        })
                    except Exception as alloc_error:
                        # Record failed allocation
                        result['success'] = False
                        result['failed_allocations'].append({
                            'item_id': item.id,
                            'tool_id': item.tool_id,
                            'quantity': item.quantity,
                            'reason': str(alloc_error)
                        })

                return result
        except (NotFoundError, ValidationError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error allocating tools for tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to allocate tools: {str(e)}")

    def return_tools(self, tool_list_id: int,
                     return_all: bool = False,
                     tool_item_ids: Optional[List[int]] = None,
                     condition_notes: Optional[Dict[int, str]] = None) -> Dict[str, Any]:
        """Return allocated tools to inventory.

        Args:
            tool_list_id: ID of the tool list
            return_all: Whether to return all tools in the list
            tool_item_ids: Optional list of specific tool items to return
            condition_notes: Optional dictionary mapping tool_item_ids to condition notes

        Returns:
            Dictionary with return results

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If both return_all and tool_item_ids are specified
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Validate return parameters
            if return_all and tool_item_ids:
                raise ValidationError("Cannot specify both return_all and tool_item_ids")

            # Validate tool list is in progress
            if tool_list.status != ToolListStatus.IN_PROGRESS.value:
                raise ValidationError(
                    f"Tool list {tool_list_id} status must be IN_PROGRESS, current status: {tool_list.status}")

            # Get items to return
            if return_all:
                items = self.tool_list_item_repository.get_by_tool_list(tool_list_id)
                # Filter to only include allocated items
                items = [item for item in items if getattr(item, 'allocated', False)]
            elif tool_item_ids:
                items = []
                for item_id in tool_item_ids:
                    item = self.tool_list_item_repository.get_by_id(item_id)
                    if not item:
                        raise NotFoundError(f"Tool list item with ID {item_id} not found")
                    if item.tool_list_id != tool_list_id:
                        raise ValidationError(f"Item {item_id} does not belong to tool list {tool_list_id}")
                    if not getattr(item, 'allocated', False):
                        raise ValidationError(f"Item {item_id} is not allocated")
                    items.append(item)
            else:
                raise ValidationError("Must specify either return_all or tool_item_ids")

            # Initialize result
            result = {
                'success': True,
                'returned_tools': [],
                'failed_returns': []
            }

            # Return tools within a transaction
            with self.transaction():
                for item in items:
                    # Try to return the tool
                    try:
                        notes = condition_notes.get(item.id) if condition_notes else None

                        # Return the tool (if you have a ToolService)
                        if hasattr(self, 'tool_service') and hasattr(item, 'checkout_id'):
                            # Use tool service to check in the tool
                            self.tool_service.check_in_tool(
                                item.tool_id,
                                checkout_id=item.checkout_id,
                                condition_notes=notes,
                                quantity=item.quantity
                            )

                        # Update tool list item
                        self.tool_list_item_repository.update(item.id, {'allocated': False})

                        # Add to successful returns
                        result['returned_tools'].append({
                            'item_id': item.id,
                            'tool_id': item.tool_id,
                            'quantity': item.quantity
                        })
                    except Exception as return_error:
                        # Record failed return
                        result['success'] = False
                        result['failed_returns'].append({
                            'item_id': item.id,
                            'tool_id': item.tool_id,
                            'quantity': item.quantity,
                            'reason': str(return_error)
                        })

                # Check if all tools are returned
                remaining_allocated = self.tool_list_item_repository.get_allocated_items(tool_list_id)
                if not remaining_allocated:
                    # All tools returned, update status to ready for completion
                    self.tool_list_repository.update(tool_list_id, {'status': ToolListStatus.PENDING.value})

                return result
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error returning tools for tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to return tools: {str(e)}")

    def complete_tool_list(self, tool_list_id: int,
                           notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark a tool list as complete.

        Args:
            tool_list_id: ID of the tool list
            notes: Optional notes about the completion

        Returns:
            Dictionary representing the updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ValidationError: If not all tools have been returned
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Check if tool list is in a valid status
            if tool_list.status not in [ToolListStatus.PENDING.value, ToolListStatus.IN_PROGRESS.value]:
                raise ValidationError(
                    f"Tool list {tool_list_id} status must be PENDING or IN_PROGRESS, current status: {tool_list.status}")

            # Check if all tools have been returned
            allocated_items = self.tool_list_item_repository.get_allocated_items(tool_list_id)
            if allocated_items:
                raise ValidationError(f"Cannot complete tool list: {len(allocated_items)} tools are still allocated")

            # Complete tool list within a transaction
            with self.transaction():
                completed_data = {
                    'status': ToolListStatus.COMPLETED.value,
                    'completed_at': datetime.now()
                }

                if notes:
                    completed_data['notes'] = f"{tool_list.notes or ''}\nCompletion: {notes}"

                updated_tool_list = self.tool_list_repository.update(tool_list_id, completed_data)
                return self._to_dict(updated_tool_list)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error completing tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to complete tool list: {str(e)}")

    def cancel_tool_list(self, tool_list_id: int, reason: str) -> Dict[str, Any]:
        """Cancel a tool list.

        Args:
            tool_list_id: ID of the tool list
            reason: Reason for cancellation

        Returns:
            Dictionary representing the updated tool list

        Raises:
            NotFoundError: If the tool list does not exist
            ServiceError: If the tool list cannot be cancelled
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Check if tool list can be cancelled
            if tool_list.status == ToolListStatus.COMPLETED.value:
                raise ServiceError(f"Cannot cancel tool list {tool_list_id} as it is already completed")

            if tool_list.status == ToolListStatus.CANCELLED.value:
                raise ServiceError(f"Tool list {tool_list_id} is already cancelled")

            # Check if any tools are still allocated
            allocated_items = self.tool_list_item_repository.get_allocated_items(tool_list_id)
            if allocated_items:
                # Attempt to return all allocated tools
                try:
                    self.return_tools(tool_list_id, return_all=True)
                except Exception as return_error:
                    self.logger.warning(
                        f"Failed to return all tools when cancelling tool list {tool_list_id}: {str(return_error)}")
                    # Continue with cancellation even if returns fail

            # Cancel tool list within a transaction
            with self.transaction():
                cancelled_data = {
                    'status': ToolListStatus.CANCELLED.value,
                    'notes': f"{tool_list.notes or ''}\nCancellation: {reason}"
                }

                updated_tool_list = self.tool_list_repository.update(tool_list_id, cancelled_data)
                return self._to_dict(updated_tool_list)
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error cancelling tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to cancel tool list: {str(e)}")

    def validate_tool_availability(self, tool_list_id: int) -> Dict[str, Any]:
        """Validate that sufficient tools are available for a tool list.

        Args:
            tool_list_id: ID of the tool list

        Returns:
            Dictionary with validation results

        Raises:
            NotFoundError: If the tool list does not exist
        """
        try:
            # Verify tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Get tool list items
            items = self.tool_list_item_repository.get_by_tool_list(tool_list_id)

            result = {
                'valid': True,
                'missing_tools': [],
                'insufficient_tools': [],
                'total_items': len(items),
                'valid_items': 0
            }

            for item in items:
                # Skip already allocated items
                if getattr(item, 'allocated', False):
                    result['valid_items'] += 1
                    continue

                # Check tool availability (if ToolService is available)
                if hasattr(self, 'tool_service'):
                    # Use tool service to check availability
                    try:
                        checkout_preview = self.tool_service.check_out_tool_preview(
                            item.tool_id,
                            quantity=item.quantity
                        )
                        result['valid_items'] += 1
                    except NotFoundError:
                        # Tool not in inventory
                        tool = self.tool_repository.get_by_id(item.tool_id)
                        tool_name = tool.name if tool else f"Tool ID {item.tool_id}"

                        result['missing_tools'].append({
                            'item_id': item.id,
                            'tool_id': item.tool_id,
                            'tool_name': tool_name,
                            'required_quantity': item.quantity
                        })

                        result['valid'] = False
                    except ValidationError as ve:
                        # Insufficient quantity
                        tool = self.tool_repository.get_by_id(item.tool_id)
                        tool_name = tool.name if tool else f"Tool ID {item.tool_id}"

                        # Try to extract available quantity from error message
                        import re
                        available_qty = 0
                        match = re.search(r'available: (\d+)', str(ve))
                        if match:
                            available_qty = int(match.group(1))

                        result['insufficient_tools'].append({
                            'item_id': item.id,
                            'tool_id': item.tool_id,
                            'tool_name': tool_name,
                            'required_quantity': item.quantity,
                            'available_quantity': available_qty,
                            'shortage': item.quantity - available_qty
                        })

                        result['valid'] = False
                else:
                    # No tool service, assume tools are available
                    result['valid_items'] += 1

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error validating tool availability for tool list {tool_list_id}: {str(e)}")
            raise ServiceError(f"Failed to validate tool availability: {str(e)}")

    def _validate_tool_list_data(self, data: Dict[str, Any]) -> None:
        """Validate tool list data.

        Args:
            data: Tool list data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate status if provided
        if 'status' in data:
            valid_statuses = [status.value for status in ToolListStatus]
            if data['status'] not in valid_statuses:
                raise ValidationError(f"Invalid status: {data['status']}. Valid statuses are: {valid_statuses}")

    def _to_dict(self, obj) -> Dict[str, Any]:
        """Convert a model object to a dictionary representation.

        Args:
            obj: Model object to convert

        Returns:
            Dictionary representation of the object
        """
        if isinstance(obj, ToolList):
            result = {
                'id': obj.id,
                'project_id': obj.project_id,
                'status': obj.status.name if hasattr(obj.status, 'name') else str(obj.status),
                'created_at': obj.created_at.isoformat() if hasattr(obj, 'created_at') and obj.created_at else None,
                'completed_at': obj.completed_at.isoformat() if hasattr(obj,
                                                                        'completed_at') and obj.completed_at else None,
                'notes': getattr(obj, 'notes', None)
            }
            return result
        elif isinstance(obj, ToolListItem):
            result = {
                'id': obj.id,
                'tool_list_id': obj.tool_list_id,
                'tool_id': obj.tool_id,
                'quantity': obj.quantity,
                'allocated': getattr(obj, 'allocated', False),
                'checkout_id': getattr(obj, 'checkout_id', None),
                'notes': getattr(obj, 'notes', None)
            }
            return result
        elif hasattr(obj, '__dict__'):
            # Generic conversion for other model types
            result = {}
            for k, v in obj.__dict__.items():
                if not k.startswith('_'):
                    # Handle datetime objects
                    if isinstance(v, datetime):
                        result[k] = v.isoformat()
                    # Handle enum objects
                    elif hasattr(v, 'name'):
                        result[k] = v.name
                    else:
                        result[k] = v
            return result
        else:
            # If not a model object, return as is
            return obj