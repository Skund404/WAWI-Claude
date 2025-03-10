# services/interfaces/material_service.py
# Protocol definition for material service

from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IMaterialService(Protocol):
    """Interface for material-related operations."""

    def get_by_id(self, material_id: int) -> Dict[str, Any]:
        """Get material by ID.

        Args:
            material_id: ID of the material to retrieve

        Returns:
            Dict representing the material

        Raises:
            NotFoundError: If material not found
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all materials, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing materials
        """
        ...

    def create(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material.

        Args:
            material_data: Dict containing material properties

        Returns:
            Dict representing the created material

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update(self, material_id: int, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing material.

        Args:
            material_id: ID of the material to update
            material_data: Dict containing updated material properties

        Returns:
            Dict representing the updated material

        Raises:
            NotFoundError: If material not found
            ValidationError: If validation fails
        """
        ...

    def delete(self, material_id: int) -> bool:
        """Delete a material by ID.

        Args:
            material_id: ID of the material to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If material not found
        """
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for materials by name or other properties.

        Args:
            query: Search query string

        Returns:
            List of materials matching the search query
        """
        ...

    def get_inventory_status(self, material_id: int) -> Dict[str, Any]:
        """Get inventory status for a material.

        Args:
            material_id: ID of the material

        Returns:
            Dict with inventory status information

        Raises:
            NotFoundError: If material not found
        """
        ...

    def adjust_inventory(self, material_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a material.

        Args:
            material_id: ID of the material
            quantity: Quantity to adjust (positive for increase, negative for decrease)
            reason: Reason for adjustment

        Returns:
            Dict representing the inventory status

        Raises:
            NotFoundError: If material not found
            ValidationError: If validation fails
        """
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get materials by supplier ID.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of materials from the specified supplier
        """
        ...

    def get_low_stock(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get materials with low stock levels.

        Args:
            threshold: Optional threshold for what's considered "low stock"

        Returns:
            List of materials with low stock
        """
        ...

    def get_materials_by_type(self, material_type: str) -> List[Dict[str, Any]]:
        """Get materials by type.

        Args:
            material_type: Type of materials to retrieve

        Returns:
            List of materials of the specified type
        """
        ...