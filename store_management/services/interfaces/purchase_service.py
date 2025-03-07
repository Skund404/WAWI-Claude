# database/services/interfaces/purchase_service.py
"""
Interface definition for Purchase Service.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from datetime import datetime

from database.models.enums import PurchaseStatus, MaterialType
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem


class IPurchaseService(ABC):
    """
    Interface defining contract for Purchase Service operations.
    """

    @abstractmethod
    def create_purchase(
        self,
        supplier_id: str,
        total_amount: float,
        status: PurchaseStatus = PurchaseStatus.PENDING,
        **kwargs
    ) -> Purchase:
        """
        Create a new purchase.

        Args:
            supplier_id: Unique identifier of the supplier
            total_amount: Total purchase amount
            status: Purchase status (default: PENDING)
            **kwargs: Additional purchase attributes

        Returns:
            Created Purchase instance
        """
        pass

    @abstractmethod
    def get_purchase_by_id(self, purchase_id: str) -> Purchase:
        """
        Retrieve a purchase by its ID.

        Args:
            purchase_id: Unique identifier of the purchase

        Returns:
            Purchase instance
        """
        pass

    @abstractmethod
    def update_purchase_status(
        self,
        purchase_id: str,
        new_status: PurchaseStatus
    ) -> Purchase:
        """
        Update the status of a purchase.

        Args:
            purchase_id: Unique identifier of the purchase
            new_status: New purchase status

        Returns:
            Updated Purchase instance
        """
        pass

    @abstractmethod
    def add_purchase_item(
        self,
        purchase_id: str,
        item_type: MaterialType,
        item_id: str,
        quantity: float,
        price: float,
        **kwargs
    ) -> PurchaseItem:
        """
        Add an item to a purchase.

        Args:
            purchase_id: Unique identifier of the purchase
            item_type: Type of material/item being purchased
            item_id: Unique identifier of the item
            quantity: Quantity of the item
            price: Price per unit
            **kwargs: Additional purchase item attributes

        Returns:
            Created PurchaseItem instance
        """
        pass

    @abstractmethod
    def get_purchase_items(self, purchase_id: str) -> List[PurchaseItem]:
        """
        Retrieve all items for a specific purchase.

        Args:
            purchase_id: Unique identifier of the purchase

        Returns:
            List of PurchaseItem instances
        """
        pass

    @abstractmethod
    def get_purchases_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[PurchaseStatus] = None
    ) -> List[Purchase]:
        """
        Retrieve purchases within a specified date range and optional status.

        Args:
            start_date: Optional start date for filtering purchases
            end_date: Optional end date for filtering purchases
            status: Optional purchase status to filter

        Returns:
            List of Purchase instances
        """
        pass

    @abstractmethod
    def delete_purchase(self, purchase_id: str) -> bool:
        """
        Delete a purchase and its associated items.

        Args:
            purchase_id: Unique identifier of the purchase

        Returns:
            Boolean indicating successful deletion
        """
        pass