# services/interfaces/supplier_service.py
"""
Interface for Supplier Service defining contract for supplier-related operations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

class SupplierStatus(Enum):
    """
    Enumeration of possible supplier statuses.
    """
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    BLACKLISTED = 'blacklisted'

class ISupplierService(ABC):
    """
    Abstract base class defining the contract for Supplier Service operations.
    """

    @abstractmethod
    def get_all_suppliers(self, status: Optional[SupplierStatus] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all suppliers, optionally filtered by status.

        Args:
            status (Optional[SupplierStatus]): Optional status to filter suppliers

        Returns:
            List of supplier dictionaries
        """
        pass

    @abstractmethod
    def get_supplier_by_id(self, supplier_id: int) -> Dict[str, Any]:
        """
        Retrieve a supplier by their unique identifier.

        Args:
            supplier_id (int): Unique identifier of the supplier

        Returns:
            Supplier details dictionary

        Raises:
            NotFoundError: If supplier is not found
        """
        pass

    @abstractmethod
    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new supplier.

        Args:
            supplier_data (Dict[str, Any]): Supplier details dictionary

        Returns:
            Created supplier details

        Raises:
            ValidationError: If supplier data is invalid
        """
        pass

    @abstractmethod
    def update_supplier(self, supplier_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing supplier.

        Args:
            supplier_id (int): ID of the supplier to update
            update_data (Dict[str, Any]): Updated supplier details

        Returns:
            Updated supplier details

        Raises:
            NotFoundError: If supplier is not found
            ValidationError: If update data is invalid
        """
        pass

    @abstractmethod
    def delete_supplier(self, supplier_id: int) -> bool:
        """
        Delete a supplier.

        Args:
            supplier_id (int): ID of the supplier to delete

        Returns:
            Boolean indicating successful deletion

        Raises:
            NotFoundError: If supplier is not found
        """
        pass

    @abstractmethod
    def search_suppliers(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for suppliers by various fields.

        Args:
            search_term (str): Term to search for

        Returns:
            List of matching suppliers
        """
        pass

    @abstractmethod
    def get_suppliers_by_status(self, status: SupplierStatus) -> List[Dict[str, Any]]:
        """
        Get suppliers by their status.

        Args:
            status (SupplierStatus): Status to filter suppliers

        Returns:
            List of suppliers with the given status
        """
        pass