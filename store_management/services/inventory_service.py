from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from store_management.database.sqlalchemy.models.part import Part
from store_management.database.sqlalchemy.models.leather import Leather
from store_management.database.sqlalchemy.models.supplier import Supplier
from store_management.database.sqlalchemy.models.enums import InventoryStatus, TransactionType
from store_management.database.sqlalchemy.models.transaction import InventoryTransaction
from store_management.database.sqlalchemy.manager_factory import get_manager


class InventoryService:
    """Service for inventory management operations"""

    def __init__(self):
        """Initialize service with appropriate managers"""
        self.part_manager = get_manager(Part)
        self.leather_manager = get_manager(Leather)
        self.supplier_manager = get_manager(Supplier)
        self.transaction_manager = get_manager(InventoryTransaction)

    def update_part_stock(self, part_id: int, quantity_change: int,
                          transaction_type: TransactionType, notes: Optional[str] = None) -> Tuple[bool, str]:
        """Update part stock with transaction tracking.

        Args:
            part_id: Part ID
            quantity_change: Change in quantity (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get the part
            part = self.part_manager.get(part_id)
            if not part:
                return False, f"Part with ID {part_id} not found"

            # Update stock
            new_stock = part.stock_level + quantity_change
            if new_stock < 0:
                return False, "Cannot reduce stock below zero"

            # Update part
            self.part_manager.update(part_id, {"stock_level": new_stock})

            # Create transaction record
            transaction_data = {
                "part_id": part_id,
                "quantity": quantity_change,
                "transaction_type": transaction_type,
                "notes": notes,
                "timestamp": datetime.now()
            }
            self.transaction_manager.create(transaction_data)

            return True, f"Stock updated successfully, new level: {new_stock}"
        except Exception as e:
            return False, f"Error updating stock: {str(e)}"