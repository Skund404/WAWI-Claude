# Path: services/interfaces/material_service.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.models.material import MaterialType, MaterialQualityGrade


class IMaterialService(ABC):
    """
    Abstract base class defining the interface for Material Service operations.
    """

    @abstractmethod
    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new material.

        Args:
            material_data (Dict[str, Any]): Data for creating a new material

        Returns:
            Dict[str, Any]: Created material details
        """
        pass

    @abstractmethod
    def get_material(self, material_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific material by ID.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            Optional[Dict[str, Any]]: Material details
        """
        pass

    @abstractmethod
    def update_material(self, material_id: int, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing material.

        Args:
            material_id (int): Unique identifier for the material
            material_data (Dict[str, Any]): Updated material information

        Returns:
            Dict[str, Any]: Updated material details
        """
        pass

    @abstractmethod
    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            bool: True if deletion was successful
        """
        pass

    @abstractmethod
    def update_stock(self, material_id: int, quantity_change: float,
                     transaction_type: str,
                     notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Update the stock of a material.

        Args:
            material_id (int): Unique identifier for the material
            quantity_change (float): Amount to change stock by
            transaction_type (str): Type of stock transaction
            notes (Optional[str]): Additional notes for the transaction

        Returns:
            Dict[str, Any]: Updated material details
        """
        pass

    @abstractmethod
    def get_low_stock_materials(self, include_zero_stock: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve materials with low stock.

        Args:
            include_zero_stock (bool): Whether to include materials with zero stock

        Returns:
            List[Dict[str, Any]]: List of materials with low stock
        """
        pass

    @abstractmethod
    def search_materials(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for materials based on various parameters.

        Args:
            search_params (Dict[str, Any]): Search criteria

        Returns:
            List[Dict[str, Any]]: List of matching materials
        """
        pass

    @abstractmethod
    def generate_material_usage_report(self,
                                       start_date: datetime,
                                       end_date: datetime) -> Dict[str, Any]:
        """
        Generate a comprehensive material usage report.

        Args:
            start_date (datetime): Start of the reporting period
            end_date (datetime): End of the reporting period
        Returns:
            Dict[str, Any]: Detailed material usage report
        """
        pass