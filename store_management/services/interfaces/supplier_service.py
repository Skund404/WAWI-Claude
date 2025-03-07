# database/services/interfaces/supplier_service.py
"""
Interface definition for Supplier Service.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any
from datetime import datetime

from database.models.enums import SupplierStatus
from database.models.supplier import Supplier
from database.models.purchase import Purchase


class ISupplierService(ABC):
    """
    Interface defining contract for Supplier Service operations.
    """

    @abstractmethod
    def create_supplier(
        self,
        name: str,
        contact_email: str,
        status: SupplierStatus = SupplierStatus.ACTIVE,
        **kwargs
    ) -> Supplier:
        """
        Create a new supplier.

        Args:
            name: Supplier name
            contact_email: Contact email address
            status: Supplier status (default: ACTIVE)
            **kwargs: Additional supplier attributes

        Returns:
            Created Supplier instance
        """
        pass

    @abstractmethod
    def get_supplier_by_id(self, supplier_id: str) -> Supplier:
        """
        Retrieve a supplier by its ID.

        Args:
            supplier_id: Unique identifier of the supplier

        Returns:
            Supplier instance
        """
        pass

    @abstractmethod
    def update_supplier(
        self,
        supplier_id: str,
        **update_data
    ) -> Supplier:
        """
        Update an existing supplier.

        Args:
            supplier_id: Unique identifier of the supplier
            update_data: Dictionary of fields to update

        Returns:
            Updated Supplier instance
        """
        pass

    @abstractmethod
    def delete_supplier(self, supplier_id: str) -> bool:
        """
        Delete a supplier.

        Args:
            supplier_id: Unique identifier of the supplier

        Returns:
            Boolean indicating successful deletion
        """
        pass

    @abstractmethod
    def get_suppliers_by_status(
        self,
        status: Optional[SupplierStatus] = None
    ) -> List[Supplier]:
        """
        Retrieve suppliers filtered by status.

        Args:
            status: Optional supplier status to filter suppliers

        Returns:
            List of Supplier instances
        """
        pass

    @abstractmethod
    def create_purchase_order(
        self,
        supplier_id: str,
        total_amount: float,
        **kwargs
    ) -> Purchase:
        """
        Create a purchase order for a specific supplier.

        Args:
            supplier_id: Unique identifier of the supplier
            total_amount: Total amount of the purchase
            **kwargs: Additional purchase order attributes

        Returns:
            Created Purchase instance
        """
        pass

    @abstractmethod
    def get_supplier_purchase_history(
        self,
        supplier_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Purchase]:
        """
        Retrieve purchase history for a specific supplier.

        Args:
            supplier_id: Unique identifier of the supplier
            start_date: Optional start date for filtering purchases
            end_date: Optional end date for filtering purchases

        Returns:
            List of Purchase instances
        """
        pass