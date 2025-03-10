# services/implementations/inventory_service.py
# Implementation of the inventory service interface

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.tool_repository import ToolRepository
from database.models.enums import InventoryStatus, TransactionType, InventoryAdjustmentType
from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError
from services.dto.inventory_dto import InventoryDTO, InventoryTransactionDTO

from di.inject import inject


class InventoryService(BaseService):
    """Implementation of the inventory service interface."""

    @inject
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
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, inventory_id: int) -> Dict[str, Any]:
        """Get inventory entry by ID.

        Args:
            inventory_id: ID of the inventory entry to retrieve

        Returns:
            Dict representing the inventory entry

        Raises:
            NotFoundError: If inventory entry not found
        """
        try:
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry with ID {inventory_id} not found")
            return InventoryDTO.from_model(inventory).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving inventory entry {inventory_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all inventory entries, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing inventory entries
        """
        try:
            inventory_entries = self.inventory_repository.get_all(filters)
            return [InventoryDTO.from_model(entry).to_dict() for entry in inventory_entries]
        except Exception as e:
            self.logger.error(f"Error retrieving inventory entries: {str(e)}")
            raise

    def create(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new inventory entry.

        Args:
            inventory_data: Dict containing inventory properties

        Returns:
            Dict representing the created inventory entry

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate inventory data
            self._validate_inventory_data(inventory_data)

            # Create inventory entry
            with self.transaction():
                inventory = self.inventory_repository.create(inventory_data)

                # Log initial inventory transaction if quantity > 0
                if inventory.quantity > 0:
                    transaction_data = {
                        'inventory_id': inventory.id,
                        'item_type': inventory.item_type,
                        'item_id': inventory.item_id,
                        'quantity': inventory.quantity,
                        'type': TransactionType.INITIAL_STOCK.value,
                        'timestamp': datetime.now(),
                        'notes': 'Initial inventory setup'
                    }
                    self.inventory_repository.create_transaction(transaction_data)

                return InventoryDTO.from_model(inventory).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating inventory entry: {str(e)}")
            raise

    def update(self, inventory_id: int, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing inventory entry.

        Args:
            inventory_id: ID of the inventory entry to update
            inventory_data: Dict containing updated inventory properties

        Returns:
            Dict representing the updated inventory entry

        Raises:
            NotFoundError: If inventory entry not found
            ValidationError: If validation fails
        """
        try:
            # Check if inventory entry exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry with ID {inventory_id} not found")

            # Validate inventory data
            self._validate_inventory_data(inventory_data, update=True)

            # Update inventory entry
            with self.transaction():
                # If quantity is being updated, log a transaction
                if 'quantity' in inventory_data and inventory_data['quantity'] != inventory.quantity:
                    quantity_diff = inventory_data['quantity'] - inventory.quantity
                    transaction_type = TransactionType.RESTOCK.value if quantity_diff > 0 else TransactionType.USAGE.value

                    transaction_data = {
                        'inventory_id': inventory.id,
                        'item_type': inventory.item_type,
                        'item_id': inventory.item_id,
                        'quantity': abs(quantity_diff),
                        'type': transaction_type,
                        'timestamp': datetime.now(),
                        'notes': 'Updated through inventory service'
                    }
                    self.inventory_repository.create_transaction(transaction_data)

                updated_inventory = self.inventory_repository.update(inventory_id, inventory_data)
                return InventoryDTO.from_model(updated_inventory).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating inventory entry {inventory_id}: {str(e)}")
            raise

    def delete(self, inventory_id: int) -> bool:
        """Delete an inventory entry by ID.

        Args:
            inventory_id: ID of the inventory entry to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If inventory entry not found
        """
        try:
            # Check if inventory entry exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry with ID {inventory_id} not found")

            # Delete inventory entry
            with self.transaction():
                # Delete related transactions first
                transactions = self.inventory_repository.get_transactions_by_inventory(inventory_id)
                for transaction in transactions:
                    self.inventory_repository.delete_transaction(transaction.id)

                # Then delete inventory entry
                self.inventory_repository.delete(inventory_id)
                return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting inventory entry {inventory_id}: {str(e)}")
            raise

    def get_by_item(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """Get inventory entry by item type and ID.

        Args:
            item_type: Type of the item (material, product, tool)
            item_id: ID of the item

        Returns:
            Dict representing the inventory entry

        Raises:
            NotFoundError: If inventory entry not found
        """
        try:
            inventory = self.inventory_repository.get_by_item(item_type, item_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry for {item_type} with ID {item_id} not found")
            return InventoryDTO.from_model(inventory).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving inventory entry for {item_type} {item_id}: {str(e)}")
            raise

    def adjust_quantity(self, inventory_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust quantity for an inventory entry.

        Args:
            inventory_id: ID of the inventory entry
            quantity: Quantity to adjust (positive for increase, negative for decrease)
            reason: Reason for adjustment

        Returns:
            Dict representing the updated inventory entry

        Raises:
            NotFoundError: If inventory entry not found
            ValidationError: If validation fails
        """
        try:
            # Check if inventory entry exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry with ID {inventory_id} not found")

            # Validate quantity
            if inventory.quantity + quantity < 0:
                raise ValidationError(f"Cannot reduce inventory below zero")

            # Update inventory
            with self.transaction():
                transaction_type = TransactionType.USAGE.value if quantity < 0 else TransactionType.RESTOCK.value

                new_quantity = inventory.quantity + quantity
                new_status = self._determine_inventory_status(new_quantity)

                inventory_data = {
                    'quantity': new_quantity,
                    'status': new_status
                }
                updated_inventory = self.inventory_repository.update(inventory_id, inventory_data)

                # Log transaction
                transaction_data = {
                    'inventory_id': inventory.id,
                    'item_type': inventory.item_type,
                    'item_id': inventory.item_id,
                    'quantity': abs(quantity),
                    'type': transaction_type,
                    'timestamp': datetime.now(),
                    'notes': reason
                }
                self.inventory_repository.create_transaction(transaction_data)

                return InventoryDTO.from_model(updated_inventory).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adjusting quantity for inventory entry {inventory_id}: {str(e)}")
            raise

    def get_low_stock_items(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get inventory items with low stock levels.

        Args:
            threshold: Optional threshold for what's considered "low stock"

        Returns:
            List of inventory items with low stock
        """
        try:
            low_stock_items = self.inventory_repository.get_low_stock(threshold)
            return [InventoryDTO.from_model(item, include_item_details=True).to_dict() for item in low_stock_items]
        except Exception as e:
            self.logger.error(f"Error retrieving low stock items: {str(e)}")
            raise

    def log_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an inventory transaction.

        Args:
            transaction_data: Dict containing transaction properties

        Returns:
            Dict representing the created transaction

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate transaction data
            self._validate_transaction_data(transaction_data)

            # Create transaction
            with self.transaction():
                # Set timestamp if not provided
                if 'timestamp' not in transaction_data:
                    transaction_data['timestamp'] = datetime.now()

                transaction = self.inventory_repository.create_transaction(transaction_data)
                return InventoryTransactionDTO.from_model(transaction).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error logging inventory transaction: {str(e)}")
            raise

    def get_transaction_history(self,
                                item_type: Optional[str] = None,
                                item_id: Optional[int] = None,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get transaction history for an item or date range.

        Args:
            item_type: Optional type of the item (material, product, tool)
            item_id: Optional ID of the item
            start_date: Optional start date for the range
            end_date: Optional end date for the range

        Returns:
            List of transactions matching the criteria
        """
        try:
            transactions = self.inventory_repository.get_transaction_history(
                item_type=item_type,
                item_id=item_id,
                start_date=start_date,
                end_date=end_date
            )
            return [InventoryTransactionDTO.from_model(transaction).to_dict() for transaction in transactions]
        except Exception as e:
            self.logger.error(f"Error retrieving transaction history: {str(e)}")
            raise

    def update_storage_location(self, inventory_id: int, location: str) -> Dict[str, Any]:
        """Update storage location for an inventory entry.

        Args:
            inventory_id: ID of the inventory entry
            location: New storage location

        Returns:
            Dict representing the updated inventory entry

        Raises:
            NotFoundError: If inventory entry not found
            ValidationError: If validation fails
        """
        try:
            # Check if inventory entry exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry with ID {inventory_id} not found")

            # Update storage location
            with self.transaction():
                old_location = inventory.storage_location

                inventory_data = {'storage_location': location}
                updated_inventory = self.inventory_repository.update(inventory_id, inventory_data)

                # Log location change
                location_history_data = {
                    'inventory_id': inventory.id,
                    'previous_location': old_location,
                    'new_location': location,
                    'timestamp': datetime.now(),
                    'notes': 'Location updated through inventory service'
                }
                self.inventory_repository.create_location_history(location_history_data)

                return InventoryDTO.from_model(updated_inventory).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating storage location for inventory entry {inventory_id}: {str(e)}")
            raise

    def update_status(self, inventory_id: int, status: str) -> Dict[str, Any]:
        """Update status for an inventory entry.

        Args:
            inventory_id: ID of the inventory entry
            status: New status

        Returns:
            Dict representing the updated inventory entry

        Raises:
            NotFoundError: If inventory entry not found
            ValidationError: If validation fails
        """
        try:
            # Check if inventory entry exists
            inventory = self.inventory_repository.get_by_id(inventory_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry with ID {inventory_id} not found")

            # Validate status
            self._validate_enum_value(InventoryStatus, status, "inventory status")

            # Update status
            with self.transaction():
                inventory_data = {'status': status}
                updated_inventory = self.inventory_repository.update(inventory_id, inventory_data)
                return InventoryDTO.from_model(updated_inventory).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating status for inventory entry {inventory_id}: {str(e)}")
            raise

    def get_item_availability(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """Get availability information for an item.

        Args:
            item_type: Type of the item (material, product, tool)
            item_id: ID of the item

        Returns:
            Dict with availability information

        Raises:
            NotFoundError: If item not found
        """
        try:
            # Check if item exists
            item = None
            if item_type == 'material':
                item = self.material_repository.get_by_id(item_id)
            elif item_type == 'product':
                item = self.product_repository.get_by_id(item_id)
            elif item_type == 'tool':
                item = self.tool_repository.get_by_id(item_id)
            else:
                raise ValidationError(f"Invalid item type: {item_type}")

            if not item:
                raise NotFoundError(f"{item_type.capitalize()} with ID {item_id} not found")

            # Get inventory entry
            inventory = self.inventory_repository.get_by_item(item_type, item_id)
            if not inventory:
                # Return default availability info
                return {
                    'item_type': item_type,
                    'item_id': item_id,
                    'item_name': getattr(item, 'name', 'Unknown'),
                    'quantity': 0,
                    'status': InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': None,
                    'last_updated': None
                }

            # Return availability info
            return {
                'item_type': item_type,
                'item_id': item_id,
                'item_name': getattr(item, 'name', 'Unknown'),
                'quantity': inventory.quantity,
                'status': inventory.status,
                'storage_location': inventory.storage_location,
                'last_updated': inventory.updated_at
            }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error getting availability for {item_type} {item_id}: {str(e)}")
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
        if not update:
            required_fields = ['item_type', 'item_id', 'quantity', 'status']
            self._validate_required_fields(data, required_fields)

        # Validate quantity
        if 'quantity' in data and data['quantity'] < 0:
            raise ValidationError(f"Quantity cannot be negative")

        # Validate status
        if 'status' in data:
            self._validate_enum_value(InventoryStatus, data['status'], "inventory status")

    def _validate_transaction_data(self, data: Dict[str, Any]) -> None:
        """Validate transaction data.

        Args:
            data: Transaction data to validate

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['item_type', 'item_id', 'quantity', 'type']
        self._validate_required_fields(data, required_fields)

        # Validate quantity
        if 'quantity' in data and data['quantity'] <= 0:
            raise ValidationError(f"Transaction quantity must be positive")

        # Validate transaction type
        if 'type' in data:
            self._validate_enum_value(TransactionType, data['type'], "transaction type")

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