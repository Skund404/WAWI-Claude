# database/repositories/purchase_item_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc

from database.models.purchase_item import PurchaseItem
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError


class PurchaseItemRepository(BaseRepository[PurchaseItem]):
    """Repository for purchase item operations.

    This repository provides methods for querying and manipulating purchase item data,
    including relationships with purchases, materials, and tools.
    """

    def _get_model_class(self) -> Type[PurchaseItem]:
        """Return the model class this repository manages.

        Returns:
            The PurchaseItem model class
        """
        return PurchaseItem

    # Purchase item-specific query methods

    def get_by_purchase(self, purchase_id: int) -> List[PurchaseItem]:
        """Get purchase items for a specific purchase.

        Args:
            purchase_id: ID of the purchase

        Returns:
            List of purchase item instances for the specified purchase
        """
        self.logger.debug(f"Getting purchase items for purchase {purchase_id}")
        return self.session.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase_id).all()

    def get_by_item(self, item_id: int, item_type: str) -> List[PurchaseItem]:
        """Get purchase items for a specific material or tool.

        Args:
            item_id: ID of the item
            item_type: Type of the item ('material' or 'tool')

        Returns:
            List of purchase item instances for the specified item
        """
        self.logger.debug(f"Getting purchase items for {item_type} with ID {item_id}")
        return self.session.query(PurchaseItem).filter(
            PurchaseItem.item_id == item_id,
            PurchaseItem.item_type == item_type
        ).all()

    def get_items_with_details(self, purchase_id: int) -> List[Dict[str, Any]]:
        """Get purchase items with details about the purchased items.

        Args:
            purchase_id: ID of the purchase

        Returns:
            List of purchase items with material or tool details
        """
        self.logger.debug(f"Getting purchase items with details for purchase {purchase_id}")
        from database.models.material import Material
        from database.models.tool import Tool

        items = self.session.query(PurchaseItem).filter(
            PurchaseItem.purchase_id == purchase_id
        ).all()

        result = []
        for item in items:
            item_dict = item.to_dict()
            item_dict['subtotal'] = item.quantity * item.price

            # Add item details based on type
            if item.item_type == 'material':
                material = self.session.query(Material).get(item.item_id)
                if material:
                    item_dict['name'] = material.name
                    item_dict['material_type'] = material.material_type.value
            elif item.item_type == 'tool':
                tool = self.session.query(Tool).get(item.item_id)
                if tool:
                    item_dict['name'] = tool.name
                    item_dict['tool_type'] = tool.tool_type.value

            result.append(item_dict)

        return result

    # Business logic methods

    def calculate_total_amount(self, purchase_id: int) -> float:
        """Calculate the total amount for a purchase.

        Args:
            purchase_id: ID of the purchase

        Returns:
            Total amount for the purchase
        """
        self.logger.debug(f"Calculating total amount for purchase {purchase_id}")

        result = self.session.query(
            func.sum(PurchaseItem.quantity * PurchaseItem.price).label('total')
        ).filter(
            PurchaseItem.purchase_id == purchase_id
        ).scalar()

        return float(result) if result is not None else 0.0

    def update_quantity(self, purchase_item_id: int, new_quantity: int) -> Dict[str, Any]:
        """Update the quantity of a purchase item.

        Args:
            purchase_item_id: ID of the purchase item
            new_quantity: New quantity value

        Returns:
            Updated purchase item data

        Raises:
            EntityNotFoundError: If purchase item not found
            ValidationError: If new quantity is invalid
        """
        self.logger.debug(f"Updating quantity for purchase item {purchase_item_id} to {new_quantity}")

        purchase_item = self.get_by_id(purchase_item_id)
        if not purchase_item:
            raise EntityNotFoundError(f"Purchase item with ID {purchase_item_id} not found")

        if new_quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")

        try:
            # Update quantity
            purchase_item.quantity = new_quantity

            # Update purchase item
            self.update(purchase_item)

            # Calculate new subtotal
            subtotal = purchase_item.quantity * purchase_item.price

            # Update total on the parent purchase
            from database.models.purchase import Purchase
            purchase = self.session.query(Purchase).get(purchase_item.purchase_id)
            if purchase:
                # Recalculate total from all items
                total = self.calculate_total_amount(purchase_item.purchase_id)
                purchase.total_amount = total
                self.session.add(purchase)
                self.session.flush()

            # Prepare result
            result = purchase_item.to_dict()
            result['subtotal'] = subtotal

            return result

        except Exception as e:
            self.logger.error(f"Error updating purchase item quantity: {str(e)}")
            raise ValidationError(f"Failed to update purchase item quantity: {str(e)}")

    def receive_item(self, purchase_item_id: int, received_quantity: int) -> Dict[str, Any]:
        """Mark a purchase item as received and update inventory.

        Args:
            purchase_item_id: ID of the purchase item
            received_quantity: Quantity received

        Returns:
            Updated purchase item data

        Raises:
            EntityNotFoundError: If purchase item not found
            ValidationError: If received quantity is invalid
        """
        self.logger.debug(f"Marking purchase item {purchase_item_id} as received with quantity {received_quantity}")

        purchase_item = self.get_by_id(purchase_item_id)
        if not purchase_item:
            raise EntityNotFoundError(f"Purchase item with ID {purchase_item_id} not found")

        if received_quantity <= 0:
            raise ValidationError("Received quantity must be greater than zero")

        if received_quantity > purchase_item.quantity:
            raise ValidationError(
                f"Received quantity ({received_quantity}) exceeds ordered quantity ({purchase_item.quantity})")

        try:
            # Update received quantity
            purchase_item.received_quantity = received_quantity

            # Update purchase item
            self.update(purchase_item)

            # Update inventory
            from database.models.inventory import Inventory
            from database.models.enums import InventoryStatus, InventoryAdjustmentType

            # Find or create inventory record
            inventory = self.session.query(Inventory).filter(
                Inventory.item_id == purchase_item.item_id,
                Inventory.item_type == purchase_item.item_type
            ).first()

            if inventory:
                # Update existing inventory
                original_quantity = inventory.quantity
                inventory.quantity += received_quantity

                # Update status based on new quantity
                if inventory.quantity > 0:
                    # Check against min_stock if available
                    if purchase_item.item_type == 'material':
                        from database.models.material import Material
                        material = self.session.query(Material).get(purchase_item.item_id)
                        if material and material.min_stock is not None and inventory.quantity <= material.min_stock:
                            inventory.status = InventoryStatus.LOW_STOCK
                        else:
                            inventory.status = InventoryStatus.IN_STOCK
                    else:
                        inventory.status = InventoryStatus.IN_STOCK
            else:
                # Create new inventory record
                inventory = Inventory(
                    item_id=purchase_item.item_id,
                    item_type=purchase_item.item_type,
                    quantity=received_quantity,
                    status=InventoryStatus.IN_STOCK
                )
                self.session.add(inventory)

            # Record inventory transaction history (if implemented)
            # self._record_inventory_transaction(...)

            # Prepare result
            result = purchase_item.to_dict()
            result['received_quantity'] = received_quantity

            return result

        except Exception as e:
            self.logger.error(f"Error receiving purchase item: {str(e)}")
            raise ValidationError(f"Failed to receive purchase item: {str(e)}")

    # GUI-specific functionality

    def get_recent_purchases_by_item(self, item_id: int, item_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent purchases for a specific item.

        Args:
            item_id: ID of the item
            item_type: Type of the item ('material' or 'tool')
            limit: Maximum number of purchases to return

        Returns:
            List of recent purchases for the specified item
        """
        self.logger.debug(f"Getting recent purchases for {item_type} with ID {item_id}")
        from database.models.purchase import Purchase
        from database.models.supplier import Supplier

        recent_purchases = self.session.query(
            PurchaseItem,
            Purchase,
            Supplier
        ).join(
            Purchase,
            Purchase.id == PurchaseItem.purchase_id
        ).join(
            Supplier,
            Supplier.id == Purchase.supplier_id
        ).filter(
            PurchaseItem.item_id == item_id,
            PurchaseItem.item_type == item_type
        ).order_by(
            Purchase.created_at.desc()
        ).limit(limit).all()

        result = []
        for item, purchase, supplier in recent_purchases:
            result.append({
                'purchase_id': purchase.id,
                'purchase_date': purchase.created_at.isoformat(),
                'supplier_name': supplier.name,
                'quantity': item.quantity,
                'price': item.price,
                'total': item.quantity * item.price,
                'status': purchase.status.value
            })

        return result