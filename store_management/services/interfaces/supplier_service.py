# services/interfaces/supplier_service.py
"""
Interface for Supplier Service in the leatherworking application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from database.models.enums import SupplierStatus
from database.models.supplier import Supplier


class ISupplierService(ABC):
    """
    Abstract base class defining the interface for Supplier Service.
    Handles operations related to suppliers in the leatherworking business.
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
            name (str): Name of the supplier
            contact_email (str): Contact email of the supplier
            status (SupplierStatus): Initial status of the supplier
            **kwargs: Additional attributes for the supplier

        Returns:
            Supplier: The created supplier
        """
        pass

    @abstractmethod
    def get_supplier_by_id(self, supplier_id: int) -> Supplier:
        """
        Retrieve a supplier by their ID.

        Args:
            supplier_id (int): ID of the supplier

        Returns:
            Supplier: The retrieved supplier
        """
        pass

    @abstractmethod
    def get_suppliers_by_status(self, status: SupplierStatus) -> List[Supplier]:
        """
        Retrieve suppliers by their status.

        Args:
            status (SupplierStatus): Status to filter suppliers

        Returns:
            List[Supplier]: List of suppliers matching the status
        """
        pass

    @abstractmethod
    def update_supplier(
        self,
        supplier_id: int,
        name: Optional[str] = None,
        contact_email: Optional[str] = None,
        status: Optional[SupplierStatus] = None,
        **kwargs
    ) -> Supplier:
        """
        Update supplier information.

        Args:
            supplier_id (int): ID of the supplier to update
            name (Optional[str]): New name of the supplier
            contact_email (Optional[str]): New contact email
            status (Optional[SupplierStatus]): New status of the supplier
            **kwargs: Additional attributes to update

        Returns:
            Supplier: The updated supplier
        """
        pass

    @abstractmethod
    def update_supplier_status(
        self,
        supplier_id: int,
        status: SupplierStatus
    ) -> Supplier:
        """
        Update the status of a supplier.

        Args:
            supplier_id (int): ID of the supplier
            status (SupplierStatus): New status for the supplier

        Returns:
            Supplier: The updated supplier
        """
        pass

    @abstractmethod
    def get_supplier_materials(self, supplier_id: int) -> List[Any]:
        """
        Retrieve materials supplied by a specific supplier.

        Args:
            supplier_id (int): ID of the supplier

        Returns:
            List[Any]: List of materials supplied by the supplier
        """
        pass

    @abstractmethod
    def get_supplier_leather(self, supplier_id: int) -> List[Any]:
        """
        Retrieve leather supplied by a specific supplier.

        Args:
            supplier_id (int): ID of the supplier

        Returns:
            List[Any]: List of leather supplied by the supplier
        """
        pass

    @abstractmethod
    def get_supplier_hardware(self, supplier_id: int) -> List[Any]:
        """
        Retrieve hardware supplied by a specific supplier.

        Args:
            supplier_id (int): ID of the supplier

        Returns:
            List[Any]: List of hardware supplied by the supplier
        """
        pass

    @abstractmethod
    def get_supplier_tools(self, supplier_id: int) -> List[Any]:
        """
        Retrieve tools supplied by a specific supplier.

        Args:
            supplier_id (int): ID of the supplier

        Returns:
            List[Any]: List of tools supplied by the supplier
        """
        pass

    @abstractmethod
    def get_supplier_purchases(self, supplier_id: int) -> List[Any]:
        """
        Retrieve purchase orders from a specific supplier.

        Args:
            supplier_id (int): ID of the supplier

        Returns:
            List[Any]: List of purchase orders from the supplier
        """
        pass

    @abstractmethod
    def delete_supplier(self, supplier_id: int) -> bool:
        """
        Delete a supplier from the system.

        Args:
            supplier_id (int): ID of the supplier to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass