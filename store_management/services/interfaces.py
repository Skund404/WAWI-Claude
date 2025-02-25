# File: services/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models.material import Material, MaterialTransaction


class MaterialService(ABC):
    """
    Abstract base class defining the interface for material-related operations.
    """

    @abstractmethod
    def create_material(self, **kwargs) -> Material:
        """
        Create a new material entry.

        Args:
            **kwargs: Keyword arguments for material creation

        Returns:
            Material: Newly created material instance
        """
        pass

    @abstractmethod
    def update_material(self, material_id: int, **kwargs) -> Material:
        """
        Update an existing material.

        Args:
            material_id (int): ID of the material to update
            **kwargs: Attributes to update

        Returns:
            Material: Updated material instance
        """
        pass

    @abstractmethod
    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material.

        Args:
            material_id (int): ID of the material to delete

        Returns:
            bool: True if deletion was successful
        """
        pass

    @abstractmethod
    def get_material_by_id(self, material_id: int) -> Optional[Material]:
        """
        Retrieve a material by its ID.

        Args:
            material_id (int): ID of the material

        Returns:
            Optional[Material]: Material instance or None
        """
        pass

    @abstractmethod
    def list_materials(self,
                       filter_params: Optional[Dict[str, Any]] = None,
                       page: int = 1,
                       per_page: int = 10) -> List[Material]:
        """
        List materials with optional filtering and pagination.

        Args:
            filter_params (dict, optional): Filtering parameters
            page (int): Page number for pagination
            per_page (int): Number of items per page

        Returns:
            List[Material]: List of material instances
        """
        pass

    @abstractmethod
    def update_stock(self,
                     material_id: int,
                     quantity_change: float,
                     transaction_type: str = 'ADJUSTMENT') -> Material:
        """
        Update stock for a specific material.

        Args:
            material_id (int): ID of the material
            quantity_change (float): Amount to change stock
            transaction_type (str): Type of stock transaction

        Returns:
            Material: Updated material instance
        """
        pass