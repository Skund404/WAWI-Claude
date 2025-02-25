# database/models/factories.py
"""
Factory classes for creating model instances.
"""

from typing import Dict, Any


class ProjectFactory:
    """
    Factory for creating project model instances.
    """

    @classmethod
    def create(cls, data: Dict[str, Any]):
        """
        Create a new project instance.

        Args:
            data (Dict[str, Any]): Project creation data

        Returns:
            Project: A new project instance
        """
        from .project import Project  # Lazy import to avoid circular dependencies

        # Validate and transform input data
        validated_data = cls._validate_project_data(data)

        # Create and return project instance
        return Project(**validated_data)

    @classmethod
    def _validate_project_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize project creation data.

        Args:
            data (Dict[str, Any]): Raw project data

        Returns:
            Dict[str, Any]: Validated project data
        """
        # Add validation logic here
        return data


class PatternFactory:
    """
    Factory for creating pattern model instances.
    """

    @classmethod
    def create(cls, data: Dict[str, Any]):
        """
        Create a new pattern instance.

        Args:
            data (Dict[str, Any]): Pattern creation data

        Returns:
            Pattern: A new pattern instance
        """
        from .pattern import Pattern  # Lazy import to avoid circular dependencies

        # Validate and transform input data
        validated_data = cls._validate_pattern_data(data)

        # Create and return pattern instance
        return Pattern(**validated_data)

    @classmethod
    def _validate_pattern_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize pattern creation data.

        Args:
            data (Dict[str, Any]): Raw pattern data

        Returns:
            Dict[str, Any]: Validated pattern data
        """
        # Add validation logic here
        return data