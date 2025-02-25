# Relative path: store_management/services/interfaces/pattern_service.py

"""
Pattern Service Interface Module

Defines the abstract base interface for pattern-related operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from di.core import inject
from services.interfaces import MaterialService


class IPatternService(ABC):
    """
    Interface for pattern management service.

    Provides a contract for management of leatherworking patterns,
    including creation, retrieval, updating, and validation.
    """

    @abstractmethod
    @inject(MaterialService)
    def get_all_patterns(self) -> List[Any]:
        """
        Get all available patterns.

        Returns:
            List[Any]: List of patterns
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_pattern_by_id(self, pattern_id: int) -> Optional[Any]:
        """
        Get pattern by ID.

        Args:
            pattern_id (int): ID of the pattern

        Returns:
            Optional[Any]: Pattern if found, None otherwise

        Raises:
            KeyError: If pattern with the given ID does not exist
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def create_pattern(self, pattern_data: Dict[str, Any]) -> Any:
        """
        Create a new pattern.

        Args:
            pattern_data (Dict[str, Any]): Pattern data dictionary

        Returns:
            Any: Created pattern

        Raises:
            ValueError: If pattern data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def update_pattern(self, pattern_id: int, pattern_data: Dict[str, Any]) -> Optional[Any]:
        """
        Update existing pattern.

        Args:
            pattern_id (int): ID of pattern to update
            pattern_data (Dict[str, Any]): Updated pattern data

        Returns:
            Optional[Any]: Updated pattern if successful, None otherwise

        Raises:
            KeyError: If pattern with the given ID does not exist
            ValueError: If pattern data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def delete_pattern(self, pattern_id: int) -> bool:
        """
        Delete pattern by ID.

        Args:
            pattern_id (int): ID of pattern to delete

        Returns:
            bool: True if deleted, False otherwise

        Raises:
            KeyError: If pattern with the given ID does not exist
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def search_patterns(self, search_term: str, search_fields: List[str]) -> List[Any]:
        """
        Search patterns based on criteria.

        Args:
            search_term (str): Term to search for
            search_fields (List[str]): Fields to search in

        Returns:
            List[Any]: List of matching patterns
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def calculate_material_requirements(self, pattern_id: int, quantity: int = 1) -> Dict[str, float]:
        """
        Calculate material requirements for pattern.

        Args:
            pattern_id (int): ID of pattern
            quantity (int): Number of items to produce

        Returns:
            Dict[str, float]: Dictionary of material requirements

        Raises:
            KeyError: If pattern with the given ID does not exist
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def validate_pattern(self, pattern_id: int) -> Dict[str, Any]:
        """
        Validate pattern data and requirements.

        Args:
            pattern_id (int): ID of pattern to validate

        Returns:
            Dict[str, Any]: Validation results dictionary

        Raises:
            KeyError: If pattern with the given ID does not exist
        """
        pass