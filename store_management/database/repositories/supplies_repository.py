# database/repositories/supplies_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime
from sqlalchemy import func, or_, and_

from database.models.material import Supplies
from database.repositories.material_repository import MaterialRepository
from database.models.enums import MaterialType, InventoryStatus
from database.repositories.base_repository import EntityNotFoundError, ValidationError, RepositoryError


class SuppliesRepository(MaterialRepository):
    """Repository for supplies-specific operations.

    This repository extends the MaterialRepository to provide specialized methods
    for supplies materials, including thread, adhesives, dyes, etc.
    """

    def _get_model_class(self) -> Type[Supplies]:
        """Return the model class this repository manages.

        Returns:
            The Supplies model class
        """
        return Supplies

    # Supplies-specific query methods

    def get_by_color(self, color: str) -> List[Supplies]:
        """Get supplies by color.

        Args:
            color: Color to filter by

        Returns:
            List of supplies instances with the specified color
        """
        self.logger.debug(f"Getting supplies with color '{color}'")
        return self.session.query(Supplies).filter(Supplies.color == color).all()

    def get_by_thickness(self, thickness: str) -> List[Supplies]:
        """Get supplies by thickness.

        Args:
            thickness: Thickness to filter by

        Returns:
            List of supplies instances with the specified thickness
        """
        self.logger.debug(f"Getting supplies with thickness '{thickness}'")
        return self.session.query(Supplies).filter(Supplies.thickness == thickness).all()

    def get_by_material_composition(self, composition: str) -> List[Supplies]:
        """Get supplies by material composition.

        Args:
            composition: Material composition to filter by (partial match)

        Returns:
            List of supplies instances with the specified material composition
        """
        self.logger.debug(f"Getting supplies with composition containing '{composition}'")
        return self.session.query(Supplies).filter(Supplies.material_composition.like(f"%{composition}%")).all()

    def get_by_supply_type(self, supply_type: str) -> List[Supplies]:
        """Get supplies by specific type (thread, adhesive, etc.).

        Args:
            supply_type: Supply type to filter by

        Returns:
            List of supplies instances of the specified type
        """
        self.logger.debug(f"Getting supplies with type '{supply_type}'")
        return self.session.query(Supplies).filter(Supplies.material_type == supply_type).all()

    # Business logic methods

    def get_supplies_for_project(self, project_id: int) -> Dict[str, Any]:
        """Get supplies needed for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            Dict with supplies information grouped by type

        Raises:
            EntityNotFoundError: If project not found
        """
        self.logger.debug(f"Getting supplies for project {project_id}")
        from database.models.project import Project
        from database.models.component import Component
        from database.models.component_material import ComponentMaterial
        from database.models.project_component import ProjectComponent

        project = self.session.query(Project).get(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        # Get project components
        project_components = self.session.query(ProjectComponent).filter(
            ProjectComponent.project_id == project_id
        ).all()

        # Calculate needed supplies
        needed_supplies = {}

        for pc in project_components:
            component = self.session.query(Component).get(pc.component_id)
            if not component:
                continue

            # Get component materials that are supplies
            component_materials = self.session.query(ComponentMaterial).filter(
                ComponentMaterial.component_id == component.id
            ).all()

            for cm in component_materials:
                material = self.session.query(Supplies).get(cm.material_id)
                if not material or not isinstance(material, Supplies):
                    continue

                supply_type = material.material_type
                if supply_type not in needed_supplies:
                    needed_supplies[supply_type] = []

                # Calculate quantity needed for this project
                quantity_needed = cm.quantity * pc.quantity

                # Get inventory information
                from database.models.inventory import Inventory
                inventory = self.session.query(Inventory).filter(
                    Inventory.item_id == material.id,
                    Inventory.item_type == 'material'
                ).first()

                in_stock = inventory.quantity if inventory else 0
                status = inventory.status.value if inventory else InventoryStatus.OUT_OF_STOCK.value

                supply_info = material.to_dict()
                supply_info['quantity_needed'] = quantity_needed
                supply_info['in_stock'] = in_stock
                supply_info['status'] = status
                supply_info['sufficient'] = in_stock >= quantity_needed

                # Check if this supply is already in the list
                existing = next((s for s in needed_supplies[supply_type] if s['id'] == material.id), None)
                if existing:
                    existing['quantity_needed'] += quantity_needed
                    existing['sufficient'] = existing['in_stock'] >= existing['quantity_needed']
                else:
                    needed_supplies[supply_type].append(supply_info)

        # Organize the result
        result = {
            'project_id': project_id,
            'project_name': project.name,
            'supplies_by_type': [
                {
                    'type': supply_type,
                    'supplies': supplies
                }
                for supply_type, supplies in needed_supplies.items()
            ],
            'missing_supplies': []
        }

        # Identify missing supplies (insufficient stock)
        for supply_type, supplies in needed_supplies.items():
            for supply in supplies:
                if not supply['sufficient']:
                    result['missing_supplies'].append({
                        'id': supply['id'],
                        'name': supply['name'],
                        'type': supply_type,
                        'needed': supply['quantity_needed'],
                        'in_stock': supply['in_stock'],
                        'shortage': supply['quantity_needed'] - supply['in_stock']
                    })

        return result

    def estimate_supply_usage(self, project_type: str) -> Dict[str, Any]:
        """Estimate supplies usage for a new project of specified type.

        Args:
            project_type: Type of project to estimate supplies for

        Returns:
            Dict with estimated supplies needed by type
        """
        self.logger.debug(f"Estimating supply usage for project type '{project_type}'")
        from database.models.project import Project
        from database.models.component import Component
        from database.models.component_material import ComponentMaterial
        from database.models.project_component import ProjectComponent
        from database.models.enums import ProjectType

        # Find similar projects
        similar_projects = self.session.query(Project).filter(
            Project.type == ProjectType(project_type)
        ).order_by(Project.created_at.desc()).limit(5).all()

        if not similar_projects:
            return {
                'project_type': project_type,
                'estimated_supplies': [],
                'note': f"No similar projects found for type '{project_type}'"
            }

        # Collect supply usage data from these projects
        supply_usage = {}

        for project in similar_projects:
            # Get project components
            project_components = self.session.query(ProjectComponent).filter(
                ProjectComponent.project_id == project.id
            ).all()

            for pc in project_components:
                component = self.session.query(Component).get(pc.component_id)
                if not component:
                    continue

                # Get component materials that are supplies
                component_materials = self.session.query(ComponentMaterial).filter(
                    ComponentMaterial.component_id == component.id
                ).all()

                for cm in component_materials:
                    material = self.session.query(Supplies).get(cm.material_id)
                    if not material or not isinstance(material, Supplies):
                        continue

                    # Calculate quantity needed for this project
                    quantity_needed = cm.quantity * pc.quantity

                    if material.id not in supply_usage:
                        supply_usage[material.id] = {
                            'material': material.to_dict(),
                            'quantities': []
                        }

                    supply_usage[material.id]['quantities'].append(quantity_needed)

        # Average the quantities across projects
        estimated_supplies = []
        for material_id, data in supply_usage.items():
            average_quantity = sum(data['quantities']) / len(data['quantities'])
            estimated_supply = data['material']
            estimated_supply['estimated_quantity'] = average_quantity
            estimated_supplies.append(estimated_supply)

        # Group by supply type
        grouped_supplies = {}
        for supply in estimated_supplies:
            supply_type = supply['material_type']
            if supply_type not in grouped_supplies:
                grouped_supplies[supply_type] = []
            grouped_supplies[supply_type].append(supply)

        return {
            'project_type': project_type,
            'estimated_supplies_by_type': [
                {
                    'type': supply_type,
                    'supplies': supplies
                }
                for supply_type, supplies in grouped_supplies.items()
            ]
        }

    # GUI-specific functionality

    def get_supplies_dashboard_data(self) -> Dict[str, Any]:
        """Get data for supplies dashboard in GUI.

        Returns:
            Dictionary with dashboard data specific to supplies
        """
        self.logger.debug("Getting supplies dashboard data")

        # Get base material dashboard data
        base_data = self.get_material_dashboard_data()

        # Add supplies-specific stats

        # Count by supplies type (thread, adhesive, etc.)
        type_counts = self.session.query(
            Supplies.material_type,
            func.count().label('count')
        ).group_by(Supplies.material_type).all()

        type_data = {str(type_): count for type_, count in type_counts}

        # Count by color
        color_counts = self.session.query(
            Supplies.color,
            func.count().label('count')
        ).group_by(Supplies.color).all()

        color_data = {str(color): count for color, count in color_counts}

        # Get low stock supplies
        from database.models.inventory import Inventory
        low_stock_query = self.session.query(Supplies, Inventory).join(
            Inventory,
            and_(
                Inventory.item_id == Supplies.id,
                Inventory.item_type == 'material',
                Inventory.status == InventoryStatus.LOW_STOCK
            )
        )

        low_stock_items = []
        for supplies, inventory in low_stock_query.all():
            item = supplies.to_dict()
            item['in_stock'] = inventory.quantity
            item['status'] = inventory.status.value
            low_stock_items.append(item)

        # Count supplies needing reorder
        reorder_count = len(low_stock_items)

        # Combine with base data
        supplies_data = {
            **base_data,
            'supplies_type_counts': type_data,
            'supplies_color_counts': color_data,
            'low_stock_count': reorder_count,
            'low_stock_items': low_stock_items[:10]  # Top 10 for preview
        }

        return supplies_data