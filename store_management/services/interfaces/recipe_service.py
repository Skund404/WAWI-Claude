# services/interfaces/recipe_service.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from database.models.recipe import Project


class IRecipeService(ABC):
    """
    Interface defining the contract for recipe management services.

    Specifies all operations that must be supported by recipe service implementations.
    """

    @abstractmethod
    def get_all_recipes(self) -> List[Project]:
        """
        Get all recipes in the system.

        Returns:
            List of Project objects

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Project]:
        """
        Get a recipe by its ID.

        Args:
            recipe_id: ID of the recipe to retrieve

        Returns:
            Project object if found, None otherwise

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def create_project(self, recipe_data: Dict[str, Any]) -> Project:
        """
        Create a new recipe.

        Args:
            recipe_data: Dictionary containing recipe data and items

        Returns:
            Created Project object

        Raises:
            Exception: If creation fails
        """
        pass

    @abstractmethod
    def update_project(self, recipe_id: int, recipe_data: Dict[str, Any]) -> Project:
        """
        Update an existing recipe.

        Args:
            recipe_id: ID of the recipe to update
            recipe_data: Dictionary containing updated recipe data

        Returns:
            Updated Project object

        Raises:
            Exception: If update fails
        """
        pass

    @abstractmethod
    def delete_project(self, recipe_id: int) -> None:
        """
        Delete a recipe.

        Args:
            recipe_id: ID of the recipe to delete

        Raises:
            Exception: If deletion fails
        """
        pass

    @abstractmethod
    def check_materials_availability(self, recipe_id: int, quantity: int = 1) -> Dict[str, Any]:
        """
        Check if materials are available for producing a recipe.

        Args:
            recipe_id: ID of the recipe to check
            quantity: Number of items to produce

        Returns:
            Dictionary containing availability status and missing materials

        Raises:
            Exception: If check fails
        """
        pass

    @abstractmethod
    def calculate_production_cost(self, recipe_id: int, quantity: int = 1) -> Dict[str, float]:
        """
        Calculate the cost of producing a recipe.

        Args:
            recipe_id: ID of the recipe to calculate
            quantity: Number of items to produce

        Returns:
            Dictionary containing material costs, labor costs, and total cost

        Raises:
            Exception: If calculation fails
        """
        pass

    @abstractmethod
    def get_recipes_by_category(self, category: str) -> List[Project]:
        """
        Get all recipes in a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of matching Project objects

        Raises:
            Exception: If retrieval fails
        """
        pass

    @abstractmethod
    def search_recipes(self, search_term: str) -> List[Project]:
        """
        Search recipes by name or description.

        Args:
            search_term: Term to search for

        Returns:
            List of matching Project objects

        Raises:
            Exception: If search fails
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the service."""
        pass