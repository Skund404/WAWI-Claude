# database/repositories/component_repository.py
"""Repository for managing component records."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.component import Component
from database.models.component_material import ComponentMaterial
from database.models.enums import ComponentType
from database.models.material import Material, Leather, Hardware
from database.models.tool import Tool

from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class ComponentRepository(BaseRepository[Component]):
    """Repository for component management operations."""

    def __init__(self, session: Session):
        """
        Initialize the Component Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Component)
        self.logger = logging.getLogger(__name__)

    def get_by_name(self, name: str) -> List[Component]:
        """
        Retrieve components by name.

        Args:
            name: Component name to search for

        Returns:
            List of matching components

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            statement = select(Component).where(
                Component.name.ilike(f"%{name}%")
            )
            result = self.session.execute(statement).scalars().all()
            return list(result)
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components by name: {str(e)}")
            raise DatabaseError(f"Database error retrieving components: {str(e)}")

    def get_by_type(self, component_type: ComponentType) -> List[Component]:
        """
        Retrieve components by component type.

        Args:
            component_type: Component type to filter by

        Returns:
            List of components with the specified type

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            statement = select(Component).where(
                Component.component_type == component_type
            )
            result = self.session.execute(statement).scalars().all()
            return list(result)
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components by type: {str(e)}")
            raise DatabaseError(f"Database error retrieving components by type: {str(e)}")

    def get_with_materials(self) -> List[Component]:
        """
        Retrieve components with their associated materials.

        Returns:
            List of components with material relationships loaded

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            statement = select(Component).options(
                joinedload(Component.component_materials)
            )
            result = self.session.execute(statement).scalars().unique().all()
            return list(result)
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components with materials: {str(e)}")
            raise DatabaseError(f"Database error retrieving components with materials: {str(e)}")

    def add_material_to_component(self, component_id: int, material_id: int, quantity: float) -> ComponentMaterial:
        """
        Add a material to a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to add
            quantity: Quantity of the material needed

        Returns:
            The created ComponentMaterial relationship

        Raises:
            ModelNotFoundError: If the component is not found
            DatabaseError: If a database error occurs
        """
        try:
            # Verify component exists
            component = self.get_by_id(component_id)
            if not component:
                raise ModelNotFoundError(f"Component with ID {component_id} not found")

            # Verify material exists
            material = self.session.get(Material, material_id)
            if not material:
                raise ModelNotFoundError(f"Material with ID {material_id} not found")

            # Check for existing relationship
            existing = self.session.execute(
                select(ComponentMaterial).where(
                    ComponentMaterial.component_id == component_id,
                    ComponentMaterial.material_id == material_id
                )
            ).scalar_one_or_none()

            if existing:
                existing.quantity = quantity
                self.session.commit()
                return existing

            # Create new relationship
            component_material = ComponentMaterial(
                component_id=component_id,
                material_id=material_id,
                quantity=quantity
            )

            self.session.add(component_material)
            self.session.commit()
            return component_material

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error adding material to component: {str(e)}")
            raise DatabaseError(f"Database error adding material to component: {str(e)}")

    def remove_material_from_component(self, component_id: int, material_id: int) -> bool:
        """
        Remove a material from a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to remove

        Returns:
            True if the material was removed, False otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Delete the specific component-material relationship
            result = self.session.execute(
                select(ComponentMaterial).where(
                    ComponentMaterial.component_id == component_id,
                    ComponentMaterial.material_id == material_id
                ).delete()
            )

            self.session.commit()
            return result.rowcount > 0

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing material from component: {str(e)}")
            raise DatabaseError(f"Database error removing material from component: {str(e)}")

    def get_component_materials(self, component_id: int) -> List[ComponentMaterial]:
        """
        Retrieve all materials associated with a specific component.

        Args:
            component_id: ID of the component

        Returns:
            List of ComponentMaterial relationships

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            statement = select(ComponentMaterial).where(
                ComponentMaterial.component_id == component_id
            ).options(
                joinedload(ComponentMaterial.material)
            )

            result = self.session.execute(statement).scalars().all()
            return list(result)

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving component materials: {str(e)}")
            raise DatabaseError(f"Database error retrieving component materials: {str(e)}")

    def search_components(
            self,
            name: Optional[str] = None,
            component_type: Optional[ComponentType] = None,
            min_weight: Optional[float] = None,
            max_weight: Optional[float] = None
    ) -> List[Component]:
        """
        Advanced search for components with multiple optional filters.

        Args:
            name: Partial name match
            component_type: Specific component type
            min_weight: Minimum component weight
            max_weight: Maximum component weight

        Returns:
            List of components matching the search criteria

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Start with base query
            statement = select(Component)

            # Apply filters
            filters = []
            if name:
                filters.append(Component.name.ilike(f"%{name}%"))

            if component_type:
                filters.append(Component.component_type == component_type)

            # Add filters to query if they exist
            if filters:
                statement = statement.where(and_(*filters))

            # Execute query
            result = self.session.execute(statement).scalars().all()
            return list(result)

        except SQLAlchemyError as e:
            self.logger.error(f"Error searching components: {str(e)}")
            raise DatabaseError(f"Database error searching components: {str(e)}")