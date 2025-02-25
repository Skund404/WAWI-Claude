#!/usr/bin/env python3
# Path: project_service.py
"""
Recipe Service Implementation

Provides functionality for managing projects/patterns and their components,
including material requirements and availability checks.
"""

from typing import Dict, List, Any, Optional, Tuple

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from database.models.project import Project, ProjectComponent
from database.models.part import Part
from database.models.leather import Leather
from database.sqlalchemy.core.manager_factory import get_manager


class RecipeService:
    """
    Service for pattern management operations.

    Provides functionality for creating, updating, and validating patterns/projects
    and checking material availability.
    """

    def __init__(self):
        """
        Initialize with appropriate managers.

        Sets up repository managers for projects, components, parts, and leather.
        """
        self.recipe_manager = get_manager(Project)
        self.recipe_item_manager = get_manager(ProjectComponent)
        self.part_manager = get_manager(Part)
        self.leather_manager = get_manager(Leather)

    def create_project(self, recipe_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Tuple[Optional[Project], str]:
        """
        Create a new pattern with items.

        Args:
            recipe_data: Dictionary with pattern data
            items: List of dictionaries with item data

        Returns:
            Tuple of (created pattern or None, result message)
        """
        try:
            # Create the pattern
            pattern = self.recipe_manager.create(recipe_data)

            # Add items to the pattern
            for item_data in items:
                item_data['recipe_id'] = pattern.id
                self.recipe_item_manager.create(item_data)

            return pattern, 'Project created successfully'

        except Exception as e:
            return None, f'Error creating pattern: {str(e)}'

    def check_materials_availability(self, recipe_id: int, quantity: int = 1) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check if materials for a pattern are available in sufficient quantity.

        Args:
            recipe_id: Project ID
            quantity: Number of items to produce

        Returns:
            Tuple of (all materials available, list of missing items)
        """
        missing_items = []

        try:
            # Get the pattern/project
            pattern = self.recipe_manager.get(recipe_id)
            if not pattern:
                return False, [{'error': f'Project with ID {recipe_id} not found'}]

            # Get all items for this pattern
            recipe_items = self.recipe_item_manager.filter_by(recipe_id=recipe_id)

            # Check each item for availability
            for item in recipe_items:
                required_quantity = item.quantity * quantity

                # Check parts
                if item.part_id:
                    part = self.part_manager.get(item.part_id)
                    if not part or part.stock_level < required_quantity:
                        missing_items.append({
                            'type': 'part',
                            'id': item.part_id,
                            'name': part.name if part else 'Unknown',
                            'required': required_quantity,
                            'available': part.stock_level if part else 0
                        })

                # Check leather
                if item.leather_id:
                    leather = self.leather_manager.get(item.leather_id)
                    if not leather or leather.area < required_quantity:
                        missing_items.append({
                            'type': 'leather',
                            'id': item.leather_id,
                            'name': leather.name if leather else 'Unknown',
                            'required': required_quantity,
                            'available': leather.area if leather else 0
                        })

            return len(missing_items) == 0, missing_items

        except Exception as e:
            return False, [{'error': f'Error checking materials: {str(e)}'}]