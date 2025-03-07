# services/implementations/project_component_service.py
"""
Comprehensive implementation of the project component service
for the leatherworking application.
"""
import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import joinedload

from database.models.components import (
    ProjectComponent,
    Component,
    ComponentMaterial,
    ComponentLeather,
    ComponentHardware
)
from database.models.picking_list import PickingListItem
from database.repositories.project_repository import ProjectRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import (
    BaseService,
    NotFoundError,
    ValidationError,
    ServiceError
)
from services.interfaces.project_component_service import IProjectComponentService

from utils.circular_import_resolver import lazy_import

# Lazy import for potential service dependencies
MaterialService = lazy_import("services.implementations.material_service", "MaterialService")
LeatherService = lazy_import("services.implementations.leather_service", "LeatherService")
HardwareService = lazy_import("services.implementations.hardware_service", "HardwareService")

logger = logging.getLogger(__name__)


class ProjectComponentService(BaseService, IProjectComponentService):
    """
    Comprehensive service for managing project components
    with advanced querying and manipulation capabilities.
    """

    def __init__(self, project_repository=None):
        """
        Initialize the Project Component Service.

        Args:
            project_repository: Optional repository for project data access
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Initialize repository and session
        self.session = get_db_session()
        self.repository = project_repository or ProjectRepository(self.session)

    def create_component(
            self,
            project_id: int,
            component_id: int,
            quantity: int = 1,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new project component with comprehensive validation.

        Args:
            project_id: ID of the project
            component_id: ID of the component
            quantity: Quantity of the component
            **kwargs: Additional component attributes

        Returns:
            Dict containing the created project component data

        Raises:
            ValidationError: If input validation fails
            NotFoundError: If project or component doesn't exist
            ServiceError: For unexpected errors
        """
        try:
            # Input validation
            if quantity <= 0:
                raise ValidationError("Quantity must be a positive number")

            # Verify project exists
            project = self.repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Verify component exists
            component = (
                self.session.query(Component)
                .filter(Component.id == component_id)
                .first()
            )
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Prepare component data
            component_data = {
                "project_id": project_id,
                "id": component_id,  # Use component_id as the id for ProjectComponent
                "component_id": component_id,
                "quantity": quantity,
                **kwargs
            }

            # Create project component
            project_component = ProjectComponent(**component_data)

            # Add and commit
            self.session.add(project_component)
            self.session.commit()

            # Log and return
            self.logger.info(
                f"Created project component: project_id={project_id}, "
                f"component_id={component_id}, quantity={quantity}"
            )
            return self._serialize_project_component(project_component)

        except (NotFoundError, ValidationError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error creating project component: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceError(error_msg) from e

    def get_component(self, project_component_id: int) -> Dict[str, Any]:
        """
        Retrieve a specific project component by ID.

        Args:
            project_component_id: ID of the project component

        Returns:
            Dict containing project component details

        Raises:
            NotFoundError: If project component doesn't exist
        """
        try:
            # Fetch project component with eager loading of related entities
            # Use a slightly different approach to load related entities
            project_component = (
                self.session.query(ProjectComponent)
                .options(
                    # Use subquery to load related entities
                    joinedload(ProjectComponent.project),
                    joinedload(ProjectComponent.picking_list_item)
                )
                .filter(ProjectComponent.id == project_component_id)
                .first()
            )

            if not project_component:
                raise NotFoundError(
                    f"Project component with ID {project_component_id} not found"
                )

            # Fetch the base component separately
            base_component = (
                self.session.query(Component)
                .filter(Component.id == project_component.component_id)
                .first()
            )

            # Add base component to the serialization context
            return self._serialize_project_component(
                project_component,
                base_component=base_component
            )

        except NotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error retrieving project component: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceError(error_msg) from e

    def get_components_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all project components for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of project component dictionaries
        """
        try:
            # Verify project exists
            project = self.repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Fetch project components with eager loading
            project_components = (
                self.session.query(ProjectComponent)
                .options(
                    joinedload(ProjectComponent.picking_list_item)
                )
                .filter(ProjectComponent.project_id == project_id)
                .all()
            )

            # Fetch base components for all project components
            base_component_map = {
                pc.component_id: self.session.query(Component)
                .filter(Component.id == pc.component_id)
                .first()
                for pc in project_components
            }

            return [
                self._serialize_project_component(
                    pc,
                    base_component=base_component_map.get(pc.component_id)
                )
                for pc in project_components
            ]

        except NotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error retrieving project components: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceError(error_msg) from e

    def link_to_picking_list_item(
        self,
        project_component_id: int,
        picking_list_item_id: int
    ) -> Dict[str, Any]:
        """
        Link a project component to a picking list item.

        Args:
            project_component_id: ID of the project component
            picking_list_item_id: ID of the picking list item

        Returns:
            Dict containing the updated project component

        Raises:
            NotFoundError: If either project component or picking list item not found
            ValidationError: If linking is invalid
        """
        try:
            # Fetch project component
            project_component = (
                self.session.query(ProjectComponent)
                .filter(ProjectComponent.id == project_component_id)
                .first()
            )
            if not project_component:
                raise NotFoundError(
                    f"Project component with ID {project_component_id} not found"
                )

            # Fetch picking list item
            from database.models.picking_list import PickingListItem
            picking_list_item = (
                self.session.query(PickingListItem)
                .filter(PickingListItem.id == picking_list_item_id)
                .first()
            )
            if not picking_list_item:
                raise NotFoundError(
                    f"Picking list item with ID {picking_list_item_id} not found"
                )

            # Additional validation if needed
            if project_component.picking_list_item_id:
                raise ValidationError(
                    f"Project component {project_component_id} "
                    "is already linked to a picking list item"
                )

            # Link the project component
            project_component.picking_list_item_id = picking_list_item_id

            # Commit changes
            self.session.commit()

            # Log and return
            self.logger.info(
                f"Linked project component {project_component_id} "
                f"to picking list item {picking_list_item_id}"
            )
            return self._serialize_project_component(project_component)

        except (NotFoundError, ValidationError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error linking project component: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceError(error_msg) from e

    def update_component(
        self,
        project_component_id: int,
        **update_data
    ) -> Dict[str, Any]:
        """
        Update a project component's attributes.

        Args:
            project_component_id: ID of the project component
            **update_data: Attributes to update

        Returns:
            Dict containing the updated project component

        Raises:
            NotFoundError: If project component doesn't exist
            ValidationError: If update fails validation
        """
        try:
            # Fetch existing project component
            project_component = (
                self.session.query(ProjectComponent)
                .filter(ProjectComponent.id == project_component_id)
                .first()
            )
            if not project_component:
                raise NotFoundError(
                    f"Project component with ID {project_component_id} not found"
                )

            # Validate and apply updates
            allowed_fields = ['quantity']
            for field, value in update_data.items():
                if field not in allowed_fields:
                    raise ValidationError(f"Cannot update field: {field}")

                if field == 'quantity' and value <= 0:
                    raise ValidationError("Quantity must be a positive number")

                setattr(project_component, field, value)

            # Commit changes
            self.session.commit()

            # Log and return
            self.logger.info(
                f"Updated project component {project_component_id}: {update_data}"
            )
            return self._serialize_project_component(project_component)

        except (NotFoundError, ValidationError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error updating project component: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceError(error_msg) from e

    def delete_component(self, project_component_id: int) -> None:
        """
        Delete a project component.

        Args:
            project_component_id: ID of the project component to delete

        Raises:
            NotFoundError: If project component doesn't exist
            ValidationError: If deletion is not allowed
        """
        try:
            # Fetch project component
            project_component = (
                self.session.query(ProjectComponent)
                .filter(ProjectComponent.id == project_component_id)
                .first()
            )
            if not project_component:
                raise NotFoundError(
                    f"Project component with ID {project_component_id} not found"
                )

            # Additional deletion checks if needed
            if project_component.picking_list_item_id:
                raise ValidationError(
                    "Cannot delete a project component linked to a picking list item"
                )

            # Delete the project component
            self.session.delete(project_component)
            self.session.commit()

            # Log deletion
            self.logger.info(
                f"Deleted project component {project_component_id}"
            )

        except (NotFoundError, ValidationError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error deleting project component: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceError(error_msg) from e

    def get_material_requirements(self, project_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get detailed material requirements for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dict of material requirements by type
        """
        try:
            # Verify project exists
            project = self.repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Fetch project components with eager loading
            project_components = (
                self.session.query(ProjectComponent)
                .filter(ProjectComponent.project_id == project_id)
                .all()
            )

            # Initialize requirement containers
            requirements = {
                'materials': [],
                'leathers': [],
                'hardware': []
            }

            # Process each project component
            for pc in project_components:
                # Get component quantity
                component_quantity = pc.quantity

                # Fetch component materials
                component_materials = (
                    self.session.query(ComponentMaterial)
                    .filter(ComponentMaterial.component_id == pc.component_id)
                    .all()
                )
                for cm in component_materials:
                    requirements['materials'].append({
                        'material_id': cm.material_id,
                        'quantity': cm.quantity * component_quantity
                    })

                # Fetch component leathers
                component_leathers = (
                    self.session.query(ComponentLeather)
                    .filter(ComponentLeather.component_id == pc.component_id)
                    .all()
                )
                for cl in component_leathers:
                    requirements['leathers'].append({
                        'leather_id': cl.leather_id,
                        'quantity': cl.quantity * component_quantity
                    })

                # Fetch component hardware
                component_hardware = (
                    self.session.query(ComponentHardware)
                    .filter(ComponentHardware.component_id == pc.component_id)
                    .all()
                )
                for ch in component_hardware:
                    requirements['hardware'].append({
                        'hardware_id': ch.hardware_id,
                        'quantity': ch.quantity * component_quantity
                    })

            return requirements

        except NotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error calculating material requirements: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceError(error_msg) from e

    def _serialize_project_component(
        self,
        project_component: ProjectComponent,
        base_component: Optional[Component] = None
    ) -> Dict[str, Any]:
        """
        Serialize a project component to a dictionary.

        Args:
            project_component: ProjectComponent instance to serialize
            base_component: Optional base Component for additional details

        Returns:
            Dictionary representation of the project component
        """
        result = {
            "id": project_component.id,
            "project_id": project_component.project_id,
            "component_id": project_component.component_id,
            "quantity": project_component.quantity
        }

        # Add optional fields
        if project_component.picking_list_item_id:
            result["picking_list_item_id"] = project_component.picking_list_item_id

        # Add base component details if available
        if base_component:
            result["component"] = {
                "id": base_component.id,
                "name": base_component.name,
                "component_type": str(base_component.component_type) if base_component.component_type else None,
                "description": base_component.description
            }

        # Add project details if available
        if hasattr(project_component, 'project') and project_component.project:
            result["project"] = {
                "id": project_component.project.id,
                "name": project_component.project.name
            }

        # Add any additional relevant project component details
        if project_component.pattern_id:
            result["pattern_id"] = project_component.pattern_id
        if project_component.leather_id:
            result["leather_id"] = project_component.leather_id
        if project_component.hardware_id:
            result["hardware_id"] = project_component.hardware_id
        if project_component.material_id:
            result["material_id"] = project_component.material_id

        return result

    def update_quantity(
            self,
            project_component_id: int,
            quantity: int
    ) -> Dict[str, Any]:
        """
        Update the quantity of a project component.

        Args:
            project_component_id: ID of the project component
            quantity: New quantity value

        Returns:
            Dict containing the updated project component

        Raises:
            NotFoundError: If the project component doesn't exist
            ValidationError: If quantity is invalid
        """
        try:
            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be a positive number")

            # Fetch existing project component
            project_component = (
                self.session.query(ProjectComponent)
                .filter(ProjectComponent.id == project_component_id)
                .first()
            )
            if not project_component:
                raise NotFoundError(
                    f"Project component with ID {project_component_id} not found"
                )

            # Update quantity
            project_component.quantity = quantity

            # Commit changes
            self.session.commit()

            # Log and return
            self.logger.info(
                f"Updated project component {project_component_id} "
                f"quantity to {quantity}"
            )
            return self._serialize_project_component(project_component)

        except (NotFoundError, ValidationError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error updating project component quantity: {str(e)}"
            self.logger.error(error_msg)
            raise ServiceError(error_msg) from e