# store_management/database/repositories/pattern_repository.py
"""
Repository for managing project (pattern) related database operations.

Provides specialized methods for retrieving, creating, and managing
leatherworking projects with advanced querying capabilities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces import ProjectService
from models.project import Project, ProjectComponent, ProjectType, ProductionStatus

# Configure logging
logger = logging.getLogger(__name__)


class ProjectRepository:
    """
    Advanced repository for managing project-related database operations.

    Provides methods to interact with projects, including 
    retrieval, filtering, and advanced querying.
    """

    @inject(ProjectService)
    def __init__(self, session):
        """
        Initialize the ProjectRepository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_project_with_details(self, project_id: int) -> Optional[Project]:
        """
        Retrieve a project with all its associated components and relationships.

        Args:
            project_id (int): Unique identifier of the project

        Returns:
            Optional[Project]: Project instance with populated relationships
        """
        try:
            return (
                self.session.query(Project)
                .options(
                    joinedload(Project.components)
                    .joinedload(ProjectComponent.material),
                    joinedload(Project.components)
                    .joinedload(ProjectComponent.hardware)
                )
                .filter(Project.id == project_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving project details for ID {project_id}: {e}')
            raise

    def search_projects(
            self,
            search_params: Optional[Dict[str, Any]] = None,
            limit: int = 50
    ) -> List[Project]:
        """
        Advanced search for projects with multiple filtering options.

        Args:
            search_params (Optional[Dict[str, Any]], optional): Search and filter criteria
            limit (int, optional): Maximum number of results. Defaults to 50.

        Returns:
            List[Project]: List of Project instances matching the search criteria
        """
        try:
            # Start with base query
            query = self.session.query(Project)

            # Normalize search parameters
            search_params = search_params or {}
            conditions = []

            # Name search (case-insensitive partial match)
            if search_params.get('name'):
                conditions.append(Project.name.ilike(f"%{search_params['name']}%"))

            # Project type filtering
            if search_params.get('project_type'):
                try:
                    project_type = ProjectType(search_params['project_type'])
                    conditions.append(Project.project_type == project_type)
                except ValueError:
                    logger.warning(f"Invalid project type: {search_params['project_type']}")

            # Skill level filtering
            if search_params.get('skill_level'):
                try:
                    skill_level = SkillLevel(search_params['skill_level'])
                    conditions.append(Project.skill_level == skill_level)
                except ValueError:
                    logger.warning(f"Invalid skill level: {search_params['skill_level']}")

            # Status filtering
            if search_params.get('status'):
                try:
                    status = ProductionStatus(search_params['status'])
                    conditions.append(Project.status == status)
                except ValueError:
                    logger.warning(f"Invalid project status: {search_params['status']}")

            # Date range filtering
            if search_params.get('start_date') and search_params.get('end_date'):
                conditions.append(
                    Project.created_at.between(
                        search_params['start_date'],
                        search_params['end_date']
                    )
                )

            # Complexity filtering
            if search_params.get('min_complexity'):
                conditions.append(
                    Project.complexity >= float(search_params['min_complexity'])
                )

            # Apply conditions if any exist
            if conditions:
                query = query.filter(and_(*conditions))

            # Optionally include components
            if search_params.get('include_components', False):
                query = query.options(
                    joinedload(Project.components)
                    .joinedload(ProjectComponent.material),
                    joinedload(Project.components)
                    .joinedload(ProjectComponent.hardware)
                )

            # Order and limit results
            query = query.order_by(Project.created_at.desc()).limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error searching projects: {e}')
            raise

    def get_project_material_usage(self, project_id: int) -> Dict[str, Any]:
        """
        Analyze material usage for a specific project.

        Args:
            project_id (int): Unique identifier of the project

        Returns:
            Dict[str, Any]: Dictionary containing material usage metrics
        """
        try:
            # Aggregate material usage details
            material_usage = (
                self.session.query(
                    ProjectComponent.material_id,
                    Material.name.label('material_name'),
                    func.sum(ProjectComponent.material_quantity).label('total_used'),
                    func.avg(ProjectComponent.material_efficiency).label('avg_efficiency')
                )
                .join(Material, ProjectComponent.material_id == Material.id)
                .filter(ProjectComponent.project_id == project_id)
                .group_by(ProjectComponent.material_id, Material.name)
                .all()
            )

            # Transform results into a more readable format
            usage_details = [
                {
                    'material_id': usage.material_id,
                    'material_name': usage.material_name,
                    'total_used': float(usage.total_used),
                    'avg_efficiency': float(usage.avg_efficiency)
                }
                for usage in material_usage
            ]

            return {
                'project_id': project_id,
                'material_usage': usage_details,
                'total_materials_used': len(usage_details)
            }
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving project material usage: {e}')
            raise

    def create(self, project_data: Dict[str, Any]) -> Project:
        """
        Create a new project with associated components.

        Args:
            project_data (Dict[str, Any]): Project creation data

        Returns:
            Project: Created Project instance

        Raises:
            ValueError: If project validation fails
        """
        try:
            # Validate project components
            if 'components' not in project_data or not project_data['components']:
                raise ValueError('Project must have at least one component')

            # Separate components from project data
            components_data = project_data.pop('components', [])

            # Create project instance
            project = Project(**project_data)

            # Calculate project complexity
            project.calculate_complexity()

            # Add project to session
            self.session.add(project)

            # Add project components
            for component_data in components_data:
                component = ProjectComponent(**component_data)
                component.project = project
                self.session.add(component)

            # Commit transaction
            self.session.commit()

            return project
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error creating project: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error creating project: {e}')
            raise

    def update(self, project_id: int, project_data: Dict[str, Any]) -> Project:
        """
        Update an existing project with new information.

        Args:
            project_id (int): ID of the project to update
            project_data (Dict[str, Any]): Updated project data

        Returns:
            Project: Updated Project instance

        Raises:
            ValueError: If project validation fails
        """
        try:
            # Retrieve existing project
            existing_project = self.get_project_with_details(project_id)

            if not existing_project:
                raise ValueError(f'Project with ID {project_id} not found')

            # Validate project components
            if 'components' not in project_data or not project_data['components']:
                raise ValueError('Project must have at least one component')

            # Separate components from project data
            components_data = project_data.pop('components', [])

            # Update project attributes
            for key, value in project_data.items():
                if hasattr(existing_project, key):
                    setattr(existing_project, key, value)

            # Recalculate project complexity
            existing_project.calculate_complexity()

            # Clear existing components
            existing_project.components.clear()

            # Add new components
            for component_data in components_data:
                component = ProjectComponent(**component_data)
                component.project = existing_project
                self.session.add(component)

            # Commit transaction
            self.session.commit()

            return existing_project
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error updating project: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error updating project: {e}')
            raise