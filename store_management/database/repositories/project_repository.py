# project_repository.py
# Relative path: project_repository.py

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from models.project import Project, ProjectComponent, ProjectType, SkillLevel, ProductionStatus, Material
from exceptions import DatabaseError, ValidationError

import logging

logger = logging.getLogger(__name__)


class ProjectRepository:
    """
    Advanced repository for managing project-related database operations.

    Provides specialized methods for retrieving, creating, and managing
    leatherworking projects with complex querying capabilities.

    Attributes:
        session (Session): SQLAlchemy database session for database interactions
    """

    @inject(MaterialService)
    def __init__(self, session: Session):
        """
        Initialize the ProjectRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self.session = session
        super().__init__(session, Project)

    def get_project_with_details(self, project_id: int) -> Optional[Project]:
        """
        Retrieve a project with all its associated components and relationships.

        Args:
            project_id (int): Unique identifier of the project

        Returns:
            Project instance with populated relationships, or None if not found

        Raises:
            DatabaseError: If there's an error retrieving project details
        """
        try:
            return (
                self.session.query(Project)
                .options(
                    joinedload(Project.components).joinedload(ProjectComponent.material),
                    joinedload(Project.components).joinedload(ProjectComponent.hardware)
                )
                .filter(Project.id == project_id)
                .first()
            )
        except Exception as e:
            logger.error(f'Error retrieving project details: {str(e)}')
            raise DatabaseError(f'Error retrieving project details: {str(e)}') from e

    def search_projects(
            self,
            search_params: Dict[str, Any] = None,
            limit: int = 50
    ) -> List[Project]:
        """
        Advanced search for projects with multiple filtering options.

        Args:
            search_params (Dict[str, Any], optional): Search and filter criteria
            limit (int, optional): Maximum number of results. Defaults to 50.

        Returns:
            List of Project instances matching the search criteria

        Raises:
            ValidationError: For invalid search parameters
            DatabaseError: For database-related errors
        """
        try:
            query = self.session.query(Project)
            search_params = search_params or {}
            conditions = []

            # Name search
            if search_params.get('name'):
                conditions.append(
                    func.lower(Project.name).like(
                        f"%{search_params['name'].lower()}%"
                    )
                )

            # Project Type filtering
            if search_params.get('project_type'):
                try:
                    project_type = ProjectType(search_params['project_type'])
                    conditions.append(Project.project_type == project_type)
                except ValueError:
                    raise ValidationError(
                        f"Invalid project type: {search_params['project_type']}"
                    )

            # Skill Level filtering
            if search_params.get('skill_level'):
                try:
                    skill_level = SkillLevel(search_params['skill_level'])
                    conditions.append(Project.skill_level == skill_level)
                except ValueError:
                    raise ValidationError(
                        f"Invalid skill level: {search_params['skill_level']}"
                    )

            # Status filtering
            if search_params.get('status'):
                try:
                    status = ProductionStatus(search_params['status'])
                    conditions.append(Project.status == status)
                except ValueError:
                    raise ValidationError(
                        f"Invalid project status: {search_params['status']}"
                    )

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

            # Apply conditions
            if conditions:
                query = query.filter(and_(*conditions))

            # Include components if requested
            if search_params.get('include_components', False):
                query = query.options(
                    joinedload(Project.components).joinedload(ProjectComponent.material),
                    joinedload(Project.components).joinedload(ProjectComponent.hardware)
                )

            # Order and limit results
            query = query.order_by(Project.created_at.desc()).limit(limit)

            return query.all()

        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f'Error searching projects: {str(e)}')
            raise DatabaseError(f'Error searching projects: {str(e)}') from e

    def get_project_material_usage(self, project_id: int) -> Dict[str, Any]:
        """
        Analyze material usage for a specific project.

        Args:
            project_id (int): Unique identifier of the project

        Returns:
            Dictionary containing material usage metrics

        Raises:
            DatabaseError: If there's an error retrieving material usage
        """
        try:
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
        except Exception as e:
            logger.error(f'Error retrieving project material usage: {str(e)}')
            raise DatabaseError(f'Error retrieving project material usage: {str(e)}') from e

    def generate_project_complexity_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive project complexity report.

        Returns:
            Dictionary containing project complexity metrics

        Raises:
            DatabaseError: If there's an error generating the report
        """
        try:
            # Complexity metrics
            complexity_metrics = (
                self.session.query(
                    func.count(Project.id).label('total_projects'),
                    func.avg(Project.complexity).label('avg_complexity'),
                    func.max(Project.complexity).label('max_complexity'),
                    func.min(Project.complexity).label('min_complexity'),
                    func.percentile_cont(0.5).within_group(Project.complexity).label('complexity_distribution')
                )
                .first()
            )

            # Type distribution
            type_distribution = (
                self.session.query(
                    Project.project_type,
                    func.count(Project.id).label('project_count'),
                    func.avg(Project.complexity).label('avg_complexity')
                )
                .group_by(Project.project_type)
                .all()
            )

            type_metrics = [
                {
                    'project_type': metric.project_type,
                    'project_count': metric.project_count,
                    'avg_complexity': float(metric.avg_complexity)
                }
                for metric in type_distribution
            ]

            return {
                'total_projects': complexity_metrics.total_projects,
                'average_complexity': float(complexity_metrics.avg_complexity),
                'max_complexity': float(complexity_metrics.max_complexity),
                'min_complexity': float(complexity_metrics.min_complexity),
                'complexity_median': float(complexity_metrics.complexity_distribution),
                'complexity_by_type': type_metrics
            }
        except Exception as e:
            logger.error(f'Error generating project complexity report: {str(e)}')
            raise DatabaseError(f'Error generating project complexity report: {str(e)}') from e

    def create(self, project: Project) -> Project:
        """
        Create a new project with associated components.

        Args:
            project (Project): Project instance to create

        Returns:
            Created Project instance

        Raises:
            ValidationError: If project creation fails validation
            DatabaseError: For database-related errors
        """
        try:
            # Validate project components
            if not project.components:
                raise ValidationError('Project must have at least one component')

            # Calculate project complexity
            project.calculate_complexity()

            # Add project to session
            self.session.add(project)

            # Add project components
            for component in project.components:
                component.project_id = project.id
                self.session.add(component)

            # Commit transaction
            self.session.commit()
            return project

        except (ValidationError, DatabaseError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f'Error creating project: {str(e)}')
            raise DatabaseError(f'Error creating project: {str(e)}') from e

    def update(self, project_id: int, project: Project) -> Project:
        """
        Update an existing project with new information.

        Args:
            project_id (int): ID of the project to update
            project (Project): Updated Project instance

        Returns:
            Updated Project instance

        Raises:
            ValidationError: If project update fails validation
            DatabaseError: For database-related errors
        """
        try:
            # Retrieve existing project
            existing_project = self.get(project_id)
            if not existing_project:
                raise ValidationError(f'Project with ID {project_id} not found')

            # Validate project components
            if not project.components:
                raise ValidationError('Project must have at least one component')

            # Calculate new project complexity
            project.calculate_complexity()

            # Update project attributes
            for key, value in project.__dict__.items():
                if not key.startswith('_') and key != 'id':
                    setattr(existing_project, key, value)

            # Clear and update components
            existing_project.components.clear()
            for component in project.components:
                component.project_id = existing_project.id
                self.session.add(component)

            # Commit transaction
            self.session.commit()
            return existing_project

        except (ValidationError, DatabaseError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f'Error updating project: {str(e)}')
            raise DatabaseError(f'Error updating project: {str(e)}') from e