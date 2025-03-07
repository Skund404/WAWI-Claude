# services/interfaces/project_service.py
"""
Interface for Project Service in the leatherworking application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from database.models.enums import (
    ProjectType,
    ProjectStatus,
    SkillLevel
)
from database.models.project import Project
from database.models.sales import Sales


class IProjectService(ABC):
    """
    Abstract base class defining the interface for Project Service.
    Handles operations related to leatherworking projects.
    """

    @abstractmethod
    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        project_type: Optional[ProjectType] = None,
        status: ProjectStatus = ProjectStatus.INITIAL_CONSULTATION,
        start_date: Optional[datetime] = None,
        sales_id: Optional[int] = None,
        **kwargs
    ) -> Project:
        """
        Create a new project.

        Args:
            name (str): Name of the project
            description (Optional[str]): Description of the project
            project_type (Optional[ProjectType]): Type of the project
            status (ProjectStatus): Initial status of the project
            start_date (Optional[datetime]): Start date of the project
            sales_id (Optional[int]): ID of associated sales order
            **kwargs: Additional attributes for the project

        Returns:
            Project: The created project
        """
        pass

    @abstractmethod
    def get_project_by_id(self, project_id: int) -> Project:
        """
        Retrieve a project by its ID.

        Args:
            project_id (int): ID of the project

        Returns:
            Project: The retrieved project
        """
        pass

    @abstractmethod
    def get_projects_by_status(self, status: ProjectStatus) -> List[Project]:
        """
        Retrieve projects by their status.

        Args:
            status (ProjectStatus): Status to filter projects

        Returns:
            List[Project]: List of projects matching the status
        """
        pass

    @abstractmethod
    def get_projects_by_type(self, project_type: ProjectType) -> List[Project]:
        """
        Retrieve projects by their type.

        Args:
            project_type (ProjectType): Type to filter projects

        Returns:
            List[Project]: List of projects matching the type
        """
        pass

    @abstractmethod
    def update_project(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        project_type: Optional[ProjectType] = None,
        status: Optional[ProjectStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> Project:
        """
        Update project information.

        Args:
            project_id (int): ID of the project to update
            name (Optional[str]): New name of the project
            description (Optional[str]): New description
            project_type (Optional[ProjectType]): New project type
            status (Optional[ProjectStatus]): New project status
            start_date (Optional[datetime]): New start date
            end_date (Optional[datetime]): New end date
            **kwargs: Additional attributes to update

        Returns:
            Project: The updated project
        """
        pass

    @abstractmethod
    def update_project_status(
        self,
        project_id: int,
        status: ProjectStatus
    ) -> Project:
        """
        Update the status of a project.

        Args:
            project_id (int): ID of the project
            status (ProjectStatus): New status for the project

        Returns:
            Project: The updated project
        """
        pass

    @abstractmethod
    def link_sales_to_project(
        self,
        project_id: int,
        sales_id: int
    ) -> Project:
        """
        Link a sales order to a project.

        Args:
            project_id (int): ID of the project
            sales_id (int): ID of the sales order

        Returns:
            Project: The updated project with sales link
        """
        pass

    @abstractmethod
    def get_project_components(self, project_id: int) -> List[Any]:
        """
        Retrieve all components associated with a project.

        Args:
            project_id (int): ID of the project

        Returns:
            List[Any]: List of project components
        """
        pass

    @abstractmethod
    def create_project_tool_list(self, project_id: int) -> Any:
        """
        Create a tool list for a specific project.

        Args:
            project_id (int): ID of the project

        Returns:
            Any: The created tool list
        """
        pass

    @abstractmethod
    def complete_project(self, project_id: int) -> Project:
        """
        Mark a project as completed.

        Args:
            project_id (int): ID of the project to complete

        Returns:
            Project: The completed project
        """
        pass

    @abstractmethod
    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project from the system.

        Args:
            project_id (int): ID of the project to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass