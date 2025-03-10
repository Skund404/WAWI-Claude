# database/repositories/component_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime
from sqlalchemy import func, or_, and_

from database.models.component import Component
from database.models.component_material import ComponentMaterial
from database.models.enums import ComponentType
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError


class ComponentRepository(BaseRepository[Component]):
    """Repository for component operations.

    This repository provides methods for querying and manipulating component data,
    including relationships with materials and patterns.
    """

    def _get_model_class(self) -> Type[Component]:
        """Return the model class this repository manages.

        Returns:
            The Component model class
        """
        return Component

    # Component-specific query methods

    def get_by_type(self, component_type: ComponentType) -> List[Component]:
        """Get components by type.

        Args:
            component_type: Component type to filter by

        Returns:
            List of component instances of the specified type
        """
        self.logger.debug(f"Getting components with type '{component_type.value}'")
        return self.session.query(Component).filter(Component.component_type == component_type).all()

    def get_by_name(self, name: str) -> List[Component]:
        """Get components by name (partial match).

        Args:
            name: Name to search for

        Returns:
            List of component instances matching the name
        """
        self.logger.debug(f"Getting components with name containing '{name}'")
        return self.session.query(Component).filter(Component.name.like(f"%{name}%")).all()

    def get_components_with_materials(self, component_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Get components with their materials.

        Args:
            component_ids: Optional list of component IDs to filter by

        Returns:
            List of components with materials
        """
        self.logger.debug(f"Getting components with materials, filtered by IDs: {component_ids}")
        from database.models.material import Material

        query = self.session.query(Component)

        if component_ids:
            query = query.filter(Component.id.in_(component_ids))

        components = query.all()
        result = []

        for component in components:
            component_dict = component.to_dict()
            component_dict['materials'] = []

            # Get materials for this component
            component_materials = self.session.query(ComponentMaterial).filter(
                ComponentMaterial.component_id == component.id
            ).all()

            for cm in component_materials:
                material = self.session.query(Material).get(cm.material_id)
                if not material:
                    continue

                material_dict = material.to_dict()
                material_dict['quantity'] = cm.quantity
                component_dict['materials'].append(material_dict)

            result.append(component_dict)

        return result

    def get_components_by_pattern(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Get components used in a pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            List of components with additional details

        Raises:
            EntityNotFoundError: If pattern not found
        """
        self.logger.debug(f"Getting components for pattern {pattern_id}")
        from database.models.pattern import Pattern

        pattern = self.session.query(Pattern).get(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        # This assumes Pattern has a relationship with Component
        components = pattern.components

        # Enhance with additional details
        result = []
        for component in components:
            component_dict = component.to_dict()

            # Get material quantities
            component_materials = self.session.query(ComponentMaterial).filter(
                ComponentMaterial.component_id == component.id
            ).all()

            component_dict['materials'] = []
            for cm in component_materials:
                from database.models.material import Material
                material = self.session.query(Material).get(cm.material_id)
                if material:
                    material_dict = material.to_dict()
                    material_dict['quantity'] = cm.quantity
                    component_dict['materials'].append(material_dict)

            result.append(component_dict)

        return result

    # Business logic methods

    def create_component_with_materials(self, component_data: Dict[str, Any],
                                        materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a component with materials.

        Args:
            component_data: Component data dictionary
            materials: List of material dictionaries with material_id and quantity

        Returns:
            Created component with materials
        """
        self.logger.debug("Creating component with materials")

        try:
            # Create component
            component = Component(**component_data)
            created_component = self.create(component)

            # Add materials
            component_materials = []
            for material_data in materials:
                component_material = ComponentMaterial(
                    component_id=created_component.id,
                    material_id=material_data['material_id'],
                    quantity=material_data['quantity']
                )
                self.session.add(component_material)
                component_materials.append(component_material)

            # Flush to get IDs
            self.session.flush()

            # Prepare result
            result = created_component.to_dict()
            result['materials'] = [
                {
                    'component_material_id': cm.id,
                    'material_id': cm.material_id,
                    'quantity': cm.quantity
                }
                for cm in component_materials
            ]

            return result

        except Exception as e:
            self.logger.error(f"Error creating component with materials: {str(e)}")
            raise ValidationError(f"Failed to create component with materials: {str(e)}")

    def update_component_materials(self, component_id: int,
                                   materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update materials for a component.

        Args:
            component_id: ID of the component
            materials: List of material dictionaries with material_id and quantity

        Returns:
            Updated component with materials

        Raises:
            EntityNotFoundError: If component not found
        """
        self.logger.debug(f"Updating materials for component {component_id}")

        component = self.get_by_id(component_id)
        if not component:
            raise EntityNotFoundError(f"Component with ID {component_id} not found")

        try:
            # Delete existing component materials
            self.session.query(ComponentMaterial).filter(
                ComponentMaterial.component_id == component_id
            ).delete(synchronize_session=False)

            # Add new materials
            component_materials = []
            for material_data in materials:
                component_material = ComponentMaterial(
                    component_id=component_id,
                    material_id=material_data['material_id'],
                    quantity=material_data['quantity']
                )
                self.session.add(component_material)
                component_materials.append(component_material)

            # Flush to get IDs
            self.session.flush()

            # Prepare result
            result = component.to_dict()
            result['materials'] = [
                {
                    'component_material_id': cm.id,
                    'material_id': cm.material_id,
                    'quantity': cm.quantity
                }
                for cm in component_materials
            ]

            return result

        except Exception as e:
            self.logger.error(f"Error updating component materials: {str(e)}")
            raise ValidationError(f"Failed to update component materials: {str(e)}")

    def calculate_component_cost(self, component_id: int) -> Dict[str, Any]:
        """Calculate the cost of a component based on its materials.

        Args:
            component_id: ID of the component

        Returns:
            Dict with cost breakdown

        Raises:
            EntityNotFoundError: If component not found
        """
        self.logger.debug(f"Calculating cost for component {component_id}")
        from database.models.material import Material

        component = self.get_by_id(component_id)
        if not component:
            raise EntityNotFoundError(f"Component with ID {component_id} not found")

        # Get component materials
        component_materials = self.session.query(ComponentMaterial).filter(
            ComponentMaterial.component_id == component_id
        ).all()

        # Calculate costs
        total_cost = 0
        material_costs = []

        for cm in component_materials:
            material = self.session.query(Material).get(cm.material_id)
            if not material:
                continue

            # Calculate cost
            material_cost = material.cost_per_unit * cm.quantity
            total_cost += material_cost

            material_costs.append({
                'material_id': material.id,
                'material_name': material.name,
                'material_type': material.material_type.value,
                'unit_cost': material.cost_per_unit,
                'quantity': cm.quantity,
                'total_cost': material_cost
            })

        return {
            'component_id': component_id,
            'component_name': component.name,
            'total_cost': total_cost,
            'material_costs': material_costs
        }

    # GUI-specific functionality

    def get_component_dashboard_data(self) -> Dict[str, Any]:
        """Get data for component dashboard in GUI.

        Returns:
            Dictionary with dashboard data for components
        """
        self.logger.debug("Getting component dashboard data")

        # Count by component type
        type_counts = self.session.query(
            Component.component_type,
            func.count().label('count')
        ).group_by(Component.component_type).all()

        type_data = {t.value: count for t, count in type_counts}

        # Get total number of components
        total_components = self.count()

        # Get most used components in patterns
        # This assumes a many-to-many relationship between Pattern and Component
        from database.models.pattern import Pattern

        # This query will need to be adjusted based on actual relationship structure
        top_components_query = self.session.query(
            Component.id,
            Component.name,
            Component.component_type,
            func.count('*').label('pattern_count')
        ).join(
            Pattern.components
        ).group_by(
            Component.id,
            Component.name,
            Component.component_type
        ).order_by(
            func.count('*').desc()
        ).limit(10)

        top_components = []
        for id, name, component_type, pattern_count in top_components_query.all():
            top_components.append({
                'id': id,
                'name': name,
                'component_type': component_type.value,
                'pattern_count': pattern_count
            })

        # Get most complex components (with most materials)
        complex_components_query = self.session.query(
            Component.id,
            Component.name,
            Component.component_type,
            func.count(ComponentMaterial.id).label('material_count')
        ).join(
            ComponentMaterial,
            ComponentMaterial.component_id == Component.id
        ).group_by(
            Component.id,
            Component.name,
            Component.component_type
        ).order_by(
            func.count(ComponentMaterial.id).desc()
        ).limit(10)

        complex_components = []
        for id, name, component_type, material_count in complex_components_query.all():
            complex_components.append({
                'id': id,
                'name': name,
                'component_type': component_type.value,
                'material_count': material_count
            })

        return {
            'type_counts': type_data,
            'total_components': total_components,
            'top_components': top_components,
            'complex_components': complex_components
        }