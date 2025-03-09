# database/repositories/project_component_repository.py
"""Repository for managing project component records."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func, select, delete
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.project_component import ProjectComponent
from database.models.project import Project
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class ProjectComponentRepository(BaseRepository[ProjectComponent]):
    """Repository for project component management operations."""

    def __init__(self, session: Session):
        """Initialize the ProjectComponent Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, ProjectComponent)
        self.logger = logging.getLogger(__name__)

    def get_by_project_id(self, project_id: int) -> List[ProjectComponent]:
        """Retrieve components for a specific project.

        Args:
            project_id: ID of the project to retrieve components for

        Returns:
            List of project components

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = select(ProjectComponent).filter(
                ProjectComponent.project_id == project_id
            ).options(joinedload(ProjectComponent.component))
            result = self.session.execute(query).scalars().all()
            return result
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting project components by project_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving project components: {str(e)}")

    def get_by_component_id(self, component_id: int) -> List[ProjectComponent]:
        """Retrieve projects using a specific component.

        Args:
            component_id: ID of the component

        Returns:
            List of project components using the specified component

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = select(ProjectComponent).filter(
                ProjectComponent.component_id == component_id
            ).options(joinedload(ProjectComponent.project))
            result = self.session.execute(query).scalars().all()
            return result
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting project components by component_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving project components: {str(e)}")

    def get_by_picking_list_item_id(self, picking_list_item_id: int) -> Optional[ProjectComponent]:
        """Retrieve a project component by its associated picking list item.

        Args:
            picking_list_item_id: ID of the picking list item

        Returns:
            ProjectComponent if found, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = select(ProjectComponent).filter(
                ProjectComponent.picking_list_item_id == picking_list_item_id
            )
            result = self.session.execute(query).scalar_one_or_none()
            return result
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting project component by picking_list_item_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving project component: {str(e)}")

    def add_component_to_project(self, project_id: int, component_id: int, quantity: int) -> ProjectComponent:
        """Add a component to a project.

        Args:
            project_id: ID of the project
            component_id: ID of the component to add
            quantity: Quantity of the component needed

        Returns:
            The created ProjectComponent relationship

        Raises:
            ModelNotFoundError: If the project or component is not found
            DatabaseError: If a database error occurs
        """
        try:
            # Check if project exists
            project = self.session.get(Project, project_id)
            if not project:
                raise ModelNotFoundError(f"Project with ID {project_id} not found")

            # Check if relationship already exists
            stmt = select(ProjectComponent).filter(
                ProjectComponent.project_id == project_id,
                ProjectComponent.component_id == component_id
            )
            existing = self.session.execute(stmt).scalar_one_or_none()

            if existing:
                existing.quantity = quantity
                self.session.commit()
                return existing

            # Create new relationship
            project_component = ProjectComponent(
                project_id=project_id,
                component_id=component_id,
                quantity=quantity
            )

            self.session.add(project_component)
            self.session.commit()
            return project_component
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error adding component to project: {str(e)}")
            raise DatabaseError(f"Database error adding component to project: {str(e)}")

    def remove_component_from_project(self, project_id: int, component_id: int) -> bool:
        """Remove a component from a project.

        Args:
            project_id: ID of the project
            component_id: ID of the component to remove

        Returns:
            True if the component was removed, False otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            stmt = delete(ProjectComponent).filter(
                ProjectComponent.project_id == project_id,
                ProjectComponent.component_id == component_id
            )
            result = self.session.execute(stmt)

            self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing component from project: {str(e)}")
            raise DatabaseError(f"Database error removing component from project: {str(e)}")

    def update_component_quantity(self, project_id: int, component_id: int, new_quantity: int) -> Optional[
        ProjectComponent]:
        """Update the quantity of a component in a project.

        Args:
            project_id: ID of the project
            component_id: ID of the component
            new_quantity: New quantity value

        Returns:
            Updated ProjectComponent if found, None otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            stmt = select(ProjectComponent).filter(
                ProjectComponent.project_id == project_id,
                ProjectComponent.component_id == component_id
            )
            project_component = self.session.execute(stmt).scalar_one_or_none()

            if not project_component:
                return None

            project_component.quantity = new_quantity
            self.session.commit()
            return project_component
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating project component quantity: {str(e)}")
            raise DatabaseError(f"Database error updating project component quantity: {str(e)}")

    def link_to_picking_list_item(self, project_component_id: int, picking_list_item_id: int) -> ProjectComponent:
        """Link a project component to a picking list item.

        Args:
            project_component_id: ID of the project component
            picking_list_item_id: ID of the picking list item

        Returns:
            Updated ProjectComponent

        Raises:
            ModelNotFoundError: If the project component is not found
            DatabaseError: If a database error occurs
        """
        try:
            project_component = self.get_by_id(project_component_id)
            if not project_component:
                raise ModelNotFoundError(f"Project component with ID {project_component_id} not found")

            project_component.picking_list_item_id = picking_list_item_id
            self.session.commit()
            return project_component
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error linking project component to picking list item: {str(e)}")
            raise DatabaseError(f"Database error linking project component to picking list item: {str(e)}")

    def get_total_components_by_project(self, project_id: int) -> int:
        """Get the total number of components used in a project.

        Args:
            project_id: ID of the project

        Returns:
            Total number of component types

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            stmt = select(func.count(ProjectComponent.id)).filter(
                ProjectComponent.project_id == project_id
            )
            result = self.session.execute(stmt).scalar_one_or_none()
            return int(result) if result else 0
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting project components: {str(e)}")
            raise DatabaseError(f"Database error counting project components: {str(e)}")

    def get_total_component_quantity_by_project(self, project_id: int) -> int:
        """Get the total quantity of all components used in a project.

        Args:
            project_id: ID of the project

        Returns:
            Total quantity of all components

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            stmt = select(func.sum(ProjectComponent.quantity)).filter(
                ProjectComponent.project_id == project_id
            )
            result = self.session.execute(stmt).scalar_one_or_none()
            return int(result) if result else 0
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating total component quantity: {str(e)}")
            raise DatabaseError(f"Database error calculating total component quantity: {str(e)}")