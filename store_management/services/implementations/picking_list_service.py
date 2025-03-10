from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.picking_list_repository import PickingListRepository
from database.repositories.project_repository import ProjectRepository
from database.repositories.sales_repository import SalesRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.component_repository import ComponentRepository

from database.models.enums import PickingListStatus, InventoryStatus, TransactionType

from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError, BusinessRuleError
from services.dto.picking_list_dto import PickingListDTO, PickingListItemDTO

from di.inject import inject


class PickingListService(BaseService):
    """Implementation of the picking list service interface."""

    @inject
    def __init__(self, session: Session,
                 picking_list_repository: Optional[PickingListRepository] = None,
                 project_repository: Optional[ProjectRepository] = None,
                 sales_repository: Optional[SalesRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 component_repository: Optional[ComponentRepository] = None):
        """Initialize the picking list service."""
        super().__init__(session)
        self.picking_list_repository = picking_list_repository or PickingListRepository(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.sales_repository = sales_repository or SalesRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, picking_list_id: int) -> Dict[str, Any]:
        """Get picking list by ID."""
        try:
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")
            return PickingListDTO.from_model(picking_list, include_items=True, include_project=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving picking list {picking_list_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all picking lists, optionally filtered."""
        try:
            picking_lists = self.picking_list_repository.get_all(filters=filters)
            return [PickingListDTO.from_model(picking_list).to_dict() for picking_list in picking_lists]
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists: {str(e)}")
            raise

    def create(self, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new picking list."""
        try:
            # Validate picking list data
            self._validate_picking_list_data(picking_list_data)

            # Set default status if not provided
            if 'status' not in picking_list_data:
                picking_list_data['status'] = PickingListStatus.DRAFT.value

            # Handle items separately if provided
            items = picking_list_data.pop('items', []) if 'items' in picking_list_data else []

            # Create picking list
            with self.transaction():
                picking_list = self.picking_list_repository.create(picking_list_data)

                # Add items if provided
                for item_data in items:
                    item_data['picking_list_id'] = picking_list.id
                    self.picking_list_repository.add_item(item_data)

                # Get the complete picking list with items
                result = self.picking_list_repository.get_by_id(picking_list.id)
                return PickingListDTO.from_model(result, include_items=True, include_project=True).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating picking list: {str(e)}")
            raise

    def update(self, picking_list_id: int, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing picking list."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Validate picking list data
            self._validate_picking_list_data(picking_list_data, update=True)

            # Prevent updating completed picking lists
            if picking_list.status == PickingListStatus.COMPLETED.value:
                raise BusinessRuleError(f"Cannot update a completed picking list")

            # Update picking list
            with self.transaction():
                updated_picking_list = self.picking_list_repository.update(picking_list_id, picking_list_data)
                return PickingListDTO.from_model(updated_picking_list, include_items=True,
                                                 include_project=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating picking list {picking_list_id}: {str(e)}")
            raise

    def delete(self, picking_list_id: int) -> bool:
        """Delete a picking list by ID."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Prevent deleting completed or in-progress picking lists
            if picking_list.status in [PickingListStatus.COMPLETED.value, PickingListStatus.IN_PROGRESS.value]:
                raise BusinessRuleError(f"Cannot delete a picking list with status {picking_list.status}")

            # Delete picking list
            with self.transaction():
                # Delete all items first
                items = self.picking_list_repository.get_items(picking_list_id)
                for item in items:
                    self.picking_list_repository.delete_item(item.id)

                # Then delete the picking list
                return self.picking_list_repository.delete(picking_list_id)
        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting picking list {picking_list_id}: {str(e)}")
            raise

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get picking lists by project ID."""
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            picking_lists = self.picking_list_repository.get_by_project(project_id)
            return [PickingListDTO.from_model(picking_list).to_dict() for picking_list in picking_lists]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists for project {project_id}: {str(e)}")
            raise

    def get_by_sales(self, sales_id: int) -> List[Dict[str, Any]]:
        """Get picking lists by sales ID."""
        try:
            # Check if sales exists
            sales = self.sales_repository.get_by_id(sales_id)
            if not sales:
                raise NotFoundError(f"Sales with ID {sales_id} not found")

            picking_lists = self.picking_list_repository.get_by_sales(sales_id)
            return [PickingListDTO.from_model(picking_list).to_dict() for picking_list in picking_lists]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists for sales {sales_id}: {str(e)}")
            raise

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get picking lists by status."""
        try:
            # Validate status
            if not hasattr(PickingListStatus, status):
                raise ValidationError(f"Invalid picking list status: {status}")

            picking_lists = self.picking_list_repository.get_by_status(status)
            return [PickingListDTO.from_model(picking_list).to_dict() for picking_list in picking_lists]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists with status '{status}': {str(e)}")
            raise

    def add_item(self, picking_list_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a picking list."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Validate item data
            self._validate_picking_list_item_data(item_data)

            # Prevent modifying completed picking lists
            if picking_list.status == PickingListStatus.COMPLETED.value:
                raise BusinessRuleError(f"Cannot add items to a completed picking list")

            # Add picking list ID to item data
            item_data['picking_list_id'] = picking_list_id

            # Add item to picking list
            with self.transaction():
                item = self.picking_list_repository.add_item(item_data)
                return PickingListItemDTO.from_model(item).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding item to picking list {picking_list_id}: {str(e)}")
            raise

    def update_item(self, picking_list_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an item in a picking list."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Check if item exists
            item = self.picking_list_repository.get_item(item_id)
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            # Ensure item belongs to the specified picking list
            if item.picking_list_id != picking_list_id:
                raise ValidationError(f"Item {item_id} does not belong to picking list {picking_list_id}")

            # Validate item data
            self._validate_picking_list_item_data(item_data, update=True)

            # Prevent modifying completed picking lists
            if picking_list.status == PickingListStatus.COMPLETED.value:
                raise BusinessRuleError(f"Cannot update items in a completed picking list")

            # Update item
            with self.transaction():
                updated_item = self.picking_list_repository.update_item(item_id, item_data)
                return PickingListItemDTO.from_model(updated_item).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating item {item_id} in picking list {picking_list_id}: {str(e)}")
            raise

    def remove_item(self, picking_list_id: int, item_id: int) -> bool:
        """Remove an item from a picking list."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Check if item exists
            item = self.picking_list_repository.get_item(item_id)
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            # Ensure item belongs to the specified picking list
            if item.picking_list_id != picking_list_id:
                raise ValidationError(f"Item {item_id} does not belong to picking list {picking_list_id}")

            # Prevent modifying completed picking lists
            if picking_list.status == PickingListStatus.COMPLETED.value:
                raise BusinessRuleError(f"Cannot remove items from a completed picking list")

            # Remove item
            with self.transaction():
                return self.picking_list_repository.delete_item(item_id)
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error removing item {item_id} from picking list {picking_list_id}: {str(e)}")
            raise

    def get_items(self, picking_list_id: int) -> List[Dict[str, Any]]:
        """Get all items in a picking list."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            items = self.picking_list_repository.get_items(picking_list_id)
            return [PickingListItemDTO.from_model(item).to_dict() for item in items]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving items for picking list {picking_list_id}: {str(e)}")
            raise

    def process_picking_list(self, picking_list_id: int, process_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a picking list (mark items as picked, update inventory)."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Prevent processing completed picking lists
            if picking_list.status == PickingListStatus.COMPLETED.value:
                raise BusinessRuleError(f"Cannot process a completed picking list")

            # Get items
            items = self.picking_list_repository.get_items(picking_list_id)
            if not items:
                raise ValidationError(f"Picking list {picking_list_id} has no items")

            # Process each item
            processed_items = []
            with self.transaction():
                # Update picking list status to in progress
                self.picking_list_repository.update(picking_list_id, {'status': PickingListStatus.IN_PROGRESS.value})

                # Process each item in the request
                for item_process in process_data.get('items', []):
                    item_id = item_process.get('item_id')
                    quantity_picked = item_process.get('quantity_picked', 0)

                    # Find the item
                    item = next((i for i in items if i.id == item_id), None)
                    if not item:
                        self.logger.warning(f"Item {item_id} not found in picking list {picking_list_id}")
                        continue

                    # Validate quantity
                    if quantity_picked < 0:
                        self.logger.warning(f"Invalid quantity picked {quantity_picked} for item {item_id}")
                        continue

                    if quantity_picked > item.quantity_ordered:
                        self.logger.warning(
                            f"Quantity picked {quantity_picked} exceeds ordered quantity {item.quantity_ordered} for item {item_id}")
                        continue

                    # Update item quantity picked
                    item_update = {'quantity_picked': quantity_picked}
                    updated_item = self.picking_list_repository.update_item(item_id, item_update)

                    # Adjust inventory if material is specified
                    if getattr(item, 'material_id', None):
                        material_id = item.material_id
                        inventory = self.inventory_repository.get_by_item('material', material_id)

                        if inventory:
                            # Calculate quantity to deduct
                            deduction = quantity_picked

                            # Check if there's enough inventory
                            if inventory.quantity < deduction:
                                self.logger.warning(
                                    f"Insufficient inventory for material {material_id}: needed {deduction}, available {inventory.quantity}")
                                # Continue processing but flag as partial
                                item_update['notes'] = f"Partially fulfilled due to insufficient inventory"
                                self.picking_list_repository.update_item(item_id, item_update)
                            else:
                                # Deduct from inventory
                                transaction_data = {
                                    'inventory_id': inventory.id,
                                    'transaction_type': TransactionType.USAGE.value,
                                    'quantity': deduction,
                                    'reason': f"Picked for picking list {picking_list_id}",
                                    'performed_by': process_data.get('performed_by', 'system')
                                }
                                self.inventory_repository.create_transaction(transaction_data)

                                # Update inventory
                                new_quantity = inventory.quantity - deduction
                                status = InventoryStatus.IN_STOCK.value if new_quantity > 0 else InventoryStatus.OUT_OF_STOCK.value
                                self.inventory_repository.update(inventory.id, {
                                    'quantity': new_quantity,
                                    'status': status
                                })

                    processed_items.append(updated_item)

                # Check if all items are fully picked
                all_items = self.picking_list_repository.get_items(picking_list_id)
                all_complete = all(item.quantity_picked == item.quantity_ordered for item in all_items)

                # Update picking list status if all items are complete
                if all_complete:
                    self.picking_list_repository.update(picking_list_id, {
                        'status': PickingListStatus.COMPLETED.value,
                        'completed_at': datetime.now()
                    })

                # Get updated picking list
                updated_picking_list = self.picking_list_repository.get_by_id(picking_list_id)
                return PickingListDTO.from_model(updated_picking_list, include_items=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error processing picking list {picking_list_id}: {str(e)}")
            raise

    def complete_picking_list(self, picking_list_id: int) -> Dict[str, Any]:
        """Mark a picking list as completed."""
        try:
            # Check if picking list exists
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Prevent completing already completed picking lists
            if picking_list.status == PickingListStatus.COMPLETED.value:
                return PickingListDTO.from_model(picking_list, include_items=True).to_dict()

            # Update picking list
            with self.transaction():
                updated_picking_list = self.picking_list_repository.update(picking_list_id, {
                    'status': PickingListStatus.COMPLETED.value,
                    'completed_at': datetime.now()
                })
                return PickingListDTO.from_model(updated_picking_list, include_items=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error completing picking list {picking_list_id}: {str(e)}")
            raise

    def generate_from_project(self, project_id: int) -> Dict[str, Any]:
        """Generate a picking list from a project."""
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Check if project already has a picking list
            existing_lists = self.picking_list_repository.get_by_project(project_id)
            if existing_lists:
                self.logger.info(f"Project {project_id} already has {len(existing_lists)} picking list(s)")
                # Return the most recent one
                return PickingListDTO.from_model(existing_lists[0], include_items=True).to_dict()

            # Get project components
            project_components = self.project_repository.get_components(project_id)
            if not project_components:
                raise ValidationError(f"Project {project_id} has no components")

            # Create picking list
            picking_list_data = {
                'project_id': project_id,
                'status': PickingListStatus.DRAFT.value,
                'notes': f"Automatically generated for project: {project.name}"
            }

            with self.transaction():
                # Create picking list
                picking_list = self.picking_list_repository.create(picking_list_data)

                # Add items for each component's materials
                for project_component in project_components:
                    component_id = project_component.component_id
                    component_quantity = project_component.quantity

                    # Get component materials
                    component_materials = self.component_repository.get_materials(component_id)

                    for cm in component_materials:
                        material_id = cm.material_id
                        material_quantity = cm.quantity * component_quantity

                        # Add material to picking list
                        item_data = {
                            'picking_list_id': picking_list.id,
                            'material_id': material_id,
                            'component_id': component_id,
                            'quantity_ordered': material_quantity,
                            'quantity_picked': 0
                        }
                        self.picking_list_repository.add_item(item_data)

                # Return complete picking list
                result = self.picking_list_repository.get_by_id(picking_list.id)
                return PickingListDTO.from_model(result, include_items=True, include_project=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error generating picking list for project {project_id}: {str(e)}")
            raise

    def _validate_picking_list_data(self, picking_list_data: Dict[str, Any], update: bool = False) -> None:
        """Validate picking list data.

        Args:
            picking_list_data: Picking list data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Check project_id if present
        if 'project_id' in picking_list_data:
            project_id = picking_list_data['project_id']
            if project_id:
                project = self.project_repository.get_by_id(project_id)
                if not project:
                    raise ValidationError(f"Project with ID {project_id} not found")

        # Check sales_id if present
        if 'sales_id' in picking_list_data:
            sales_id = picking_list_data['sales_id']
            if sales_id:
                sales = self.sales_repository.get_by_id(sales_id)
                if not sales:
                    raise ValidationError(f"Sales with ID {sales_id} not found")

        # Validate status if provided
        if 'status' in picking_list_data and picking_list_data['status']:
            status = picking_list_data['status']
            if not hasattr(PickingListStatus, status):
                raise ValidationError(f"Invalid picking list status: {status}")

    def _validate_picking_list_item_data(self, item_data: Dict[str, Any], update: bool = False) -> None:
        """Validate picking list item data.

        Args:
            item_data: Picking list item data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # For new items, either material_id or component_id must be present
        if not update and 'material_id' not in item_data and 'component_id' not in item_data:
            raise ValidationError("Either material_id or component_id must be specified")

        # Check material_id if present
        if 'material_id' in item_data and item_data['material_id']:
            material_id = item_data['material_id']
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise ValidationError(f"Material with ID {material_id} not found")

        # Check component_id if present
        if 'component_id' in item_data and item_data['component_id']:
            component_id = item_data['component_id']
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise ValidationError(f"Component with ID {component_id} not found")

        # Validate quantities
        if 'quantity_ordered' in item_data:
            quantity_ordered = item_data['quantity_ordered']
            if quantity_ordered < 0:
                raise ValidationError("Quantity ordered cannot be negative")

        if 'quantity_picked' in item_data:
            quantity_picked = item_data['quantity_picked']
            if quantity_picked < 0:
                raise ValidationError("Quantity picked cannot be negative")

            # If both quantities are provided, picked cannot exceed ordered
            if 'quantity_ordered' in item_data and item_data['quantity_picked'] > item_data['quantity_ordered']:
                raise ValidationError("Quantity picked cannot exceed quantity ordered")