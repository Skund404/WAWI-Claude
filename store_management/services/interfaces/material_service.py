# Path: services/interfaces/material_service.py
"""
Defines the interface for material management services in the leatherworking system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum


class MaterialType(Enum):
    """Enum defining different types of materials in the leatherworking system."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    ADHESIVE = "adhesive"
    TOOL = "tool"


class IMaterialService(ABC):
    """
    Abstract base class defining the contract for material management services.

    This interface ensures consistent material management operations across
    different implementation strategies.
    """

    @abstractmethod
    def create_material(self, material_data: Dict[str, Any]) -> Any:
        """
        Create a new material entry.

        Args:
            material_data (Dict[str, Any]): Detailed information about the material

        Returns:
            Material object representing the created material

        Raises:
            ValueError: If material data is invalid
        """
        pass

    @abstractmethod
    def get_material(self, material_id: int) -> Any:
        """
        Retrieve a specific material by its ID.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            Material object

        Raises:
            NotFoundError: If material doesn't exist
        """
        pass

    @abstractmethod
    def update_material(self, material_id: int, material_data: Dict[str, Any]) -> Any:
        """
        Update an existing material's details.

        Args:
            material_id (int): Unique identifier for the material
            material_data (Dict[str, Any]): Updated material information

        Returns:
            Updated Material object

        Raises:
            ValueError: If update data is invalid
            NotFoundError: If material doesn't exist
        """
        pass

    @abstractmethod
    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material from the system.

        Args:
            material_id (int): Unique identifier for the material to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If material doesn't exist
        """
        pass

    @abstractmethod
    def get_low_stock_materials(self, include_zero_stock: bool = False) -> List[Any]:
        """
        Retrieve materials with low stock levels.

        Args:
            include_zero_stock (bool, optional): Whether to include materials
            with zero stock. Defaults to False.

        Returns:
            List of materials with low stock
        """
        pass

    @abstractmethod
    def track_material_usage(self, material_id: int, quantity_used: float) -> Dict[str, Any]:
        """
        Track the usage of a specific material.

        Args:
            material_id (int): Unique identifier for the material
            quantity_used (float): Amount of material used

        Returns:
            Dict with material usage tracking details
        """
        pass

    @abstractmethod
    def search_materials(self, search_params: Dict[str, Any]) -> List[Any]:
        """
        Search for materials based on various parameters.

        Args:
            search_params (Dict[str, Any]): Search criteria
            (e.g., type, supplier, quality)

        Returns:
            List of Material objects matching the search criteria
        """
        pass

    @abstractmethod
    def generate_sustainability_report(self) -> List[Dict[str, Any]]:
        """
        Generate a sustainability report for materials.

        Returns:
            List of dictionaries with material sustainability metrics
        """
        pass

    @abstractmethod
    def calculate_material_efficiency(self, material_id: int, period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate efficiency metrics for a specific material.

        Args:
            material_id (int): Unique identifier for the material
            period_days (int, optional): Number of days to analyze. Defaults to 30.

        Returns:
            Dict containing material efficiency metrics
        """
        pass