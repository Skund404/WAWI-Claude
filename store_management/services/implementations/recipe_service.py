# Path: store_management/services/implementations/recipe_service.py
from typing import List, Dict, Any, Optional, Tuple

from di.service import Service
from di.container import DependencyContainer
from services.interfaces.recipe_service import IRecipeService
from database.sqlalchemy.core.specialized.recipe_manager import RecipeManager

class RecipeService(Service, IRecipeService):
    """Service for recipe management operations"""

    def __init__(self, container: DependencyContainer):
        """
        Initialize with appropriate managers.

        Args:
            container: Dependency injection container
        """
        super().__init__(container)
        self.recipe_manager = self.get_dependency(RecipeManager)

    def get_all_recipes(self) -> List[Dict[str, Any]]:
        """
        Retrieve all recipes.

        Returns:
            List of recipe dictionaries
        """
        try:
            recipes = self.recipe_manager.get_all()
            return [self._to_dict(recipe) for recipe in recipes]
        except Exception as e:
            print(f"Error retrieving recipes: {e}")
            return []

    def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Get recipe details by ID.

        Args:
            recipe_id: Recipe ID

        Returns:
            Recipe details or None if not found
        """
        try:
            recipe = self.recipe_manager.get(recipe_id)
            return self._to_dict(recipe) if recipe else None
        except Exception as e:
            print(f"Error retrieving recipe {recipe_id}: {e}")
            return None

    def create_recipe(self, recipe_data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new recipe with items.

        Args:
            recipe_data: Dictionary with recipe data
            items: Optional list of recipe item data

        Returns:
            Tuple of (created recipe or None, result message)
        """
        try:
            # Prepare items if provided
            if items:
                recipe_data['items'] = items

            new_recipe = self.recipe_manager.create(recipe_data)
            return self._to_dict(new_recipe)
        except Exception as e:
            print(f"Error creating recipe: {e}")
            return None

    def update_recipe(self, recipe_id: int, recipe_data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing recipe.

        Args:
            recipe_id: ID of the recipe to update
            recipe_data:
            Updated recipe data
            items: Optional list of recipe item data

        Returns:
            Updated recipe or None
        """
        try:
            # Prepare update data
            update_data = recipe_data.copy()

            # If items are provided, include them in the update
            if items:
                update_data['items'] = items

            updated_recipe = self.recipe_manager.update(recipe_id, update_data)
            return self._to_dict(updated_recipe)
        except Exception as e:
            print(f"Error updating recipe {recipe_id}: {e}")
            return None

    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe.

        Args:
            recipe_id: ID of the recipe to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            return self.recipe_manager.delete(recipe_id)
        except Exception as e:
            print(f"Error deleting recipe {recipe_id}: {e}")
            return False

    def check_materials_availability(self, recipe_id: int, quantity: int) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check if materials for a recipe are available in sufficient quantity.

        Args:
            recipe_id: Recipe ID
            quantity: Number of items to produce

        Returns:
            Tuple of (all materials available, list of missing items)
        """
        try:
            # Delegate to recipe manager's availability check
            available, missing_items = self.recipe_manager.check_materials_availability(recipe_id, quantity)

            # Convert missing items to dictionaries if needed
            formatted_missing_items = [
                {
                    'item_id': item.get('id'),
                    'name': item.get('name', 'Unknown'),
                    'required_quantity': item.get('required_quantity'),
                    'available_quantity': item.get('available_quantity')
                }
                for item in missing_items
            ]

            return available, formatted_missing_items
        except Exception as e:
            print(f"Error checking materials availability for recipe {recipe_id}: {e}")
            return False, []

    def _to_dict(self, recipe):
        """
        Convert recipe model to dictionary.

        Args:
            recipe: Recipe model instance

        Returns:
            Dictionary representation of the recipe
        """
        if not recipe:
            return {}

        # Convert recipe to dictionary
        recipe_dict = {
            'id': recipe.id,
            'name': getattr(recipe, 'name', ''),
            'description': getattr(recipe, 'description', ''),
            'product_id': getattr(recipe, 'product_id', None),
            'estimated_production_time': getattr(recipe, 'estimated_production_time', 0.0),
            'notes': getattr(recipe, 'notes', ''),
            'created_at': str(getattr(recipe, 'created_at', '')),
            'updated_at': str(getattr(recipe, 'updated_at', '')),
            'items': []
        }

        # Add recipe items if available
        try:
            # Attempt to load recipe items
            # This might require a specific method from the recipe manager
            items = self.recipe_manager.get_recipe_items(recipe.id) if recipe.id else []

            recipe_dict['items'] = [
                {
                    'id': item.id,
                    'name': getattr(item, 'name', 'Unknown'),
                    'part_id': getattr(item, 'part_id', None),
                    'leather_id': getattr(item, 'leather_id', None),
                    'quantity': getattr(item, 'quantity', 0),
                    'is_optional': getattr(item, 'is_optional', False),
                    'notes': getattr(item, 'notes', '')
                }
                for item in items
            ]
        except Exception as e:
            print(f"Error loading recipe items: {e}")

        return recipe_dict