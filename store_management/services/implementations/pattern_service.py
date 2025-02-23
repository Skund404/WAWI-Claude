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
    Service implementation for managing recipes.

    Handles:
    - Project CRUD operations
    - Material requirements checking
    - Cost calculations
    - Project search and categorization
    """

    def __init__(self, container: Any) -> None:
        """
        Initialize the recipe service.

        Args:
            container: Dependency injection container
        """
        self.logger = logging.getLogger(__name__)
        self.session: Session = get_db_session()

    def get_all_recipes(self) -> List[Project]:
        """Get all recipes from the database."""
        try:
            return self.session.query(Project).order_by(Project.name).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving recipes: {str(e)}")
            raise Exception("Failed to retrieve recipes") from e

    def get_recipe_by_id(self, recipe_id: int) -> Optional[Project]:
        """Get a specific recipe by ID."""
        try:
            return self.session.query(Project).filter(Project.id == recipe_id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving recipe {recipe_id}: {str(e)}")
            raise Exception(f"Failed to retrieve recipe {recipe_id}") from e

    def create_project(self, recipe_data: Dict[str, Any]) -> Project:
        """Create a new recipe with its items."""
        try:
            # Create recipe
            recipe = Project(
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
                    recipe.items.append(item)

            # Calculate initial cost
            recipe.total_cost = self._calculate_materials_cost(recipe)

            self.session.add(recipe)
            self.session.commit()

            self.logger.info(f"Created recipe: {recipe.name}")
            return recipe

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating recipe: {str(e)}")
            raise Exception("Failed to create recipe") from e

    def update_project(self, recipe_id: int, recipe_data: Dict[str, Any]) -> Project:
        """Update an existing recipe."""
        try:
            recipe = self.get_recipe_by_id(recipe_id)
            if not recipe:
                raise Exception(f"Project {recipe_id} not found")

            # Update basic fields
            recipe.name = recipe_data.get('name', recipe.name)
            recipe.description = recipe_data.get('description', recipe.description)
            recipe.preparation_time = recipe_data.get('preparation_time', recipe.preparation_time)

            # Update items if provided
            if 'items' in recipe_data:
                # Clear existing items
                recipe.items.clear()

                # Add new items
                for item_data in recipe_data['items']:
                    item = ProjectComponent(
                        material_name=item_data['material_name'],
                        quantity=item_data['quantity'],
                        unit=item_data['unit']
                    )
                    recipe.items.append(item)

                # Recalculate cost
                recipe.total_cost = self._calculate_materials_cost(recipe)

            self.session.commit()
            self.logger.info(f"Updated recipe: {recipe.name}")
            return recipe

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating recipe {recipe_id}: {str(e)}")
            raise Exception(f"Failed to update recipe {recipe_id}") from e

    def delete_project(self, recipe_id: int) -> None:
        """Delete a recipe and its items."""
        try:
            recipe = self.get_recipe_by_id(recipe_id)
            if not recipe:
                raise Exception(f"Project {recipe_id} not found")

            self.session.delete(recipe)
            self.session.commit()
            self.logger.info(f"Deleted recipe: {recipe.name}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
            raise Exception(f"Failed to delete recipe {recipe_id}") from e

    def check_materials_availability(self, recipe_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Check if all materials are available for producing a recipe."""
        try:
            recipe = self.get_recipe_by_id(recipe_id)
            if not recipe:
                raise Exception(f"Project {recipe_id} not found")

            missing_materials = []
            available_materials = []

            for item in recipe.items:
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
                'recipe_name': recipe.name,
                'quantity': quantity,
                'can_produce': len(missing_materials) == 0,
                'missing_materials': missing_materials,
                'available_materials': available_materials
            }

        except Exception as e:
            self.logger.error(f"Error checking materials for recipe {recipe_id}: {str(e)}")
            raise Exception(f"Failed to check materials for recipe {recipe_id}") from e

    def calculate_production_cost(self, recipe_id: int, quantity: int = 1) -> Dict[str, float]:
        """Calculate the total cost of producing a recipe."""
        try:
            recipe = self.get_recipe_by_id(recipe_id)
            if not recipe:
                raise Exception(f"Project {recipe_id} not found")

            material_cost = self._calculate_materials_cost(recipe) * quantity
            labor_cost = self._calculate_labor_cost(recipe) * quantity
            total_cost = material_cost + labor_cost

            return {
                'material_cost': material_cost,
                'labor_cost': labor_cost,
                'total_cost': total_cost
            }

        except Exception as e:
            self.logger.error(f"Error calculating costs for recipe {recipe_id}: {str(e)}")
            raise Exception(f"Failed to calculate costs for recipe {recipe_id}") from e

    def get_recipes_by_category(self, category: str) -> List[Project]:
        """Get all recipes in a specific category."""
        try:
            return (self.session.query(Project)
                    .filter(Project.category == category)
                    .order_by(Project.name)
                    .all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving recipes for category {category}: {str(e)}")
            raise Exception(f"Failed to retrieve recipes for category {category}") from e

    def search_recipes(self, search_term: str) -> List[Project]:
        """Search recipes by name or description."""
        try:
            return (self.session.query(Project)
                    .filter(or_(
                Project.name.ilike(f"%{search_term}%"),
                Project.description.ilike(f"%{search_term}%")
            ))
                    .order_by(Project.name)
                    .all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error searching recipes: {str(e)}")
            raise Exception("Failed to search recipes") from e

    def _calculate_materials_cost(self, recipe: Project) -> float:
        """Calculate the total cost of materials for a recipe."""
        total_cost = 0.0
        for item in recipe.items:
            # TODO: Get actual material costs from inventory/pricing service
            # For now, we'll use a mock cost
            unit_cost = 1.0  # This should get the actual material cost
            total_cost += item.quantity * unit_cost
        return total_cost

    def _calculate_labor_cost(self, recipe: Project) -> float:
        """Calculate the labor cost for a recipe."""
        # TODO: Implement proper labor cost calculation
        # For now, use a simple time-based calculation
        hourly_rate = 20.0  # This should be configurable
        hours = recipe.preparation_time / 60.0  # Convert minutes to hours
        return hours * hourly_rate

    def cleanup(self) -> None:
        """Clean up service resources."""
        if self.session:
            self.session.close()