"""
database/repositories/project_component_repository.py

Repository for managing project component relationships in the Leatherworking ERP System.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from database.models.project_component import ProjectComponent
from database.models.project import Project
from database.models.component import Component
from database.repositories.base_repository import (
    BaseRepository,
    EntityNotFoundError,
    ValidationError,
    RepositoryError
)


class ProjectComponentRepository(BaseRepository[ProjectComponent]):
    """
    Repository for handling project component operations with advanced querying capabilities.
    """

    def __init__(self, session: Session):
        """
        Initialize the project component repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_model_class(self):
        """
        Get the model class for this repository.

        Returns:
            ProjectComponent model class
        """
        return ProjectComponent

    def get_by_project(self, project_id: int) -> List[ProjectComponent]:
        """
        Retrieve all project components for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of project components with joined component and project details
        """
        try:
            # Verify project exists
            project = self.session.query(Project).filter_by(id=project_id).first()
            if not project:
                raise EntityNotFoundError(f"Project with ID {project_id} not found")

            # Retrieve project components with eager loading of related entities
            return (self.session.query(ProjectComponent)
                    .filter_by(project_id=project_id)
                    .options(joinedload(ProjectComponent.component))
                    .all())
        except Exception as e:
            self.logger.error(f"Error retrieving project components for project {project_id}: {str(e)}")
            raise RepositoryError(f"Failed to retrieve project components: {str(e)}")

    def get_by_component(self, component_id: int) -> List[ProjectComponent]:
        """
        Retrieve all project components for a specific component.

        Args:
            component_id: ID of the component

        Returns:
            List of project components with joined component and project details
        """
        try:
            # Verify component exists
            component = self.session.query(Component).filter_by(id=component_id).first()
            if not component:
                raise EntityNotFoundError(f"Component with ID {component_id} not found")

            # Retrieve project components with eager loading of related entities
            return (self.session.query(ProjectComponent)
                    .filter_by(component_id=component_id)
                    .options(joinedload(ProjectComponent.project))
                    .all())
        except Exception as e:
            self.logger.error(f"Error retrieving project components for component {component_id}: {str(e)}")
            raise RepositoryError(f"Failed to retrieve project components: {str(e)}")

    def add_component_to_project(
            self,
            project_id: int,
            component_id: int,
            quantity: float = 1.0,
            notes: Optional[str] = None
    ) -> ProjectComponent:
        """
        Add a component to a project with optional quantity and notes.

        Args:
            project_id: ID of the project
            component_id: ID of the component
            quantity: Quantity of the component (default 1.0)
            notes: Optional notes about the component's usage

        Returns:
            Created project component relationship
        """
        try:
            # Verify project exists
            project = self.session.query(Project).filter_by(id=project_id).first()
            if not project:
                raise EntityNotFoundError(f"Project with ID {project_id} not found")

            # Verify component exists
            component = self.session.query(Component).filter_by(id=component_id).first()
            if not component:
                raise EntityNotFoundError(f"Component with ID {component_id} not found")

            # Check for existing project component relationship
            existing = self.session.query(ProjectComponent).filter_by(
                project_id=project_id,
                component_id=component_id
            ).first()

            if existing:
                # Update existing relationship
                existing.quantity = quantity
                existing.notes = notes
                existing.updated_at = datetime.now()
                self.session.flush()
                return existing

            # Create new project component relationship
            project_component = ProjectComponent(
                project_id=project_id,
                component_id=component_id,
                quantity=quantity,
                notes=notes,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            self.session.add(project_component)
            self.session.flush()

            return project_component

        except (EntityNotFoundError, ValidationError):
            self.session.rollback()
            raise
        except Exception as e:
            self.logger.error(
                f"Error adding component {component_id} to project {project_id}: {str(e)}"
            )
            self.session.rollback()
            raise RepositoryError(f"Failed to add component to project: {str(e)}")

    def remove_component_from_project(
            self,
            project_id: int,
            component_id: int
    ) -> bool:
        """
        Remove a component from a project.

        Args:
            project_id: ID of the project
            component_id: ID of the component

        Returns:
            True if removal was successful
        """
        try:
            # Find the specific project component relationship
            project_component = (self.session.query(ProjectComponent)
                                 .filter_by(
                project_id=project_id,
                component_id=component_id
            ).first())

            if not project_component:
                raise EntityNotFoundError(
                    f"Project component relationship not found for project {project_id} "
                    f"and component {component_id}"
                )

            # Delete the relationship
            self.session.delete(project_component)
            self.session.flush()

            return True

        except EntityNotFoundError:
            self.session.rollback()
            raise
        except Exception as e:
            self.logger.error(
                f"Error removing component {component_id} from project {project_id}: {str(e)}"
            )
            self.session.rollback()
            raise RepositoryError(f"Failed to remove component from project: {str(e)}")

    def filter_project_components(
            self,
            project_id: Optional[int] = None,
            component_id: Optional[int] = None,
            min_quantity: Optional[float] = None,
            max_quantity: Optional[float] = None,
            sort_by: str = 'quantity',
            sort_dir: str = 'desc',
            skip: int = 0,
            limit: int = 100
    ) -> List[ProjectComponent]:
        """
        Advanced filtering for project components with pagination and sorting.

        Args:
            project_id: Optional project ID filter
            component_id: Optional component ID filter
            min_quantity: Optional minimum quantity filter
            max_quantity: Optional maximum quantity filter
            sort_by: Field to sort by (default 'quantity')
            sort_dir: Sort direction (default 'desc')
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return

        Returns:
            List of filtered and sorted project components
        """
        try:
            # Build query with multiple optional filters
            query = self.session.query(ProjectComponent)

            # Apply filters
            filter_conditions = []
            if project_id is not None:
                filter_conditions.append(ProjectComponent.project_id == project_id)
            if component_id is not None:
                filter_conditions.append(ProjectComponent.component_id == component_id)
            if min_quantity is not None:
                filter_conditions.append(ProjectComponent.quantity >= min_quantity)
            if max_quantity is not None:
                filter_conditions.append(ProjectComponent.quantity <= max_quantity)

            # Apply combined filters
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

            # Apply sorting
            sort_column = getattr(ProjectComponent, sort_by, ProjectComponent.quantity)
            query = (query.order_by(sort_column.desc() if sort_dir == 'desc' else sort_column.asc())
                     .offset(skip)
                     .limit(limit))

            return query.all()

        except Exception as e:
            self.logger.error(f"Error filtering project components: {str(e)}")
            raise RepositoryError(f"Failed to filter project components: {str(e)}")

    def get_component_project_summary(self, component_id: int) -> Dict[str, Any]:
        """
        Get a summary of projects using a specific component.

        Args:
            component_id: ID of the component

        Returns:
            Dictionary with component project usage summary
        """
        try:
            # Verify component exists
            component = self.session.query(Component).filter_by(id=component_id).first()
            if not component:
                raise EntityNotFoundError(f"Component with ID {component_id} not found")

            # Query project component relationships
            project_components = (self.session.query(ProjectComponent)
                                  .filter_by(component_id=component_id)
                                  .options(joinedload(ProjectComponent.project))
                                  .all())

            return {
                'component_id': component_id,
                'component_name': component.name,
                'total_projects': len(project_components),
                'total_quantity_used': sum(pc.quantity for pc in project_components),
                'projects': [
                    {
                        'project_id': pc.project.id,
                        'project_name': pc.project.name,
                        'quantity': pc.quantity,
                        'created_at': pc.created_at
                    } for pc in project_components
                ]
            }

        except Exception as e:
            self.logger.error(f"Error getting component project summary for {component_id}: {str(e)}")
            raise RepositoryError(f"Failed to get component project summary: {str(e)}")