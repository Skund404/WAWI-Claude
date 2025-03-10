# services/implementations/picking_list_service.py
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.picking_list import PickingList
from database.models.picking_list_item import PickingListItem
from database.models.enums import PickingListStatus, InventoryStatus
from database.repositories.picking_list_repository import PickingListRepository
from database.repositories.picking_list_item_repository import PickingListItemRepository
from database.repositories.project_repository import ProjectRepository
from database.repositories.component_repository import ComponentRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.inventory_repository import InventoryRepository

from services.base_service import BaseService, ValidationError, NotFoundError, ServiceError
from services.interfaces.picking_list_service import IPickingListService

from di.core import inject


class PickingListService(BaseService, IPickingListService):
    """Implementation of the PickingList Service interface.

    This service provides functionality for managing material picking lists
    for leatherworking projects, including generating lists, tracking progress,
    and validating inventory.
    """

    @inject
    def __init__(self,
                 session: Session,
                 picking_list_repository: Optional[PickingListRepository] = None,
                 picking_list_item_repository: Optional[PickingListItemRepository] = None,
                 project_repository: Optional[ProjectRepository] = None,
                 component_repository: Optional[ComponentRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the PickingList Service.

        Args:
            session: SQLAlchemy database session
            picking_list_repository: Optional PickingListRepository instance
            picking_list_item_repository: Optional PickingListItemRepository instance
            project_repository: Optional ProjectRepository instance
            component_repository: Optional ComponentRepository instance
            material_repository: Optional MaterialRepository instance
            inventory_repository: Optional InventoryRepository instance
        """
        super().__init__(session)
        self.picking_list_repository = picking_list_repository or PickingListRepository(session)
        self.picking_list_item_repository = picking_list_item_repository or PickingListItemRepository(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, picking_list_id: int) -> Dict[str, Any]:
        """Retrieve a picking list by its ID.

        Args:
            picking_list_id: The ID of the picking list to retrieve

        Returns:
            A dictionary representation of the picking list

        Raises:
            NotFoundError: If the picking list does not exist
        """
        try:
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")
            return self._to_dict(picking_list)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve picking list: {str(e)}")

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all picking lists with optional filtering.

        Args:
            filters: Optional filters to apply to the picking list query

        Returns:
            List of dictionaries representing picking lists
        """
        try:
            picking_lists = self.picking_list_repository.get_all(filters)
            return [self._to_dict(picking_list) for picking_list in picking_lists]
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists: {str(e)}")
            raise ServiceError(f"Failed to retrieve picking lists: {str(e)}")

    def create_for_project(self, project_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a new picking list for a project.

        Args:
            project_id: ID of the project
            notes: Optional notes about the picking list

        Returns:
            Dictionary representation of the created picking list

        Raises:
            NotFoundError: If the project does not exist
            ValidationError: If the project has no components
            ServiceError: If a picking list already exists for the project
        """
        try:
            # Verify project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Check if active picking list already exists
            existing_lists = self.picking_list_repository.get_by_project(
                project_id,
                status=[PickingListStatus.DRAFT.value, PickingListStatus.PENDING.value,
                        PickingListStatus.IN_PROGRESS.value]
            )

            if existing_lists:
                raise ServiceError(f"Active picking list already exists for project {project_id}")

            # Get project components
            project_components = self.project_repository.get_components(project_id)
            if not project_components or len(project_components) == 0:
                raise ValidationError(f"Project {project_id} has no components")

            # Create the picking list within a transaction
            with self.transaction():
                # Create picking list
                picking_list_data = {
                    'project_id': project_id,
                    'status': PickingListStatus.DRAFT.value,
                    'created_at': datetime.now(),
                    'notes': notes
                }

                picking_list = self.picking_list_repository.create(picking_list_data)

                # Create picking list items for each component's materials
                for project_component in project_components:
                    component_id = project_component.component_id
                    component_quantity = project_component.quantity

                    # Get component materials
                    component_materials = self.component_repository.get_materials(component_id)

                    for component_material in component_materials:
                        material_id = component_material.material_id
                        material_quantity = component_material.quantity * component_quantity

                        # Create picking list item
                        item_data = {
                            'picking_list_id': picking_list.id,
                            'component_id': component_id,
                            'material_id': material_id,
                            'quantity_ordered': material_quantity,
                            'quantity_picked': 0
                        }

                        self.picking_list_item_repository.create(item_data)

                # Get the created picking list with items
                result = self._to_dict(picking_list)
                result['items'] = self.get_picking_list_items(picking_list.id)

                return result
        except (NotFoundError, ValidationError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating picking list for project {project_id}: {str(e)}")
            raise ServiceError(f"Failed to create picking list: {str(e)}")

    def update(self, picking_list_id: int, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing picking list.

        Args:
            picking_list_id: ID of the picking list to update
            picking_list_data: Dictionary containing updated picking list data

        Returns:
            Dictionary representation of the updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the updated data is invalid
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Validate picking list data
            self._validate_picking_list_data(picking_list_data)

            # Update the picking list within a transaction
            with self.transaction():
                updated_picking_list = self.picking_list_repository.update(picking_list_id, picking_list_data)
                return self._to_dict(updated_picking_list)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to update picking list: {str(e)}")

    def delete(self, picking_list_id: int) -> bool:
        """Delete a picking list by its ID.

        Args:
            picking_list_id: ID of the picking list to delete

        Returns:
            True if the picking list was successfully deleted

        Raises:
            NotFoundError: If the picking list does not exist
            ServiceError: If the picking list cannot be deleted (e.g., in progress)
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Check if picking list can be deleted
            if picking_list.status == PickingListStatus.IN_PROGRESS:
                raise ServiceError(f"Cannot delete picking list {picking_list_id} as it is in progress")

            if picking_list.status == PickingListStatus.COMPLETED:
                raise ServiceError(f"Cannot delete picking list {picking_list_id} as it is completed")

            # Delete the picking list within a transaction
            with self.transaction():
                # Delete all picking list items first
                items = self.picking_list_item_repository.get_by_picking_list(picking_list_id)
                for item in items:
                    self.picking_list_item_repository.delete(item.id)

                # Then delete the picking list
                self.picking_list_repository.delete(picking_list_id)
                return True
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to delete picking list: {str(e)}")

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get picking lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of dictionaries representing picking lists for the project

        Raises:
            NotFoundError: If the project does not exist
        """
        try:
            # Verify project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            picking_lists = self.picking_list_repository.get_by_project(project_id)
            return [self._to_dict(picking_list) for picking_list in picking_lists]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting picking lists for project {project_id}: {str(e)}")
            raise ServiceError(f"Failed to get picking lists for project: {str(e)}")

    def get_picking_list_items(self, picking_list_id: int) -> List[Dict[str, Any]]:
        """Get all items in a picking list.

        Args:
            picking_list_id: ID of the picking list

        Returns:
            List of dictionaries representing picking list items

        Raises:
            NotFoundError: If the picking list does not exist
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            items = self.picking_list_item_repository.get_by_picking_list(picking_list_id)
            result = []

            for item in items:
                item_dict = self._to_dict(item)

                # Get material details
                material = self.material_repository.get_by_id(item.material_id)
                if material:
                    item_dict['material'] = {
                        'id': material.id,
                        'name': material.name,
                        'material_type': material.material_type.name if hasattr(material.material_type,
                                                                                'name') else str(material.material_type)
                    }

                # Get component details
                if item.component_id:
                    component = self.component_repository.get_by_id(item.component_id)
                    if component:
                        item_dict['component'] = {
                            'id': component.id,
                            'name': component.name
                        }

                # Get inventory status
                inventory_entries = self.inventory_repository.get_by_item(item_type='material',
                                                                          item_id=item.material_id)
                if inventory_entries:
                    inventory = inventory_entries[0]
                    item_dict['available_quantity'] = inventory.quantity
                    item_dict['inventory_status'] = inventory.status.name if hasattr(inventory.status, 'name') else str(
                        inventory.status)
                else:
                    item_dict['available_quantity'] = 0
                    item_dict['inventory_status'] = InventoryStatus.OUT_OF_STOCK.value

                result.append(item_dict)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting items for picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to get picking list items: {str(e)}")

    def add_item(self, picking_list_id: int,
                 material_id: int,
                 component_id: Optional[int] = None,
                 quantity: float = 1.0) -> Dict[str, Any]:
        """Add an item to a picking list.

        Args:
            picking_list_id: ID of the picking list
            material_id: ID of the material
            component_id: Optional ID of the component using the material
            quantity: Quantity of the material needed

        Returns:
            Dictionary representing the added picking list item

        Raises:
            NotFoundError: If the picking list or material does not exist
            ValidationError: If the quantity is invalid
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Verify material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Verify component exists if provided
            if component_id:
                component = self.component_repository.get_by_id(component_id)
                if not component:
                    raise NotFoundError(f"Component with ID {component_id} not found")

            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Check if item already exists
            existing_items = self.picking_list_item_repository.get_by_picking_list_and_material(
                picking_list_id,
                material_id,
                component_id
            )

            # Add or update item within a transaction
            with self.transaction():
                if existing_items:
                    # Update existing item
                    existing_item = existing_items[0]
                    updated_data = {
                        'quantity_ordered': existing_item.quantity_ordered + quantity
                    }
                    updated_item = self.picking_list_item_repository.update(existing_item.id, updated_data)
                    return self._to_dict(updated_item)
                else:
                    # Create new item
                    item_data = {
                        'picking_list_id': picking_list_id,
                        'material_id': material_id,
                        'component_id': component_id,
                        'quantity_ordered': quantity,
                        'quantity_picked': 0
                    }

                    new_item = self.picking_list_item_repository.create(item_data)
                    return self._to_dict(new_item)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding item to picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to add item to picking list: {str(e)}")

    def remove_item(self, picking_list_id: int, item_id: int) -> bool:
        """Remove an item from a picking list.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the picking list item

        Returns:
            True if the item was successfully removed

        Raises:
            NotFoundError: If the picking list or item does not exist
            ServiceError: If the item cannot be removed (e.g., already picked)
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Verify item exists and belongs to the picking list
            item = self.picking_list_item_repository.get_by_id(item_id)
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            if item.picking_list_id != picking_list_id:
                raise ValidationError(f"Item {item_id} does not belong to picking list {picking_list_id}")

            # Check if item has been picked
            if item.quantity_picked > 0:
                raise ServiceError(f"Cannot remove item {item_id} as it has already been picked")

            # Remove item within a transaction
            with self.transaction():
                self.picking_list_item_repository.delete(item_id)
                return True
        except (NotFoundError, ValidationError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error removing item {item_id} from picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to remove item from picking list: {str(e)}")

    def update_item_quantity(self, picking_list_id: int,
                             item_id: int,
                             quantity: float) -> Dict[str, Any]:
        """Update the quantity of an item in a picking list.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the picking list item
            quantity: New quantity of the material needed

        Returns:
            Dictionary representing the updated picking list item

        Raises:
            NotFoundError: If the picking list or item does not exist
            ValidationError: If the quantity is invalid
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Verify item exists and belongs to the picking list
            item = self.picking_list_item_repository.get_by_id(item_id)
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            if item.picking_list_id != picking_list_id:
                raise ValidationError(f"Item {item_id} does not belong to picking list {picking_list_id}")

            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Check if item has been picked
            if item.quantity_picked > quantity:
                raise ValidationError(
                    f"Cannot set quantity to less than already picked (ordered: {quantity}, picked: {item.quantity_picked})")

            # Update item quantity within a transaction
            with self.transaction():
                updated_data = {
                    'quantity_ordered': quantity
                }

                updated_item = self.picking_list_item_repository.update(item_id, updated_data)
                return self._to_dict(updated_item)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating item {item_id} quantity in picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to update item quantity: {str(e)}")

    def record_picking(self, picking_list_id: int,
                       item_id: int,
                       quantity_picked: float,
                       notes: Optional[str] = None) -> Dict[str, Any]:
        """Record picking of an item.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the picking list item
            quantity_picked: Quantity picked
            notes: Optional notes about the picking

        Returns:
            Dictionary representing the updated picking list item

        Raises:
            NotFoundError: If the picking list or item does not exist
            ValidationError: If the quantity is invalid
            ServiceError: If insufficient inventory is available
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Check if picking list is in a valid status
            valid_statuses = [PickingListStatus.PENDING.value, PickingListStatus.IN_PROGRESS.value]
            if picking_list.status not in valid_statuses:
                raise ValidationError(
                    f"Picking list {picking_list_id} status must be PENDING or IN_PROGRESS, current status: {picking_list.status}")

            # Verify item exists and belongs to the picking list
            item = self.picking_list_item_repository.get_by_id(item_id)
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            if item.picking_list_id != picking_list_id:
                raise ValidationError(f"Item {item_id} does not belong to picking list {picking_list_id}")

            # Validate quantity
            if quantity_picked <= 0:
                raise ValidationError("Quantity picked must be greater than zero")

            # Check if picking would exceed ordered quantity
            total_picked = item.quantity_picked + quantity_picked
            if total_picked > item.quantity_ordered:
                raise ValidationError(
                    f"Total picked quantity ({total_picked}) cannot exceed ordered quantity ({item.quantity_ordered})")

            # Check inventory availability
            inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=item.material_id)

            if not inventory_entries:
                raise ServiceError(f"No inventory record found for material {item.material_id}")

            inventory = inventory_entries[0]
            if inventory.quantity < quantity_picked:
                raise ServiceError(
                    f"Insufficient inventory for material {item.material_id} (available: {inventory.quantity}, required: {quantity_picked})")

            # Record picking within a transaction
            with self.transaction():
                # Update picking list status if necessary
                if picking_list.status == PickingListStatus.PENDING.value:
                    self.picking_list_repository.update(picking_list_id,
                                                        {'status': PickingListStatus.IN_PROGRESS.value})

                # Update picking list item
                updated_data = {
                    'quantity_picked': item.quantity_picked + quantity_picked
                }

                if notes:
                    updated_data['notes'] = notes

                updated_item = self.picking_list_item_repository.update(item_id, updated_data)

                # Update inventory
                inventory_data = {
                    'quantity': inventory.quantity - quantity_picked
                }

                # Update status if necessary
                if inventory.quantity - quantity_picked == 0:
                    inventory_data['status'] = InventoryStatus.OUT_OF_STOCK.value
                elif inventory.quantity - quantity_picked < 5:  # Configurable threshold
                    inventory_data['status'] = InventoryStatus.LOW_STOCK.value

                self.inventory_repository.update(inventory.id, inventory_data)

                return self._to_dict(updated_item)
        except (NotFoundError, ValidationError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error recording picking for item {item_id} in picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to record picking: {str(e)}")

    def complete_picking_list(self, picking_list_id: int,
                              notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark a picking list as complete.

        Args:
            picking_list_id: ID of the picking list
            notes: Optional notes about the completion

        Returns:
            Dictionary representing the updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If not all items have been picked
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Check if picking list is in a valid status
            if picking_list.status != PickingListStatus.IN_PROGRESS.value:
                raise ValidationError(
                    f"Picking list {picking_list_id} status must be IN_PROGRESS, current status: {picking_list.status}")

            # Check if all items have been picked
            items = self.picking_list_item_repository.get_by_picking_list(picking_list_id)
            incomplete_items = []

            for item in items:
                if item.quantity_picked < item.quantity_ordered:
                    incomplete_items.append(item.id)

            if incomplete_items:
                raise ValidationError(
                    f"Cannot complete picking list: {len(incomplete_items)} items have not been fully picked")

            # Complete picking list within a transaction
            with self.transaction():
                completed_data = {
                    'status': PickingListStatus.COMPLETED.value,
                    'completed_at': datetime.now()
                }

                if notes:
                    completed_data['notes'] = f"{picking_list.notes or ''}\nCompletion: {notes}"

                updated_picking_list = self.picking_list_repository.update(picking_list_id, completed_data)
                return self._to_dict(updated_picking_list)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error completing picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to complete picking list: {str(e)}")

    def cancel_picking_list(self, picking_list_id: int,
                            reason: str) -> Dict[str, Any]:
        """Cancel a picking list.

        Args:
            picking_list_id: ID of the picking list
            reason: Reason for cancellation

        Returns:
            Dictionary representing the updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ServiceError: If the picking list cannot be cancelled
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Check if picking list can be cancelled
            if picking_list.status == PickingListStatus.COMPLETED.value:
                raise ServiceError(f"Cannot cancel picking list {picking_list_id} as it is already completed")

            if picking_list.status == PickingListStatus.CANCELLED.value:
                raise ServiceError(f"Picking list {picking_list_id} is already cancelled")

            # Cancel picking list within a transaction
            with self.transaction():
                # If any materials have been picked, return them to inventory
                items = self.picking_list_item_repository.get_by_picking_list(picking_list_id)

                for item in items:
                    if item.quantity_picked > 0:
                        # Return picked materials to inventory
                        inventory_entries = self.inventory_repository.get_by_item(item_type='material',
                                                                                  item_id=item.material_id)

                        if inventory_entries:
                            inventory = inventory_entries[0]

                            inventory_data = {
                                'quantity': inventory.quantity + item.quantity_picked
                            }

                            # Update status if necessary
                            if inventory.quantity + item.quantity_picked > 0:
                                if inventory.status == InventoryStatus.OUT_OF_STOCK.value:
                                    if inventory.quantity + item.quantity_picked < 5:  # Configurable threshold
                                        inventory_data['status'] = InventoryStatus.LOW_STOCK.value
                                    else:
                                        inventory_data['status'] = InventoryStatus.IN_STOCK.value

                            self.inventory_repository.update(inventory.id, inventory_data)

                # Cancel picking list
                cancelled_data = {
                    'status': PickingListStatus.CANCELLED.value,
                    'notes': f"{picking_list.notes or ''}\nCancellation: {reason}"
                }

                updated_picking_list = self.picking_list_repository.update(picking_list_id, cancelled_data)
                return self._to_dict(updated_picking_list)
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error cancelling picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to cancel picking list: {str(e)}")

    def validate_inventory(self, picking_list_id: int) -> Dict[str, Any]:
        """Validate that sufficient inventory exists for all items in a picking list.

        Args:
            picking_list_id: ID of the picking list

        Returns:
            Dictionary with validation results

        Raises:
            NotFoundError: If the picking list does not exist
        """
        try:
            # Verify picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Get picking list items
            items = self.picking_list_item_repository.get_by_picking_list(picking_list_id)

            result = {
                'valid': True,
                'missing_materials': [],
                'insufficient_materials': [],
                'total_items': len(items),
                'valid_items': 0
            }

            for item in items:
                # Get remaining quantity to pick
                remaining_quantity = item.quantity_ordered - item.quantity_picked

                if remaining_quantity <= 0:
                    result['valid_items'] += 1
                    continue

                # Check inventory
                inventory_entries = self.inventory_repository.get_by_item(item_type='material',
                                                                          item_id=item.material_id)

                if not inventory_entries:
                    # Material not in inventory
                    material = self.material_repository.get_by_id(item.material_id)
                    material_name = material.name if material else f"Material ID {item.material_id}"

                    result['missing_materials'].append({
                        'item_id': item.id,
                        'material_id': item.material_id,
                        'material_name': material_name,
                        'required_quantity': remaining_quantity
                    })

                    result['valid'] = False
                else:
                    inventory = inventory_entries[0]

                    if inventory.quantity < remaining_quantity:
                        # Insufficient quantity
                        material = self.material_repository.get_by_id(item.material_id)
                        material_name = material.name if material else f"Material ID {item.material_id}"

                        result['insufficient_materials'].append({
                            'item_id': item.id,
                            'material_id': item.material_id,
                            'material_name': material_name,
                            'required_quantity': remaining_quantity,
                            'available_quantity': inventory.quantity,
                            'shortage': remaining_quantity - inventory.quantity
                        })

                        result['valid'] = False
                    else:
                        result['valid_items'] += 1

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error validating inventory for picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to validate inventory: {str(e)}")

    def _validate_picking_list_data(self, data: Dict[str, Any]) -> None:
        """Validate picking list data.

        Args:
            data: Picking list data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate status if provided
        if 'status' in data:
            valid_statuses = [status.value for status in PickingListStatus]
            if data['status'] not in valid_statuses:
                raise ValidationError(f"Invalid status: {data['status']}. Valid statuses are: {valid_statuses}")

    def _to_dict(self, obj) -> Dict[str, Any]:
        """Convert a model object to a dictionary representation.

        Args:
            obj: Model object to convert

        Returns:
            Dictionary representation of the object
        """
        if isinstance(obj, PickingList):
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
        elif isinstance(obj, PickingListItem):
            result = {
                'id': obj.id,
                'picking_list_id': obj.picking_list_id,
                'material_id': obj.material_id,
                'component_id': getattr(obj, 'component_id', None),
                'quantity_ordered': obj.quantity_ordered,
                'quantity_picked': obj.quantity_picked,
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