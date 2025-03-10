# services/interfaces/supplier_service.py
from typing import Any, Dict, List, Optional, Protocol


class ISupplierService(Protocol):
    """Protocol defining the supplier service interface."""

    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """Get all suppliers.

        Returns:
            List[Dict[str, Any]]: List of supplier dictionaries
        """
        ...

    def get_supplier_by_id(self, supplier_id: int) -> Dict[str, Any]:
        """Get supplier by ID.

        Args:
            supplier_id: ID of the supplier

        Returns:
            Dict[str, Any]: Supplier dictionary

        Raises:
            NotFoundError: If supplier not found
        """
        ...

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier.

        Args:
            supplier_data: Supplier data dictionary

        Returns:
            Dict[str, Any]: Created supplier dictionary

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier.

        Args:
            supplier_id: ID of the supplier to update
            supplier_data: Updated supplier data

        Returns:
            Dict[str, Any]: Updated supplier dictionary

        Raises:
            NotFoundError: If supplier not found
            ValidationError: If validation fails
        """
        ...

    def delete_supplier(self, supplier_id: int) -> bool:
        """Delete a supplier.

        Args:
            supplier_id: ID of the supplier to delete

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If supplier not found
        """
        ...

    def get_supplier_materials(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get materials supplied by a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List[Dict[str, Any]]: List of material dictionaries

        Raises:
            NotFoundError: If supplier not found
        """
        ...

    def get_supplier_purchase_history(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get purchase history for a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List[Dict[str, Any]]: List of purchase dictionaries

        Raises:
            NotFoundError: If supplier not found
        """
        ...

    def search_suppliers(self, query: str) -> List[Dict[str, Any]]:
        """Search for suppliers by name or contact information.

        Args:
            query: Search query string

        Returns:
            List[Dict[str, Any]]: List of matching supplier dictionaries
        """
        ...

    def update_supplier_status(self, supplier_id: int, status: str) -> Dict[str, Any]:
        """Update the status of a supplier.

        Args:
            supplier_id: ID of the supplier
            status: New status value

        Returns:
            Dict[str, Any]: Updated supplier dictionary

        Raises:
            NotFoundError: If supplier not found
            ValidationError: If validation fails
        """
        ...