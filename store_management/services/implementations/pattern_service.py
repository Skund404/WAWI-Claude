# services/implementations/pattern_service.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

from database.repositories.interfaces.pattern_service import IRecipeService
from database.models.pattern import Project, ProjectComponent
from database.session import get_db_session


class RecipeService(IRecipeService):
    """
    Service implementation for managing patterns.

    Handles:
    - Project CRUD operations
    - Material requirements checking
    - Cost calculations
    - Project search and categorization
    """

    def __init__(self, container: Any) -> None:
        """
        Initialize the pattern service.

        Args:
            container: Dependency injection container
        """
        self.logger = logging.getLogger(__name__)
        self.session: Session = get_db_session()

    def get_all_recipes(self) -> List[Project]:
        """Get all patterns from the database."""
        try:
            return self.session.query(Project).order_by(Project.name).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving patterns: {str(e)}")
            raise Exception("Failed to retrieve patterns") from e

    def get_recipe_by_id(self, recipe_id: int) -> Optional[Project]:
        """Get a specific pattern by ID."""
        try:
            return self.session.query(Project).filter(Project.id == recipe_id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving pattern {recipe_id}: {str(e)}")
            raise Exception(f"Failed to retrieve pattern {recipe_id}") from e

    def create_project(self, recipe_data: Dict[str, Any]) -> Project:
        """Create a new pattern with its items."""
        try:
            # Create pattern
            pattern = Project(
                name=recipe_data['name'],
                description=recipe_data.get('description', ''),
                preparation_time=recipe_data.get('preparation_time', 0)
            )

            # Add items
            if 'items' in recipe_data:
                for item_data in recipe_data['items']:
                    item = ProjectComponent(
                        material_name=item_data['material_name'],
                        quantity=item_data['quantity'],
                        unit=item_data['unit']
                    )
                    pattern.items.append(item)

            # Calculate initial cost
            pattern.total_cost = self._calculate_materials_cost(pattern)

            self.session.add(pattern)
            self.session.commit()

            self.logger.info(f"Created pattern: {pattern.name}")
            return pattern

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating pattern: {str(e)}")
            raise Exception("Failed to create pattern") from e

    def update_project(self, recipe_id: int, recipe_data: Dict[str, Any]) -> Project:
        """Update an existing pattern."""
        try:
            pattern = self.get_recipe_by_id(recipe_id)
            if not pattern:
                raise Exception(f"Project {recipe_id} not found")

            # Update basic fields
            pattern.name = recipe_data.get('name', pattern.name)
            pattern.description = recipe_data.get('description', pattern.description)
            pattern.preparation_time = recipe_data.get('preparation_time', pattern.preparation_time)

            # Update items if provided
            if 'items' in recipe_data:
                # Clear existing items
                pattern.items.clear()

                # Add new items
                for item_data in recipe_data['items']:
                    item = ProjectComponent(
                        material_name=item_data['material_name'],
                        quantity=item_data['quantity'],
                        unit=item_data['unit']
                    )
                    pattern.items.append(item)

                # Recalculate cost
                pattern.total_cost = self._calculate_materials_cost(pattern)

            self.session.commit()
            self.logger.info(f"Updated pattern: {pattern.name}")
            return pattern

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating pattern {recipe_id}: {str(e)}")
            raise Exception(f"Failed to update pattern {recipe_id}") from e

    def delete_project(self, recipe_id: int) -> None:
        """Delete a pattern and its items."""
        try:
            pattern = self.get_recipe_by_id(recipe_id)
            if not pattern:
                raise Exception(f"Project {recipe_id} not found")

            self.session.delete(pattern)
            self.session.commit()
            self.logger.info(f"Deleted pattern: {pattern.name}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting pattern {recipe_id}: {str(e)}")
            raise Exception(f"Failed to delete pattern {recipe_id}") from e

    def check_materials_availability(self, recipe_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Check if all materials are available for producing a pattern."""
        try:
            pattern = self.get_recipe_by_id(recipe_id)
            if not pattern:
                raise Exception(f"Project {recipe_id} not found")

            missing_materials = []
            available_materials = []

            for item in pattern.items:
                # TODO: Integrate with inventory service
                # For now, we'll mock the availability check
                available = True  # This should check actual inventory
                required_quantity = item.quantity * quantity

                if available:
                    available_materials.append({
                        'material_name': item.material_name,
                        'required_quantity': required_quantity,
                        'unit': item.unit
                    })
                else:
                    missing_materials.append({
                        'material_name': item.material_name,
                        'required_quantity': required_quantity,
                        'unit': item.unit
                    })

            return {
                'recipe_id': recipe_id,
                'recipe_name': pattern.name,
                'quantity': quantity,
                'can_produce': len(missing_materials) == 0,
                'missing_materials': missing_materials,
                'available_materials': available_materials
            }

        except Exception as e:
            self.logger.error(f"Error checking materials for pattern {recipe_id}: {str(e)}")
            raise Exception(f"Failed to check materials for pattern {recipe_id}") from e

    def calculate_production_cost(self, recipe_id: int, quantity: int = 1) -> Dict[str, float]:
        """Calculate the total cost of producing a pattern."""
        try:
            pattern = self.get_recipe_by_id(recipe_id)
            if not pattern:
                raise Exception(f"Project {recipe_id} not found")

            material_cost = self._calculate_materials_cost(pattern) * quantity
            labor_cost = self._calculate_labor_cost(pattern) * quantity
            total_cost = material_cost + labor_cost

            return {
                'material_cost': material_cost,
                'labor_cost': labor_cost,
                'total_cost': total_cost
            }

        except Exception as e:
            self.logger.error(f"Error calculating costs for pattern {recipe_id}: {str(e)}")
            raise Exception(f"Failed to calculate costs for pattern {recipe_id}") from e

    def get_recipes_by_category(self, category: str) -> List[Project]:
        """Get all patterns in a specific category."""
        try:
            return (self.session.query(Project)
                    .filter(Project.category == category)
                    .order_by(Project.name)
                    .all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving patterns for category {category}: {str(e)}")
            raise Exception(f"Failed to retrieve patterns for category {category}") from e

    def search_recipes(self, search_term: str) -> List[Project]:
        """Search patterns by name or description."""
        try:
            return (self.session.query(Project)
                    .filter(or_(
                Project.name.ilike(f"%{search_term}%"),
                Project.description.ilike(f"%{search_term}%")
            ))
                    .order_by(Project.name)
                    .all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error searching patterns: {str(e)}")
            raise Exception("Failed to search patterns") from e

    def _calculate_materials_cost(self, pattern: Project) -> float:
        """Calculate the total cost of materials for a pattern."""
        total_cost = 0.0
        for item in pattern.items:
            # TODO: Get actual material costs from inventory/pricing service
            # For now, we'll use a mock cost
            unit_cost = 1.0  # This should get the actual material cost
            total_cost += item.quantity * unit_cost
        return total_cost

    def _calculate_labor_cost(self, pattern: Project) -> float:
        """Calculate the labor cost for a pattern."""
        # TODO: Implement proper labor cost calculation
        # For now, use a simple time-based calculation
        hourly_rate = 20.0  # This should be configurable
        hours = pattern.preparation_time / 60.0  # Convert minutes to hours
        return hours * hourly_rate

    def cleanup(self) -> None:
        """Clean up service resources."""
        if self.session:
            self.session.close()