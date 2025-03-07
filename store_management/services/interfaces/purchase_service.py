# services/interfaces/purchase_service.py
from abc import ABC, abstractmethod
from database.models.purchase import Purchase, PurchaseItem
from database.models.enums import PurchaseStatus
from typing import Any, Dict, List, Optional

class IPurchaseService(ABC):
    """
    Interface for Purchase Service defining core operations for purchases.
    """

    @abstractmethod
    def create_purchase(
        self,
        supplier_id: int,
        total_amount: float,
        items: List[Dict[str, Any]]
    ) -> Purchase:
        """
        Create a new purchase with associated purchase items.

        Args:
            supplier_id: ID of the supplier
            total_amount: Total purchase amount
            items: List of purchase item details

        Returns:
            Created Purchase instance
        """
        pass

    @abstractmethod
    def get_purchase_by_id(self, purchase_id: int) -> Purchase:
        """
        Retrieve a purchase by its ID.

        Args:
            purchase_id: ID of the purchase to retrieve

        Returns:
            Purchase instance
        """
        pass

    @abstractmethod
    def update_purchase_status(
        self,
        purchase_id: int,
        status: PurchaseStatus
    ) -> Purchase:
        """
        Update the status of a purchase.

        Args:
            purchase_id: ID of the purchase to update
            status: New status for the purchase

        Returns:
            Updated Purchase instance
        """
        pass

    @abstractmethod
    def get_purchases_by_supplier(
        self,
        supplier_id: int,
        status: Optional[PurchaseStatus] = None
    ) -> List[Purchase]:
        """
        Retrieve purchases for a specific supplier, optionally filtered by status.

        Args:
            supplier_id: ID of the supplier
            status: Optional status to filter purchases

        Returns:
            List of Purchase instances
        """
        pass