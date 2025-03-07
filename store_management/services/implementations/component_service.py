# services/implementations/component_service.py
import logging
from typing import Any, Dict, List, Optional

from database.models.components import Component, ComponentMaterial
from database.models.enums import ComponentType
from database.models.material import Material

from database.repositories.component_repository import ComponentRepository
from database.repositories.material_repository import MaterialRepository

from database.sqlalchemy.session import get_db_session
from di.core import inject

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.component_service import IComponentService

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


class ComponentService(BaseService[Component], IComponentService):
    """
    Concrete implementation of the Component Service interface.
    Manages component-related operations in the leatherworking application.
    """

    @inject
    def __init__(
            self,
            session: Session = None,
            component_repository: ComponentRepository = None,
            material_repository: MaterialRepository = None
    ):
        """
        Initialize the Component Service with repositories.

        Args:
            session: SQLAlchemy database session
            component_repository: Repository for component data access
            material_repository: Repository for material data access
        """
        self.session = session or get_db_session()
        self.component_repository = component_repository or ComponentRepository(self.session)
        self.material_repository = material_repository or MaterialRepository(self.session)

        super().__init__(self.component_repository)

    def create_component(
            self,
            name: str,
            description: Optional[str] = None,
            component_type: Optional[ComponentType] = None,
            attributes: Optional[Dict[str, Any]] = None
    ) -> Component:
        """
        Create a new component with specified details.

        Args:
            name: Name of the component
            description: Optional description of the component
            component_type: Type of the component
            attributes: Optional JSON-compatible attributes for the component

        Returns:
            The created Component instance

        Raises:
            ValidationError: If component creation fails
        """
        try:
            component = Component(
                name=name,
                description=description,
                component_type=component_type,
                attributes=attributes
            )

            return self.component_repository.create(component)

        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Error creating component: {e}")
            raise ValidationError(str(e))

    def get_component_by_id(self, component_id: int) -> Optional[Component]:
        """
        Retrieve a component by its unique identifier.

        Args:
            component_id: Unique identifier of the component

        Returns:
            Component instance or None if not found
        """
        return self.component_repository.get_by_id(component_id)

    def update_component(
            self,
            component_id: int,
            updates: Dict[str, Any]
    ) -> Optional[Component]:
        """
        Update an existing component's details.

        Args:
            component_id: Unique identifier of the component
            updates: Dictionary of attributes to update

        Returns:
            Updated Component instance or None if update failed

        Raises:
            NotFoundError: If component is not found
            ValidationError: If update fails
        """
        try:
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            for key, value in updates.items():
                setattr(component, key, value)

            return self.component_repository.update(component)

        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Error updating component: {e}")
            raise ValidationError(str(e))

    def delete_component(self, component_id: int) -> bool:
        """
        Delete a component by its unique identifier.

        Args:
            component_id: Unique identifier of the component

        Returns:
            Boolean indicating successful deletion

        Raises:
            NotFoundError: If component is not found
            ValidationError: If deletion fails
        """
        try:
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            self.component_repository.delete(component)
            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Error deleting component: {e}")
            raise ValidationError(str(e))

    def list_components(
            self,
            component_type: Optional[ComponentType] = None,
            **filters
    ) -> List[Component]:
        """
        List components with optional filtering.

        Args:
            component_type: Optional filter by component type
            **filters: Additional optional filters

        Returns:
            List of matching Component instances
        """
        return self.component_repository.list_components(
            component_type=component_type,
            **filters
        )

    def associate_materials(
            self,
            component_id: int,
            material_ids: List[int],
            quantities: Optional[List[float]] = None
    ) -> bool:
        """
        Associate materials with a component.

        Args:
            component_id: ID of the component
            material_ids: List of material IDs to associate
            quantities: Optional list of quantities corresponding to materials

        Returns:
            Boolean indicating successful association

        Raises:
            NotFoundError: If component or materials are not found
            ValidationError: If association fails
        """
        try:
            # Verify component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Validate materials
            for material_id in material_ids:
                material = self.material_repository.get_by_id(material_id)
                if not material:
                    raise NotFoundError(f"Material with ID {material_id} not found")

            # Create material associations
            component_materials = []
            for i, material_id in enumerate(material_ids):
                quantity = quantities[i] if quantities and i < len(quantities) else None
                component_material = ComponentMaterial(
                    component_id=component_id,
                    material_id=material_id,
                    quantity=quantity
                )
                component_materials.append(component_material)

            # Bulk create associations
            self.session.add_all(component_materials)
            self.session.commit()

            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"Error associating materials with component: {e}")
            raise ValidationError(str(e))

    def get_component_materials(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve materials associated with a specific component.

        Args:
            component_id: ID of the component

        Returns:
            List of dictionaries containing material details

        Raises:
            NotFoundError: If component is not found
        """
        try:
            # Verify component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Retrieve associated materials
            component_materials = self.session.query(ComponentMaterial).filter(
                ComponentMaterial.component_id == component_id
            ).all()

            # Transform to rich dictionary representation
            materials_details = []
            for cm in component_materials:
                material = self.material_repository.get_by_id(cm.material_id)
                materials_details.append({
                    'material_id': material.id,
                    'name': material.name,
                    'type': material.type,
                    'quantity': cm.quantity
                })

            return materials_details

        except SQLAlchemyError as e:
            logging.error(f"Error retrieving component materials: {e}")
            raise ValidationError(str(e))