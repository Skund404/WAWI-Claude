# Path: database/models/interfaces.py
"""
Interface definitions for database models.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any

class IModel(ABC):
    """
    Base interface for all database models.
    """
    @abstractmethod
    def to_dict(self, exclude_fields: Optional[list[str]] = None) -> dict:
        """
        Convert model to a dictionary representation.

        Args:
            exclude_fields (Optional[list[str]], optional): Fields to exclude. Defaults to None.

        Returns:
            dict: Dictionary representation of the model.
        """
        pass

class IProject(IModel):
    """
    Interface for Project-related models.
    """
    @abstractmethod
    def calculate_complexity(self) -> float:
        """
        Calculate the complexity of the project.

        Returns:
            float: Complexity score.
        """
        pass

    @abstractmethod
    def calculate_total_cost(self) -> float:
        """
        Calculate the total cost of the project.

        Returns:
            float: Total project cost.
        """
        pass

    @abstractmethod
    def update_status(self, new_status: Any) -> None:
        """
        Update the status of the project.

        Args:
            new_status (Any): New status to set.
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate the project model.

        Returns:
            bool: True if valid, False otherwise.
        """
        pass