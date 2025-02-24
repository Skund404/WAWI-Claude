# Path: store_management/services/interfaces/supplier_service.py
"""
Interface definition for Supplier Service.

Defines the contract for supplier-related operations
and management in the application.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime


class ISupplierService(ABC):
    """
    Abstract base class defining the contract for supplier services.

    Provides a standardized interface for supplier-related operations,
    ensuring consistent implementation across different service layers.
    """

    @abstractmethod
    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """
        Retrieve all suppliers in the system.

        Returns:
            List[Dict[str, Any]]: List of supplier dictionaries.
        """
        pass

    @abstractmethod
    def get_supplier_by_id(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific supplier by their unique identifier.

        Args:
            supplier_id (int): Unique identifier for the supplier.

        Returns:
            Optional[Dict[str, Any]]: Supplier details, or None if not found.
        """
        pass

    @abstractmethod
    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new supplier in the system.

        Args:
            supplier_data (Dict[str, Any]): Details of the supplier to create.

        Returns:
            Dict[str, Any]: Created supplier details.

        Raises:
            ValueError: If supplier data is invalid.
        """
        pass

    @abstractmethod
    def update_supplier(self,
                        supplier_id: int,
                        update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing supplier's information.

        Args:
            supplier_id (int): Unique identifier of the supplier to update.
            update_data (Dict[str, Any]): Updated supplier information.

        Returns:
            Dict[str, Any]: Updated supplier details.

        Raises:
            ValueError: If update data is invalid.
            KeyError: If supplier is not found.
        """
        pass

    @abstractmethod
    def delete_supplier(self, supplier_id: int) -> bool:
        """
        Delete a supplier from the system.

        Args:
            supplier_id (int): Unique identifier of the supplier to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.

        Raises:
            KeyError: If supplier is not found.
        """
        pass

    @abstractmethod
    def get_supplier_performance(self,
                                 supplier_id: int,
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """
        Retrieve performance metrics for a specific supplier.

        Args:
            supplier_id (int): Unique identifier of the supplier.
            start_date (datetime, optional): Start of performance period.
            end_date (datetime, optional): End of performance period.

        Returns:
            Dict[str, Any]: Supplier performance metrics.
        """
        pass

    @abstractmethod
    def search_suppliers(self,
                         search_term: str,
                         search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for suppliers based on a search term.

        Args:
            search_term (str): Term to search for.
            search_fields (List[str], optional): Fields to search within.

        Returns:
            List[Dict[str, Any]]: List of matching suppliers.
        """
        pass

    @abstractmethod
    def generate_supplier_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of all suppliers.

        Returns:
            Dict[str, Any]: Detailed supplier report.
        """
        pass