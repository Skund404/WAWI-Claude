"""
Interface for the Material Service.

This module defines the interface for the Material Service,
which is responsible for managing materials used in leatherworking projects.
"""

from abc import ABC, abstractmethod
import enum
from typing import Any, Dict, List, Optional, Union
from .base_service import IBaseService


class MaterialType(enum.Enum):
    """Types of materials used in leatherworking."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    LINING = "lining"
    ADHESIVE = "adhesive"
    OTHER = "other"


class IMaterialService(IBaseService):
    """Interface for the Material Service."""

    @abstractmethod
    def get_all_materials(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """Get material by ID.

        Args:
            material_id: ID of the material to retrieve

        Returns:
            Optional[Dict[str, Any]]: Material data if found, None otherwise
        """
        pass

    @abstractmethod
    def get_materials(self,
                      material_type: Optional[MaterialType] = None,
                      limit: int = 100,
                      offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a list of materials, optionally filtered by type.

        Args:
            material_type: Optional filter by material type
            limit: Maximum number of records to return
            offset: Number of records to skip for pagination

        Returns:
            List of dictionaries containing material details
        """
        pass

    @abstractmethod
    def search_materials(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for materials.

        Args:
            search_term: Term to search for

        Returns:
            List[Dict[str, Any]]: List of matching materials
        """
        pass

    @abstractmethod
    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material.

        Args:
            material_data: Data for the new material

        Returns:
            Dict[str, Any]: Created material data
        """
        pass

    @abstractmethod
    def update_material(self, material_id: int, material_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing material.

        Args:
            material_id: ID of the material to update
            material_data: New material data

        Returns:
            Optional[Dict[str, Any]]: Updated material data if successful, None otherwise
        """
        pass

    @abstractmethod
    def delete_material(self, material_id: int) -> bool:
        """Delete a material.

        Args:
            material_id: ID of the material to delete

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_material_types(self) -> List[Dict[str, Any]]:
        """
        Get a list of all material types.

        Returns:
            List of dictionaries containing material type details
        """
        pass

    @abstractmethod
    def record_material_transaction(self,
                                    material_id: int,
                                    quantity: float,
                                    transaction_type: str,
                                    notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a material transaction (purchase, usage, etc.).

        Args:
            material_id: Unique identifier of the material
            quantity: Quantity of material in the transaction (positive for additions, negative for removals)
            transaction_type: Type of transaction (purchase, usage, adjustment, etc.)
            notes: Optional notes about the transaction

        Returns:
            Dictionary containing the transaction details

        Raises:
            NotFoundError: If material with given ID doesn't exist
            ValidationError: If transaction data is invalid
        """
        pass

    @abstractmethod
    def get_material_transactions(self,
                                  material_id: int,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of transactions for a specific material.

        Args:
            material_id: Unique identifier of the material
            start_date: Optional start date for filtering transactions
            end_date: Optional end date for filtering transactions

        Returns:
            List of dictionaries containing transaction details

        Raises:
            NotFoundError: If material with given ID doesn't exist
        """
        pass

    @abstractmethod
    def calculate_material_cost(self,
                                material_id: int,
                                quantity: float) -> float:
        """
        Calculate the cost of a specified quantity of material.

        Args:
            material_id: Unique identifier of the material
            quantity: Quantity of material to calculate cost for

        Returns:
            Calculated cost

        Raises:
            NotFoundError: If material with given ID doesn't exist
        """
        pass