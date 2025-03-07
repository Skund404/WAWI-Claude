# services/implementations/component_service.py
"""
Implementation of Component Service that manages component-related business logic.
"""

import logging
from typing import Any, Dict, List, Optional

from database.models.components import Component, ComponentMaterial
from database.models.enums import ComponentType
from database.models.material import Material
from database.repositories.component_repository import ComponentRepository
from database.repositories.material_repository import MaterialRepository
from database.sqlalchemy.session import get_db_session
from di.core import inject
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.component_service import IComponentService


class ComponentService(BaseService[Component], IComponentService):
    """
    Implementation of the Component Service interface that handles component-related operations.
    """

    @inject
    def __init__(self, component_repository: Optional[ComponentRepository] = None):
        """
        Initialize the Component Service with a repository.

        Args:
            component_repository: Optional repository for component data access
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.session = get_db_session()
        self.component_repository = component_repository or ComponentRepository(self.session)
        self.material_repository = MaterialRepository(self.session)

    def get_component(self, component_id: int) -> Component:
        """
        Retrieve a component by its ID.

        Args:
            component_id: ID of the component to retrieve

        Returns:
            Component: The retrieved component

        Raises:
            NotFoundError: If the component does not exist
        """
        try:
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")
            return component
        except SQLAlchemyError as e:
            self.logger.error(f"Database error when retrieving component {component_id}: {str(e)}")
            raise NotFoundError(f"Error retrieving component: {str(e)}")

    def get_components(self, **filters) -> List[Component]:
        """
        Retrieve components based on optional filters.

        Args:
            **filters: Optional keyword arguments for filtering components

        Returns:
            List[Component]: List of components matching the filters
        """
        try:
            return self.component_repository.find_all(**filters)
        except SQLAlchemyError as e:
            self.logger.error(f"Database error when retrieving components: {str(e)}")
            return []

    def create_component(self, component_data: Dict[str, Any]) -> Component:
        """
        Create a new component with the provided data.

        Args:
            component_data: Data for creating the component

        Returns:
            Component: The created component

        Raises:
            ValidationError: If the component data is invalid
        """
        try:
            # Validate component data
            if not component_data.get("name"):
                raise ValidationError("Component name is required")

            # Create component
            component = Component(**component_data)
            return self.component_repository.add(component)
        except SQLAlchemyError as e:
            self.logger.error(f"Database error when creating component: {str(e)}")
            raise ValidationError(f"Error creating component: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating component: {str(e)}")
            raise ValidationError(f"Error creating component: {str(e)}")

    def update_component(self, component_id: int, component_data: Dict[str, Any]) -> Component:
        """
        Update a component with the provided data.

        Args:
            component_id: ID of the component to update
            component_data: Data for updating the component

        Returns:
            Component: The updated component

        Raises:
            NotFoundError: If the component does not exist
            ValidationError: If the component data is invalid
        """
        try:
            # Get the component
            component = self.get_component(component_id)

            # Update component
            for key, value in component_data.items():
                if hasattr(component, key):
                    setattr(component, key, value)

            return self.component_repository.update(component)
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error when updating component {component_id}: {str(e)}")
            raise ValidationError(f"Error updating component: {str(e)}")

    def delete_component(self, component_id: int) -> bool:
        """
        Delete a component by its ID.

        Args:
            component_id: ID of the component to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the component does not exist
        """
        try:
            # Get the component
            component = self.get_component(component_id)

            # Delete component
            self.component_repository.delete(component)
            return True
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error when deleting component {component_id}: {str(e)}")
            raise NotFoundError(f"Error deleting component: {str(e)}")

    def get_components_by_type(self, component_type: ComponentType) -> List[Component]:
        """
        Retrieve components filtered by their type.

        Args:
            component_type: Type of components to retrieve

        Returns:
            List[Component]: List of components of the specified type
        """
        try:
            return self.component_repository.find_all(type=component_type)
        except SQLAlchemyError as e:
            self.logger.error(f"Database error when retrieving components by type: {str(e)}")
            return []

    def get_component_materials(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve materials associated with a component.

        Args:
            component_id: ID of the component

        Returns:
            List[Dict[str, Any]]: List of materials with quantities used in the component

        Raises:
            NotFoundError: If the component does not exist
        """
        try:
            # Get the component
            component = self.get_component(component_id)

            # Get component materials
            result = []
            for cm in component.component_materials:
                material = self.material_repository.get_by_id(cm.material_id)
                if material:
                    result.append({
                        "material_id": material.id,
                        "name": material.name,
                        "type": material.type,
                        "quantity": cm.quantity,
                        "unit": material.unit
                    })
            return result
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error when retrieving component materials: {str(e)}")
            raise NotFoundError(f"Error retrieving component materials: {str(e)}")

    def add_material_to_component(
        self, component_id: int, material_id: int, quantity: float
    ) -> bool:
        """
        Add a material to a component or update its quantity.

        Args:
            component_id: ID of the component
            material_id: ID of the material to add
            quantity: Quantity of the material to use

        Returns:
            bool: True if the material was added/updated successfully

        Raises:
            NotFoundError: If the component or material does not exist
            ValidationError: If the quantity is invalid
        """
        try:
            # Validate inputs
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Get the component and material
            component = self.get_component(component_id)
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Check if this material is already associated with the component
            existing = None
            for cm in component.component_materials:
                if cm.material_id == material_id:
                    existing = cm
                    break

            if existing:
                # Update existing association
                existing.quantity = quantity
                self.session.commit()
            else:
                # Create new association
                component_material = ComponentMaterial(
                    component_id=component_id,
                    material_id=material_id,
                    quantity=quantity
                )
                self.session.add(component_material)
                self.session.commit()

            return True
        except (NotFoundError, ValidationError):
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error when adding material to component: {str(e)}")
            raise ValidationError(f"Error adding material to component: {str(e)}")

    def remove_material_from_component(self, component_id: int, material_id: int) -> bool:
        """
        Remove a material from a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to remove

        Returns:
            bool: True if the material was removed successfully

        Raises:
            NotFoundError: If the component or component-material association does not exist
        """
        try:
            # Get the component
            component = self.get_component(component_id)

            # Find the component-material association
            found = False
            for cm in component.component_materials:
                if cm.material_id == material_id:
                    self.session.delete(cm)
                    found = True
                    break

            if not found:
                raise NotFoundError(
                    f"Material {material_id} not associated with component {component_id}"
                )

            self.session.commit()
            return True
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error when removing material from component: {str(e)}")
            raise NotFoundError(f"Error removing material from component: {str(e)}")