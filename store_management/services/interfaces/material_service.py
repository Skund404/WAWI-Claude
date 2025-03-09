# services/interfaces/material_service.py
"""
Interface for material-related services.
Defines methods for material management including materials, leather, hardware, and supplies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from database.models.enums import (
    InventoryStatus, MaterialType, LeatherType, HardwareType,
    TransactionType, QualityGrade
)
from database.models.material import Material, Leather, Hardware


class IMaterialService(ABC):
    """
    Interface for material-related services.

    Defines methods for managing materials in the leatherworking application.
    """

    @abstractmethod
    def get_all_materials(self,
                          include_deleted: bool = False,
                          status: Optional[InventoryStatus] = None,
                          material_type: Optional[MaterialType] = None) -> List[Material]:
        """
        Get all materials with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted materials
            status: Filter by inventory status
            material_type: Filter by material type

        Returns:
            List of material objects
        """
        pass

    @abstractmethod
    def get_material_by_id(self, material_id: int) -> Optional[Material]:
        """
        Get material by ID.

        Args:
            material_id: ID of the material

        Returns:
            Material object or None if not found
        """
        pass

    @abstractmethod
    def create_material(self, material_data: Dict[str, Any]) -> Material:
        """
        Create a new material.

        Args:
            material_data: Material data dictionary

        Returns:
            Created material object
        """
        pass

    @abstractmethod
    def update_material(self, material_id: int, update_data: Dict[str, Any]) -> Material:
        """
        Update existing material.

        Args:
            material_id: ID of the material
            update_data: Updated material data

        Returns:
            Updated material object
        """
        pass

    @abstractmethod
    def delete_material(self, material_id: int) -> bool:
        """
        Soft delete a material.

        Args:
            material_id: ID of the material

        Returns:
            Success status
        """
        pass

    @abstractmethod
    def search_materials(self, search_term: str) -> List[Material]:
        """
        Search for materials matching a search term.

        Args:
            search_term: Text to search for

        Returns:
            List of matching materials
        """
        pass

    @abstractmethod
    def update_inventory_quantity(self,
                                  material_id: int,
                                  quantity_change: float,
                                  transaction_type: TransactionType,
                                  notes: Optional[str] = None) -> bool:
        """
        Update material inventory quantity.

        Args:
            material_id: ID of the material
            quantity_change: Amount to adjust (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Returns:
            Success status
        """
        pass

    # Leather-specific methods
    @abstractmethod
    def get_all_leathers(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         leather_type: Optional[LeatherType] = None,
                         quality: Optional[QualityGrade] = None) -> List[Leather]:
        """
        Get all leather materials with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted leathers
            status: Filter by inventory status
            leather_type: Filter by leather type
            quality: Filter by quality grade

        Returns:
            List of leather objects
        """
        pass

    @abstractmethod
    def get_leather_by_id(self, leather_id: int) -> Optional[Leather]:
        """
        Get leather by ID.

        Args:
            leather_id: ID of the leather

        Returns:
            Leather object or None if not found
        """
        pass

    # Hardware-specific methods
    @abstractmethod
    def get_all_hardware(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         hardware_type: Optional[HardwareType] = None) -> List[Hardware]:
        """
        Get all hardware materials with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted hardware
            status: Filter by inventory status
            hardware_type: Filter by hardware type

        Returns:
            List of hardware objects
        """
        pass

    @abstractmethod
    def get_hardware_by_id(self, hardware_id: int) -> Optional[Hardware]:
        """
        Get hardware by ID.

        Args:
            hardware_id: ID of the hardware

        Returns:
            Hardware object or None if not found
        """
        pass

    # Supplies-specific methods
    @abstractmethod
    def get_all_supplies(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         material_type: Optional[MaterialType] = None) -> List[Material]:
        """
        Get all supply materials with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted supplies
            status: Filter by inventory status
            material_type: Filter by specific material type

        Returns:
            List of supply objects
        """
        pass

    @abstractmethod
    def get_supply_by_id(self, supply_id: int) -> Optional[Material]:
        """
        Get supply by ID.

        Args:
            supply_id: ID of the supply

        Returns:
            Supply object or None if not found
        """
        pass

    @abstractmethod
    def get_supplies_by_type(self, material_type: MaterialType) -> List[Material]:
        """
        Get supplies by material type.

        Args:
            material_type: Type of material to filter by

        Returns:
            List of supply objects matching the type
        """
        pass

    # Inventory statistics methods
    @abstractmethod
    def get_low_stock_materials(self) -> Dict[str, List[Material]]:
        """
        Get all materials with low stock, grouped by category.

        Returns:
            Dictionary of low stock materials by category
            (leather, hardware, supplies)
        """
        pass

    @abstractmethod
    def get_out_of_stock_materials(self) -> Dict[str, List[Material]]:
        """
        Get all materials that are out of stock, grouped by category.

        Returns:
            Dictionary of out of stock materials by category
            (leather, hardware, supplies)
        """
        pass

    @abstractmethod
    def get_inventory_value_report(self) -> Dict[str, Any]:
        """
        Get comprehensive inventory value report.

        Returns:
            Dictionary with inventory value statistics
        """
        pass

    @abstractmethod
    def get_materials_by_supplier(self, supplier_id: int) -> Dict[str, List[Material]]:
        """
        Get all materials from a specific supplier, grouped by category.

        Args:
            supplier_id: ID of the supplier

        Returns:
            Dictionary of materials by category
            (leather, hardware, supplies)
        """
        pass