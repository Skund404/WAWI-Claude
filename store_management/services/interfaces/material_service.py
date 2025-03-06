# services/interfaces/material_service.py
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

class MaterialType(Enum):
    """Types of materials used in leatherworking."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    LINING = "lining"
    ADHESIVE = "adhesive"
    OTHER = "other"

class IMaterialService(ABC):
    """Interface for the Material Service."""

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        """
        Create a new material.

        Args:
            data (Dict[str, Any]): Material creation data

        Returns:
            Any: Created material identifier
        """
        pass

    @abstractmethod
    def get_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        Get material by ID.

        Args:
            material_id (str): Unique identifier of the material

        Returns:
            Optional[Dict[str, Any]]: Material details or None if not found
        """
        pass

    @abstractmethod
    def update(self, material_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing material.

        Args:
            material_id (str): Unique identifier of the material
            updates (Dict[str, Any]): Update data for the material

        Returns:
            Optional[Dict[str, Any]]: Updated material details or None if update failed
        """
        pass

    @abstractmethod
    def delete(self, material_id: str) -> bool:
        """
        Delete a material.

        Args:
            material_id (str): Unique identifier of the material to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_materials(
        self,
        material_type: Optional[MaterialType] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get materials with optional filtering.

        Args:
            material_type (Optional[MaterialType], optional): Filter by material type
            **kwargs: Additional filter parameters

        Returns:
            List[Dict[str, Any]]: List of materials matching the filter criteria
        """
        pass

    def search_materials(
        self,
        search_text: str,
        material_type: Optional[MaterialType] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search materials with optional filtering.

        Args:
            search_text (str): Text to search for
            material_type (Optional[MaterialType], optional): Filter by material type
            **kwargs: Additional filter parameters

        Returns:
            List[Dict[str, Any]]: List of materials matching the search and filter criteria
        """
        kwargs['search'] = search_text
        if material_type:
            kwargs['material_type'] = material_type
        return self.get_materials(**kwargs)

    @abstractmethod
    def record_material_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a material transaction.

        Args:
            transaction_data (Dict[str, Any]): Transaction details

        Returns:
            Dict[str, Any]: Recorded transaction details
        """
        pass

    @abstractmethod
    def get_material_transactions(
        self,
        material_id: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get material transactions with optional filtering.

        Args:
            material_id (Optional[str], optional): Filter by material ID
            transaction_type (Optional[str], optional): Filter by transaction type

        Returns:
            List[Dict[str, Any]]: List of material transactions
        """
        pass

    @abstractmethod
    def calculate_material_cost(self, material_id: str, quantity: float) -> float:
        """
        Calculate cost for a given material quantity.

        Args:
            material_id (str): Unique identifier of the material
            quantity (float): Quantity of the material

        Returns:
            float: Total cost for the specified quantity
        """
        pass

    @abstractmethod
    def get_material_types(self) -> List[str]:
        """
        Get all available material types.

        Returns:
            List[str]: List of material type names
        """
        pass