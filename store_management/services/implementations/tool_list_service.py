"""
services/implementations/tool_list_service.py

Implementation of the tool list service for managing tool lists in leatherworking projects.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.models.enums import (
    ToolListStatus,
    ToolCategory,
    ProjectType,
    InventoryStatus,
    TransactionType
)
from database.repositories.tool_list_repository import ToolListRepository
from database.repositories.project_repository import ProjectRepository
from database.repositories.tool_repository import ToolRepository
from database.repositories.inventory_repository import InventoryRepository

from services.base_service import BaseService
from services.exceptions import (
    ValidationError,
    NotFoundError,
    BusinessRuleError
)
from services.dto.tool_list_dto import ToolListDTO, ToolListItemDTO

from di.inject import inject


class ToolListService(BaseService):
    """
    Service for managing tool lists, including generation, checkout,
    and tracking of tools for projects.
    """

    @inject
    def __init__(
            self,
            session: Session,
            tool_list_repository: Optional[ToolListRepository] = None,
            project_repository: Optional[ProjectRepository] = None,
            tool_repository: Optional[ToolRepository] = None,
            inventory_repository: Optional[InventoryRepository] = None
    ):
        """
        Initialize the tool list service with necessary repositories.

        Args:
            session: Database session
            tool_list_repository: Repository for tool list operations
            project_repository: Repository for project operations
            tool_repository: Repository for tool operations
            inventory_repository: Repository for inventory operations
        """
        super().__init__(session)
        self.tool_list_repository = tool_list_repository or ToolListRepository(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.tool_repository = tool_repository or ToolRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, tool_list_id: int) -> Dict[str, Any]:
        """
        Retrieve a tool list by its ID.

        Args:
            tool_list_id: ID of the tool list to retrieve

        Returns:
            Tool list data as a dictionary
        """
        try:
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            return ToolListDTO.from_model(
                tool_list,
                include_items=True,
                include_project=True
            ).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving tool list {tool_list_id}: {str(e)}")
            raise

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all tool lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of tool lists for the project
        """
        try:
            # Verify project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Get tool lists
            tool_lists = self.tool_list_repository.get_by_project(project_id)

            return [
                ToolListDTO.from_model(
                    tool_list,
                    include_items=True
                ).to_dict()
                for tool_list in tool_lists
            ]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving tool lists for project {project_id}: {str(e)}")
            raise

    def create(self, tool_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tool list.

        Args:
            tool_list_data: Data for creating the tool list

        Returns:
            Created tool list data
        """
        try:
            # Validate project
            project_id = tool_list_data.get('project_id')
            if not project_id:
                raise ValidationError("Project ID is required")

            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Set default status if not provided
            tool_list_data['status'] = tool_list_data.get(
                'status',
                ToolListStatus.DRAFT.value
            )
            tool_list_data['created_at'] = datetime.now()

            # Handle items separately
            items = tool_list_data.pop('items', [])

            with self.transaction():
                # Create tool list
                tool_list = self.tool_list_repository.create(tool_list_data)

                # Add items
                for item in items:
                    item['tool_list_id'] = tool_list.id
                    self.tool_list_repository.add_item(item)

                # Retrieve and return complete tool list
                result = self.tool_list_repository.get_by_id(tool_list.id)
                return ToolListDTO.from_model(
                    result,
                    include_items=True,
                    include_project=True
                ).to_dict()

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating tool list: {str(e)}")
            raise

    def update(self, tool_list_id: int, tool_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing tool list.

        Args:
            tool_list_id: ID of the tool list to update
            tool_list_data: Updated data for the tool list

        Returns:
            Updated tool list data
        """
        try:
            # Check if tool list exists
            existing_tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not existing_tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Prevent updating completed tool lists
            if existing_tool_list.status == ToolListStatus.COMPLETED.value:
                raise BusinessRuleError("Cannot update a completed tool list")

            # Update tool list
            with self.transaction():
                updated_tool_list = self.tool_list_repository.update(
                    tool_list_id,
                    tool_list_data
                )

                return ToolListDTO.from_model(
                    updated_tool_list,
                    include_items=True,
                    include_project=True
                ).to_dict()

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool list {tool_list_id}: {str(e)}")
            raise

    def delete(self, tool_list_id: int) -> bool:
        """
        Delete a tool list.

        Args:
            tool_list_id: ID of the tool list to delete

        Returns:
            True if deletion was successful
        """
        try:
            # Check if tool list exists
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            # Prevent deleting active tool lists
            if tool_list.status in [
                ToolListStatus.IN_PROGRESS.value,
                ToolListStatus.COMPLETED.value
            ]:
                raise BusinessRuleError(
                    f"Cannot delete tool list with status {tool_list.status}"
                )

            # Delete tool list
            with self.transaction():
                # First delete associated items
                items = self.tool_list_repository.get_items(tool_list_id)
                for item in items:
                    self.tool_list_repository.delete_item(item.id)

                # Then delete the tool list
                return self.tool_list_repository.delete(tool_list_id)

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting tool list {tool_list_id}: {str(e)}")
            raise

    def checkout_tool(self, tool_list_id: int, item_id: int) -> Dict[str, Any]:
        """
        Checkout a tool from a tool list.

        Args:
            tool_list_id: ID of the tool list
            item_id: ID of the tool list item to checkout

        Returns:
            Updated tool list item data
        """
        try:
            # Validate tool list and item
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            item = self.tool_list_repository.get_item(item_id)
            if not item:
                raise NotFoundError(f"Tool list item with ID {item_id} not found")

            # Validate item belongs to the tool list
            if item.tool_list_id != tool_list_id:
                raise ValidationError(
                    f"Item {item_id} does not belong to tool list {tool_list_id}"
                )

            # Prevent checkout of already checked out tools
            if getattr(item, 'checked_out', False):
                raise BusinessRuleError(f"Tool is already checked out")

            with self.transaction():
                # Update tool list status if it's the first checkout
                if tool_list.status == ToolListStatus.DRAFT.value:
                    self.tool_list_repository.update(
                        tool_list_id,
                        {'status': ToolListStatus.IN_PROGRESS.value}
                    )

                # Update item checkout status
                item_update = {
                    'checked_out': True,
                    'checked_out_date': datetime.now(),
                    'returned': False,
                    'returned_date': None
                }
                updated_item = self.tool_list_repository.update_item(item_id, item_update)

                # Update tool inventory
                tool_id = getattr(item, 'tool_id', None)
                if tool_id:
                    inventory = self.inventory_repository.get_by_item('tool', tool_id)
                    if inventory:
                        # Reduce available quantity
                        new_quantity = max(0, inventory.quantity - 1)
                        status = (
                            InventoryStatus.OUT_OF_STOCK.value
                            if new_quantity == 0
                            else InventoryStatus.IN_STOCK.value
                        )

                        # Record transaction
                        transaction_data = {
                            'inventory_id': inventory.id,
                            'transaction_type': TransactionType.USAGE.value,
                            'quantity': 1,
                            'reason': f"Tool checkout for tool list {tool_list_id}",
                            'performed_by': 'system'
                        }
                        self.inventory_repository.create_transaction(transaction_data)

                        # Update inventory
                        self.inventory_repository.update(
                            inventory.id,
                            {'quantity': new_quantity, 'status': status}
                        )

                return ToolListItemDTO.from_model(updated_item).to_dict()

        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(
                f"Error checking out tool for item {item_id} in tool list {tool_list_id}: {str(e)}"
            )
            raise

    def return_tool(self, tool_list_id: int, item_id: int) -> Dict[str, Any]:
        """
        Return a tool to a tool list.

        Args:
            tool_list_id: ID of the tool list
            item_id: ID of the tool list item to return

        Returns:
            Updated tool list item data
        """
        try:
            # Validate tool list and item
            tool_list = self.tool_list_repository.get_by_id(tool_list_id)
            if not tool_list:
                raise NotFoundError(f"Tool list with ID {tool_list_id} not found")

            item = self.tool_list_repository.get_item(item_id)
            if not item:
                raise NotFoundError(f"Tool list item with ID {item_id} not found")

            # Validate item belongs to the tool list
            if item.tool_list_id != tool_list_id:
                raise ValidationError(
                    f"Item {item_id} does not belong to tool list {tool_list_id}"
                )

            # Prevent returning an already returned or unchecked out tool
            if not getattr(item, 'checked_out', False) or getattr(item, 'returned', False):
                raise BusinessRuleError(f"Tool is not checked out")

            with self.transaction():
                # Update item return status
                item_update = {
                    'returned': True,
                    'returned_date': datetime.now()
                }
                updated_item = self.tool_list_repository.update_item(item_id, item_update)

                # Update tool inventory
                tool_id = getattr(item, 'tool_id', None)
                if tool_id:
                    inventory = self.inventory_repository.get_by_item('tool', tool_id)
                    if inventory:
                        # Increase available quantity
                        new_quantity = inventory.quantity + 1
                        status = InventoryStatus.IN_STOCK.value

                        # Record transaction
                        transaction_data = {
                            'inventory_id': inventory.id,
                            'transaction_type': TransactionType.RESTOCK.value,
                            'quantity': 1,
                            'reason': f"Tool return for tool list {tool_list_id}",
                            'performed_by': 'system'
                        }
                        self.inventory_repository.create_transaction(transaction_data)

                        # Update inventory
                        self.inventory_repository.update(
                            inventory.id,
                            {'quantity': new_quantity, 'status': status}
                        )

                # Check if all tools are returned
                all_items = self.tool_list_repository.get_items(tool_list_id)
                all_returned = all(
                    (not getattr(item, 'checked_out', False)) or
                    getattr(item, 'returned', False)
                    for item in all_items
                )

                # Mark tool list as completed if all tools are returned
                if all_returned and tool_list.status == ToolListStatus.IN_PROGRESS.value:
                    self.tool_list_repository.update(
                        tool_list_id,
                        {'status': ToolListStatus.COMPLETED.value}
                    )

                return ToolListItemDTO.from_model(updated_item).to_dict()

        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(
                f"Error returning tool for item {item_id} in tool list {tool_list_id}: {str(e)}"
            )
            raise

    def generate_for_project(
            self,
            project_id: int,
            project_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a recommended tool list for a specific project.

        Args:
            project_id: ID of the project
            project_type: Optional project type override

        Returns:
            Generated tool list data
        """
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Check for existing tool lists
            existing_lists = self.tool_list_repository.get_by_project(project_id)
            if existing_lists:
                self.logger.info(f"Project {project_id} already has {len(existing_lists)} tool list(s)")
                return ToolListDTO.from_model(
                    existing_lists[0],
                    include_items=True,
                    include_project=True
                ).to_dict()

            # Determine project type
            if not project_type:
                project_type = getattr(project, 'project_type', None)
                if not project_type:
                    raise ValidationError(
                        f"No project type specified for project {project_id}"
                    )

            # Create tool list
            tool_list_data = {
                'project_id': project_id,
                'status': ToolListStatus.DRAFT.value,
                'notes': f"Automatically generated for project: {project.name}",
                'created_at': datetime.now()
            }

            with self.transaction():
                # Create tool list
                tool_list = self.tool_list_repository.create(tool_list_data)

                # Get recommended tools
                recommended_tools = self._get_project_recommended_tools(project_type)

                # Add tools to tool list
                for tool_data in recommended_tools:
                    tool_id = tool_data.get('id')

                    item_data = {
                        'tool_list_id': tool_list.id,
                        'tool_id': tool_id,
                        'quantity': 1,
                        'checked_out': False,
                        'returned': False
                    }
                    self.tool_list_repository.add_item(item_data)

                # Retrieve and return complete tool list
                result = self.tool_list_repository.get_by_id(tool_list.id)
                return ToolListDTO.from_model(
                    result,
                    include_items=True,
                    include_project=True
                ).to_dict()

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(
                f"Error generating tool list for project {project_id}: {str(e)}"
            )
            raise

    def _get_project_recommended_tools(
            self,
            project_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get recommended tools for a specific project type.

        Args:
            project_type: Type of project to get tools for

        Returns:
            List of recommended tools
        """
        try:
            # Validate project type
            if not hasattr(ProjectType, project_type):
                raise ValidationError(f"Invalid project type: {project_type}")

            # Define base tool categories for all projects
            common_tools = [
                ToolCategory.MEASURING.value,
                ToolCategory.CUTTING.value
            ]

            # Project-specific tool categories
            project_tools = {
                ProjectType.WALLET.value: [
                    ToolCategory.PUNCHING.value,
                    ToolCategory.STITCHING.value,
                    ToolCategory.EDGE_WORK.value
                ],
                ProjectType.BELT.value: [
                    ToolCategory.PUNCHING.value,
                    ToolCategory.EDGE_WORK.value
                ],
                ProjectType.BAG.value: [
                    ToolCategory.PUNCHING.value,
                    ToolCategory.STITCHING.value,
                    ToolCategory.HARDWARE_INSTALLATION.value
                ],
                # Add more project-specific tool requirements
            }

            # Combine tool categories
            tool_categories = common_tools.copy()
            if project_type in project_tools:
                tool_categories.extend(project_tools[project_type])

            # Find available tools in these categories
            recommended_tools = []
            for category in tool_categories:
                # Get tools in category with available inventory
                tools = self.tool_repository.get_available_tools_by_category(category, limit=1)

                for tool in tools:
                    tool_dict = {
                        'id': tool.id,
                        'name': tool.name,
                        'category': tool.tool_category,
                        'description': getattr(tool, 'description', None)
                    }
                    recommended_tools.append(tool_dict)

            return recommended_tools

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error getting recommended tools for project type {project_type}: {str(e)}"
            )
            raise