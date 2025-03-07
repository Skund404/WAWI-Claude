# database/repositories/component_repository.py
"""Repository for managing component records."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.enums import ComponentType
from database.models.components import Component, ComponentMaterial, ComponentLeather, ComponentHardware, ComponentTool
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class ComponentRepository(BaseRepository[Component]):
    """Repository for component management operations."""

    def __init__(self, session: Session):
        """Initialize the Component Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Component)
        self.logger = logging.getLogger(__name__)

    def get_by_name(self, name: str) -> List[Component]:
        """Retrieve components by name.

        Args:
            name: Component name to search for

        Returns:
            List of matching components

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(Component).filter(
                Component.name.ilike(f"%{name}%")
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components by name: {str(e)}")
            raise DatabaseError(f"Database error retrieving components: {str(e)}")

    def get_by_type(self, component_type: ComponentType) -> List[Component]:
        """Retrieve components by component type.

        Args:
            component_type: Component type to filter by

        Returns:
            List of components with the specified type

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(Component).filter(
                Component.type == component_type
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components by type: {str(e)}")
            raise DatabaseError(f"Database error retrieving components by type: {str(e)}")

    def get_with_materials(self) -> List[Component]:
        """Retrieve components with their associated materials.

        Returns:
            List of components with material relationships loaded

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(Component).options(
                joinedload(Component.materials)
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components with materials: {str(e)}")
            raise DatabaseError(f"Database error retrieving components with materials: {str(e)}")

    def get_with_leathers(self) -> List[Component]:
        """Retrieve components with their associated leathers.

        Returns:
            List of components with leather relationships loaded

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(Component).options(
                joinedload(Component.leathers)
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components with leathers: {str(e)}")
            raise DatabaseError(f"Database error retrieving components with leathers: {str(e)}")

    def get_with_hardware(self) -> List[Component]:
        """Retrieve components with their associated hardware.

        Returns:
            List of components with hardware relationships loaded

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(Component).options(
                joinedload(Component.hardware)
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components with hardware: {str(e)}")
            raise DatabaseError(f"Database error retrieving components with hardware: {str(e)}")

    def get_with_tools(self) -> List[Component]:
        """Retrieve components with their associated tools.

        Returns:
            List of components with tool relationships loaded

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(Component).options(
                joinedload(Component.tools)
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting components with tools: {str(e)}")
            raise DatabaseError(f"Database error retrieving components with tools: {str(e)}")

    def get_complete_components(self) -> List[Component]:
        """Retrieve components with all their associated resources loaded.

        Returns:
            List of components with all relationships loaded

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(Component).options(
                joinedload(Component.materials),
                joinedload(Component.leathers),
                joinedload(Component.hardware),
                joinedload(Component.tools)
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting complete components: {str(e)}")
            raise DatabaseError(f"Database error retrieving complete components: {str(e)}")

    def add_material_to_component(self, component_id: int, material_id: int, quantity: float) -> ComponentMaterial:
        """Add a material to a component.

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
            component = self.get_by_id(component_id)
            if not component:
                raise ModelNotFoundError(f"Component with ID {component_id} not found")

            # Check if relationship already exists
            existing = self.session.query(ComponentMaterial).filter(
                ComponentMaterial.component_id == component_id,
                ComponentMaterial.material_id == material_id
            ).first()

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

    def add_leather_to_component(self, component_id: int, leather_id: int, quantity: float) -> ComponentLeather:
        """Add a leather to a component.

        Args:
            component_id: ID of the component
            leather_id: ID of the leather to add
            quantity: Quantity of the leather needed

        Returns:
            The created ComponentLeather relationship

        Raises:
            ModelNotFoundError: If the component is not found
            DatabaseError: If a database error occurs
        """
        try:
            component = self.get_by_id(component_id)
            if not component:
                raise ModelNotFoundError(f"Component with ID {component_id} not found")

            # Check if relationship already exists
            existing = self.session.query(ComponentLeather).filter(
                ComponentLeather.component_id == component_id,
                ComponentLeather.leather_id == leather_id
            ).first()

            if existing:
                existing.quantity = quantity
                self.session.commit()
                return existing

            # Create new relationship
            component_leather = ComponentLeather(
                component_id=component_id,
                leather_id=leather_id,
                quantity=quantity
            )

            self.session.add(component_leather)
            self.session.commit()
            return component_leather
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error adding leather to component: {str(e)}")
            raise DatabaseError(f"Database error adding leather to component: {str(e)}")

    def add_hardware_to_component(self, component_id: int, hardware_id: int, quantity: int) -> ComponentHardware:
        """Add hardware to a component.

        Args:
            component_id: ID of the component
            hardware_id: ID of the hardware to add
            quantity: Quantity of the hardware needed

        Returns:
            The created ComponentHardware relationship

        Raises:
            ModelNotFoundError: If the component is not found
            DatabaseError: If a database error occurs
        """
        try:
            component = self.get_by_id(component_id)
            if not component:
                raise ModelNotFoundError(f"Component with ID {component_id} not found")

            # Check if relationship already exists
            existing = self.session.query(ComponentHardware).filter(
                ComponentHardware.component_id == component_id,
                ComponentHardware.hardware_id == hardware_id
            ).first()

            if existing:
                existing.quantity = quantity
                self.session.commit()
                return existing

            # Create new relationship
            component_hardware = ComponentHardware(
                component_id=component_id,
                hardware_id=hardware_id,
                quantity=quantity
            )

            self.session.add(component_hardware)
            self.session.commit()
            return component_hardware
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error adding hardware to component: {str(e)}")
            raise DatabaseError(f"Database error adding hardware to component: {str(e)}")

    def add_tool_to_component(self, component_id: int, tool_id: int) -> ComponentTool:
        """Add a tool to a component.

        Args:
            component_id: ID of the component
            tool_id: ID of the tool to add

        Returns:
            The created ComponentTool relationship

        Raises:
            ModelNotFoundError: If the component is not found
            DatabaseError: If a database error occurs
        """
        try:
            component = self.get_by_id(component_id)
            if not component:
                raise ModelNotFoundError(f"Component with ID {component_id} not found")

            # Check if relationship already exists
            existing = self.session.query(ComponentTool).filter(
                ComponentTool.component_id == component_id,
                ComponentTool.tool_id == tool_id
            ).first()

            if existing:
                return existing

            # Create new relationship
            component_tool = ComponentTool(
                component_id=component_id,
                tool_id=tool_id
            )

            self.session.add(component_tool)
            self.session.commit()
            return component_tool
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error adding tool to component: {str(e)}")
            raise DatabaseError(f"Database error adding tool to component: {str(e)}")

    def remove_material_from_component(self, component_id: int, material_id: int) -> bool:
        """Remove a material from a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to remove

        Returns:
            True if the material was removed, False otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(ComponentMaterial).filter(
                ComponentMaterial.component_id == component_id,
                ComponentMaterial.material_id == material_id
            ).delete()

            self.session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing material from component: {str(e)}")
            raise DatabaseError(f"Database error removing material from component: {str(e)}")

    def remove_leather_from_component(self, component_id: int, leather_id: int) -> bool:
        """Remove a leather from a component.

        Args:
            component_id: ID of the component
            leather_id: ID of the leather to remove

        Returns:
            True if the leather was removed, False otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(ComponentLeather).filter(
                ComponentLeather.component_id == component_id,
                ComponentLeather.leather_id == leather_id
            ).delete()

            self.session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing leather from component: {str(e)}")
            raise DatabaseError(f"Database error removing leather from component: {str(e)}")

    def remove_hardware_from_component(self, component_id: int, hardware_id: int) -> bool:
        """Remove hardware from a component.

        Args:
            component_id: ID of the component
            hardware_id: ID of the hardware to remove

        Returns:
            True if the hardware was removed, False otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(ComponentHardware).filter(
                ComponentHardware.component_id == component_id,
                ComponentHardware.hardware_id == hardware_id
            ).delete()

            self.session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing hardware from component: {str(e)}")
            raise DatabaseError(f"Database error removing hardware from component: {str(e)}")

    def remove_tool_from_component(self, component_id: int, tool_id: int) -> bool:
        """Remove a tool from a component.

        Args:
            component_id: ID of the component
            tool_id: ID of the tool to remove

        Returns:
            True if the tool was removed, False otherwise

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(ComponentTool).filter(
                ComponentTool.component_id == component_id,
                ComponentTool.tool_id == tool_id
            ).delete()

            self.session.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing tool from component: {str(e)}")
            raise DatabaseError(f"Database error removing tool from component: {str(e)}")