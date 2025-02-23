# Path: services/interfaces/project_service.py
"""
Defines the interface for project management services in the leatherworking system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum


class ProjectType(Enum):
    """Enum defining different types of leatherworking projects."""
    WALLET = "wallet"
    BAG = "bag"
    ACCESSORY = "accessory"
    CUSTOM = "custom"


class SkillLevel(Enum):
    """Enum defining skill levels for projects."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class IProjectService(ABC):
    """
    Abstract base class defining the contract for project management services.

    This interface ensures consistent project management operations across
    different implementation strategies.
    """

    @abstractmethod
    def create_project(self, project_data: Dict[str, Any]) -> Any:
        """
        Create a new leatherworking project.

        Args:
            project_data (Dict[str, Any]): Detailed information about the project

        Returns:
            Project object representing the created project

        Raises:
            ValueError: If project data is invalid
        """
        pass

    @abstractmethod
    def get_project(self, project_id: int, include_components: bool = False) -> Any:
        """
        Retrieve a specific project by its ID.

        Args:
            project_id (int): Unique identifier for the project
            include_components (bool, optional): Whether to include project components. Defaults to False.

        Returns:
            Project object with optional components

        Raises:
            NotFoundError: If project doesn't exist
        """
        pass

    @abstractmethod
    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> Any:
        """
        Update an existing project's details.

        Args:
            project_id (int): Unique identifier for the project
            project_data (Dict[str, Any]): Updated project information

        Returns:
            Updated Project object

        Raises:
            ValueError: If update data is invalid
            NotFoundError: If project doesn't exist
        """
        pass

    @abstractmethod
    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project from the system.

        Args:
            project_id (int): Unique identifier for the project to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If project doesn't exist
        """
        pass

    @abstractmethod
    def search_projects(self, search_params: Dict[str, Any]) -> List[Any]:
        """
        Search for projects based on various parameters.

        Args:
            search_params (Dict[str, Any]): Search criteria
            (e.g., type, skill_level, date range)

        Returns:
            List of Project objects matching the search criteria
        """
        pass

    @abstractmethod
    def get_complex_projects(self, complexity_threshold: int) -> List[Any]:
        """
        Retrieve projects above a certain complexity level.

        Args:
            complexity_threshold (int): Minimum complexity level to filter projects

        Returns:
            List of complex Project objects
        """
        pass

    @abstractmethod
    def analyze_project_material_usage(self, project_id: int) -> Dict[str, Any]:
        """
        Analyze material usage for a specific project.

        Args:
            project_id (int): Unique identifier for the project

        Returns:
            Dict containing material usage analysis details
        """
        pass

    @abstractmethod
    def generate_project_complexity_report(self) -> List[Dict[str, Any]]:
        """
        Generate a comprehensive report of project complexities.

        Returns:
            List of dictionaries with project complexity metrics
        """
        pass

    @abstractmethod
    def update_project_status(self, project_id: int, new_status: str) -> Any:
        """
        Update the status of a specific project.

        Args:
            project_id (int): Unique identifier for the project
            new_status (str): New status for the project

        Returns:
            Updated Project object

        Raises:
            ValueError: If status is invalid
            NotFoundError: If project doesn't exist
        """
        pass