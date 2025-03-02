# services/interfaces/project_service.py
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional, Dict, Any
from datetime import datetime


class ProjectType(Enum):
    """Defines the types of leatherworking projects."""
    BAG = auto()
    WALLET = auto()
    BELT = auto()
    CASE = auto()
    HOLSTER = auto()
    ACCESSORY = auto()
    GARMENT = auto()
    CUSTOM = auto()
    OTHER = auto()


class SkillLevel(Enum):
    """Defines the skill levels required for projects."""
    BEGINNER = auto()
    INTERMEDIATE = auto()
    ADVANCED = auto()
    EXPERT = auto()


class ProjectStatus(Enum):
    """Defines the possible status of a project."""
    PLANNING = auto()
    IN_PROGRESS = auto()
    REFINEMENT = auto()
    COMPLETED = auto()
    ON_HOLD = auto()
    CANCELLED = auto()


class IProjectService(ABC):
    """Abstract base class defining the interface for project-related operations."""

    @abstractmethod
    def create_project(self, project_data: Dict[str, Any]) -> 'Project':
        """
        Create a new project.

        Args:
            project_data (Dict[str, Any]): Project creation data

        Returns:
            Project: Created project instance
        """
        pass

    @abstractmethod
    def get_project(self, project_id: str) -> 'Project':
        """
        Retrieve a project by its ID.

        Args:
            project_id (str): Unique project identifier

        Returns:
            Project: Retrieved project instance
        """
        pass

    @abstractmethod
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> 'Project':
        """
        Update an existing project.

        Args:
            project_id (str): Unique project identifier
            updates (Dict[str, Any]): Project update data

        Returns:
            Project: Updated project instance
        """
        pass

    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id (str): Unique project identifier

        Returns:
            bool: True if deletion was successful
        """
        pass

    @abstractmethod
    def add_component_to_project(self, project_id: str, component_data: Dict[str, Any]) -> 'Project':
        """
        Add a component to a project.

        Args:
            project_id (str): Project identifier
            component_data (Dict[str, Any]): Component details

        Returns:
            Project: Updated project with new component
        """
        pass

    @abstractmethod
    def remove_component_from_project(self, project_id: str, component_id: str) -> 'Project':
        """
        Remove a component from a project.

        Args:
            project_id (str): Project identifier
            component_id (str): Component identifier

        Returns:
            Project: Updated project after component removal
        """
        pass

    @abstractmethod
    def update_project_progress(self, project_id: str, progress: int) -> 'Project':
        """
        Update project progress and adjust status accordingly.

        Args:
            project_id (str): Project identifier
            progress (int): Progress percentage (0-100)

        Returns:
            Project: Updated project
        """
        pass

    @abstractmethod
    def list_projects(
            self,
            project_type: Optional[ProjectType] = None,
            skill_level: Optional[SkillLevel] = None,
            status: Optional[ProjectStatus] = None
    ) -> List['Project']:
        """
        List projects with optional filtering.

        Args:
            project_type: Optional filter by project type
            skill_level: Optional filter by skill level
            status: Optional filter by project status

        Returns:
            List[Project]: Filtered list of projects
        """
        pass

    @abstractmethod
    def generate_project_complexity_report(self, project_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive project complexity report.

        Args:
            project_id (str): Project identifier

        Returns:
            Dict[str, Any]: Project complexity report
        """
        pass

    @abstractmethod
    def duplicate_project(self, project_id: str, new_name: Optional[str] = None) -> 'Project':
        """
        Duplicate an existing project.

        Args:
            project_id (str): Project identifier to duplicate
            new_name (Optional[str]): Name for the duplicated project

        Returns:
            Project: Newly created duplicated project
        """
        pass

    @abstractmethod
    def calculate_project_material_requirements(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate material requirements for a project.

        Args:
            project_id (str): Project identifier

        Returns:
            Dict[str, Any]: Material requirements analysis
        """
        pass

    @abstractmethod
    def analyze_project_material_usage(self, project_id: str) -> Dict[str, Any]:
        """
        Analyze material usage and efficiency for a project.

        Args:
            project_id (str): Project identifier

        Returns:
            Dict[str, Any]: Material usage analysis
        """
        pass

    @abstractmethod
    def get_projects_by_deadline(
            self,
            before_date: Optional[datetime] = None,
            after_date: Optional[datetime] = None
    ) -> List['Project']:
        """
        Retrieve projects within a specific deadline range.

        Args:
            before_date (Optional[datetime]): Maximum deadline date
        after_date (Optional[datetime]): Minimum deadline date

        Returns:
            List[Project]: Projects matching the deadline criteria
        """
        pass

    @abstractmethod
    def get_complex_projects(self, min_components: int = 5) -> List['Project']:
        """
        Retrieve projects with a high number of components.

        Args:
            min_components (int): Minimum number of components to consider a project complex

        Returns:
            List[Project]: Complex projects
        """
        pass

    @abstractmethod
    def get_projects_by_status(self, status: ProjectStatus) -> List['Project']:
        """
        Retrieve projects with a specific status.

        Args:
            status (ProjectStatus): Project status to filter by

        Returns:
            List[Project]: Projects with the specified status
        """
        pass

    @abstractmethod
    def search_projects(self, query: str) -> List['Project']:
        """
        Search for projects by name or description.

        Args:
            query (str): Search term

        Returns:
            List[Project]: Projects matching the search query
        """
        pass