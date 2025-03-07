# services/interfaces/pattern_service.py
"""
Interface for Pattern Service in the leatherworking application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from database.models.enums import SkillLevel, PatternStatus
from database.models.pattern import Pattern
from database.models.components import Component


class IPatternService(ABC):
    """
    Abstract base class defining the interface for Pattern Service.
    Handles operations related to leatherworking patterns.
    """

    @abstractmethod
    def create_pattern(
        self,
        name: str,
        description: Optional[str] = None,
        skill_level: Optional[SkillLevel] = None,
        status: Optional[PatternStatus] = None,
        components: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Pattern:
        """
        Create a new pattern.

        Args:
            name (str): Name of the pattern
            description (Optional[str]): Description of the pattern
            skill_level (Optional[SkillLevel]): Skill level required for the pattern
            status (Optional[PatternStatus]): Current status of the pattern
            components (Optional[List[Dict[str, Any]]]): List of components for the pattern
            **kwargs: Additional attributes for the pattern

        Returns:
            Pattern: The created pattern
        """
        pass

    @abstractmethod
    def get_pattern_by_id(self, pattern_id: int) -> Pattern:
        """
        Retrieve a pattern by its ID.

        Args:
            pattern_id (int): ID of the pattern

        Returns:
            Pattern: The retrieved pattern
        """
        pass

    @abstractmethod
    def get_patterns_by_skill_level(self, skill_level: SkillLevel) -> List[Pattern]:
        """
        Retrieve patterns by skill level.

        Args:
            skill_level (SkillLevel): Skill level to filter patterns

        Returns:
            List[Pattern]: List of patterns matching the skill level
        """
        pass

    @abstractmethod
    def update_pattern(self, pattern_id: int, **kwargs) -> Pattern:
        """
        Update an existing pattern.

        Args:
            pattern_id (int): ID of the pattern to update
            **kwargs: Attributes to update

        Returns:
            Pattern: The updated pattern
        """
        pass

    @abstractmethod
    def delete_pattern(self, pattern_id: int) -> bool:
        """
        Delete a pattern.

        Args:
            pattern_id (int): ID of the pattern to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def add_component_to_pattern(
        self,
        pattern_id: int,
        component_id: int,
        quantity: int = 1
    ) -> Any:
        """
        Add a component to a pattern.

        Args:
            pattern_id (int): ID of the pattern
            component_id (int): ID of the component
            quantity (int, optional): Quantity of the component. Defaults to 1.

        Returns:
            Any: The created pattern component association
        """
        pass