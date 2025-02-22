# services/inventory_service.py

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from database.models.part import Part
from database.models.leather import Leather
from database.models.InventoryStatus import InventoryStatus
from database.models.TransactionType import TransactionType
from database.models.InventoryTransaction import InventoryTransaction
from database.sqlalchemy.core.manager_factory import get_manager


class InventoryService:
    """Service for inventory management operations."""

    def __init__(self):
        """Initialize service with appropriate managers."""
        self.part_manager = get_manager(Part)
        self.leather_manager = get_manager(Leather)
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

            # Check if the operation would result in negative stock
            if part.stock_level + quantity_change < 0:
                return False, "Operation would result in negative stock level"

            # Update part stock level
            part.stock_level += quantity_change

            # Update part status if needed
            if part.stock_level <= part.min_stock_level:
                part.status = InventoryStatus.LOW_STOCK
            elif part.stock_level == 0:
                part.status = InventoryStatus.OUT_OF_STOCK
            else:
                part.status = InventoryStatus.IN_STOCK

            # Create transaction record
            transaction = InventoryTransaction(
                part_id=part_id,
                quantity=quantity_change,
                transaction_type=transaction_type,
                notes=notes,
                timestamp=datetime.now()
            )

            # Update the part and create the transaction
            self.part_manager.update(part_id, part.__dict__)
            self.transaction_manager.create(transaction.__dict__)

            return True, "Stock updated successfully"
        except Exception as e:
            return False, f"Error updating stock: {str(e)}"

    # Additional methods would be implemented here...
    def update_leather_area(self, leather_id: int, area_change: float,
                            transaction_type: TransactionType, notes: Optional[str] = None,
                            wastage: Optional[float] = None) -> Tuple[bool, str]:
        """Update leather area with transaction tracking.

        Args:
            leather_id: Leather ID
            area_change: Change in area (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes
            wastage: Optional wastage area

        Returns:
            Tuple of (success, message)
        """
        # Implementation similar to update_part_stock but for leather
        pass

    def get_low_stock_parts(self, include_out_of_stock: bool = True) -> List[Part]:
        """Get parts with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of parts with low stock
        """
        # Implementation would use the part_manager to fetch parts with low stock
        pass

    def get_low_stock_leather(self, include_out_of_stock: bool = True) -> List[Leather]:
        """Get leather with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of leather with low stock
        """
        # Implementation would use the leather_manager to fetch leather with low stock
        pass