# store_management/database/repositories/recipe_repository.py

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from ..interfaces.base_repository import BaseRepository
from ..models.recipe import Project, ProjectComponent


class RecipeRepository(BaseRepository[Project]):
    """Repository for Project model operations"""

    def __init__(self, session: Session):
        super().__init__(session, Project)

    def get_with_items(self, recipe_id: int) -> Optional[Project]:
        """
        Get recipe with all items.

        Args:
            recipe_id: Project ID

        Returns:
            Project with loaded items or None
        """
        return self.session.query(Project) \
            .options(joinedload(Project.items).joinedload(ProjectComponent.part),
                     joinedload(Project.items).joinedload(ProjectComponent.leather)) \
            .filter(Project.id == recipe_id) \
            .first()

    def get_by_product(self, product_id: int) -> List[Project]:
        """
        Get recipes for a product.

        Args:
            product_id: Product ID

        Returns:
            List of recipes for the product
        """
        return self.session.query(Project).filter(Project.product_id == product_id).all()

    def get_recipe_item(self, item_id: int) -> Optional[ProjectComponent]:
        """
        Get a specific recipe item.

        Args:
            item_id: Project item ID

        Returns:
            Project item or None
        """
        return self.session.query(ProjectComponent).get(item_id)

    def add_recipe_item(self, recipe_id: int, item_data: dict) -> ProjectComponent:
        """
        Add an item to a recipe.

        Args:
            recipe_id: Project ID
            item_data: Item data

        Returns:
            Created recipe item
        """
        item_data['recipe_id'] = recipe_id
        item = ProjectComponent(**item_data)
        self.session.add(item)
        return item