# database/repositories/picking_list_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc

from database.models.picking_list import PickingList
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import PickingListStatus


class PickingListRepository(BaseRepository[PickingList]):
    """Repository for picking list operations.

    This repository provides methods for querying and manipulating picking list data,
    including relationships with sales, projects, and inventory.
    """

    def _get_model_class(self) -> Type[PickingList]:
        """Return the model class this repository manages.

        Returns:
            The PickingList model class
        """
        return PickingList

    # Picking list-specific query methods

    def get_by_status(self, status: PickingListStatus) -> List[PickingList]:
        """Get picking lists by status.

        Args:
            status: Picking list status to filter by

        Returns:
            List of picking list instances with the specified status
        """
        self.logger.debug(f"Getting picking lists with status '{status.value}'")
        return self.session.query(PickingList).filter(PickingList.status == status).all()

    def get_by_project(self, project_id: int) -> List[PickingList]:
        """Get picking lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of picking list instances for the specified project
        """
        self.logger.debug(f"Getting picking lists for project {project_id}")
        return self.session.query(PickingList).filter(PickingList.project_id == project_id).all()

    def get_by_sales(self, sales_id: int) -> List[PickingList]:
        """Get picking lists for a specific sales order.

        Args:
            sales_id: ID of the sales order

        Returns:
            List of picking list instances for the specified sales order
        """
        self.logger.debug(f"Getting picking lists for sales order {sales_id}")
        return self.session.query(PickingList).filter(PickingList.sales_id == sales_id).all()

    def get_active_picking_lists(self) -> List[PickingList]:
        """Get all active picking lists (not completed or cancelled).

        Returns:
            List of active picking list instances
        """
        self.logger.debug("Getting all active picking lists")
        active_statuses = [
            PickingListStatus.DRAFT,
            PickingListStatus.PENDING,
            PickingListStatus.IN_PROGRESS,
            PickingListStatus.ON_HOLD
        ]
        return self.session.query(PickingList).filter(PickingList.status.in_(active_statuses)).all()

    def get_picking_list_with_items(self, picking_list_id: int) -> Optional[Dict[str, Any]]:
        """Get picking list with its items.

        Args:
            picking_list_id: ID of the picking list

        Returns:
            Picking list with items or None if not found
        """
        self.logger.debug(f"Getting picking list {picking_list_id} with items")
        from database.models.picking_list_item import PickingListItem
        from database.models.component import Component
        from database.models.material import Material

        picking_list = self.get_by_id(picking_list_id)
        if not picking_list:
            return None

        # Get picking list data
        result = picking_list.to_dict()

        # Get items
        items = self.session.query(PickingListItem).filter(
            PickingListItem.picking_list_id == picking_list_id
        ).all()

        result['items'] = []
        for item in items:
            item_dict = item.to_dict()

            # Add component details if available
            if item.component_id:
                component = self.session.query(Component).get(item.component_id)
                if component:
                    item_dict['component_name'] = component.name
                    item_dict['component_type'] = component.component_type.value

            # Add material details if available
            if item.material_id:
                material = self.session.query(Material).get(item.material_id)
                if material:
                    item_dict['material_name'] = material.name
                    item_dict['material_type'] = material.material_type.value

            result['items'].append(item_dict)

        # Add related info
        if picking_list.project_id:
            from database.models.project import Project
            project = self.session.query(Project).get(picking_list.project_id)
            if project:
                result['project_name'] = project.name

        if picking_list.sales_id:
            from database.models.sales import Sales
            sales = self.session.query(Sales).get(picking_list.sales_id)
            if sales:
                result['sales_reference'] = f"Order #{sales.id}"

        return result

    # Business logic methods

    def create_picking_list_with_items(self, picking_list_data: Dict[str, Any],
                                       items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a picking list with items.

        Args:
            picking_list_data: Picking list data dictionary
            items: List of item dictionaries (component_id or material_id required)

        Returns:
            Created picking list with items
        """
        self.logger.debug("Creating picking list with items")
        from database.models.picking_list_item import PickingListItem

        try:
            # Create picking list
            picking_list = PickingList(**picking_list_data)
            created_picking_list = self.create(picking_list)

            # Add items
            picking_list_items = []
            for item_data in items:
                # Validate that at least one ID is provided
                if not item_data.get('component_id') and not item_data.get('material_id'):
                    raise ValidationError("Either component_id or material_id must be provided for picking list item")

                picking_list_item = PickingListItem(
                    picking_list_id=created_picking_list.id,
                    component_id=item_data.get('component_id'),
                    material_id=item_data.get('material_id'),
                    quantity_ordered=item_data.get('quantity_ordered', 0),
                    quantity_picked=item_data.get('quantity_picked', 0)
                )
                self.session.add(picking_list_item)
                picking_list_items.append(picking_list_item)

            # Flush to get IDs
            self.session.flush()

            # Prepare result
            result = created_picking_list.to_dict()
            result['items'] = [item.to_dict() for item in picking_list_items]

            return result

        except Exception as e:
            self.logger.error(f"Error creating picking list with items: {str(e)}")
            raise ValidationError(f"Failed to create picking list with items: {str(e)}")

    def update_picking_list_status(self, picking_list_id: int,
                                   status: PickingListStatus,
                                   notes: Optional[str] = None) -> Dict[str, Any]:
        """Update picking list status.

        Args:
            picking_list_id: ID of the picking list
            status: New status
            notes: Optional notes about the status change

        Returns:
            Updated picking list data

        Raises:
            EntityNotFoundError: If picking list not found
        """
        self.logger.debug(f"Updating status for picking list {picking_list_id} to {status.value}")

        picking_list = self.get_by_id(picking_list_id)
        if not picking_list:
            raise EntityNotFoundError(f"Picking list with ID {picking_list_id} not found")

        try:
            # Update status
            picking_list.status = status

            # Add notes if provided
            if notes:
                # Append to existing notes or create new ones
                if picking_list.notes:
                    picking_list.notes += f"\n\n{datetime.now().isoformat()}: Status changed to {status.value}\n{notes}"
                else:
                    picking_list.notes = f"{datetime.now().isoformat()}: Status changed to {status.value}\n{notes}"

            # Special handling for status changes
            if status == PickingListStatus.COMPLETED:
                picking_list.completed_at = datetime.now()

                # Update inventory when picking list is completed
                # This would typically be done in a service layer with transaction management
                from database.models.picking_list_item import PickingListItem
                from database.models.inventory import Inventory
                from database.models.enums import InventoryStatus, InventoryAdjustmentType

                # Get picking list items
                items = self.session.query(PickingListItem).filter(
                    PickingListItem.picking_list_id == picking_list_id
                ).all()

                for item in items:
                    # Only process items that have been picked
                    if item.quantity_picked <= 0:
                        continue

                    # Determine the item type and ID (component or material)
                    if item.material_id:
                        item_type = 'material'
                        item_id = item.material_id
                    elif item.component_id:
                        # Components themselves aren't typically in inventory
                        # This would be handled differently in a real implementation
                        continue
                    else:
                        continue

                    # Find inventory record
                    inventory = self.session.query(Inventory).filter(
                        Inventory.item_id == item_id,
                        Inventory.item_type == item_type
                    ).first()

                    if inventory:
                        # Update inventory
                        original_quantity = inventory.quantity
                        inventory.quantity -= item.quantity_picked

                        # Don't allow negative inventory
                        if inventory.quantity < 0:
                            inventory.quantity = 0

                        # Update status based on new quantity
                        if inventory.quantity <= 0:
                            inventory.status = InventoryStatus.OUT_OF_STOCK
                        elif hasattr(item, 'min_stock') and inventory.quantity <= item.min_stock:
                            inventory.status = InventoryStatus.LOW_STOCK

                        # Record inventory transaction history (if implemented)
                        # self._record_inventory_transaction(...)

            # Update picking list
            self.update(picking_list)

            return picking_list.to_dict()

        except Exception as e:
            self.logger.error(f"Error updating picking list status: {str(e)}")
            raise ValidationError(f"Failed to update picking list status: {str(e)}")

    def generate_picking_list_for_project(self, project_id: int) -> Dict[str, Any]:
        """Generate a picking list for a project based on its components and materials.

        Args:
            project_id: ID of the project

        Returns:
            Generated picking list with items

        Raises:
            EntityNotFoundError: If project not found
        """
        self.logger.debug(f"Generating picking list for project {project_id}")
        from database.models.project import Project
        from database.models.project_component import ProjectComponent
        from database.models.component import Component
        from database.models.component_material import ComponentMaterial

        project = self.session.query(Project).get(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        try:
            # Create picking list
            picking_list = PickingList(
                project_id=project_id,
                status=PickingListStatus.DRAFT,
                created_at=datetime.now()
            )
            self.session.add(picking_list)
            self.session.flush()  # Get the ID

            # Get project components
            project_components = self.session.query(ProjectComponent).filter(
                ProjectComponent.project_id == project_id
            ).all()

            # Generate items
            from database.models.picking_list_item import PickingListItem

            picking_list_items = []

            # Add component items
            for pc in project_components:
                component = self.session.query(Component).get(pc.component_id)
                if not component:
                    continue

                # Add the component itself
                component_item = PickingListItem(
                    picking_list_id=picking_list.id,
                    component_id=component.id,
                    quantity_ordered=pc.quantity,
                    quantity_picked=0
                )
                self.session.add(component_item)
                picking_list_items.append(component_item)

                # Get materials for this component
                component_materials = self.session.query(ComponentMaterial).filter(
                    ComponentMaterial.component_id == component.id
                ).all()

                # Add materials
                for cm in component_materials:
                    # Calculate quantity based on project component quantity
                    quantity = cm.quantity * pc.quantity

                    material_item = PickingListItem(
                        picking_list_id=picking_list.id,
                        material_id=cm.material_id,
                        quantity_ordered=quantity,
                        quantity_picked=0
                    )
                    self.session.add(material_item)
                    picking_list_items.append(material_item)

            self.session.flush()

            # Prepare result
            result = picking_list.to_dict()
            result['items'] = [item.to_dict() for item in picking_list_items]

            return result

        except Exception as e:
            self.logger.error(f"Error generating picking list for project: {str(e)}")
            raise ValidationError(f"Failed to generate picking list for project: {str(e)}")

    # GUI-specific functionality

    def get_picking_list_dashboard_data(self) -> Dict[str, Any]:
        """Get data for picking list dashboard in GUI.

        Returns:
            Dictionary with dashboard data for picking lists
        """
        self.logger.debug("Getting picking list dashboard data")

        # Count by status
        status_counts = self.session.query(
            PickingList.status,
            func.count().label('count')
        ).group_by(PickingList.status).all()

        status_data = {s.value: count for s, count in status_counts}

        # Get active picking lists
        active_picking_lists = self.get_active_picking_lists()

        # Get completed picking lists for the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_completed = self.session.query(PickingList).filter(
            PickingList.status == PickingListStatus.COMPLETED,
            PickingList.completed_at >= thirty_days_ago
        ).order_by(PickingList.completed_at.desc()).all()

        # Calculate completion time statistics
        completion_times = []
        for pl in recent_completed:
            if pl.created_at and pl.completed_at:
                duration = (pl.completed_at - pl.created_at).total_seconds() / 3600  # Hours
                completion_times.append(duration)

        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else None

        # Get projects with active picking lists
        projects_with_lists = {}
        for pl in active_picking_lists:
            if pl.project_id:
                if pl.project_id not in projects_with_lists:
                    projects_with_lists[pl.project_id] = 0
                projects_with_lists[pl.project_id] += 1

        return {
            'status_counts': status_data,
            'active_count': len(active_picking_lists),
            'recently_completed_count': len(recent_completed),
            'avg_completion_time': avg_completion_time,  # In hours
            'active_picking_lists': [p.to_dict() for p in active_picking_lists[:5]],  # Top 5
            'recent_completed': [p.to_dict() for p in recent_completed[:5]],  # Top 5
            'projects_with_lists_count': len(projects_with_lists)
        }