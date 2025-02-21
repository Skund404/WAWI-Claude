# store_management/services/interfaces/inventory_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple


class IInventoryService(ABC):
    """Interface for inventory management operations."""

    @abstractmethod
    def update_part_stock(self, part_id: int, quantity_change: int,
                          transaction_type: str, notes: Optional[str] = None) -> Tuple[bool, str]:
        """
        Update part stock with transaction tracking.

        Args:
            part_id: Part ID
            quantity_change: Change in quantity (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes

        Returns:
            Tuple of (success, message)
        """
        pass

    @abstractmethod
    def update_leather_area(self, leather_id: int, area_change: float,
                            transaction_type: str, notes: Optional[str] = None,
                            wastage: Optional[float] = None) -> Tuple[bool, str]:
        """
        Update leather area with transaction tracking.

        Args:
            leather_id: Leather ID
            area_change: Change in area (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes
            wastage: Optional wastage area

        Returns:
            Tuple of (success, message)
        """
        pass

    @abstractmethod
    def get_low_stock_parts(self, include_out_of_stock: bool = True) -> List[Dict[str, Any]]:
        """
        Get parts with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of parts with low stock
        """
        pass

    @abstractmethod
    def get_low_stock_leather(self, include_out_of_stock: bool = True) -> List[Dict[str, Any]]:
        """
        Get leather with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of leather with low stock
        """
        pass