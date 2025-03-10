from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc

from database.models.tool_list import ToolList
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import ToolListStatus


class ToolListRepository(BaseRepository[ToolList]):
    """Repository for tool list operations.

    This repository provides methods for querying and manipulating tool list data,
    including relationships with projects and tools.
    """

    def _get_model_class(self) -> Type[ToolList]:
        """Return the model class this repository manages.

        Returns:
            The ToolList model class
        """
        return ToolList

    # Tool list-specific query methods

    def get_by_status(self, status: ToolListStatus) -> List[ToolList]:
        """Get tool lists by status.

        Args:
            status: Tool list status to filter by

        Returns:
            List of tool list instances with the specified status
        """
        self.logger.debug(f"Getting tool lists with status '{status.value}'")
        return self.session.query(ToolList).filter(ToolList.status == status).all()

    def get_by_project(self, project_id: int) -> List[ToolList]:
        """Get tool lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of tool list instances for the specified project
        """
        self.logger.debug(f"Getting tool lists for project {project_id}")
        return self.session.query(ToolList).filter(ToolList.project_id == project_id).all()

    def get_active_tool_lists(self) -> List[ToolList]:
        """Get all active tool lists (not completed or cancelled).

        Returns:
            List of active tool list instances
        """
        self.logger.debug("Getting all active tool lists")
        active_statuses = [
            ToolListStatus.DRAFT,
            ToolListStatus.PENDING,
            ToolListStatus.IN_PROGRESS,
            ToolListStatus.ON_HOLD,
            ToolListStatus.READY,
            ToolListStatus.IN_USE
        ]
        return self.session.query(ToolList).filter(ToolList.status.in_(active_statuses)).all()

    def get_tool_list_with_items(self, tool_list_id: int) -> Optional[Dict[str, Any]]:
        """Get tool list with its items.

        Args:
            tool_list_id: ID of the tool list

        Returns:
            Tool list with items or None if not found
        """
        self.logger.debug(f"Getting tool list {tool_list_id} with items")
        from database.models.tool_list_item import ToolListItem
        from database.models.tool import Tool

        tool_list = self.get_by_id(tool_list_id)
        if not tool_list:
            return None

        # Get tool list data
        result = tool_list.to_dict()

        # Get items
        items = self.session.query(ToolListItem).filter(
            ToolListItem.tool_list_id == tool_list_id
        ).all()

        result['items'] = []
        for item in items:
            item_dict = item.to_dict()

            # Add tool details
            tool = self.session.query(Tool).get(item.tool_id)
            if tool:
                item_dict['tool_name'] = tool.name
                item_dict['tool_type'] = tool.tool_type.value

            result['items'].append(item_dict)

        # Add related info
        if tool_list.project_id:
            from database.models.project import Project
            project = self.session.query(Project).get(tool_list.project_id)
            if project:
                result['project_name'] = project.name

        return result

    # Business logic methods

    def create_tool_list_with_items(self, tool_list_data: Dict[str, Any],
                                    items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a tool list with items.

        Args:
            tool_list_data: Tool list data dictionary
            items: List of item dictionaries with tool_id and quantity

        Returns:
            Created tool list with items
        """
        self.logger.debug("Creating tool list with items")
        from database.models.tool_list_item import ToolListItem

        try:
            # Create tool list
            tool_list = ToolList(**tool_list_data)
            created_tool_list = self.create(tool_list)

            # Add items
            tool_list_items = []
            for item_data in items:
                tool_list_item = ToolListItem(
                    tool_list_id=created_tool_list.id,
                    tool_id=item_data['tool_id'],
                    quantity=item_data['quantity']
                )
                self.session.add(tool_list_item)
                tool_list_items.append(tool_list_item)

            # Flush to get IDs
            self.session.flush()

            # Prepare result
            result = created_tool_list.to_dict()
            result['items'] = [item.to_dict() for item in tool_list_items]

            return result

        except Exception as e:
            self.logger.error(f"Error creating tool list with items: {str(e)}")
            raise ValidationError(f"Failed to create tool list with items: {str(e)}")

    def update_tool_list_status(self, tool_list_id: int,
                                status: ToolListStatus,
                                notes: Optional[str] = None) -> Dict[str, Any]:
        """Update tool list status.

        Args:
            tool_list_id: ID of the tool list
            status: New status
            notes: Optional notes about the status change

        Returns:
            Updated tool list data

        Raises:
            EntityNotFoundError: If tool list not found
        """
        self.logger.debug(f"Updating status for tool list {tool_list_id} to {status.value}")

        tool_list = self.get_by_id(tool_list_id)
        if not tool_list:
            raise EntityNotFoundError(f"Tool list with ID {tool_list_id} not found")

        try:
            # Update status
            tool_list.status = status

            # Add notes if provided
            if notes:
                # Append to existing notes or create new ones
                if tool_list.notes:
                    tool_list.notes += f"\n\n{datetime.now().isoformat()}: Status changed to {status.value}\n{notes}"
                else:
                    tool_list.notes = f"{datetime.now().isoformat()}: Status changed to {status.value}\n{notes}"

            # Update tool list
            self.update(tool_list)

            return tool_list.to_dict()

        except Exception as e:
            self.logger.error(f"Error updating tool list status: {str(e)}")
            raise ValidationError(f"Failed to update tool list status: {str(e)}")

    def generate_tool_list_for_project(self, project_id: int) -> Dict[str, Any]:
        """Generate a tool list for a project based on its type and requirements.

        Args:
            project_id: ID of the project

        Returns:
            Generated tool list with items

        Raises:
            EntityNotFoundError: If project not found
        """
        self.logger.debug(f"Generating tool list for project {project_id}")
        from database.models.project import Project
        from database.models.tool import Tool
        from database.models.enums import ToolCategory, ProjectType

        project = self.session.query(Project).get(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        try:
            # Create tool list
            tool_list = ToolList(
                project_id=project_id,
                status=ToolListStatus.DRAFT,
                created_at=datetime.now()
            )
            self.session.add(tool_list)
            self.session.flush()  # Get the ID

            # Determine required tool categories based on project type
            required_categories = []

            # This is a simplified logic - in a real system this would be more sophisticated
            # and likely based on a mapping table or similar configuration
            if project.type == ProjectType.WALLET:
                required_categories = [
                    ToolCategory.CUTTING,
                    ToolCategory.STITCHING,
                    ToolCategory.EDGE_WORK,
                    ToolCategory.FINISHING
                ]
            elif project.type == ProjectType.BELT:
                required_categories = []

                # This is a simplified logic - in a real system this would be more sophisticated
                # and likely based on a mapping table or similar configuration
                if project.type == ProjectType.WALLET:
                    required_categories = [
                        ToolCategory.CUTTING,
                        ToolCategory.STITCHING,
                        ToolCategory.EDGE_WORK,
                        ToolCategory.FINISHING
                    ]
                elif project.type == ProjectType.BELT:
                    required_categories = [
                        ToolCategory.CUTTING,
                        ToolCategory.PUNCHING,
                        ToolCategory.EDGE_WORK
                    ]
                elif project.type in [ProjectType.MESSENGER_BAG, ProjectType.TOTE_BAG, ProjectType.BACKPACK]:
                    required_categories = [
                        ToolCategory.CUTTING,
                        ToolCategory.STITCHING,
                        ToolCategory.EDGE_WORK,
                        ToolCategory.HARDWARE_INSTALLATION
                    ]
                else:
                    # Default tool categories for any project
                    required_categories = [
                        ToolCategory.CUTTING,
                        ToolCategory.MEASURING,
                        ToolCategory.FINISHING
                    ]

                # Get tools for each required category
                from database.models.tool_list_item import ToolListItem

                tool_list_items = []

                for category in required_categories:
                    # Get tools in this category
                    tools = self.session.query(Tool).filter(
                        Tool.tool_type == category
                    ).all()

                    for tool in tools:
                        # Add tool to list (assuming quantity 1 for simplicity)
                        tool_item = ToolListItem(
                            tool_list_id=tool_list.id,
                            tool_id=tool.id,
                            quantity=1
                        )
                        self.session.add(tool_item)
                        tool_list_items.append(tool_item)

                self.session.flush()

                # Prepare result
                result = tool_list.to_dict()
                result['items'] = [item.to_dict() for item in tool_list_items]

                return result

        except Exception as e:
            self.logger.error(f"Error generating tool list for project: {str(e)}")
            raise ValidationError(f"Failed to generate tool list for project: {str(e)}")

    # GUI-specific functionality

    def get_tool_list_dashboard_data(self) -> Dict[str, Any]:
        """Get data for tool list dashboard in GUI.

        Returns:
            Dictionary with dashboard data for tool lists
        """
        self.logger.debug("Getting tool list dashboard data")

        # Count by status
        status_counts = self.session.query(
            ToolList.status,
            func.count().label('count')
        ).group_by(ToolList.status).all()

        status_data = {s.value: count for s, count in status_counts}

        # Get active tool lists
        active_tool_lists = self.get_active_tool_lists()

        # Get completed tool lists for the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        completed = self.session.query(ToolList).filter(
            ToolList.status == ToolListStatus.COMPLETED,
            ToolList.created_at >= thirty_days_ago
        ).all()

        # Get projects with active tool lists
        projects_with_lists = {}
        for tl in active_tool_lists:
            if tl.project_id:
                if tl.project_id not in projects_with_lists:
                    projects_with_lists[tl.project_id] = 0
                projects_with_lists[tl.project_id] += 1

        # Get most used tools
        from database.models.tool_list_item import ToolListItem
        from database.models.tool import Tool

        most_used_tools_query = self.session.query(
            Tool.id,
            Tool.name,
            Tool.tool_type,
            func.count(ToolListItem.id).label('usage_count')
        ).join(
            ToolListItem,
            ToolListItem.tool_id == Tool.id
        ).group_by(
            Tool.id,
            Tool.name,
            Tool.tool_type
        ).order_by(
            func.count(ToolListItem.id).desc()
        ).limit(5)

        most_used_tools = []
        for id, name, tool_type, usage_count in most_used_tools_query.all():
            most_used_tools.append({
                'id': id,
                'name': name,
                'tool_type': tool_type.value,
                'usage_count': usage_count
            })

        return {
            'status_counts': status_data,
            'active_count': len(active_tool_lists),
            'completed_count': len(completed),
            'active_tool_lists': [tl.to_dict() for tl in active_tool_lists[:5]],  # Top 5
            'projects_with_lists_count': len(projects_with_lists),
            'most_used_tools': most_used_tools
        }