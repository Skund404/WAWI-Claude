# store_management/services/interfaces/supplier_service.py
"""
Interface for Supplier Service in Leatherworking Store Management.

Defines the contract for supplier-related operations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from di.core import inject
from utils.circular_import_resolver import CircularImportResolver

class SupplierStatus(Enum):
    """
    Enumeration of possible supplier statuses.
    """
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"
    BLACKLISTED = "Blacklisted"

class ISupplierService(ABC):
    """
    Abstract base class defining the interface for supplier-related operations.
    """

    @abstractmethod
    @inject('IMaterialService')
    def create_supplier(
        self,
        name: str,
        contact_info: Dict[str, str],
        status: SupplierStatus = SupplierStatus.ACTIVE,
        description: Optional[str] = None,
        material_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new supplier.

        Args:
            name (str): Name of the supplier
            contact_info (Dict[str, str]): Contact information for the supplier
            status (SupplierStatus, optional): Current status of the supplier
            description (Optional[str], optional): Additional details about the supplier
            material_service (Optional[Any], optional): Material service for additional operations

        Returns:
            Dict[str, Any]: Details of the created supplier
        """
        pass

    @abstractmethod
    def update_supplier(
        self,
        supplier_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing supplier.

        Args:
            supplier_id (str): Unique identifier of the supplier
            updates (Dict[str, Any]): Dictionary of fields to update

        Returns:
            Dict[str, Any]: Updated supplier details
        """
        pass

    @abstractmethod
    def get_supplier(
        self,
        supplier_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific supplier by its ID.

        Args:
            supplier_id (str): Unique identifier of the supplier

        Returns:
            Optional[Dict[str, Any]]: Supplier details, or None if not found
        """
        pass

    @abstractmethod
    def list_suppliers(
        self,
        status: Optional[SupplierStatus] = None,
        rating_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        List suppliers with optional filtering.

        Args:
            status (Optional[SupplierStatus], optional): Filter by supplier status
            rating_threshold (Optional[float], optional): Minimum supplier rating

        Returns:
            List[Dict[str, Any]]: List of suppliers matching the criteria
        """
        pass

    @abstractmethod
    def delete_supplier(
        self,
        supplier_id: str
    ) -> bool:
        """
        Delete a supplier.

        Args:
            supplier_id (str): Unique identifier of the supplier to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    @inject('IMaterialService')
    def evaluate_supplier_performance(
        self,
        supplier_id: str,
        material_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a supplier's performance based on various metrics.

        Args:
            supplier_id (str): Unique identifier of the supplier
            material_service (Optional[Any], optional): Material service for performance evaluation

        Returns:
            Dict[str, Any]: Performance evaluation details
        """
        pass

    @abstractmethod
    def search_suppliers(
        self,
        query: Optional[str] = None,
        material_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for suppliers with optional filtering.

        Args:
            query (Optional[str], optional): Search term
            material_types (Optional[List[str]], optional): List of material types

        Returns:
            List[Dict[str, Any]]: List of suppliers matching the search criteria
        """
        pass