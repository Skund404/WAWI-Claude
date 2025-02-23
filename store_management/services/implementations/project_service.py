# Path: services/implementations/project_service.py
"""
Concrete implementation of the Project Service for leatherworking projects.
"""

from typing import Dict, Any, List
from services.interfaces.project_service import IProjectService, ProjectType, SkillLevel
from database.repositories.project_repository import ProjectRepository
from database.models.project import Project
from database.models.project_component import ProjectComponent
from utils.error_handler import ApplicationError, ValidationError
from utils.logger import get_logger


class ProjectService(IProjectService):
    """
    Concrete implementation of project management services.

    Provides business logic and validation for project-related operations.
    """

    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize the project service with a project repository.

        Args:
            project_repository (ProjectRepository): Repository for project data access
        """
        self.project_repository = project_repository
        self.logger = get_logger(__name__)

    def _validate_project_data(self, project_data: Dict[str, Any]) -> None:
        """
        Validate project data before creation or update.

        Args:
            project_data (Dict[str, Any]): Project data to validate

        Raises:
            ValidationError: If project data is invalid
        """
        # Validate required fields
        required_fields = ['name', 'type', 'skill_level', 'complexity_level']
        for field in required_fields:
            if field not in project_data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate project type
        if project_data['type'] not in [t.value for t in ProjectType]:
            raise ValidationError(f"Invalid project type: {project_data['type']}")

        # Validate skill level
        if project_data['skill_level'] not in [s.value for s in SkillLevel]:
            raise ValidationError(f"Invalid skill level: {project_data['skill_level']}")

        # Validate complexity level
        if not isinstance(project_data['complexity_level'], int) or \
                project_data['complexity_level'] < 1 or \
                project_data['complexity_level'] > 10:
            raise ValidationError("Complexity level must be an integer between 1 and 10")

    def create_project(self, project_data: Dict[str, Any]) -> Project:
        """
        Create a new leatherworking project.

        Args:
            project_data (Dict[str, Any]): Detailed information about the project

        Returns:
            Project: Created project object

        Raises:
            ValidationError: If project data is invalid
        """
        try:
            # Validate input data
            self._validate_project_data(project_data)

            # Create project
            project = Project(**project_data)
            created_project = self.project_repository.create(project)

            self.logger.info(f"Created project: {created_project.name}")
            return created_project

        except Exception as e:
            self.logger.error(f"Error creating project: {str(e)}")
            raise ApplicationError("Failed to create project", details=str(e))

    def get_project(self, project_id: int, include_components: bool = False) -> Project:
        """
        Retrieve a specific project by its ID.

        Args:
            project_id (int): Unique identifier for the project
            include_components (bool, optional): Whether to include project components

        Returns:
            Project: Project object with optional components

        Raises:
            ApplicationError: If project retrieval fails
        """
        try:
            # If include_components is True, use a specialized repository method
            if include_components:
                project = self.project_repository.get_project_with_details(project_id)
            else:
                project = self.project_repository.get(project_id)

            if not project:
                raise ApplicationError(f"Project with ID {project_id} not found")

            return project

        except Exception as e:
            self.logger.error(f"Error retrieving project {project_id}: {str(e)}")
            raise ApplicationError(f"Failed to retrieve project {project_id}", details=str(e))

    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> Project:
        """
        Update an existing project's details.

        Args:
            project_id (int): Unique identifier for the project
            project_data (Dict[str, Any]): Updated project information

        Returns:
            Project: Updated project object

        Raises:
            ValidationError: If update data is invalid
            ApplicationError: If project update fails
        """
        try:
            # Validate input data
            self._validate_project_data(project_data)

            # Update project
            updated_project = self.project_repository.update(project_id, project_data)

            self.logger.info(f"Updated project: {updated_project.name}")
            return updated_project

        except Exception as e:
            self.logger.error(f"Error updating project {project_id}: {str(e)}")
            raise ApplicationError(f"Failed to update project {project_id}", details=str(e))

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project from the system.

        Args:
            project_id (int): Unique identifier for the project to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            ApplicationError: If project deletion fails
        """
        try:
            self.project_repository.delete(project_id)
            self.logger.info(f"Deleted project with ID: {project_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {str(e)}")
            raise ApplicationError(f"Failed to delete project {project_id}", details=str(e))

    def search_projects(self, search_params: Dict[str, Any]) -> List[Project]:
        """
        Search for projects based on various parameters.

        Args:
            search_params (Dict[str, Any]): Search criteria

        Returns:
            List[Project]: Projects matching the search criteria
        """
        try:
            projects = self.project_repository.search_projects(search_params)
            return projects

        except Exception as e:
            self.logger.error(f"Error searching projects: {str(e)}")
            raise ApplicationError("Failed to search projects", details=str(e))

    def get_complex_projects(self, complexity_threshold: int) -> List[Project]:
        """
        Retrieve projects above a certain complexity level.

        Args:
            complexity_threshold (int): Minimum complexity level to filter projects

        Returns:
            List[Project]: Complex projects
        """
        try:
            complex_projects = self.project_repository.generate_project_complexity_report(complexity_threshold)
            return complex_projects

        except Exception as e:
            self.logger.error(f"Error retrieving complex projects: {str(e)}")
            raise ApplicationError("Failed to retrieve complex projects", details=str(e))

    def analyze_project_material_usage(self, project_id: int) -> Dict[str, Any]:
        """
        Analyze material usage for a specific project.

        Args:
            project_id (int): Unique identifier for the project

        Returns:
            Dict containing material usage analysis details
        """
        try:
            material_usage = self.project_repository.get_project_material_usage(project_id)
            return material_usage

        except Exception as e:
            self.logger.error(f"Error analyzing material usage for project {project_id}: {str(e)}")
            raise ApplicationError(f"Failed to analyze material usage for project {project_id}", details=str(e))

    def generate_project_complexity_report(self) -> List[Dict[str, Any]]:
        """
        Generate a comprehensive report of project complexities.

        Returns:
            List of dictionaries with project complexity metrics
        """
        try:
            complexity_report = self.project_repository.generate_project_complexity_report()
            return complexity_report

        except Exception as e:
            self.logger.error(f"Error generating project complexity report: {str(e)}")
            raise ApplicationError("Failed to generate project complexity report", details=str(e))

    def update_project_status(self, project_id: int, new_status: str) -> Project:
        """
        Update the status of a specific project.

        Args:
            project_id (int): Unique identifier for the project
            new_status (str): New status for the project

        Returns:
            Updated Project object

        Raises:
            ValidationError: If status is invalid
        """
        try:
            # Validate status (assuming status is from ProductionStatus enum)
            updated_project = self.project_repository.update(
                project_id,
                {'production_status': new_status}
            )

            self.logger.info(f"Updated project {project_id} status to {new_status}")
            return updated_project

        except Exception as e:
            self.logger.error(f"Error updating project {project_id} status: {str(e)}")
            raise ApplicationError(f"Failed to update project {project_id} status", details=str(e))