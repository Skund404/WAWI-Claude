# Relative path: store_management/services/interfaces/material_service.py

"""
Material Service Interface Module

Defines the abstract base interface for material-related operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type

from database.models import Part


class MaterialService(ABC):
    """
    Abstract base class defining the interface for material-related operations.

    This service provides methods for managing materials,
    including validation, creation, and manipulation.
    """

    @abstractmethod
    def validate_model_creation(
        self,
        model_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate data before model creation.

        Args:
            model_name (str): Name of the model being created.
            data (Dict[str, Any]): Data to be validated.

        Returns:
            Dict[str, Any]: Validated and potentially modified data.

        Raises:
            ValueError: If data validation fails.
        """
        pass

    @abstractmethod
    def get_material_by_name(self, name: str) -> Optional[Part]:
        """
        Retrieve a material by its name.

        Args:
            name (str): Name of the material to retrieve.

        Returns:
            Optional[Part]: The material if found, None otherwise.
        """
        pass

    @abstractmethod
    def create_material(
        self,
        name: str,
        **kwargs
    ) -> Part:
        """
        Create a new material.

        Args:
            name (str): Name of the material.
            **kwargs: Additional material attributes.

        Returns:
            Part: The newly created material.

        Raises:
            ValueError: If material creation fails validation.
        """
        pass

    @abstractmethod
    def update_material(
        self,
        material: Part,
        **kwargs
    ) -> Part:
        """
        Update an existing material.

        Args:
            material (Part): The material to update.
            **kwargs: Attributes to update.

        Returns:
            Part: The updated material.

        Raises:
            ValueError: If material update fails validation.
        """
        pass

    @abstractmethod
    def list_materials(
        self,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Part]:
        """
        List materials with optional filtering.

        Args:
            filter_criteria (Optional[Dict[str, Any]], optional):
                Filtering parameters. Defaults to None.

        Returns:
            List[Part]: List of materials matching the criteria.
        """
        pass

    @abstractmethod
    def delete_material(self, material: Part) -> bool:
        """
        Delete a material.

        Args:
            material (Part): The material to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    def validate_material_quantity(
        self,
        material: Part,
        quantity: float
    ) -> bool:
        """
        Validate if a given quantity is valid for a material.

        Args:
            material (Part): The material to validate.
            quantity (float): Quantity to check.

        Returns:
            bool: True if the quantity is valid, False otherwise.
        """
        pass