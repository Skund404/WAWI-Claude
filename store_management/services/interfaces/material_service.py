# database/services/interfaces/material_service.py
"""
Interface definition for Material Service.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any

from database.models.enums import (
    MaterialType,
    MaterialQualityGrade,
    InventoryStatus,
    TransactionType
)
from database.models.material import Material
from database.models.material_inventory import MaterialInventory
from database.models.transaction import MaterialTransaction


class IMaterialService(ABC):
    """
    Interface defining contract for Material Service operations.
    """

    @abstractmethod
    def create_material(
        self,
        name: str,
        material_type: MaterialType,
        quality_grade: MaterialQualityGrade,
        supplier_id: Optional[str] = None,
        **kwargs
    ) -> Material:
        """
        Create a new material.

        Args:
            name: Material name
            material_type: Type of material
            quality_grade: Quality grade of the material
            supplier_id: Optional supplier identifier
            **kwargs: Additional material attributes

        Returns:
            Created Material instance
        """
        pass

    @abstractmethod
    def get_material_by_id(self, material_id: str) -> Material:
        """
        Retrieve a material by its ID.

        Args:
            material_id: Unique identifier of the material

        Returns:
            Material instance
        """
        pass

    @abstractmethod
    def update_material(
        self,
        material_id: str,
        **update_data
    ) -> Material:
        """
        Update an existing material.

        Args:
            material_id: Unique identifier of the material
            update_data: Dictionary of fields to update

        Returns:
            Updated Material instance
        """
        pass

    @abstractmethod
    def delete_material(self, material_id: str) -> bool:
        """
        Delete a material.

        Args:
            material_id: Unique identifier of the material

        Returns:
            Boolean indicating successful deletion
        """
        pass

    @abstractmethod
    def get_materials_by_type(
        self,
        material_type: Optional[MaterialType] = None,
        quality_grade: Optional[MaterialQualityGrade] = None
    ) -> List[Material]:
        """
        Retrieve materials filtered by type and quality grade.

        Args:
            material_type: Optional material type to filter materials
            quality_grade: Optional quality grade to filter materials

        Returns:
            List of Material instances
        """
        pass

    @abstractmethod
    def add_material_inventory(
        self,
        material_id: str,
        quantity: float,
        storage_location: Optional[str] = None,
        inventory_status: InventoryStatus = InventoryStatus.IN_STOCK
    ) -> MaterialInventory:
        """
        Add inventory for a specific material.

        Args:
            material_id: Unique identifier of the material
            quantity: Quantity to add to inventory
            storage_location: Optional storage location
            inventory_status: Inventory status (default: IN_STOCK)

        Returns:
            MaterialInventory instance
        """
        pass

    @abstractmethod
    def record_material_transaction(
        self,
        material_id: str,
        quantity: float,
        transaction_type: TransactionType,
        description: Optional[str] = None,
        related_entity_id: Optional[str] = None
    ) -> MaterialTransaction:
        """
        Record a transaction for a material.

        Args:
            material_id: Unique identifier of the material
            quantity: Transaction quantity
            transaction_type: Type of transaction
            description: Optional transaction description
            related_entity_id: Optional ID of related entity (e.g., purchase, project)

        Returns:
            MaterialTransaction instance
        """
        pass