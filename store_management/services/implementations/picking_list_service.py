# services/implementations/picking_list_service.py
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from database.repositories.picking_list_repository import PickingListRepository
from database.repositories.project_repository import ProjectRepository
from database.repositories.order_repository import OrderRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.storage_repository import StorageRepository

from services.interfaces.picking_list_service import IPickingListService
from services.base_service import BaseService, NotFoundError, ValidationError
from models.picking_list import PickingList, PickingListItem, PickingListStatus


class PickingListService(BaseService, IPickingListService):
    """Implementation of the picking list service."""

    def __init__(self,
                 picking_list_repository=None,
                 project_repository=None,
                 order_repository=None,
                 material_repository=None,
                 storage_repository=None):
        """Initialize the picking list service."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Initialize repositories - use dependency injection if provided
        self.picking_list_repository = picking_list_repository or PickingListRepository()
        self.project_repository = project_repository or ProjectRepository()
        self.order_repository = order_repository or OrderRepository()
        self.material_repository = material_repository or MaterialRepository()
        self.storage_repository = storage_repository or StorageRepository()

        self.logger.info("Picking List Service initialized")

    def create_picking_list(self, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new picking list."""
        # Validate required fields
        if "name" not in picking_list_data:
            raise ValidationError("Picking list name is required")

        try:
            # Create picking list
            picking_list = self.picking_list_repository.create(picking_list_data)
            self.logger.info(f"Created picking list: {picking_list.name} (ID: {picking_list.id})")

            # Return as dictionary
            return self._format_picking_list(picking_list)
        except Exception as e:
            self.logger.error(f"Error creating picking list: {str(e)}")
            raise

    def get_picking_list(self, picking_list_id: int) -> Dict[str, Any]:
        """Get a picking list by ID."""
        try:
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            return self._format_picking_list(picking_list)
        except Exception as e:
            self.logger.error(f"Error retrieving picking list {picking_list_id}: {str(e)}")
            raise

    def get_all_picking_lists(self) -> List[Dict[str, Any]]:
        """Get all picking lists."""
        try:
            picking_lists = self.picking_list_repository.get_all()
            return [self._format_picking_list(pl) for pl in picking_lists]
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists: {str(e)}")
            raise

    def get_picking_lists_by_status(self, status: PickingListStatus) -> List[Dict[str, Any]]:
        """Get picking lists by status."""
        try:
            picking_lists = self.picking_list_repository.get_by_status(status)
            return [self._format_picking_list(pl) for pl in picking_lists]
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists with status {status}: {str(e)}")
            raise

    def update_picking_list(self, picking_list_id: int, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a picking list."""
        try:
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Update picking list
            updated = self.picking_list_repository.update(picking_list_id, picking_list_data)
            self.logger.info(f"Updated picking list: {updated.name} (ID: {updated.id})")

            return self._format_picking_list(updated)
        except Exception as e:
            self.logger.error(f"Error updating picking list {picking_list_id}: {str(e)}")
            raise

    def delete_picking_list(self, picking_list_id: int) -> bool:
        """Delete a picking list."""
        try:
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Delete picking list
            result = self.picking_list_repository.delete(picking_list_id)
            self.logger.info(f"Deleted picking list ID: {picking_list_id}")

            return result
        except Exception as e:
            self.logger.error(f"Error deleting picking list {picking_list_id}: {str(e)}")
            raise

    def add_item_to_picking_list(self, picking_list_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a picking list."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Validate required fields
            if "name" not in item_data:
                raise ValidationError("Item name is required")

            if "quantity_required" not in item_data:
                raise ValidationError("Item quantity is required")

            if "item_type" not in item_data:
                raise ValidationError("Item type is required")

            # Set picking list ID
            item_data["picking_list_id"] = picking_list_id

            # If material_id is provided, get storage location
            if "material_id" in item_data and item_data["material_id"]:
                material = self.material_repository.get_by_id(item_data["material_id"])
                if material and material.storage_location_id:
                    item_data["storage_location_id"] = material.storage_location_id

            # Create item
            item = self.picking_list_repository.add_item(item_data)
            self.logger.info(f"Added item to picking list {picking_list_id}: {item.name} (ID: {item.id})")

            return self._format_picking_list_item(item)
        except Exception as e:
            self.logger.error(f"Error adding item to picking list {picking_list_id}: {str(e)}")
            raise

    # Additional methods implementation...

    def generate_picking_list_from_project(self, project_id: int) -> Dict[str, Any]:
        """Generate a picking list from a project's required materials."""
        try:
            # Get project
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Create picking list
            picking_list_data = {
                "name": f"Project: {project.name}",
                "project_id": project_id,
                "status": PickingListStatus.DRAFT.name,
                "notes": f"Auto-generated from project {project.name}"
            }

            picking_list = self.create_picking_list(picking_list_data)

            # Get project components
            components = self.project_repository.get_components(project_id)

            # Add components as items
            for component in components:
                item_data = {
                    "name": component.name,
                    "description": component.description,
                    "item_type": component.component_type,
                    "material_id": component.material_id,
                    "quantity_required": component.quantity,
                    "unit": component.unit,
                    "notes": f"From project component: {component.name}"
                }

                self.add_item_to_picking_list(picking_list["id"], item_data)

            # Get updated picking list with items
            return self.get_picking_list(picking_list["id"])
        except Exception as e:
            self.logger.error(f"Error generating picking list from project {project_id}: {str(e)}")
            raise

    def _format_picking_list(self, picking_list: PickingList) -> Dict[str, Any]:
        """Format a picking list model as a dictionary."""
        result = {
            "id": picking_list.id,
            "name": picking_list.name,
            "project_id": picking_list.project_id,
            "order_id": picking_list.order_id,
            "status": picking_list.status.name if picking_list.status else None,
            "created_at": picking_list.created_at.isoformat() if picking_list.created_at else None,
            "updated_at": picking_list.updated_at.isoformat() if picking_list.updated_at else None,
            "notes": picking_list.notes,
            "priority": picking_list.priority,
            "assigned_to": picking_list.assigned_to,
            "items": [self._format_picking_list_item(item) for item in picking_list.items]
        }

        # Add related project/order info if available
        if picking_list.project:
            result["project_name"] = picking_list.project.name

        if picking_list.order:
            result["order_reference"] = picking_list.order.reference_number

        return result

    def _format_picking_list_item(self, item: PickingListItem) -> Dict[str, Any]:
        """Format a picking list item model as a dictionary."""
        result = {
            "id": item.id,
            "picking_list_id": item.picking_list_id,
            "material_id": item.material_id,
            "hardware_id": item.hardware_id,
            "storage_location_id": item.storage_location_id,
            "item_type": item.item_type,
            "name": item.name,
            "description": item.description,
            "quantity_required": item.quantity_required,
            "quantity_picked": item.quantity_picked,
            "unit": item.unit,
            "notes": item.notes,
            "is_picked": item.is_picked,
            "sort_order": item.sort_order
        }

        # Add storage location info if available
        if item.storage_location:
            result["storage_location"] = {
                "id": item.storage_location.id,
                "name": item.storage_location.name,
                "section": getattr(item.storage_location, "section", None),
                "shelf": getattr(item.storage_location, "shelf", None),
                "bin": getattr(item.storage_location, "bin", None)
            }

        return result