# Path: store_management/services/interfaces/supplier_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from services.interfaces.base_service import IBaseService


class ISupplierService(IBaseService):
    """
    Abstract base class defining the interface for supplier-related operations.

    This interface provides a contract for supplier management services,
    ensuring consistent method signatures across different implementations.
    """

    @abstractmethod
    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """
        Retrieve all suppliers.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing supplier information.
        """
        pass

    @abstractmethod
    def get_supplier_by_id(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a supplier by their ID.

        Args:
            supplier_id (int): The unique identifier of the supplier.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing supplier information if found, None otherwise.
        """
        pass

    @abstractmethod
    def create_supplier(self, supplier_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new supplier.

        Args:
            supplier_data (Dict[str, Any]): A dictionary containing the new supplier's information.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the created supplier's information.
        """
        pass

    @abstractmethod
    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing supplier's information.

        Args:
            supplier_id (int): The unique identifier of the supplier to update.
            supplier_data (Dict[str, Any]): A dictionary containing the updated supplier information.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the updated supplier information if successful, None otherwise.
        """
        pass

    @abstractmethod
    def delete_supplier(self, supplier_id: int) -> bool:
        """
        Delete a supplier by their ID.

        Args:
            supplier_id (int): The unique identifier of the supplier to delete.

        Returns:
            bool: True if the supplier was successfully deleted, False otherwise.
        """
        pass