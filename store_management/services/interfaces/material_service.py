# services/interfaces/material_service.py
"""
Interface definition for the material service. This service is responsible
for managing all aspects of materials in the leatherworking store.
"""

from abc import ABC, abstractmethod
import enum
from typing import Any, Dict, List, Optional, Union


class MaterialType(enum.Enum):
    """Enumeration of material types used in leatherworking."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    LINING = "lining"
    ADHESIVE = "adhesive"
    OTHER = "other"


class IMaterialService(ABC):
    """Interface for material service operations."""

    @abstractmethod
    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new material.

        Args:
            material_data: Dictionary with material properties

        Returns:
            Dictionary representing the created material

        Raises:
            ValidationError: If material data is invalid
        """
        pass

    @abstractmethod
    def get_material(self, material_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieve a material by ID.

        Args:
            material_id: ID of the material to retrieve

        Returns:
            Dictionary representing the material

        Raises:
            NotFoundError: If material is not found
        """
        pass

    @abstractmethod
    def update_material(self, material_id: Union[int, str], material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing material.

        Args:
            material_id: ID of the material to update
            material_data: Dictionary with updated material properties

        Returns:
            Dictionary representing the updated material

        Raises:
            NotFoundError: If material is not found
            ValidationError: If material data is invalid
        """
        pass

    @abstractmethod
    def delete_material(self, material_id: Union[int, str]) -> bool:
        """
        Delete a material.

        Args:
            material_id: ID of the material to delete

        Returns:
            True if deletion was successful

        Raises:
            NotFoundError: If material is not found
        """
        pass

    @abstractmethod
    def list_materials(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """
        List all materials, optionally filtered by type.

        Args:
            material_type: Optional filter for material type

        Returns:
            List of dictionaries representing materials
        """
        pass

    @abstractmethod
    def search_materials(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for materials by name or description.

        Args:
            query: Search query string

        Returns:
            List of dictionaries representing matching materials
        """
        pass

    @abstractmethod
    def get_material_inventory(self, material_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get inventory information for a material.

        Args:
            material_id: ID of the material

        Returns:
            Dictionary with inventory information

        Raises:
            NotFoundError: If material is not found
        """
        pass

    @abstractmethod
    def update_material_inventory(self,
                                  material_id: Union[int, str],
                                  quantity_change: float,
                                  notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Update inventory quantities for a material.

        Args:
            material_id: ID of the material
            quantity_change: Amount to add (positive) or remove (negative)
            notes: Optional notes about the inventory change

        Returns:
            Dictionary with updated inventory information

        Raises:
            NotFoundError: If material is not found
            ValidationError: If quantity change is invalid
        """
        pass

    @abstractmethod
    def get_low_stock_materials(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get a list of materials with low stock levels.

        Args:
            threshold: Optional custom threshold for low stock

        Returns:
            List of dictionaries representing low stock materials
        """
        pass