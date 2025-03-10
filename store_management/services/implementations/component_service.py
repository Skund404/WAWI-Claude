"""
services/implementations/component_service.py

Implementation of the component service for managing components in leatherworking projects.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.models.enums import ComponentType
from database.repositories.component_repository import ComponentRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.pattern_repository import PatternRepository

from services.base_service import BaseService
from services.exceptions import (
    ValidationError,
    NotFoundError,
    BusinessRuleError
)
from services.dto.component_dto import ComponentDTO, ComponentMaterialDTO

from di.inject import inject


class ComponentService(BaseService):
    """
    Service for managing components, their materials, and relationships.
    """

    @inject
    def __init__(
            self,
            session: Session,
            component_repository: Optional[ComponentRepository] = None,
            material_repository: Optional[MaterialRepository] = None,
            pattern_repository: Optional[PatternRepository] = None
    ):
        """
        Initialize the component service with necessary repositories.

        Args:
            session: Database session
            component_repository: Repository for component operations
            material_repository: Repository for material operations
            pattern_repository: Repository for pattern operations
        """
        super().__init__(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.pattern_repository = pattern_repository or PatternRepository(session)
        self.logger = logging.getLogger(__name__)

    def _validate_component_data(
            self,
            component_data: Dict[str, Any],
            update: bool = False
    ) -> None:
        """
        Validate component data before creation or update.

        Args:
            component_data: Data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields for new components
        if not update:
            required_fields = ['name', 'component_type']
            for field in required_fields:
                if field not in component_data or not component_data[field]:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate component type
        if 'component_type' in component_data:
            component_type = component_data['component_type']
            if not hasattr(ComponentType, component_type):
                raise ValidationError(f"Invalid component type: {component_type}")

        # Validate attributes if provided
        if 'attributes' in component_data:
            attributes = component_data['attributes']
            if not isinstance(attributes, dict):
                raise ValidationError("Attributes must be a dictionary")

        # Validate materials if provided
        if 'materials' in component_data:
            materials = component_data['materials']
            if not isinstance(materials, list):
                raise ValidationError("Materials must be a list")

            for material_data in materials:
                if not isinstance(material_data, dict):
                    raise ValidationError("Each material entry must be a dictionary")

                if 'material_id' not in material_data:
                    raise ValidationError("Missing material_id in material entry")

                # Validate quantity if provided
                if 'quantity' in material_data and material_data['quantity'] <= 0:
                    raise ValidationError("Material quantity must be greater than zero")

    def get_by_id(self, component_id: int) -> Dict[str, Any]:
        """
        Retrieve a component by its ID.

        Args:
            component_id: ID of the component to retrieve

        Returns:
            Component data as a dictionary
        """
        try:
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            return ComponentDTO.from_model(
                component,
                include_patterns=True
            ).to_dict()

        except NotFoundError:
            raise

        except Exception as e:
            self.logger.error(f"Error retrieving component {component_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all components, optionally filtered.

        Args:
            filters: Optional dictionary of filter criteria

        Returns:
            List of component data dictionaries
        """
        try:
            components = self.component_repository.get_all(filters=filters)
            return [
                ComponentDTO.from_model(component).to_dict()
                for component in components
            ]
        except Exception as e:
            self.logger.error(f"Error retrieving components: {str(e)}")
            raise

    def create(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new component.

        Args:
            component_data: Data for creating the component

        Returns:
            Created component data
        """
        try:
            # Validate component data
            self._validate_component_data(component_data)

            # Separate materials if provided
            materials = component_data.pop('materials', [])

            # Add timestamps
            component_data['created_at'] = datetime.now()
            component_data['updated_at'] = datetime.now()

            with self.transaction():
                # Create component
                component = self.component_repository.create(component_data)

                # Add materials if provided
                for material_data in materials:
                    material_id = material_data.get('material_id')
                    quantity = material_data.get('quantity', 1.0)

                    # Verify material exists
                    material = self.material_repository.get_by_id(material_id)
                    if not material:
                        self.logger.warning(
                            f"Material with ID {material_id} not found, skipping association"
                        )
                        continue

                    # Add material to component
                    self.component_repository.add_material(
                        component.id,
                        material_id,
                        quantity
                    )

                # Retrieve updated component with materials
                result = self.component_repository.get_by_id(component.id)
                return ComponentDTO.from_model(
                    result,
                    include_materials=True,
                    include_patterns=True
                ).to_dict()

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating component: {str(e)}")
            raise

    def update(self, component_id: int, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing component.

        Args:
            component_id: ID of the component to update
            component_data: Updated data for the component

        Returns:
            Updated component data
        """
        try:
            # Check if component exists
            existing_component = self.component_repository.get_by_id(component_id)
            if not existing_component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Validate component data
            self._validate_component_data(component_data, update=True)

            # Add update timestamp
            component_data['updated_at'] = datetime.now()

            with self.transaction():
                # Update component
                updated_component = self.component_repository.update(
                    component_id,
                    component_data
                )

                # Handle materials if provided
                if 'materials' in component_data:
                    # First remove existing materials
                    existing_materials = self.component_repository.get_materials(component_id)
                    for material_rel in existing_materials:
                        self.component_repository.remove_material(
                            component_id,
                            material_rel.material_id
                        )

                    # Add new materials
                    for material_data in component_data['materials']:
                        material_id = material_data.get('material_id')
                        quantity = material_data.get('quantity', 1.0)

                        # Verify material exists
                        material = self.material_repository.get_by_id(material_id)
                        if not material:
                            self.logger.warning(
                                f"Material with ID {material_id} not found, skipping association"
                            )
                            continue

                        # Add material to component
                        self.component_repository.add_material(
                            component_id,
                            material_id,
                            quantity
                        )

                return ComponentDTO.from_model(
                    updated_component,
                    include_materials=True,
                    include_patterns=True
                ).to_dict()

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating component {component_id}: {str(e)}")
            raise

    def delete(self, component_id: int) -> bool:
        """
        Delete a component.

        Args:
            component_id: ID of the component to delete

        Returns:
            True if deletion was successful
        """
        try:
            # Check if component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Check if component is used in any patterns
            patterns = self.pattern_repository.get_by_component(component_id)
            if patterns:
                pattern_names = ", ".join([p.name for p in patterns])
                raise BusinessRuleError(
                    f"Cannot delete component with ID {component_id} because it is used in patterns: {pattern_names}"
                )

            with self.transaction():
                # First remove all material associations
                materials = self.component_repository.get_materials(component_id)
                for material_relationship in materials:
                    material_id = getattr(material_relationship, 'material_id', None)
                    if material_id:
                        self.component_repository.remove_material(component_id, material_id)

                # Then delete the component
                return self.component_repository.delete(component_id)

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting component {component_id}: {str(e)}")
            raise

    def get_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """
        Retrieve components by their type.

        Args:
            component_type: Type of components to retrieve

        Returns:
            List of components matching the specified type
        """
        try:
            # Validate component type
            if not hasattr(ComponentType, component_type):
                raise ValidationError(f"Invalid component type: {component_type}")

            # Retrieve components
            components = self.component_repository.get_by_type(component_type)

            return [
                ComponentDTO.from_model(component).to_dict()
                for component in components
            ]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error retrieving components of type '{component_type}': {str(e)}"
            )
            raise

    def get_materials(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve materials used by a component.

        Args:
            component_id: ID of the component

        Returns:
            List of materials used by the component
        """
        try:
            # Check if component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Get materials
            material_relationships = self.component_repository.get_materials(component_id)

            return [
                ComponentMaterialDTO.from_relationship(
                    relationship,
                    include_material_details=True
                ).to_dict()
                for relationship in material_relationships
            ]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error retrieving materials for component {component_id}: {str(e)}"
            )
            raise

    def add_material(
            self,
            component_id: int,
            material_id: int,
            quantity: float = 1.0
    ) -> Dict[str, Any]:
        """
        Add a material to a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to add
            quantity: Quantity of the material (default 1.0)

        Returns:
            Updated component data
        """
        try:
            # Check if component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Check if material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            with self.transaction():
                # Check if material is already associated
                existing = self.component_repository.get_material_relationship(
                    component_id,
                    material_id
                )

                if existing:
                    # Update existing relationship
                    self.component_repository.update_material_relationship(
                        component_id,
                        material_id,
                        {'quantity': quantity}
                    )
                else:
                    # Add new material relationship
                    self.component_repository.add_material(
                        component_id,
                        material_id,
                        quantity
                    )

                # Retrieve updated component
                updated_component = self.component_repository.get_by_id(component_id)

                return ComponentDTO.from_model(
                    updated_component,
                    include_materials=True
                ).to_dict()

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(
                f"Error adding material {material_id} to component {component_id}: {str(e)}"
            )
            raise

    def remove_material(
            self,
            component_id: int,
            material_id: int
    ) -> bool:
        """
        Remove a material from a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to remove

        Returns:
            True if material was successfully removed
        """
        try:
            # Check if component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Check if material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Check if material is associated with component
            existing = self.component_repository.get_material_relationship(
                component_id,
                material_id
            )
            if not existing:
                raise NotFoundError(
                    f"Material {material_id} is not associated with component {component_id}"
                )

            with self.transaction():
                # Remove material from component
                return self.component_repository.remove_material(
                    component_id,
                    material_id
                )

        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error removing material {material_id} from component {component_id}: {str(e)}"
            )
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for components by name or other properties.

        Args:
            query: Search query string

        Returns:
            List of components matching the search query
        """
        try:
            components = self.component_repository.search(query)
            return [
                ComponentDTO.from_model(component).to_dict()
                for component in components
            ]
        except Exception as e:
            self.logger.error(f"Error searching components with query '{query}': {str(e)}")
            raise

    def get_patterns_using_component(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve patterns that use a specific component.

        Args:
            component_id: ID of the component

        Returns:
            List of patterns using the component
        """
        try:
            # Check if component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Retrieve patterns
            patterns = self.pattern_repository.get_by_component(component_id)

            result = []
            for pattern in patterns:
                pattern_data = {
                    'id': pattern.id,
                    'name': pattern.name,
                    'skill_level': getattr(pattern, 'skill_level', None),
                    'project_type': getattr(pattern, 'project_type', None)
                }

                # Get quantity if available
                if hasattr(pattern, 'components'):
                    for component_relationship in pattern.components:
                        if getattr(component_relationship, 'component_id', None) == component_id:
                            pattern_data['quantity'] = getattr(
                                component_relationship,
                                'quantity',
                                1
                            )
                            break

                result.append(pattern_data)

            return result

        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error retrieving patterns using component {component_id}: {str(e)}"
            )
            raise

    def calculate_component_cost(self, component_id: int) -> Dict[str, Any]:
        """
        Calculate the total cost of a component based on its materials.

        Args:
            component_id: ID of the component

        Returns:
            Detailed cost breakdown for the component
        """
        try:
            # Check if component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Get materials
            material_relationships = self.component_repository.get_materials(component_id)

            total_material_cost = 0
            material_breakdown = []

            # Calculate material costs
            for relationship in material_relationships:
                material = getattr(relationship, 'material', None)
                if not material:
                    continue

                quantity = getattr(relationship, 'quantity', 0)
                cost_per_unit = getattr(material, 'cost_price', 0) or 0
                material_cost = quantity * cost_per_unit

                total_material_cost += material_cost

                material_breakdown.append({
                    'material_id': material.id,
                    'material_name': material.name,
                    'quantity': quantity,
                    'unit': material.unit,
                    'cost_per_unit': cost_per_unit,
                    'total_material_cost': material_cost
                })

            # Estimated labor cost (simplified)
            # This could be more complex based on component complexity
            complexity_factor = getattr(component, 'complexity_factor', 1)
            labor_rate = 20  # Assumed hourly rate
            labor_hours = complexity_factor
            labor_cost = labor_hours * labor_rate

            # Overhead calculation
            overhead_percentage = 0.15  # 15% overhead
            overhead_cost = (total_material_cost + labor_cost) * overhead_percentage

            # Total cost calculation
            total_cost = total_material_cost + labor_cost + overhead_cost

            return {
                'component_id': component_id,
                'component_name': component.name,
                'total_material_cost': total_material_cost,
                'labor_cost': labor_cost,
                'labor_hours': labor_hours,
                'overhead_cost': overhead_cost,
                'total_cost': total_cost,
                'material_breakdown': material_breakdown,
                'overhead_percentage': overhead_percentage * 100,
                'complexity_factor': complexity_factor
            }

        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error calculating cost for component {component_id}: {str(e)}"
            )
            raise