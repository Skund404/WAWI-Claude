# path: services/interfaces/inventory_service.py
"""
Inventory service interface definitions for the leatherworking store management application.

This module defines the interface for inventory-related services,
which provide functionality related to managing inventory of leather,
hardware, and other materials used in leatherworking projects.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from utils.circular_import_resolver import lazy_import
from typing import Any, Callable, Dict, List, Optional

# Lazy import to avoid circular dependency
MaterialType = lazy_import("services.interfaces.material_service", "MaterialType")


class IInventoryService(ABC):
    """
    Interface for inventory service.

    This interface defines the contract for services that manage inventory
    in the leatherworking store management system.
    """

    @abstractmethod
    def update_part_stock(self, part_id: int, quantity_change: int,
                          transaction_type: str, notes: Optional[str] = None) -> bool:
        """
        Update the stock quantity of a part.

        Args:
            part_id: ID of the part
            quantity_change: Amount to change the quantity by (positive or negative)
            transaction_type: Type of transaction (e.g., 'purchase', 'usage')
            notes: Optional notes about the transaction

        Returns:
            True if the update was successful, False otherwise
        """
        pass

    @abstractmethod
    def update_leather_area(self, leather_id: int, area_change: float,
                            transaction_type: str, notes: Optional[str] = None,
                            wastage: float = 0.0) -> bool:
        """
        Update the available area of a leather.

        Args:
            leather_id: ID of the leather
            area_change: Amount to change the area by (positive or negative)
            transaction_type: Type of transaction (e.g., 'purchase', 'usage')
            notes: Optional notes about the transaction
            wastage: Amount of leather wasted during cutting

        Returns:
            True if the update was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_low_stock_parts(self, include_out_of_stock: bool = True) -> List[Dict[str, Any]]:
        """
        Get parts with low stock levels.

        Args:
            include_out_of_stock: Whether to include parts with zero stock

        Returns:
            List of dictionaries representing parts with low stock
        """
        pass

    @abstractmethod
    def get_low_stock_leather(self, include_out_of_stock: bool = True) -> List[Dict[str, Any]]:
        """
        Get leather with low stock levels.

        Args:
            include_out_of_stock: Whether to include leather with zero area

        Returns:
            List of dictionaries representing leather with low stock
        """
        pass

    @abstractmethod
    def check_material_availability(self, material_id: int, quantity_needed: float) -> bool:
        """
        Check if a material is available in sufficient quantity.

        Args:
            material_id: ID of the material
            quantity_needed: Quantity needed

        Returns:
            True if the material is available in sufficient quantity, False otherwise
        """
        pass

    @abstractmethod
    def reserve_materials(self, project_id: int, materials: List[Dict[str, Any]]) -> bool:
        """
        Reserve materials for a project.

        Args:
            project_id: ID of the project
            materials: List of dictionaries with material IDs and quantities

        Returns:
            True if all materials were reserved, False otherwise
        """
        pass

    @abstractmethod
    def release_reserved_materials(self, project_id: int) -> bool:
        """
        Release reserved materials for a project.

        Args:
            project_id: ID of the project

        Returns:
            True if all materials were released, False otherwise
        """
        pass

    @abstractmethod
    def get_inventory_value(self) -> Dict[str, float]:
        """
        Get the total value of inventory by category.

        Returns:
            Dictionary mapping inventory categories to their values
        """
        pass

    @abstractmethod
    def generate_inventory_report(self, include_details: bool = False) -> Dict[str, Any]:
        """
        Generate a comprehensive inventory report.

        Args:
            include_details: Whether to include detailed item information

        Returns:
            Dictionary containing inventory statistics and optionally item details
        """
        pass


# Class type alias for backward compatibility
InventoryService = IInventoryService