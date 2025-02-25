# database/models/interfaces.py
"""
Interface definitions for database models.
"""

import abc
from typing import Any, Dict, Optional


class IModel(abc.ABC):
    """
    Abstract base interface for all database models.
    """

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        pass

    @classmethod
    @abc.abstractmethod
    def create(cls, data: Dict[str, Any]) -> 'IModel':
        """
        Create a new model instance from provided data.

        Args:
            data (Dict[str, Any]): Data to create the model instance

        Returns:
            IModel: A new model instance
        """
        pass

    @abc.abstractmethod
    def validate(self) -> bool:
        """
        Validate the current model instance.

        Returns:
            bool: Whether the model instance is valid
        """
        pass


class IProject(IModel):
    """
    Interface for project-related models.
    """

    @abc.abstractmethod
    def update_status(self, new_status: str) -> None:
        """
        Update the project status.

        Args:
            new_status (str): New status for the project
        """
        pass

    @abc.abstractmethod
    def add_component(self, component: Any) -> None:
        """
        Add a component to the project.

        Args:
            component (Any): Component to add to the project
        """
        pass


class IInventoryItem(IModel):
    """
    Interface for inventory-related models.
    """

    @abc.abstractmethod
    def adjust_quantity(self, quantity_change: float) -> None:
        """
        Adjust the quantity of the inventory item.

        Args:
            quantity_change (float): Amount to adjust the quantity by
        """
        pass

    @abc.abstractmethod
    def get_stock_value(self) -> float:
        """
        Calculate the total stock value.

        Returns:
            float: Total value of the item in stock
        """
        pass


def validate_model_data(data: Dict[str, Any], required_fields: Optional[list] = None) -> bool:
    """
    Generic data validation function for model data.

    Args:
        data (Dict[str, Any]): Data to validate
        required_fields (Optional[list], optional): List of required field names

    Returns:
        bool: Whether the data is valid
    """
    if required_fields is None:
        return True

    # Check if all required fields are present and not None
    return all(
        field in data and data[field] is not None
        for field in required_fields
    )