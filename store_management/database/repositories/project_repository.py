# Path: database/repositories/project_repository.py
"""Project Repository for managing project-related database operations."""

from typing import Any, Dict, List, Optional
import logging

import sqlalchemy
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.repositories.base_repository import BaseRepository
from database.models.project import Project, ProjectComponent
from database.models.enums import ProjectType, SkillLevel, ProjectStatus
from database.models.material import Material


class ProjectRepository(BaseRepository):
    """
    Repository for managing project-related database operations.

    Provides methods for CRUD operations and complex queries on projects.
    """

    def __init__(self, session):
        """
        Initialize the Project Repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session, Project)
        self._logger = logging.getLogger(__name__)

    def create_project(self, project_data: Dict[str, Any]) -> Project:
        """
        Create a new project.

        Args:
            project_data (Dict[str, Any]): Data for the new project

        Returns:
            Project: Created project instance
        """
        try:
            # Validate and set default values
            project_data.setdefault('type', ProjectType.CUSTOM)
            project_data.setdefault('skill_level', SkillLevel.BEGINNER)
            project_data.setdefault('status', ProjectStatus.PLANNING)

            project = Project(**project_data)
            self._session.add(project)
            self._session.commit()
            return project
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Error creating project: {str(e)}")
            raise

    def get_project_with_components(self, project_id: int) -> Optional[Project]:
        """
        Retrieve a project with its associated components.

        Args:
            project_id (int): ID of the project to retrieve

        Returns:
            Optional[Project]: Project instance with loaded components
        """
        try:
            return (
                self._session.query(Project)
                .options(joinedload(Project.components))
                .filter(Project.id == project_id)
                .first()
            )
        except SQLAlchemyError as e:
            self._logger.error(f"Error retrieving project {project_id}: {str(e)}")
            return None

    def update_project_status(self, project_id: int, new_status: ProjectStatus) -> Optional[Project]:
        """
        Update the status of a project.

        Args:
            project_id (int): ID of the project to update
            new_status (ProjectStatus): New status for the project

        Returns:
            Optional[Project]: Updated project instance
        """
        try:
            project = self._session.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = new_status
                self._session.commit()
                return project
            return None
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Error updating project status: {str(e)}")
            return None

    def list_projects(
            self,
            filter_criteria: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[Project]:
        """
        List projects with optional filtering and sorting.

        Args:
            filter_criteria (Optional[Dict[str, Any]], optional): Filters to apply
            sort_by (Optional[str], optional): Field to sort by
            limit (Optional[int], optional): Maximum number of results

        Returns:
            List[Project]: List of project objects
        """
        try:
            query = self._session.query(Project)

            # Apply filtering
            if filter_criteria:
                for key, value in filter_criteria.items():
                    query = query.filter(getattr(Project, key) == value)

            # Apply sorting
            if sort_by:
                query = query.order_by(getattr(Project, sort_by))

            # Apply limit
            if limit:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            self._logger.error(f"Error listing projects: {str(e)}")
            return []

    def add_project_component(self, project_id: int, component_data: Dict[str, Any]) -> Optional[ProjectComponent]:
        """
        Add a component to an existing project.

        Args:
            project_id (int): ID of the project to add component to
            component_data (Dict[str, Any]): Data for the new component

        Returns:
            Optional[ProjectComponent]: Created project component
        """
        try:
            project = self._session.query(Project).filter(Project.id == project_id).first()
            if project:
                component = ProjectComponent(**component_data)
                project.components.append(component)
                self._session.commit()
                return component
            return None
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Error adding project component: {str(e)}")
            return None