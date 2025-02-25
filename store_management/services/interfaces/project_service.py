# Relative path: store_management/services/interfaces/project_service.py

"""
Project Service Interface Module

Defines the abstract base interface for project-related operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum

from di.core import inject
from services.interfaces import MaterialService


class ProjectType(Enum):
    """Enumeration of different project types"""
    LEATHER_BAG = 'leather_bag'
    WALLET = 'wallet'
    BELT = 'belt'
    CUSTOM = 'custom'


class SkillLevel(Enum):
    """Enumeration of skill levels required for projects"""
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'


class IProjectService(ABC):
    """
    Interface defining the contract for project service implementations.
    Handles project creation, management, and analysis functionality.
    """

    @abstractmethod
    @inject(MaterialService)
    def create_project(self, project_data: Dict) -> Dict:
        """
        Create a new project with the given data.

        Args:
            project_data (Dict): Dictionary containing project information including:
                - name: str
                - project_type: ProjectType
                - skill_level: SkillLevel
                - description: str
                - estimated_hours: float

        Returns:
            Dict: Created project data

        Raises:
            ValidationError: If project data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_project(self, project_id: int, include_components: bool = False) -> Dict:
        """
        Retrieve project details by ID.

        Args:
            project_id (int): ID of the project to retrieve
            include_components (bool): Whether to include component details

        Returns:
            Dict: Project details

        Raises:
            NotFoundError: If project is not found
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def update_project(self, project_id: int, project_data: Dict) -> Dict:
        """
        Update an existing project.

        Args:
            project_id (int): ID of the project to update
            project_data (Dict): Updated project data

        Returns:
            Dict: Updated project details

        Raises:
            NotFoundError: If project is not found
            ValidationError: If update data is invalid
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project by ID.

        Args:
            project_id (int): ID of the project to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If project is not found
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def search_projects(self, search_params: Dict) -> List[Dict]:
        """
        Search projects based on given parameters.

        Args:
            search_params (Dict): Search parameters which may include:
                - name: str
                - project_type: ProjectType
                - skill_level: SkillLevel
                - status: str
                - date_range: tuple

        Returns:
            List[Dict]: List of matching projects
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def get_complex_projects(self, complexity_threshold: float) -> List[Dict]:
        """
        Get projects above specified complexity threshold.

        Args:
            complexity_threshold (float): Minimum complexity score

        Returns:
            List[Dict]: List of complex projects
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def analyze_project_material_usage(self, project_id: int) -> Dict:
        """
        Analyze material usage for a specific project.

        Args:
            project_id (int): ID of the project to analyze

        Returns:
            Dict: Material usage analysis including:
                - total_materials: float
                - material_efficiency: float
                - wastage: float
                - cost_analysis: Dict

        Raises:
            NotFoundError: If project is not found
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def generate_project_complexity_report(self) -> Dict:
        """
        Generate a report on project complexities across the system.

        Returns:
            Dict: Complexity report including:
                - average_complexity: float
                - complexity_distribution: Dict
                - skill_level_breakdown: Dict
        """
        pass

    @abstractmethod
    @inject(MaterialService)
    def update_project_status(self, project_id: int, new_status: str) -> Dict:
        """
        Update the status of a project.

        Args:
            project_id (int): ID of the project
            new_status (str): New status to set

        Returns:
            Dict: Updated project details

        Raises:
            NotFoundError: If project is not found
            ValidationError: If status is invalid
        """
        pass