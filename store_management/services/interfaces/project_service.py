# path: services/interfaces/project_service.py
"""
Project service interface definitions.

This module defines the interface for project-related services,
which provide functionality related to managing projects in the system.
"""

import enum
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union


class ProjectType(enum.Enum):
    """Enumeration of project types."""
    BAG = "bag"
    WALLET = "wallet"
    BELT = "belt"
    CASE = "case"
    HOLSTER = "holster"
    ACCESSORY = "accessory"
    GARMENT = "garment"
    CUSTOM = "custom"
    OTHER = "other"


class SkillLevel(enum.Enum):
    """Enumeration of skill levels required for projects."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class IProjectService(ABC):
    """
    Interface for project service.

    This interface defines the contract for services that manage projects
    in the leatherworking store management system.
    """

    @abstractmethod
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            project_data: Dictionary containing project attributes

        Returns:
            Dictionary representing the created project
        """
        pass

    @abstractmethod
    def get_project(self, project_id: int, include_components: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID.

        Args:
            project_id: ID of the project to retrieve
            include_components: Whether to include project components in the result

        Returns:
            Dictionary representing the project or None if not found
        """
        pass

    @abstractmethod
    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a project.

        Args:
            project_id: ID of the project to update
            project_data: Dictionary containing updated attributes

        Returns:
            Dictionary representing the updated project or None if not found
        """
        pass

    @abstractmethod
    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if the project was deleted, False otherwise
        """
        pass

    @abstractmethod
    def search_projects(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for projects based on parameters.

        Args:
            search_params: Dictionary of search parameters

        Returns:
            List of dictionaries representing matching projects
        """
        pass

    @abstractmethod
    def get_complex_projects(self, complexity_threshold: float = 7.0) -> List[Dict[str, Any]]:
        """
        Get projects above a certain complexity threshold.

        Args:
            complexity_threshold: The minimum complexity score

        Returns:
            List of dictionaries representing complex projects
        """
        pass

    @abstractmethod
    def analyze_project_material_usage(self, project_id: int) -> Dict[str, Any]:
        """
        Analyze material usage for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary containing material usage analysis
        """
        pass

    @abstractmethod
    def generate_project_complexity_report(self) -> Dict[str, Any]:
        """
        Generate a report on project complexity across the system.

        Returns:
            Dictionary containing project complexity metrics
        """
        pass

    @abstractmethod
    def update_project_status(self, project_id: int, new_status: str) -> bool:
        """
        Update the status of a project.

        Args:
            project_id: ID of the project
            new_status: New status for the project

        Returns:
            True if the status was updated, False otherwise
        """
        pass


# Class type alias for backward compatibility
ProjectService = IProjectService