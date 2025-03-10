# services/implementations/purchase_service.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from di.inject import inject
from sqlalchemy.orm import Session

from database.models.enums import InventoryStatus, PurchaseStatus, TransactionType
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.purchase_item_repository import PurchaseItemRepository
from database.repositories.purchase_repository import PurchaseRepository
from database.repositories.supplier_repository import SupplierRepository
from database.repositories.tool_repository import ToolRepository

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.purchase_service import IPurchaseService

import logging


class PurchaseService(BaseService, IPurchaseService):
    """Implementation of the purchase service interface.

    This class provides functionality for managing purchase orders,
    including creation, retrieval, updating, and processing.
    """

    @inject
    def __init__(
            self,
            session: Session,
            purchase_repository: PurchaseRepository,
            purchase_item_repository: PurchaseItemRepository,
            supplier_repository: SupplierRepository,
            material_repository: MaterialRepository,
            tool_repository: ToolRepository,
            inventory_repository: InventoryRepository
    ):
        """Initialize the PurchaseService with required repositories.

        Args:
            session: SQLAlchemy database session
            purchase_repository: Repository for purchase operations
            purchase_item_repository: Repository for purchase item operations
            supplier_repository: Repository for supplier operations
            material_repository: Repository for material operations
            tool_repository: Repository for tool operations
            inventory_repository: Repository for inventory operations
        """
        super().__init__(session)
        self._logger = logging.getLogger(__name__)
        self._purchase_repository = purchase_repository
        self._purchase_item_repository = purchase_item_repository
        self._supplier_repository = supplier_repository
        self._material_repository = material_repository
        self._tool_repository = tool_repository
        self._inventory_repository = inventory_repository

    def get_all_purchases(self) -> List[Dict[str, Any]]:
        """Get all purchases.

        Returns:
            List[Dict[str, Any]]: List of purchase dictionaries
        """
        self._logger.info("Retrieving all purchases")
        purchases = self._purchase_repository.get_all()
        return [self._to_dict(purchase) for purchase in purchases]

    def get_purchase_by_id(self, purchase_id: int) -> Dict[str, Any]:
        """Get purchase by ID.

        Args:
            purchase_id: ID of the purchase

        Returns:
            Dict[str, Any]: Purchase dictionary

        Raises:
            NotFoundError: If purchase not found
        """
        self._logger.info(f"Retrieving purchase with ID: {purchase_id}")
        purchase = self._purchase_repository.get_by_id(purchase_id)
        if not purchase:
            self._logger.error(f"Purchase with ID {purchase_id} not found")
            raise NotFoundError(f"Purchase with ID {purchase_id} not found")
        return self._to_dict(purchase)

    def create_purchase(self, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new purchase order.

        Args:
            purchase_data: Purchase data dictionary

        Returns:
            Dict[str, Any]: Created purchase dictionary

        Raises:
            ValidationError: If validation fails
        """
        self._logger.info("Creating new purchase")
        self._validate_purchase_data(purchase_data)

        # Ensure supplier exists if provided
        supplier_id = purchase_data.get('supplier_id')
        if supplier_id:
            supplier = self._supplier_repository.get_by_id(supplier_id)
            if not supplier:
                self._logger.error(f"Supplier with ID {supplier_id} not found")
                raise ValidationError(f"Supplier with ID {supplier_id} not found")

        # Ensure purchase has a status
        if 'status' not in purchase_data:
            purchase_data['status'] = PurchaseStatus.DRAFT.name

        try:
            purchase = self._purchase_repository.create(purchase_data)
            self._session.commit()
            self._logger.info(f"Created purchase with ID: {purchase.id}")
            return self._to_dict(purchase)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to create purchase: {str(e)}")
            raise ValidationError(f"Failed to create purchase: {str(e)}")

    def update_purchase(self, purchase_id: int, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing purchase.

        Args:
            purchase_id: ID of the purchase to update
            purchase_data: Updated purchase data

        Returns:
            Dict[str, Any]: Updated purchase dictionary

        Raises:
            NotFoundError: If purchase not found
            ValidationError: If validation fails
        """
        self._logger.info(f"Updating purchase with ID: {purchase_id}")
        purchase = self._purchase_repository.get_by_id(purchase_id)
        if not purchase:
            self._logger.error(f"Purchase with ID {purchase_id} not found")
            raise NotFoundError(f"Purchase with ID {purchase_id} not found")

        self._validate_purchase_data(purchase_data, is_update=True)

        # Ensure supplier exists if provided
        supplier_id = purchase_data.get('supplier_id')
        if supplier_id:
            supplier = self._supplier_repository.get_by_id(supplier_id)
            if not supplier:
                self._logger.error(f"Supplier with ID {supplier_id} not found")
                raise ValidationError(f"Supplier with ID {supplier_id} not found")

        try:
            updated_purchase = self._purchase_repository.update(purchase_id, purchase_data)
            self._session.commit()
            self._logger.info(f"Updated purchase with ID: {purchase_id}")
            return self._to_dict(updated_purchase)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to update purchase: {str(e)}")
            raise ValidationError(f"Failed to update purchase: {str(e)}")

    def delete_purchase(self, purchase_id: int) -> bool:
        """Delete a purchase.

        Args:
            purchase_id: ID of the purchase to delete

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If purchase not found
        """
        self._logger.info(f"Deleting purchase with ID: {purchase_id}")
        purchase = self._purchase_repository.get_by_id(purchase_id)
        if not purchase:
            self._logger.error(f"Purchase with ID {purchase_id} not found")
            raise NotFoundError(f"Purchase with ID {purchase_id} not found")

        # Check if purchase can be deleted (only DRAFT or CANCELLED can be deleted)
        if purchase.status not in [PurchaseStatus.DRAFT, PurchaseStatus.CANCELLED]:
            self._logger.error(f"Cannot delete purchase with status {purchase.status.name}")
            raise ValidationError(f"Cannot delete purchase with status {purchase.status.name}")

        try:
            # Delete all purchase items first
            purchase_items = self._purchase_item_repository.get_by_purchase_id(purchase_id)
            for item in purchase_items:
                self._purchase_item_repository.delete(item.id)

            self._purchase_repository.delete(purchase_id)
            self._session.commit()
            self._logger.info(f"Deleted purchase with ID: {purchase_id}")
            return True
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to delete purchase: {str(e)}")
            raise ValidationError(f"Failed to delete purchase: {str(e)}")

    def add_purchase_item(self, purchase_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a purchase.

        Args:
            purchase_id: ID of the purchase
            item_data: Purchase item data

        Returns:
            Dict[str, Any]: Created purchase item dictionary

        Raises:
            NotFoundError: If purchase not found
            ValidationError: If validation fails
        """
        self._logger.info(f"Adding item to purchase with ID: {purchase_id}")
        purchase = self._purchase_repository.get_by_id(purchase_id)
        if not purchase:
            self._logger.error(f"Purchase with ID {purchase_id} not found")
            raise NotFoundError(f"Purchase with ID {purchase_id} not found")

        # Can only add items to purchases in DRAFT or ORDERED status
        if purchase.status not in [PurchaseStatus.DRAFT, PurchaseStatus.ORDERED]:
            self._logger.error(f"Cannot add items to purchase with status {purchase.status.name}")
            raise ValidationError(f"Cannot add items to purchase with status {purchase.status.name}")

        self._validate_purchase_item_data(item_data)

        # Add purchase_id to item data
        item_data['purchase_id'] = purchase_id

        try:
            purchase_item = self._purchase_item_repository.create(item_data)

            # Update purchase total amount
            total_amount = purchase.total_amount or 0
            item_total = purchase_item.price * purchase_item.quantity
            self._purchase_repository.update(purchase_id, {'total_amount': total_amount + item_total})

            self._session.commit()
            self._logger.info(f"Added item to purchase with ID: {purchase_id}")
            return self._to_dict_item(purchase_item)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to add purchase item: {str(e)}")
            raise ValidationError(f"Failed to add purchase item: {str(e)}")

    def update_purchase_status(self, purchase_id: int, status: str) -> Dict[str, Any]:
        """Update the status of a purchase.

        Args:
            purchase_id: ID of the purchase
            status: New status value

        Returns:
            Dict[str, Any]: Updated purchase dictionary

        Raises:
            NotFoundError: If purchase not found
            ValidationError: If validation fails
        """
        self._logger.info(f"Updating status of purchase with ID: {purchase_id} to {status}")
        purchase = self._purchase_repository.get_by_id(purchase_id)
        if not purchase:
            self._logger.error(f"Purchase with ID {purchase_id} not found")
            raise NotFoundError(f"Purchase with ID {purchase_id} not found")

        # Validate status value
        try:
            status_enum = PurchaseStatus[status.upper()]
        except KeyError:
            self._logger.error(f"Invalid purchase status: {status}")
            raise ValidationError(f"Invalid purchase status: {status}")

        # Validate status transition
        current_status = purchase.status
        if not self._is_valid_status_transition(current_status, status_enum):
            self._logger.error(f"Invalid status transition from {current_status.name} to {status_enum.name}")
            raise ValidationError(f"Invalid status transition from {current_status.name} to {status_enum.name}")

        try:
            updated_purchase = self._purchase_repository.update(purchase_id, {'status': status_enum})
            self._session.commit()
            self._logger.info(f"Updated status of purchase with ID: {purchase_id} to {status_enum.name}")
            return self._to_dict(updated_purchase)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to update purchase status: {str(e)}")
            raise ValidationError(f"Failed to update purchase status: {str(e)}")

    def receive_purchase(self, purchase_id: int, received_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mark a purchase as received and update inventory.

        Args:
            purchase_id: ID of the purchase
            received_items: List of received items with quantities

        Returns:
            Dict[str, Any]: Updated purchase dictionary

        Raises:
            NotFoundError: If purchase not found
            ValidationError: If validation fails
        """
        self._logger.info(f"Processing receipt for purchase with ID: {purchase_id}")
        purchase = self._purchase_repository.get_by_id(purchase_id)
        if not purchase:
            self._logger.error(f"Purchase with ID {purchase_id} not found")
            raise NotFoundError(f"Purchase with ID {purchase_id} not found")

        # Purchase must be in ORDERED status
        if purchase.status != PurchaseStatus.ORDERED:
            self._logger.error(f"Cannot receive purchase with status {purchase.status.name}")
            raise ValidationError(f"Cannot receive purchase with status {purchase.status.name}")

        # Validate received items
        purchase_items = self._purchase_item_repository.get_by_purchase_id(purchase_id)
        purchase_items_dict = {item.id: item for item in purchase_items}

        for received_item in received_items:
            item_id = received_item.get('item_id')
            received_quantity = received_item.get('quantity')

            if not item_id or item_id not in purchase_items_dict:
                self._logger.error(f"Invalid purchase item ID: {item_id}")
                raise ValidationError(f"Invalid purchase item ID: {item_id}")

            if not received_quantity or received_quantity <= 0:
                self._logger.error(f"Invalid received quantity: {received_quantity}")
                raise ValidationError(f"Invalid received quantity: {received_quantity}")

            if received_quantity > purchase_items_dict[item_id].quantity:
                self._logger.error(f"Received quantity exceeds ordered quantity for item {item_id}")
                raise ValidationError(f"Received quantity exceeds ordered quantity for item {item_id}")

        try:
            # Process each received item
            all_items_received = True

            for received_item in received_items:
                item_id = received_item['item_id']
                received_quantity = received_item['quantity']
                purchase_item = purchase_items_dict[item_id]

                # Update inventory
                self._update_inventory_for_received_item(purchase_item, received_quantity)

                # Update purchase item received quantity
                current_received = purchase_item.received_quantity or 0
                new_received = current_received + received_quantity
                self._purchase_item_repository.update(item_id, {'received_quantity': new_received})

                # Check if all ordered quantity is received
                if new_received < purchase_item.quantity:
                    all_items_received = False

            # Update purchase status based on received items
            new_status = PurchaseStatus.RECEIVED if all_items_received else PurchaseStatus.PARTIALLY_RECEIVED
            updated_purchase = self._purchase_repository.update(purchase_id, {'status': new_status})

            self._session.commit()
            self._logger.info(f"Processed receipt for purchase with ID: {purchase_id}")
            return self._to_dict(updated_purchase)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to process purchase receipt: {str(e)}")
            raise ValidationError(f"Failed to process purchase receipt: {str(e)}")

    def get_purchases_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get purchases by supplier ID.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List[Dict[str, Any]]: List of purchase dictionaries

        Raises:
            NotFoundError: If supplier not found
        """
        self._logger.info(f"Retrieving purchases for supplier with ID: {supplier_id}")
        supplier = self._supplier_repository.get_by_id(supplier_id)
        if not supplier:
            self._logger.error(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        purchases = self._purchase_repository.get_by_supplier_id(supplier_id)
        return [self._to_dict(purchase) for purchase in purchases]

    def get_purchases_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get purchases within a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List[Dict[str, Any]]: List of purchase dictionaries
        """
        self._logger.info(f"Retrieving purchases between {start_date} and {end_date}")
        purchases = self._purchase_repository.get_by_date_range(start_date, end_date)
        return [self._to_dict(purchase) for purchase in purchases]

    def _validate_purchase_data(self, purchase_data: Dict[str, Any], is_update: bool = False) -> None:
        """Validate purchase data.

        Args:
            purchase_data: Purchase data to validate
            is_update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # For create operations, supplier_id is required
        if not is_update and 'supplier_id' not in purchase_data:
            raise ValidationError("supplier_id is required")

        # Validate status if provided
        if 'status' in purchase_data:
            try:
                PurchaseStatus[purchase_data['status'].upper()]
            except KeyError:
                raise ValidationError(f"Invalid purchase status: {purchase_data['status']}")

    def _validate_purchase_item_data(self, item_data: Dict[str, Any]) -> None:
        """Validate purchase item data.

        Args:
            item_data: Purchase item data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Required fields
        required_fields = ['item_id', 'item_type', 'quantity', 'price']
        for field in required_fields:
            if field not in item_data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate item type
        item_type = item_data['item_type'].lower()
        if item_type not in ['material', 'tool']:
            raise ValidationError(f"Invalid item type: {item_type}")

        # Validate item exists
        item_id = item_data['item_id']
        if item_type == 'material':
            item = self._material_repository.get_by_id(item_id)
        else:  # tool
            item = self._tool_repository.get_by_id(item_id)

        if not item:
            raise ValidationError(f"{item_type.capitalize()} with ID {item_id} not found")

        # Validate quantity and price
        quantity = item_data['quantity']
        price = item_data['price']

        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise ValidationError(f"Invalid quantity: {quantity}")

        if not isinstance(price, (int, float)) or price < 0:
            raise ValidationError(f"Invalid price: {price}")

    def _is_valid_status_transition(self, current_status: PurchaseStatus, new_status: PurchaseStatus) -> bool:
        """Check if a status transition is valid.

        Args:
            current_status: Current purchase status
            new_status: New purchase status

        Returns:
            bool: True if the transition is valid
        """
        # Define valid transitions
        valid_transitions = {
            PurchaseStatus.DRAFT: [PurchaseStatus.ORDERED, PurchaseStatus.CANCELLED],
            PurchaseStatus.ORDERED: [PurchaseStatus.PARTIALLY_RECEIVED, PurchaseStatus.RECEIVED,
                                     PurchaseStatus.CANCELLED],
            PurchaseStatus.PARTIALLY_RECEIVED: [PurchaseStatus.RECEIVED],
            PurchaseStatus.RECEIVED: [],
            PurchaseStatus.CANCELLED: []
        }

        # Allow setting the same status
        if current_status == new_status:
            return True

        return new_status in valid_transitions.get(current_status, [])

    def _update_inventory_for_received_item(self, purchase_item, received_quantity):
        """Update inventory for a received purchase item.

        Args:
            purchase_item: Purchase item model
            received_quantity: Quantity received
        """
        item_id = purchase_item.item_id
        item_type = purchase_item.item_type.lower()

        # Find existing inventory entry or create new one
        inventory_entry = self._inventory_repository.get_by_item(item_type, item_id)

        if inventory_entry:
            # Update existing inventory
            current_quantity = inventory_entry.quantity or 0
            new_quantity = current_quantity + received_quantity

            # Determine new status
            new_status = InventoryStatus.IN_STOCK
            if new_quantity <= 0:
                new_status = InventoryStatus.OUT_OF_STOCK

            self._inventory_repository.update(inventory_entry.id, {
                'quantity': new_quantity,
                'status': new_status
            })

            # Create inventory transaction
            self._inventory_repository.create_transaction(
                inventory_id=inventory_entry.id,
                transaction_type=TransactionType.PURCHASE,
                quantity=received_quantity,
                purchase_id=purchase_item.purchase_id
            )
        else:
            # Create new inventory entry
            inventory_data = {
                'item_type': item_type,
                'item_id': item_id,
                'quantity': received_quantity,
                'status': InventoryStatus.IN_STOCK
            }

            new_inventory = self._inventory_repository.create(inventory_data)

            # Create inventory transaction
            self._inventory_repository.create_transaction(
                inventory_id=new_inventory.id,
                transaction_type=TransactionType.PURCHASE,
                quantity=received_quantity,
                purchase_id=purchase_item.purchase_id
            )

    def _to_dict(self, purchase) -> Dict[str, Any]:
        """Convert purchase model to dictionary.

        Args:
            purchase: Purchase model object

        Returns:
            Dict[str, Any]: Purchase dictionary
        """
        # Get purchase items
        purchase_items = self._purchase_item_repository.get_by_purchase_id(purchase.id)

        # Get supplier name if available
        supplier_name = None
        if purchase.supplier_id:
            supplier = self._supplier_repository.get_by_id(purchase.supplier_id)
            if supplier:
                supplier_name = supplier.name

        return {
            'id': purchase.id,
            'supplier_id': purchase.supplier_id,
            'supplier_name': supplier_name,
            'total_amount': round(purchase.total_amount, 2) if purchase.total_amount else 0,
            'status': purchase.status.name if purchase.status else None,
            'created_at': purchase.created_at.isoformat() if purchase.created_at else None,
            'updated_at': purchase.updated_at.isoformat() if purchase.updated_at else None,
            'items': [self._to_dict_item(item) for item in purchase_items]
        }

    def _to_dict_item(self, purchase_item) -> Dict[str, Any]:
        """Convert purchase item model to dictionary.

        Args:
            purchase_item: Purchase item model object

        Returns:
            Dict[str, Any]: Purchase item dictionary
        """
        # Get item details based on type
        item_name = None
        item_type = purchase_item.item_type.lower() if purchase_item.item_type else 'unknown'

        if item_type == 'material':
            material = self._material_repository.get_by_id(purchase_item.item_id)
            if material:
                item_name = material.name
        elif item_type == 'tool':
            tool = self._tool_repository.get_by_id(purchase_item.item_id)
            if tool:
                item_name = tool.name

        return {
            'id': purchase_item.id,
            'purchase_id': purchase_item.purchase_id,
            'item_id': purchase_item.item_id,
            'item_type': item_type,
            'item_name': item_name,
            'quantity': purchase_item.quantity,
            'received_quantity': purchase_item.received_quantity or 0,
            'price': round(purchase_item.price, 2) if purchase_item.price else 0,
            'total': round(purchase_item.price * purchase_item.quantity,
                           2) if purchase_item.price and purchase_item.quantity else 0
        }