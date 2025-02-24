# database/repositories/interfaces/pattern_service.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from enum import Enum

class RecipeStatus(Enum):
    """Enumeration of recipe statuses"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    TESTING = "testing"

class IRecipeService(ABC):
    """
    Interface defining the contract for recipe service implementations.
    Handles recipe creation, management, and analysis functionality.
    """

    @abstractmethod
    def get_all_recipes(self) -> List[Dict]:
        """
        Retrieve all recipes.

        Returns:
            List[Dict]: List of all recipes
        """
        pass

    @abstractmethod
    def get_recipe_by_id(self, recipe_id: int) -> Dict:
        """
        Retrieve recipe details by ID.

        Args:
            recipe_id (int): ID of the recipe to retrieve

        Returns:
            Dict: Recipe details

        Raises:
            NotFoundError: If recipe is not found
        """
        pass

    @abstractmethod
    def get_recipe_by_number(self, recipe_number: str) -> Dict:
        """
        Retrieve recipe by its unique number.

        Args:
            recipe_number (str): Unique recipe number

        Returns:
            Dict: Recipe details

        Raises:
            NotFoundError: If recipe is not found
        """
        pass

    @abstractmethod
    def create_recipe(self, recipe_data: Dict) -> Dict:
        """
        Create a new recipe.

        Args:
            recipe_data (Dict): Recipe information including:
                - name: str
                - description: str
                - status: RecipeStatus
                - items: List[Dict]
                - estimated_time: float
                - difficulty_level: str

        Returns:
            Dict: Created recipe data

        Raises:
            ValidationError: If recipe data is invalid
        """
        pass

    @abstractmethod
    def update_recipe(self, recipe_id: int, recipe_data: Dict) -> Dict:
        """
        Update an existing recipe.

        Args:
            recipe_id (int): ID of the recipe to update
            recipe_data (Dict): Updated recipe information

        Returns:
            Dict: Updated recipe details

        Raises:
            NotFoundError: If recipe is not found
            ValidationError: If update data is invalid
        """
        pass

    @abstractmethod
    def delete_recipe(self, recipe_id: int) -> bool:
        """
        Delete a recipe by ID.

        Args:
            recipe_id (int): ID of the recipe to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If recipe is not found
        """
        pass

    @abstractmethod
    def add_recipe_item(self, recipe_id: int, item_data: Dict) -> Dict:
        """
        Add an item to an existing recipe.

        Args:
            recipe_id (int): ID of the recipe
            item_data (Dict): Item information including:
                - material_id: int
                - quantity: float
                - instructions: str
                - order: int

        Returns:
            Dict: Updated recipe details

        Raises:
            NotFoundError: If recipe is not found
            ValidationError: If item data is invalid
        """
        pass

    @abstractmethod
    def remove_recipe_item(self, recipe_id: int, item_id: int) -> Dict:
        """
        Remove an item from a recipe.

        Args:
            recipe_id (int): ID of the recipe
            item_id (int): ID of the item to remove

        Returns:
            Dict: Updated recipe details

        Raises:
            NotFoundError: If recipe or item is not found
        """
        pass

    @abstractmethod
    def check_materials_availability(self, recipe_id: int, quantity: int = 1) -> Dict:
        """
        Check if all materials for a recipe are available.

        Args:
            recipe_id (int): ID of the recipe to check
            quantity (int): Number of times to make the recipe

        Returns:
            Dict: Availability status for each material

        Raises:
            NotFoundError: If recipe is not found
        """
        pass

    @abstractmethod
    def calculate_recipe_cost(self, recipe_id: int, include_labor: bool = True) -> Dict:
        """
        Calculate the total cost of a recipe.

        Args:
            recipe_id (int): ID of the recipe
            include_labor (bool): Whether to include labor costs

        Returns:
            Dict: Cost breakdown including:
                - materials_cost: float
                - labor_cost: float
                - total_cost: float

        Raises:
            NotFoundError: If recipe is not found
        """
        pass

    @abstractmethod
    def duplicate_recipe(self, recipe_id: int, new_name: str) -> Dict:
        """
        Create a duplicate of an existing recipe.

        Args:
            recipe_id (int): ID of the recipe to duplicate
            new_name (str): Name for the new recipe

        Returns:
            Dict: New recipe details

        Raises:
            NotFoundError: If recipe is not found
            ValidationError: If new name is invalid
        """
        pass

    @abstractmethod
    def search_recipes(self, search_params: Dict) -> List[Dict]:
        """
        Search recipes based on given parameters.

        Args:
            search_params (Dict): Search parameters which may include:
                - name: str
                - status: RecipeStatus
                - difficulty_level: str
                - material_id: int
                - date_range: tuple

        Returns:
            List[Dict]: List of matching recipes
        """
        pass