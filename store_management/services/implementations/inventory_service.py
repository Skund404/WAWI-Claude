# services/implementations/inventory_service.py
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.tool_repository import ToolRepository
from database.models.enums import InventoryStatus, InventoryAdjustmentType, TransactionType
from services.base_service import BaseService, ValidationError, NotFoundError


class InventoryService(BaseService):
    """Implementation of the inventory service interface."""

    def __init__(self, session: Session,
                 inventory_repository: Optional[InventoryRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 product_repository: Optional[ProductRepository] = None,
                 tool_repository: Optional[ToolRepository] = None):
        """Initialize the inventory service.

        Args:
            session: SQLAlchemy database session
            inventory_repository: Optional InventoryRepository instance
            material_repository: Optional MaterialRepository instance
            product_repository: Optional ProductRepository instance
            tool_repository: Optional ToolRepository instance
        """
        super().__init__(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.product_repository = product_repository or ProductRepository(session)
        self.tool_repository = tool_repository or ToolRepository(session)

    def get_by_id(self, inventory_id: int) -> Dict[str, Any]:
        """Get inventory by ID.

        Args:
            inventory_id: ID of the inventory to retrieve

        Returns:
            Dict representing the inventory

        Raises:
            NotFoundError: If inventory not found
        """
        try:
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory with ID {inventory_id} not found")

            # Get item details
            inventory_dict = self._to_dict(inventory)
            item_details = self._get_item_details(inventory.item_type, inventory.item_id)
            if item_details:
                inventory_dict['item_details'] = item_details

            return inventory_dict
        except Exception as e:
            self.logger.error(f"Error retrieving inventory {inventory_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all inventory, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing inventory
        """
        try:
            inventory_items = self.inventory_repository.get_all(filters)

            # Build inventory list with item details
            inventory_list = []
            for inventory in inventory_items:
                inventory_dict = self._to_dict(inventory)

                # Get item details
                item_details = self._get_item_details(inventory.item_type, inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                inventory_list.append(inventory_dict)

            return inventory_list
        except Exception as e:
            self.logger.error(f"Error retrieving inventory: {str(e)}")
            raise

    def get_by_item(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """Get inventory by item type and ID.

        Args:
            item_type: Type of the item (material, product, tool)
            item_id: ID of the item

        Returns:
            Dict representing the inventory

        Raises:
            NotFoundError: If inventory not found
        """
        try:
            inventory = self.inventory_repository.get_by_item(item_type, item_id)
            if not inventory:
                raise NotFoundError(f"Inventory for {item_type} with ID {item_id} not found")

            # Get item details
            inventory_dict = self._to_dict(inventory)
            item_details = self._get_item_details(item_type, item_id)
            if item_details:
                inventory_dict['item_details'] = item_details

            return inventory_dict
        except Exception as e:
            self.logger.error(f"Error retrieving inventory for {item_type} {item_id}: {str(e)}")
            raise

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get inventory by status.

        Args:
            status: Inventory status

        Returns:
            List of dicts representing inventory with the given status

        Raises:
            ValidationError: If invalid status
        """
        try:
            # Validate status
            try:
                InventoryStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid inventory status: {status}")

            # Get inventory by status
            inventory_items = self.inventory_repository.get_by_status(status)

            # Build inventory list with item details
            inventory_list = []
            for inventory in inventory_items:
                inventory_dict = self._to_dict(inventory)

                # Get item details
                item_details = self._get_item_details(inventory.item_type, inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                inventory_list.append(inventory_dict)

            return inventory_list
        except Exception as e:
            self.logger.error(f"Error retrieving inventory with status {status}: {str(e)}")
            raise

    def get_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Get inventory by storage location.

        Args:
            location: Storage location

        Returns:
            List of dicts representing inventory in the given location
        """
        try:
            # Get inventory by location
            inventory_items = self.inventory_repository.get_by_location(location)

            # Build inventory list with item details
            inventory_list = []
            for inventory in inventory_items:
                inventory_dict = self._to_dict(inventory)

                # Get item details
                item_details = self._get_item_details(inventory.item_type, inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                inventory_list.append(inventory_dict)

            return inventory_list
        except Exception as e:
            self.logger.error(f"Error retrieving inventory in location {location}: {str(e)}")
            raise

    def get_low_stock(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get inventory with low stock levels.

        Args:
            threshold: Optional quantity threshold (if not provided, uses LOW_STOCK status)

        Returns:
            List of dicts representing inventory with low stock
        """
        try:
            # Get low stock inventory
            if threshold is not None:
                inventory_items = self.inventory_repository.get_by_quantity_below(threshold)
            else:
                inventory_items = self.inventory_repository.get_by_status(InventoryStatus.LOW_STOCK.value)

            # Build inventory list with item details
            inventory_list = []
            for inventory in inventory_items:
                inventory_dict = self._to_dict(inventory)

                # Get item details
                item_details = self._get_item_details(inventory.item_type, inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                inventory_list.append(inventory_dict)

            return inventory_list
        except Exception as e:
            self.logger.error(f"Error retrieving low stock inventory: {str(e)}")
            raise

    def get_out_of_stock(self) -> List[Dict[str, Any]]:
        """Get out of stock inventory.

        Returns:
            List of dicts representing out of stock inventory
        """
        try:
            # Get out of stock inventory
            inventory_items = self.inventory_repository.get_by_status(InventoryStatus.OUT_OF_STOCK.value)

            # Build inventory list with item details
            inventory_list = []
            for inventory in inventory_items:
                inventory_dict = self._to_dict(inventory)

                # Get item details
                item_details = self._get_item_details(inventory.item_type, inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                inventory_list.append(inventory_dict)

            return inventory_list
        except Exception as e:
            self.logger.error(f"Error retrieving out of stock inventory: {str(e)}")
            raise

    def create(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new inventory entry.

        Args:
            inventory_data: Dict containing inventory properties

        Returns:
            Dict representing the created inventory

        Raises:
            ValidationError: If validation fails
            NotFoundError: If item not found
        """
        try:
            # Validate inventory data
            self._validate_inventory_data(inventory_data)

            # Check if item exists
            item_type = inventory_data['item_type']
            item_id = inventory_data['item_id']
            self._check_item_exists(item_type, item_id)

            # Check if inventory already exists for this item
            existing_inventory = self.inventory_repository.get_by_item(item_type, item_id)
            if existing_inventory:
                raise ValidationError(f"Inventory already exists for {item_type} with ID {item_id}")

            # Set default status if not provided
            if 'status' not in inventory_data:
                quantity = inventory_data.get('quantity', 0)
                inventory_data['status'] = self._determine_inventory_status(quantity)

            # Create inventory
            with self.transaction():
                inventory = self.inventory_repository.create(inventory_data)

                # Get item details
                inventory_dict = self._to_dict(inventory)
                item_details = self._get_item_details(item_type, item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                return inventory_dict
        except Exception as e:
            self.logger.error(f"Error creating inventory: {str(e)}")
            raise

    def update(self, inventory_id: int, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing inventory entry.

        Args:
            inventory_id: ID of the inventory to update
            inventory_data: Dict containing updated inventory properties

        Returns:
            Dict representing the updated inventory

        Raises:
            NotFoundError: If inventory not found
            ValidationError: If validation fails
        """
        try:
            # Check if inventory exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory with ID {inventory_id} not found")

            # Validate inventory data
            self._validate_inventory_data(inventory_data, update=True)

            # Check if item type and ID are being changed
            if ('item_type' in inventory_data or 'item_id' in inventory_data):
                item_type = inventory_data.get('item_type', inventory.item_type)
                item_id = inventory_data.get('item_id', inventory.item_id)

                # Check if the new item exists
                self._check_item_exists(item_type, item_id)

                # Check if inventory already exists for this item
                if item_type != inventory.item_type or item_id != inventory.item_id:
                    existing_inventory = self.inventory_repository.get_by_item(item_type, item_id)
                    if existing_inventory:
                        raise ValidationError(f"Inventory already exists for {item_type} with ID {item_id}")

            # Update status based on quantity if quantity is being changed
            if 'quantity' in inventory_data and 'status' not in inventory_data:
                inventory_data['status'] = self._determine_inventory_status(inventory_data['quantity'])

            # Update inventory
            with self.transaction():
                updated_inventory = self.inventory_repository.update(inventory_id, inventory_data)

                # Get item details
                inventory_dict = self._to_dict(updated_inventory)
                item_details = self._get_item_details(updated_inventory.item_type, updated_inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                return inventory_dict
        except Exception as e:
            self.logger.error(f"Error updating inventory {inventory_id}: {str(e)}")
            raise

    def delete(self, inventory_id: int) -> bool:
        """Delete an inventory entry by ID.

        Args:
            inventory_id: ID of the inventory to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If inventory not found
        """
        try:
            # Check if inventory exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory with ID {inventory_id} not found")

            # Delete inventory
            with self.transaction():
                self.inventory_repository.delete(inventory_id)
                return True
        except Exception as e:
            self.logger.error(f"Error deleting inventory {inventory_id}: {str(e)}")
            raise

    def adjust_quantity(self, inventory_id: int, adjustment: float,
                        adjustment_type: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Adjust inventory quantity.

        Args:
            inventory_id: ID of the inventory
            adjustment: Quantity to adjust (positive for increase, negative for decrease)
            adjustment_type: Type of adjustment
            notes: Optional notes for the adjustment

        Returns:
            Dict representing the updated inventory

        Raises:
            NotFoundError: If inventory not found
            ValidationError: If validation fails
        """
        try:
            # Check if inventory exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory with ID {inventory_id} not found")

            # Validate adjustment type
            try:
                InventoryAdjustmentType(adjustment_type)
            except ValueError:
                raise ValidationError(f"Invalid adjustment type: {adjustment_type}")

            # Calculate new quantity
            new_quantity = inventory.quantity + adjustment

            # Validate new quantity
            if new_quantity < 0:
                raise ValidationError(f"Adjustment would result in negative quantity")

            # Update inventory
            with self.transaction():
                # Determine new status
                new_status = self._determine_inventory_status(new_quantity)

                # Update inventory
                inventory_data = {
                    'quantity': new_quantity,
                    'status': new_status
                }
                updated_inventory = self.inventory_repository.update(inventory_id, inventory_data)

                # Record transaction if transaction repository is available
                if hasattr(self, 'transaction_repository'):
                    transaction_type = TransactionType.USAGE.value if adjustment < 0 else TransactionType.RESTOCK.value
                    transaction_data = {
                        'item_type': inventory.item_type,
                        'item_id': inventory.item_id,
                        'quantity': abs(adjustment),
                        'type': transaction_type,
                        'notes': notes or f"{adjustment_type} adjustment",
                        'created_at': datetime.now()
                    }
                    self.transaction_repository.create(transaction_data)

                # Get item details
                inventory_dict = self._to_dict(updated_inventory)
                item_details = self._get_item_details(inventory.item_type, inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                return inventory_dict
        except Exception as e:
            self.logger.error(f"Error adjusting inventory {inventory_id}: {str(e)}")
            raise

    def transfer_location(self, inventory_id: int, new_location: str) -> Dict[str, Any]:
        """Transfer inventory to a new location.

        Args:
            inventory_id: ID of the inventory
            new_location: New storage location

        Returns:
            Dict representing the updated inventory

        Raises:
            NotFoundError: If inventory not found
        """
        try:
            # Check if inventory exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory with ID {inventory_id} not found")

            # Validate location
            if not new_location:
                raise ValidationError(f"New location cannot be empty")

            # Update inventory location
            with self.transaction():
                updated_inventory = self.inventory_repository.update(inventory_id, {'storage_location': new_location})

                # Get item details
                inventory_dict = self._to_dict(updated_inventory)
                item_details = self._get_item_details(inventory.item_type, inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                return inventory_dict
        except Exception as e:
            self.logger.error(f"Error transferring inventory {inventory_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for inventory by query string.

        Args:
            query: Search query string

        Returns:
            List of dicts representing matching inventory
        """
        try:
            # Search inventory
            inventory_items = self.inventory_repository.search(query)

            # Build inventory list with item details
            inventory_list = []
            for inventory in inventory_items:
                inventory_dict = self._to_dict(inventory)

                # Get item details
                item_details = self._get_item_details(inventory.item_type, inventory.item_id)
                if item_details:
                    inventory_dict['item_details'] = item_details

                inventory_list.append(inventory_dict)

            return inventory_list
        except Exception as e:
            self.logger.error(f"Error searching inventory: {str(e)}")
            raise

    # Helper methods

    def _validate_inventory_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate inventory data.

        Args:
            data: Inventory data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields for new inventory
        if not update:
            required_fields = ['item_type', 'item_id', 'quantity']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate item_type if provided
        if 'item_type' in data:
            item_type = data['item_type']
            valid_types = ['material', 'product', 'tool']
            if item_type not in valid_types:
                raise ValidationError(f"Invalid item type: {item_type}")

        # Validate quantity if provided
        if 'quantity' in data:
            quantity = data['quantity']
            if not isinstance(quantity, (int, float)) or quantity < 0:
                raise ValidationError(f"Quantity must be non-negative")

        # Validate status if provided
        if 'status' in data:
            try:
                InventoryStatus(data['status'])
            except ValueError:
                raise ValidationError(f"Invalid inventory status: {data['status']}")

    def _check_item_exists(self, item_type: str, item_id: int) -> None:
        """Check if an item exists.

        Args:
            item_type: Type of the item
            item_id: ID of the item

        Raises:
            NotFoundError: If item not found
        """
        if item_type == 'material':
            material = self.material_repository.get_by_id(item_id)
            if not material:
                raise NotFoundError(f"Material with ID {item_id} not found")
        elif item_type == 'product':
            product = self.product_repository.get_by_id(item_id)
            if not product:
                raise NotFoundError(f"Product with ID {item_id} not found")
        elif item_type == 'tool':
            tool = self.tool_repository.get_by_id(item_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {item_id} not found")
        else:
            raise ValidationError(f"Invalid item type: {item_type}")

    def _get_item_details(self, item_type: str, item_id: int) -> Optional[Dict[str, Any]]:
        """Get details for an item.

        Args:
            item_type: Type of the item
            item_id: ID of the item

        Returns:
            Dict with item details, or None if item not found
        """
        try:
            if item_type == 'material':
                material = self.material_repository.get_by_id(item_id)
                if material:
                    details = self._to_dict(material)

                    # Add material-specific details
                    details['type'] = 'Material'
                    if hasattr(material, 'material_type'):
                        details['subtype'] = material.material_type

                    return details
            elif item_type == 'product':
                product = self.product_repository.get_by_id(item_id)
                if product:
                    details = self._to_dict(product)
                    details['type'] = 'Product'
                    return details
            elif item_type == 'tool':
                tool = self.tool_repository.get_by_id(item_id)
                if tool:
                    details = self._to_dict(tool)
                    details['type'] = 'Tool'
                    if hasattr(tool, 'tool_type'):
                        details['subtype'] = tool.tool_type
                    return details
        except Exception as e:
            self.logger.warning(f"Error getting details for {item_type} {item_id}: {str(e)}")

        return None

    def _determine_inventory_status(self, quantity: float) -> str:
        """Determine inventory status based on quantity.

        Args:
            quantity: Current inventory quantity

        Returns:
            Inventory status string
        """
        if quantity <= 0:
            return InventoryStatus.OUT_OF_STOCK.value
        elif quantity < 5:  # This threshold could be configurable
            return InventoryStatus.LOW_STOCK.value
        else:
            return InventoryStatus.IN_STOCK.value