# services/interfaces/pattern_service.py
from typing import Any, Dict, List, Optional, Protocol


class IPatternService(Protocol):
    """Protocol defining the pattern service interface."""

    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns.

        Returns:
            List[Dict[str, Any]]: List of pattern dictionaries
        """
        ...

    def get_pattern_by_id(self, pattern_id: int) -> Dict[str, Any]:
        """Get pattern by ID.

        Args:
            pattern_id: ID of the pattern

        Returns:
            Dict[str, Any]: Pattern dictionary

        Raises:
            NotFoundError: If pattern not found
        """
        ...

    def create_pattern(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pattern.

        Args:
            pattern_data: Pattern data dictionary

        Returns:
            Dict[str, Any]: Created pattern dictionary

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update_pattern(self, pattern_id: int, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing pattern.

        Args:
            pattern_id: ID of the pattern to update
            pattern_data: Updated pattern data

        Returns:
            Dict[str, Any]: Updated pattern dictionary

        Raises:
            NotFoundError: If pattern not found
            ValidationError: If validation fails
        """
        ...

    def delete_pattern(self, pattern_id: int) -> bool:
        """Delete a pattern.

        Args:
            pattern_id: ID of the pattern to delete

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If pattern not found
        """
        ...

    def get_patterns_by_skill_level(self, skill_level: str) -> List[Dict[str, Any]]:
        """Get patterns by skill level.

        Args:
            skill_level: Skill level to filter by

        Returns:
            List[Dict[str, Any]]: List of matching pattern dictionaries
        """
        ...