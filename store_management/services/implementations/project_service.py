# Path: services/implementations/project_service.py
"""Project Service Implementation for Leatherworking Store Management."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from services.interfaces.project_service import IProjectService, ProjectType, SkillLevel
from services.base_service import Service
from database.repositories.project_repository import ProjectRepository
from database.sqlalchemy.core.manager_factory import get_manager

# Configure logging
logger = logging.getLogger(__name__)


class ProjectService(Service[Any], IProjectService):
    """
    Project Service implementation for managing leatherworking projects.

    This service provides comprehensive methods for handling project-related
    operations in the leatherworking store management system.
    """

    def __init__(self, project_repository: Optional[ProjectRepository] = None):
        """
        Initialize the Project Service.

        Args:
            project_repository (Optional[ProjectRepository]): Repository for project operations
        """
        self._project_repository = project_repository or get_manager('Project')
        super().__init__()

    def create_pattern(self, pattern_data: Dict[str, Any]) -> Any:
        """
        Create a new pattern in the system.

        Args:
            pattern_data (Dict[str, Any]): Data for the new pattern

        Returns:
            Any: Created pattern object
        """
        try:
            # Validate and set default values
            pattern_data.setdefault('created_date', datetime.now())
            pattern_data.setdefault('type', ProjectType.CUSTOM)
            pattern_data.setdefault('skill_level', SkillLevel.BEGINNER)

            # Use repository to create pattern
            pattern = self._project_repository.create(pattern_data)
            return pattern
        except Exception as e:
            # Log the error and re-raise
            logger.error(f"Error creating pattern: {str(e)}")
            raise

    def get_pattern_by_id(self, pattern_id: int) -> Any:
        """
        Retrieve a pattern by its ID.

        Args:
            pattern_id (int): Unique identifier for the pattern

        Returns:
            Any: Pattern object
        """
        try:
            return self._project_repository.get_by_id(pattern_id)
        except Exception as e:
            logger.error(f"Error retrieving pattern {pattern_id}: {str(e)}")
            raise

    def update_pattern(self, pattern_id: int, update_data: Dict[str, Any]) -> Any:
        """
        Update an existing pattern.

        Args:
            pattern_id (int): ID of the pattern to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Any: Updated pattern object
        """
        try:
            return self._project_repository.update(pattern_id, update_data)
        except Exception as e:
            logger.error(f"Error updating pattern {pattern_id}: {str(e)}")
            raise

    def delete_pattern(self, pattern_id: int) -> bool:
        """
        Delete a pattern from the system.

        Args:
            pattern_id (int): ID of the pattern to delete

        Returns:
            bool: True if deletion was successful
        """
        try:
            self._project_repository.delete(pattern_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting pattern {pattern_id}: {str(e)}")
            return False

    def list_patterns(
            self,
            filter_criteria: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[Any]:
        """
        List patterns with optional filtering and sorting.

        Args:
            filter_criteria (Optional[Dict[str, Any]], optional): Filters to apply
            sort_by (Optional[str], optional): Field to sort by
            limit (Optional[int], optional): Maximum number of results

        Returns:
            List[Any]: List of pattern objects
        """
        try:
            return self._project_repository.list(
                filter_criteria=filter_criteria,
                sort_by=sort_by,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error listing patterns: {str(e)}")
            return []

    def create_project(self, project_data: Dict[str, Any]) -> Any:
        """
        Create a new leatherworking project.

        Args:
            project_data (Dict[str, Any]): Data for the new project

        Returns:
            Any: Created project object
        """
        try:
            # Set default values
            project_data.setdefault('created_date', datetime.now())
            project_data.setdefault('type', ProjectType.CUSTOM)
            project_data.setdefault('skill_level', SkillLevel.BEGINNER)

            # Use repository to create project
            project = self._project_repository.create(project_data)
            return project
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise


# Create service implementation variant
ProjectServiceImpl = ProjectService