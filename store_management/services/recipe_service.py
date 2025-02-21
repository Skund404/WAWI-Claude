from typing import List, Dict, Any, Optional, Tuple
from store_management.database.sqlalchemy.models.recipe import Recipe, RecipeItem
from store_management.database.sqlalchemy.models.part import Part
from store_management.database.sqlalchemy.models.leather import Leather
from store_management.database.sqlalchemy.manager_factory import get_manager


class RecipeService:
    """Service for recipe management operations"""

    def __init__(self):
        """Initialize with appropriate managers"""
        self.recipe_manager = get_manager(Recipe)
        self.recipe_item_manager = get_manager(RecipeItem)
        self.part_manager = get_manager(Part)
        self.leather_manager = get_manager(Leather)

    def create_recipe(self, recipe_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Tuple[Optional[Recipe], str]:
        """Create a new recipe with items.

        Args:
            recipe_data: Dictionary with recipe data
            items: List of dictionaries with item data

        Returns:
            Tuple of (created recipe or None, result message)
        """
        try:
            # Create recipe
            recipe = self.recipe_manager.create(recipe_data)

            # Create recipe items
            for item_data in items:
                item_data['recipe_id'] = recipe.id
                self.recipe_item_manager.create(item_data)

            return recipe, "Recipe created successfully"
        except Exception as e:
            return None, f"Error creating recipe: {str(e)}"

    def check_materials_availability(self, recipe_id: int, quantity: int = 1) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check if materials for a recipe are available in sufficient quantity.

        Args:
            recipe_id: Recipe ID
            quantity: Number of items to produce

        Returns:
            Tuple of (all materials available, list of missing items)
        """
        missing_items = []

        try:
            recipe = self.recipe_manager.get(recipe_id)
            if not recipe:
                return False, [{"error": f"Recipe with ID {recipe_id} not found"}]

            # Get recipe items
            recipe_items = self.recipe_item_manager.filter_by(recipe_id=recipe_id)

            for item in recipe_items:
                required_quantity = item.quantity * quantity

                if item.part_id:
                    part = self.part_manager.get(item.part_id)
                    if not part or part.stock_level < required_quantity:
                        missing_items.append({
                            "type": "part",
                            "id": item.part_id,
                            "name": part.name if part else "Unknown",
                            "required": required_quantity,
                            "available": part.stock_level if part else 0
                        })

                if item.leather_id:
                    leather = self.leather_manager.get(item.leather_id)
                    if not leather or leather.area < required_quantity:
                        missing_items.append({
                            "type": "leather",
                            "id": item.leather_id,
                            "name": leather.name if leather else "Unknown",
                            "required": required_quantity,
                            "available": leather.area if leather else 0
                        })

            return len(missing_items) == 0, missing_items
        except Exception as e:
            return False, [{"error": f"Error checking materials: {str(e)}"}]