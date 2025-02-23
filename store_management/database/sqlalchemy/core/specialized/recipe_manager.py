# database/sqlalchemy/core/specialized/recipe_manager.py
"""
database/sqlalchemy/core/specialized/recipe_manager.py
Specialized manager for Project models with additional capabilities.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload

from database.sqlalchemy.core.base_manager import BaseManager
from database.sqlalchemy.models_file import Project, ProjectComponent, Part, Leather
from utils.error_handling import DatabaseError


class RecipeManager(BaseManager[Project]):
    """
    Specialized manager for Project model operations.

    Extends BaseManager with recipe-specific operations.
    """

    def get_recipe_with_items(self, recipe_id: int) -> Optional[Project]:
        """
        Get recipe with all its items.

        Args:
            recipe_id: Project ID

        Returns:
            Project with items loaded or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Project).options(
                    joinedload(Project.items)
                ).where(Project.id == recipe_id)

                result = session.execute(query)
                return result.scalars().first()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve recipe with items", str(e))

    def create_project(self, recipe_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Optional[Project]:
        """
        Create a new recipe with items.

        Args:
            recipe_data: Dictionary containing recipe data
            items: List of dictionaries containing recipe item data

        Returns:
            Created Project instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self.session_scope() as session:
                # Create recipe
                recipe = Project(**recipe_data)
                session.add(recipe)
                session.flush()  # Get recipe ID

                # Create recipe items
                for item_data in items:
                    item_data['recipe_id'] = recipe.id
                    recipe_item = ProjectComponent(**item_data)
                    session.add(recipe_item)

                session.flush()
                return recipe
        except Exception as e:
            raise DatabaseError(f"Failed to create recipe with items", str(e))

    def update_recipe_items(self, recipe_id: int, items: List[Dict[str, Any]]) -> Optional[Project]:
        """
        Update recipe items (replace existing items).

        Args:
            recipe_id: Project ID
            items: New list of recipe items

        Returns:
            Updated Project instance

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                # Get recipe
                recipe = session.get(Project, recipe_id)
                if not recipe:
                    return None

                # Delete existing items
                delete_query = ProjectComponent.__table__.delete().where(
                    ProjectComponent.recipe_id == recipe_id
                )
                session.execute(delete_query)

                # Create new items
                for item_data in items:
                    item_data['recipe_id'] = recipe_id
                    recipe_item = ProjectComponent(**item_data)
                    session.add(recipe_item)

                session.flush()
                # Reload recipe with new items
                session.refresh(recipe)
                return recipe
        except Exception as e:
            raise DatabaseError(f"Failed to update recipe items", str(e))

    def add_recipe_item(self, recipe_id: int, item_data: Dict[str, Any]) -> Optional[ProjectComponent]:
        """
        Add a single item to a recipe.

        Args:
            recipe_id: Project ID
            item_data: Dictionary containing item data

        Returns:
            Created ProjectComponent instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self.session_scope() as session:
                # Get recipe
                recipe = session.get(Project, recipe_id)
                if not recipe:
                    return None

                # Create recipe item
                item_data['recipe_id'] = recipe_id
                recipe_item = ProjectComponent(**item_data)
                session.add(recipe_item)

                session.flush()
                return recipe_item
        except Exception as e:
            raise DatabaseError(f"Failed to add recipe item", str(e))

    def check_materials_availability(self, recipe_id: int, quantity: int = 1) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check if all materials for a recipe are available in sufficient quantity.

        Args:
            recipe_id: Project ID
            quantity: Number of items to produce

        Returns:
            Tuple of (all materials available, list of missing items)

        Raises:
            DatabaseError: If check fails
        """
        try:
            with self.session_scope() as session:
                # Get recipe with items
                recipe = session.execute(
                    select(Project).options(
                        joinedload(Project.items)
                    ).where(Project.id == recipe_id)
                ).scalars().first()

                if not recipe:
                    raise ValueError(f"Project not found with ID {recipe_id}")

                missing_items = []

                # Check availability of each item
                for item in recipe.items:
                    required_quantity = item.quantity * quantity

                    if item.item_type == 'part':
                        # Check part availability
                        part = session.get(Part, item.item_id)
                        if not part or part.stock_level < required_quantity:
                            missing_items.append({
                                'item_id': item.item_id,
                                'item_type': 'part',
                                'name': part.name if part else f"Part {item.item_id}",
                                'required': required_quantity,
                                'available': part.stock_level if part else 0
                            })

                    elif item.item_type == 'leather':
                        # Check leather availability
                        leather = session.get(Leather, item.item_id)
                        if not leather or leather.area < required_quantity:
                            missing_items.append({
                                'item_id': item.item_id,
                                'item_type': 'leather',
                                'name': leather.name if leather else f"Leather {item.item_id}",
                                'required': required_quantity,
                                'available': leather.area if leather else 0
                            })

                return len(missing_items) == 0, missing_items
        except Exception as e:
            raise DatabaseError(f"Failed to check materials availability", str(e))