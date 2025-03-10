# services/implementations/component_service.py
import logging
from typing import Dict, List, Any, Optional, Union, cast
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.component import Component
from database.models.component_material import ComponentMaterial
from database.models.material import Material
from database.models.enums import ComponentType
from database.repositories.component_repository import ComponentRepository
from database.repositories.material_repository import MaterialRepository

from services.base_service import BaseService, ValidationError, NotFoundError, ServiceError
from services.interfaces.component_service import IComponentService
from services.interfaces.material_service import IMaterialService

from di.core import inject


class ComponentService(BaseService, IComponentService):
    """Implementation of the Component Service interface.

    This service provides functionality for managing components used in
    leatherworking projects, including their materials and attributes.
    """

    @inject
    def __init__(self,
                 session: Session,
                 repository: Optional[ComponentRepository] = None,
                 material_service: Optional[IMaterialService] = None):
        """Initialize the Component Service.

        Args:
            session: SQLAlchemy database session
            repository: Optional ComponentRepository instance (will be created if not provided)
            material_service: Optional MaterialService for cost calculations
        """
        super().__init__(session)
        self.repository = repository or ComponentRepository(session)
        self.material_service = material_service
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, component_id: int) -> Dict[str, Any]:
        """Retrieve a component by its ID.

        Args:
            component_id: The ID of the component to retrieve

        Returns:
            A dictionary representation of the component

        Raises:
            NotFoundError: If the component does not exist
        """
        try:
            component = self.repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")
            return self._to_dict(component)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving component {component_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve component: {str(e)}")

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all components with optional filtering.

        Args:
            filters: Optional filters to apply to the component query

        Returns:
            List of dictionaries representing components
        """
        try:
            components = self.repository.get_all(filters)
            return [self._to_dict(component) for component in components]
        except Exception as e:
            self.logger.error(f"Error retrieving components: {str(e)}")
            raise ServiceError(f"Failed to retrieve components: {str(e)}")

    def create(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new component.

        Args:
            component_data: Dictionary containing component data

        Returns:
            Dictionary representation of the created component

        Raises:
            ValidationError: If the component data is invalid
        """
        try:
            # Validate the component data
            self._validate_component_data(component_data)

            # Create the component within a transaction
            with self.transaction():
                component = Component(**component_data)
                created_component = self.repository.create(component)

                # Add materials if provided
                if 'materials' in component_data and isinstance(component_data['materials'], list):
                    for material_entry in component_data['materials']:
                        if isinstance(material_entry,
                                      dict) and 'material_id' in material_entry and 'quantity' in material_entry:
                            self.repository.add_material(
                                created_component.id,
                                material_entry['material_id'],
                                material_entry['quantity']
                            )

                return self._to_dict(created_component)
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating component: {str(e)}")
            raise ServiceError(f"Failed to create component: {str(e)}")

    def update(self, component_id: int, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing component.

        Args:
            component_id: ID of the component to update
            component_data: Dictionary containing updated component data

        Returns:
            Dictionary representation of the updated component

        Raises:
            NotFoundError: If the component does not exist
            ValidationError: If the updated data is invalid
        """
        try:
            # Verify component exists
            component = self.repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Validate component data
            self._validate_component_data(component_data, update=True)

            # Update the component within a transaction
            with self.transaction():
                updated_component = self.repository.update(component_id, component_data)

                # Update materials if provided
                if 'materials' in component_data and isinstance(component_data['materials'], list):
                    # Optional: clear existing materials if specified
                    if component_data.get('replace_materials', False):
                        self.repository.clear_materials(component_id)

                    for material_entry in component_data['materials']:
                        if isinstance(material_entry,
                                      dict) and 'material_id' in material_entry and 'quantity' in material_entry:
                            self.repository.add_material(
                                component_id,
                                material_entry['material_id'],
                                material_entry['quantity']
                            )

                return self._to_dict(updated_component)
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating component {component_id}: {str(e)}")
            raise ServiceError(f"Failed to update component: {str(e)}")

    def delete(self, component_id: int) -> bool:
        """Delete a component by its ID.

        Args:
            component_id: ID of the component to delete

        Returns:
            True if the component was successfully deleted

        Raises:
            NotFoundError: If the component does not exist
            ServiceError: If the component cannot be deleted (e.g., in use)
        """
        try:
            # Verify component exists
            component = self.repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Check if component is used in any projects
            project_components = self.repository.get_project_usage(component_id)
            if project_components and len(project_components) > 0:
                project_ids = [pc.project_id for pc in project_components]
                raise ServiceError(f"Cannot delete component {component_id} as it is used in projects: {project_ids}")

            # Delete the component within a transaction
            with self.transaction():
                # First remove all material relationships
                self.repository.clear_materials(component_id)

                # Then delete the component
                self.repository.delete(component_id)
                return True
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting component {component_id}: {str(e)}")
            raise ServiceError(f"Failed to delete component: {str(e)}")

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find components by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching components
        """
        try:
            components = self.repository.find_by_name(name)
            return [self._to_dict(component) for component in components]
        except Exception as e:
            self.logger.error(f"Error finding components by name '{name}': {str(e)}")
            raise ServiceError(f"Failed to find components by name: {str(e)}")

    def find_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Find components by type.

        Args:
            component_type: Component type to filter by

        Returns:
            List of dictionaries representing components of the specified type
        """
        try:
            # Validate component type
            self._validate_component_type(component_type)

            components = self.repository.find_by_type(component_type)
            return [self._to_dict(component) for component in components]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding components by type '{component_type}': {str(e)}")
            raise ServiceError(f"Failed to find components by type: {str(e)}")

    def get_materials(self, component_id: int) -> List[Dict[str, Any]]:
        """Get all materials used by a component.

        Args:
            component_id: ID of the component

        Returns:
            List of dictionaries representing materials with quantities

        Raises:
            NotFoundError: If the component does not exist
        """
        try:
            # Verify component exists
            component = self.repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Get component materials with quantities
            component_materials = self.repository.get_materials(component_id)

            result = []
            for cm in component_materials:
                material_dict = self._to_dict(cm.material)
                material_dict['quantity'] = cm.quantity
                result.append(material_dict)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting materials for component {component_id}: {str(e)}")
            raise ServiceError(f"Failed to get materials: {str(e)}")

    def add_material(self,
                     component_id: int,
                     material_id: int,
                     quantity: float) -> Dict[str, Any]:
        """Add a material to a component or update its quantity.

        Args:
            component_id: ID of the component
            material_id: ID of the material to add
            quantity: Quantity of the material needed

        Returns:
            Dictionary representing the component-material relationship

        Raises:
            NotFoundError: If the component or material does not exist
            ValidationError: If the quantity is invalid
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")

        try:
            # Verify component exists
            component = self.repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Verify material exists (using material repository)
            material_repo = MaterialRepository(self.session)
            material = material_repo.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Add or update material within a transaction
            with self.transaction():
                component_material = self.repository.add_material(component_id, material_id, quantity)

                result = {
                    'component_id': component_id,
                    'material_id': material_id,
                    'material_name': material.name,
                    'quantity': quantity
                }

                return result
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding material {material_id} to component {component_id}: {str(e)}")
            raise ServiceError(f"Failed to add material: {str(e)}")

    def remove_material(self, component_id: int, material_id: int) -> bool:
        """Remove a material from a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to remove

        Returns:
            True if the material was successfully removed

        Raises:
            NotFoundError: If the component or material relationship does not exist
        """
        try:
            # Verify component exists
            component = self.repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Remove the material within a transaction
            with self.transaction():
                result = self.repository.remove_material(component_id, material_id)
                if not result:
                    raise NotFoundError(f"Material {material_id} not found in component {component_id}")

                return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error removing material {material_id} from component {component_id}: {str(e)}")
            raise ServiceError(f"Failed to remove material: {str(e)}")

    def get_components_using_material(self, material_id: int) -> List[Dict[str, Any]]:
        """Find all components that use a specific material.

        Args:
            material_id: ID of the material

        Returns:
            List of dictionaries representing components that use the material

        Raises:
            NotFoundError: If the material does not exist
        """
        try:
            # Verify material exists
            material_repo = MaterialRepository(self.session)
            material = material_repo.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Get components using the material
            components = self.repository.get_components_using_material(material_id)

            result = []
            for component, quantity in components:
                component_dict = self._to_dict(component)
                component_dict['material_quantity'] = quantity
                result.append(component_dict)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding components using material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to find components using material: {str(e)}")

    def calculate_component_cost(self, component_id: int) -> Dict[str, float]:
        """Calculate the cost of a component based on its materials.

        Args:
            component_id: ID of the component

        Returns:
            Dictionary with cost details (material_cost, labor_cost, total_cost)

        Raises:
            NotFoundError: If the component does not exist
        """
        try:
            # Verify component exists
            component = self.repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Get component materials
            component_materials = self.repository.get_materials(component_id)

            # Calculate material cost
            material_cost = 0.0
            for cm in component_materials:
                material = cm.material
                # Get the material unit cost
                unit_cost = getattr(material, 'unit_cost', 0.0)
                # Calculate cost based on quantity
                material_cost += unit_cost * cm.quantity

            # Calculate labor cost - can be enhanced with more sophisticated calculations
            # For now, use a simple calculation based on material cost and component type
            labor_multiplier = 0.5  # Default multiplier

            # Adjust labor multiplier based on component type if applicable
            if hasattr(component, 'component_type'):
                if component.component_type == ComponentType.LEATHER:
                    labor_multiplier = 0.7  # Leather components require more labor
                elif component.component_type == ComponentType.HARDWARE:
                    labor_multiplier = 0.3  # Hardware components require less labor

            labor_cost = material_cost * labor_multiplier

            # Calculate total cost
            total_cost = material_cost + labor_cost

            return {
                'material_cost': round(material_cost, 2),
                'labor_cost': round(labor_cost, 2),
                'total_cost': round(total_cost, 2)
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error calculating cost for component {component_id}: {str(e)}")
            raise ServiceError(f"Failed to calculate component cost: {str(e)}")

    def _validate_component_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate component data.

        Args:
            data: Component data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Required fields for new components
        if not update:
            required_fields = ['name', 'component_type']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate component type if provided
        if 'component_type' in data:
            self._validate_component_type(data['component_type'])

        # Validate materials if provided
        if 'materials' in data:
            if not isinstance(data['materials'], list):
                raise ValidationError("Materials must be a list")

            for material in data['materials']:
                if not isinstance(material, dict):
                    raise ValidationError("Each material entry must be a dictionary")

                if 'material_id' not in material:
                    raise ValidationError("Missing material_id in material entry")

                if 'quantity' not in material:
                    raise ValidationError("Missing quantity in material entry")

                if material.get('quantity', 0) <= 0:
                    raise ValidationError("Material quantity must be greater than zero")

    def _validate_component_type(self, component_type: str) -> None:
        """Validate that the component type is a valid enum value.

        Args:
            component_type: Component type to validate

        Raises:
            ValidationError: If the component type is invalid
        """
        try:
            # Check if the type is a valid enum value
            ComponentType[component_type]
        except (KeyError, ValueError):
            valid_types = [t.name for t in ComponentType]
            raise ValidationError(f"Invalid component type: {component_type}. Valid types are: {valid_types}")

    def _to_dict(self, obj) -> Dict[str, Any]:
        """Convert a model object to a dictionary representation.

        Args:
            obj: Model object to convert

        Returns:
            Dictionary representation of the object
        """
        if isinstance(obj, Component):
            result = {
                'id': obj.id,
                'name': obj.name,
                'description': getattr(obj, 'description', None),
                'component_type': obj.component_type.name if hasattr(obj, 'component_type') else None,
                'created_at': obj.created_at.isoformat() if hasattr(obj, 'created_at') and obj.created_at else None,
                'updated_at': obj.updated_at.isoformat() if hasattr(obj, 'updated_at') and obj.updated_at else None,
            }

            # Include attributes if present
            if hasattr(obj, 'attributes') and obj.attributes:
                result['attributes'] = obj.attributes

            return result
        elif isinstance(obj, Material):
            result = {
                'id': obj.id,
                'name': obj.name,
                'material_type': obj.material_type.name if hasattr(obj, 'material_type') else None,
                'unit_cost': getattr(obj, 'unit_cost', None),
                'unit': getattr(obj, 'unit', None)
            }
            return result
        elif hasattr(obj, '__dict__'):
            # Generic conversion for other model types
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        else:
            # If not a model object, return as is
            return obj