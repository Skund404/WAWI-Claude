# database/repositories/tool_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Union, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, case, distinct

from database.models.tool import Tool
from database.models.inventory import Inventory
from database.models.enums import ToolCategory, InventoryStatus, ToolListStatus
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError


class ToolRepository(BaseRepository[Tool]):
    """Repository for tool management operations.

    This repository provides specialized methods for accessing and manipulating
    tool data, along with business logic operations and GUI-specific functionality.
    """

    def _get_model_class(self) -> Type[Tool]:
        """Return the model class this repository manages.

        Returns:
            The Tool model class
        """
        return Tool

    # Basic query methods

    def get_by_name(self, name: str) -> Optional[Tool]:
        """Get tool by exact name match.

        Args:
            name: Tool name to search for

        Returns:
            Tool instance or None if not found
        """
        self.logger.debug(f"Getting tool with name '{name}'")
        return self.session.query(Tool).filter(Tool.name == name).first()

    def get_by_category(self, category: ToolCategory) -> List[Tool]:
        """Get tools by category.

        Args:
            category: Tool category to filter by

        Returns:
            List of tool instances matching the category
        """
        self.logger.debug(f"Getting tools with category '{category.value}'")
        return self.session.query(Tool).filter(Tool.tool_type == category).all()

    def get_by_supplier(self, supplier_id: int) -> List[Tool]:
        """Get tools from a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of tool instances from the specified supplier
        """
        self.logger.debug(f"Getting tools from supplier ID {supplier_id}")
        return self.session.query(Tool).filter(Tool.supplier_id == supplier_id).all()

    def search_tools(self, search_term: str, categories: Optional[List[ToolCategory]] = None) -> List[Tool]:
        """Search tools by term with optional category filtering.

        Args:
            search_term: Term to search for in name and description
            categories: Optional list of categories to filter by

        Returns:
            List of matching tool instances
        """
        self.logger.debug(f"Searching tools with term '{search_term}' and categories {categories}")
        query = self.session.query(Tool).filter(
            or_(
                Tool.name.ilike(f"%{search_term}%"),
                Tool.description.ilike(f"%{search_term}%")
            )
        )

        if categories:
            query = query.filter(Tool.tool_type.in_(categories))

        return query.all()

    # Inventory-related methods

    def get_with_inventory_status(self) -> List[Dict[str, Any]]:
        """Get tools with current inventory status.

        Returns:
            List of tool dictionaries with inventory information
        """
        self.logger.debug("Getting tools with inventory status")
        from database.models.inventory import Inventory

        query = self.session.query(Tool, Inventory). \
            outerjoin(Inventory,
                      (Inventory.item_id == Tool.id) &
                      (Inventory.item_type == 'tool'))

        result = []
        for tool, inventory in query.all():
            tool_dict = tool.to_dict()
            if inventory:
                tool_dict['current_stock'] = inventory.quantity
                tool_dict['stock_status'] = inventory.status.value
                tool_dict['storage_location'] = inventory.storage_location
            else:
                tool_dict['current_stock'] = 0
                tool_dict['stock_status'] = 'NOT_TRACKED'
                tool_dict['storage_location'] = None
            result.append(tool_dict)

        return result

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get tools that are currently available (in stock).

        Returns:
            List of available tool dictionaries with inventory information
        """
        self.logger.debug("Getting available tools")
        from database.models.inventory import Inventory

        query = self.session.query(Tool, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Tool.id) &
                 (Inventory.item_type == 'tool')). \
            filter(Inventory.quantity > 0)

        result = []
        for tool, inventory in query.all():
            tool_dict = tool.to_dict()
            tool_dict['current_stock'] = inventory.quantity
            tool_dict['stock_status'] = inventory.status.value
            tool_dict['storage_location'] = inventory.storage_location
            result.append(tool_dict)

        return result

    def get_low_stock_tools(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Get tools with low stock levels.

        Args:
            threshold: Quantity threshold for low stock determination

        Returns:
            List of low stock tool dictionaries with inventory information
        """
        self.logger.debug(f"Getting low stock tools (threshold: {threshold})")
        from database.models.inventory import Inventory

        query = self.session.query(Tool, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Tool.id) &
                 (Inventory.item_type == 'tool')). \
            filter(Inventory.quantity <= threshold). \
            filter(Inventory.quantity > 0)

        result = []
        for tool, inventory in query.all():
            tool_dict = tool.to_dict()
            tool_dict['current_stock'] = inventory.quantity
            tool_dict['stock_status'] = inventory.status.value
            tool_dict['storage_location'] = inventory.storage_location
            result.append(tool_dict)

        return result

    def get_out_of_stock_tools(self) -> List[Dict[str, Any]]:
        """Get tools that are currently out of stock.

        Returns:
            List of out-of-stock tool dictionaries with inventory information
        """
        self.logger.debug("Getting out of stock tools")
        from database.models.inventory import Inventory

        query = self.session.query(Tool, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Tool.id) &
                 (Inventory.item_type == 'tool')). \
            filter(Inventory.quantity <= 0)

        result = []
        for tool, inventory in query.all():
            tool_dict = tool.to_dict()
            tool_dict['current_stock'] = inventory.quantity
            tool_dict['stock_status'] = inventory.status.value
            tool_dict['storage_location'] = inventory.storage_location
            result.append(tool_dict)

        return result

    # Business logic methods

    def create_tool_with_inventory(self, tool_data: Dict[str, Any], inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tool with associated inventory record.

        Args:
            tool_data: Tool data dictionary
            inventory_data: Inventory data dictionary

        Returns:
            Created tool with inventory information

        Raises:
            ValidationError: If validation fails
        """
        self.logger.debug("Creating new tool with inventory")
        from database.models.inventory import Inventory

        try:
            # Start transaction
            # Create tool
            tool = Tool(**tool_data)
            created_tool = self.create(tool)

            # Create inventory record
            inventory = Inventory(
                item_id=created_tool.id,
                item_type='tool',
                **inventory_data
            )
            self.session.add(inventory)
            self.session.flush()

            # Prepare result
            result = created_tool.to_dict()
            result['inventory'] = inventory.to_dict()

            return result
        except Exception as e:
            self.logger.error(f"Error creating tool with inventory: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to create tool with inventory: {str(e)}")

    def update_tool_status(self, tool_id: int, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update tool status and inventory information.

        Args:
            tool_id: ID of the tool to update
            status_data: Status data including quantity, status, location

        Returns:
            Updated tool with inventory information

        Raises:
            EntityNotFoundError: If tool not found
            ValidationError: If validation fails
        """
        self.logger.debug(f"Updating tool status for tool ID {tool_id}")
        from database.models.inventory import Inventory

        tool = self.get_by_id(tool_id)
        if not tool:
            raise EntityNotFoundError(f"Tool with ID {tool_id} not found")

        try:
            # Get or create inventory record
            inventory = self.session.query(Inventory). \
                filter(Inventory.item_id == tool_id). \
                filter(Inventory.item_type == 'tool').first()

            if not inventory:
                inventory = Inventory(
                    item_id=tool_id,
                    item_type='tool',
                    quantity=status_data.get('quantity', 0),
                    status=status_data.get('status', InventoryStatus.IN_STOCK),
                    storage_location=status_data.get('storage_location', '')
                )
                self.session.add(inventory)
            else:
                # Update inventory fields
                if 'quantity' in status_data:
                    inventory.quantity = status_data['quantity']
                if 'status' in status_data:
                    inventory.status = status_data['status']
                if 'storage_location' in status_data:
                    inventory.storage_location = status_data['storage_location']

            self.session.flush()

            # Prepare result
            result = tool.to_dict()
            result['inventory'] = inventory.to_dict()

            return result
        except Exception as e:
            self.logger.error(f"Error updating tool status: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to update tool status: {str(e)}")

    def get_tool_usage_history(self, tool_id: int,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get tool usage history from tool lists.

        Args:
            tool_id: ID of the tool
            start_date: Optional start date for history range
            end_date: Optional end date for history range

        Returns:
            List of tool usage records

        Raises:
            EntityNotFoundError: If tool not found
        """
        self.logger.debug(f"Getting usage history for tool ID {tool_id}")
        from database.models.tool_list import ToolList
        from database.models.tool_list_item import ToolListItem
        from database.models.project import Project

        tool = self.get_by_id(tool_id)
        if not tool:
            raise EntityNotFoundError(f"Tool with ID {tool_id} not found")

        # Base query
        query = self.session.query(
            ToolListItem, ToolList, Project
        ).join(
            ToolList, ToolList.id == ToolListItem.tool_list_id
        ).join(
            Project, Project.id == ToolList.project_id
        ).filter(
            ToolListItem.tool_id == tool_id
        )

        # Apply date filters if provided
        if start_date:
            query = query.filter(ToolList.created_at >= start_date)
        if end_date:
            query = query.filter(ToolList.created_at <= end_date)

        # Order by date
        query = query.order_by(ToolList.created_at.desc())

        # Execute query
        result = []
        for item, tool_list, project in query.all():
            result.append({
                'tool_list_id': tool_list.id,
                'tool_list_status': tool_list.status.value,
                'project_id': project.id,
                'project_name': project.name,
                'project_type': project.type.value,
                'quantity': item.quantity,
                'date_required': tool_list.created_at.isoformat(),
                'is_complete': tool_list.status == ToolListStatus.COMPLETED
            })

        return result

    def get_tools_with_maintenance_info(self) -> List[Dict[str, Any]]:
        """Get tools with maintenance status and information.

        Returns:
            List of tools with maintenance information
        """
        self.logger.debug("Getting tools with maintenance information")
        # In a real implementation, this would join with a maintenance table
        # For now, we'll simulate this with tool attributes

        tools = self.get_all(limit=1000)
        result = []

        for tool in tools:
            tool_dict = tool.to_dict()

            # Add maintenance info (in a real system, this would come from a maintenance table)
            # This is a placeholder for demonstration
            tool_dict['last_maintenance'] = None
            tool_dict['maintenance_due'] = False
            tool_dict['maintenance_notes'] = ""

            # In a real implementation, you would calculate this based on actual maintenance records
            # For demo purposes, we'll randomly mark some tools for maintenance
            import random
            if random.random() < 0.3:  # 30% of tools need maintenance
                last_maintenance = datetime.now() - timedelta(days=random.randint(90, 120))
                tool_dict['last_maintenance'] = last_maintenance.isoformat()
                tool_dict['maintenance_due'] = True
                tool_dict['maintenance_notes'] = "Regular maintenance required"
            elif random.random() < 0.7:  # Another 40% had recent maintenance
                last_maintenance = datetime.now() - timedelta(days=random.randint(1, 60))
                tool_dict['last_maintenance'] = last_maintenance.isoformat()

            result.append(tool_dict)

        return result

    # GUI-specific functionality

    def get_tool_dashboard_data(self) -> Dict[str, Any]:
        """Get data for tool dashboard in GUI.

        Returns:
            Dictionary with dashboard data
        """
        self.logger.debug("Getting tool dashboard data")
        from database.models.inventory import Inventory
        from database.models.tool_list import ToolList
        from database.models.tool_list_item import ToolListItem

        # Get counts by category
        category_counts = self.session.query(
            Tool.tool_type,
            func.count().label('count')
        ).group_by(Tool.tool_type).all()

        category_data = {category.value: count for category, count in category_counts}

        # Get inventory status counts
        inventory_status = self.session.query(
            Inventory.status,
            func.count().label('count')
        ).filter(
            Inventory.item_type == 'tool'
        ).group_by(Inventory.status).all()

        status_data = {status.value: count for status, count in inventory_status}

        # Get tools currently in use (in active tool lists)
        tools_in_use_query = self.session.query(
            Tool.id,
            Tool.name,
            func.sum(ToolListItem.quantity).label('in_use_count')
        ).join(
            ToolListItem, ToolListItem.tool_id == Tool.id
        ).join(
            ToolList, ToolList.id == ToolListItem.tool_list_id
        ).filter(
            ToolList.status.in_([ToolListStatus.IN_PROGRESS])
        ).group_by(
            Tool.id, Tool.name
        ).order_by(
            func.sum(ToolListItem.quantity).desc()
        )

        tools_in_use = [{
            'id': t.id,
            'name': t.name,
            'in_use_count': t.in_use_count
        } for t in tools_in_use_query.all()]

        # Get low stock tools
        low_stock_tools = self.get_low_stock_tools()

        # Combine all data
        return {
            'category_counts': category_data,
            'status_counts': status_data,
            'total_tools': sum(category_data.values()),
            'tools_in_use': tools_in_use[:5],  # Top 5
            'low_stock_count': len(low_stock_tools),
            'low_stock_tools': low_stock_tools[:5],  # Top 5
            'tools_by_location': self._get_tools_by_location(),
            'recent_activity': self._get_recent_tool_activity()
        }

    def _get_tools_by_location(self) -> Dict[str, int]:
        """Get tool counts by storage location.

        Returns:
            Dictionary of location to count
        """
        from database.models.inventory import Inventory

        location_query = self.session.query(
            Inventory.storage_location,
            func.count().label('count')
        ).filter(
            Inventory.item_type == 'tool'
        ).group_by(
            Inventory.storage_location
        ).order_by(
            func.count().desc()
        )

        return {loc: count for loc, count in location_query.all() if loc}

    def _get_recent_tool_activity(self) -> List[Dict[str, Any]]:
        """Get recent tool activity for dashboard.

        Returns:
            List of recent activity records
        """
        # In a real implementation, this would pull from an activity log
        # For this example, we'll return a placeholder
        return [
            {
                'tool_id': 1,
                'tool_name': 'Sample Tool',
                'action': 'CHECKED_OUT',
                'date': datetime.now().isoformat(),
                'user': 'John Doe',
                'project': 'Wallet Project'
            }
        ]

    def export_tools_data(self, format: str = "csv") -> Dict[str, Any]:
        """Export tools data to specified format.

        Args:
            format: Export format ("csv" or "json")

        Returns:
            Dict with export data and metadata
        """
        self.logger.debug(f"Exporting tools data in {format} format")
        tools = self.get_with_inventory_status()

        # Create metadata
        metadata = {
            'count': len(tools),
            'timestamp': datetime.now().isoformat(),
            'format': format,
            'categories': self._get_category_counts()
        }

        return {
            'data': tools,
            'metadata': metadata
        }

    def _get_category_counts(self) -> Dict[str, int]:
        """Get tool counts by category.

        Returns:
            Dictionary of category to count
        """
        category_counts = self.session.query(
            Tool.tool_type,
            func.count().label('count')
        ).group_by(Tool.tool_type).all()

        return {category.value: count for category, count in category_counts}

    def filter_tools_for_gui(self,
                             search_term: Optional[str] = None,
                             categories: Optional[List[ToolCategory]] = None,
                             in_stock_only: bool = False,
                             sort_by: str = 'name',
                             sort_dir: str = 'asc',
                             page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate tools for GUI display.

        Args:
            search_term: Optional search term
            categories: Optional list of categories to filter by
            in_stock_only: Whether to only include in-stock tools
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            page: Page number
            page_size: Page size

        Returns:
            Dict with paginated results and metadata
        """
        self.logger.debug(
            f"Filtering tools for GUI: search='{search_term}', categories={categories}, in_stock_only={in_stock_only}")
        from database.models.inventory import Inventory

        # Start with a query that joins Tool and Inventory
        query = self.session.query(Tool, Inventory). \
            outerjoin(Inventory,
                      (Inventory.item_id == Tool.id) &
                      (Inventory.item_type == 'tool'))

        # Apply search filter if provided
        if search_term:
            query = query.filter(
                or_(
                    Tool.name.ilike(f"%{search_term}%"),
                    Tool.description.ilike(f"%{search_term}%")
                )
            )

        # Apply category filter if provided
        if categories:
            query = query.filter(Tool.tool_type.in_(categories))

        # Apply stock filter if requested
        if in_stock_only:
            query = query.filter(
                (Inventory.quantity > 0) & (Inventory.status != InventoryStatus.OUT_OF_STOCK)
            )

        # Get total count for pagination
        total_count = query.count()

        # Apply sorting
        if sort_by == 'name':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Tool.name.desc())
            else:
                query = query.order_by(Tool.name.asc())
        elif sort_by == 'category':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Tool.tool_type.desc())
            else:
                query = query.order_by(Tool.tool_type.asc())
        elif sort_by == 'stock':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Inventory.quantity.desc())
            else:
                query = query.order_by(Inventory.quantity.asc())
        else:
            # Default to name
            query = query.order_by(Tool.name.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query and format results
        items = []
        for tool, inventory in query.all():
            tool_dict = tool.to_dict()
            if inventory:
                tool_dict['current_stock'] = inventory.quantity
                tool_dict['stock_status'] = inventory.status.value
                tool_dict['storage_location'] = inventory.storage_location
            else:
                tool_dict['current_stock'] = 0
                tool_dict['stock_status'] = 'NOT_TRACKED'
                tool_dict['storage_location'] = None
            items.append(tool_dict)

        # Return paginated results with metadata
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'pages': (total_count + page_size - 1) // page_size,
            'has_next': page < ((total_count + page_size - 1) // page_size),
            'has_prev': page > 1
        }