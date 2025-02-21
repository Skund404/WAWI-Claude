# store_management/database/repositories/recipe_repository.py

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from ..interfaces.base_repository import BaseRepository
from ..models.recipe import Recipe, RecipeItem


class RecipeRepository(BaseRepository[Recipe]):
    """Repository for Recipe model operations"""

    def __init__(self, session: Session):
        super().__init__(session, Recipe)

    def get_with_items(self, recipe_id: int) -> Optional[Recipe]:
        """
        Get recipe with all items.

        Args:
            recipe_id: Recipe ID

        Returns:
            Recipe with loaded items or None
        """
        return self.session.query(Recipe) \
            .options(joinedload(Recipe.items).joinedload(RecipeItem.part),
                     joinedload(Recipe.items).joinedload(RecipeItem.leather)) \
            .filter(Recipe.id == recipe_id) \
            .first()

    def get_by_product(self, product_id: int) -> List[Recipe]:
        """
        Get recipes for a product.

        Args:
            product_id: Product ID

        Returns:
            List of recipes for the product
        """
        return self.session.query(Recipe).filter(Recipe.product_id == product_id).all()

    def get_recipe_item(self, item_id: int) -> Optional[RecipeItem]:
        """
        Get a specific recipe item.

        Args:
            item_id: Recipe item ID

        Returns:
            Recipe item or None
        """
        return self.session.query(RecipeItem).get(item_id)

    def add_recipe_item(self, recipe_id: int, item_data: dict) -> RecipeItem:
        """
        Add an item to a recipe.

        Args:
            recipe_id: Recipe ID
            item_data: Item data

        Returns:
            Created recipe item
        """
        item_data['recipe_id'] = recipe_id
        item = RecipeItem(**item_data)
        self.session.add(item)
        return item