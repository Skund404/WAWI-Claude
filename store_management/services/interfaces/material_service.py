# services/interfaces/material_service.py
"""
Material service interface definitions.

This module defines the interface for material-related services,
which provide functionality related to managing materials in the system.
"""

import enum
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union


class MaterialType(enum.Enum):
    """Enumeration of material types."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    LINING = "lining"
    ADHESIVE = "adhesive"
    OTHER = "other"


class IMaterialService(ABC):
    """
    Interface for material service.

    This interface defines the contract for services that manage materials
    in the leatherworking store management system.
    """

    @abstractmethod
    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new material.

        Args:
            material_data: Dictionary containing material attributes

        Returns:
            Dictionary representing the created material

        Raises:
            ValidationError: If material data is invalid
        """
        pass

    @abstractmethod
    def get_material(self, material_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a material by ID.

        Args:
            material_id: ID of the material to retrieve

        Returns:
            Dictionary representing the material or None if not found

        Raises:
            NotFoundError: If material is not found
        """
        pass

    @abstractmethod
    def update_material(self, material_id: int, material_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a material.

        Args:
            material_id: ID of the material to update
            material_data: Dictionary containing updated attributes

        Returns:
            Dictionary representing the updated material or None if not found

        Raises:
            ValidationError: If update data is invalid
            NotFoundError: If material is not found
        """
        pass

    @abstractmethod
    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material.

        Args:
            material_id: ID of the material to delete

        Returns:
            True if the material was deleted, False otherwise

        Raises:
            NotFoundError: If material is not found
        """
        pass

    @abstractmethod
    def list_materials(
        self,
        material_type: Optional[MaterialType] = None,
        page: int = 1,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List materials with optional filtering and pagination.

        Args:
            material_type: Optional filter by material type
            page: Page number for pagination
            page_size: Number of items per page

        Returns:
            List of material dictionaries
        """
        pass

    @abstractmethod
    def get_low_stock_materials(self, include_zero_stock: bool = True) -> List[Dict[str, Any]]:
        """
        Get materials with low stock levels.

        Args:
            include_zero_stock: Whether to include materials with zero stock

        Returns:
            List of dictionaries representing materials with low stock
        """
        pass

    @abstractmethod
    def track_material_usage(self, material_id: int, quantity_used: float) -> bool:
        """
        Track usage of a material.

        Args:
            material_id: ID of the material used
            quantity_used: Quantity of material used

        Returns:
            True if the usage was tracked successfully, False otherwise

        Raises:
            NotFoundError: If material is not found
            ValidationError: If usage tracking fails
        """
        pass

    @abstractmethod
    def search_materials(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for materials based on parameters.

        Args:
            search_params: Dictionary of search parameters

        Returns:
            List of dictionaries representing matching materials
        """
        pass

    @abstractmethod
    def generate_sustainability_report(self) -> Dict[str, Any]:
        """
        Generate a sustainability report for materials.

        Returns:
            Dictionary containing sustainability metrics
        """
        pass

    @abstractmethod
    def calculate_material_efficiency(self, material_id: int, period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate efficiency metrics for a material.

        Args:
            material_id: ID of the material
            period_days: Number of days to include in the calculation

        Returns:
            Dictionary containing efficiency metrics

        Raises:
            NotFoundError: If material is not found
        """
        pass


# Class type alias for backward compatibility
MaterialService = IMaterialService