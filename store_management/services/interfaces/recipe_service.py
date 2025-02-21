# Path: store_management/services/interfaces/recipe_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

from store_management.services.interfaces.base_service import IBaseService


class IRecipeService(IBaseService):
    """
    Interface for recipe management operations.

    Defines the contract for services handling recipe-related functionality.
    """

    @abstractmethod
    def get_all_recipes(self) -> List[Dict[str, Any]]:
        """
        Retrieve all recipes.

        Returns:
            List of recipe dictionaries
        """
        pass

    @abstractmethod
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Get recipe details by ID.

        Args:
            recipe_id: Recipe ID

        Returns:
            Recipe details or None if not found
        """
        pass

    @abstractmethod
    def create_recipe(self, recipe_data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Optional[
        Dict[str, Any]]:
        """
        Create a new recipe with items.

        Args:
            recipe_data: Dictionary with recipe data
            items: Optional list of recipe item data

        Returns:
            Created recipe or None
        """
        pass

    @abstractmethod
    def update_recipe(self, recipe_id: int, recipe_data: Dict[str, Any],
                      items: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing recipe.

        Args:
            recipe_id: ID of the recipe to update
            recipe_data: Updated recipe data
            items: Optional list of updated recipe items

        Returns:
            Updated recipe or None
        """
        pass

    @abstractmethod
    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe.

        Args:
            recipe_id: ID of the recipe to delete

        Returns:
            True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    def check_materials_availability(self, recipe_id: int, quantity: int) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check if materials for a recipe are available in sufficient quantity.

        Args:
            recipe_id: Recipe ID
            quantity: Number of items to produce

        Returns:
            Tuple of (all materials available, list of missing items)
        """
        pass