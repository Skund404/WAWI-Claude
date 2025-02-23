from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.sqlalchemy.base_manager import BaseManager
from database.sqlalchemy.models_file import Project, ProjectComponent, Part, Leather
from utils.error_handler import DatabaseError
from utils.logger import logger


class RecipeManager(BaseManager[Project]):
    """
    Project manager implementing specialized recipe operations
    while leveraging base manager functionality.
    """

    def __init__(self, session_factory):
        """Initialize RecipeManager with session factory."""
        super().__init__(session_factory, Project)

    def create_project(self, recipe_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Project:
        """
        Create a new recipe with items.

        Args:
            recipe_data: Dictionary containing recipe data
            items: List of dictionaries containing recipe item data

        Returns:
            Created Project instance

        Raises:
            DatabaseError: If validation fails or database operation fails
        """
        try:
            # Validate required recipe fields
            required_fields = ['name', 'type', 'collection']
            missing_fields = [field for field in required_fields if field not in recipe_data]
            if missing_fields:
                raise DatabaseError(f"Missing required recipe fields: {', '.join(missing_fields)}")

            with self.session_scope() as session:
                # Create recipe
                recipe = Project(**recipe_data)
                session.add(recipe)
                session.flush()

                # Create recipe items
                for item_data in items:
                    if not all(k in item_data for k in ['item_type', 'item_id', 'quantity']):
                        raise DatabaseError("Invalid recipe item data")

                    recipe_item = ProjectComponent(
                        recipe_id=recipe.id,
                        **item_data
                    )
                    session.add(recipe_item)

                return recipe

        except SQLAlchemyError as e:
            logger.error(f"Failed to create recipe: {str(e)}")
            raise DatabaseError(f"Failed to create recipe: {str(e)}")

    def get_recipe_with_items(self, recipe_id: int) -> Optional[Project]:
        """
        Get recipe with all its items.

        Args:
            recipe_id: Project ID

        Returns:
            Project instance with items loaded or None if not found
        """
        with self.session_scope() as session:
            query = select(Project).options(
                joinedload(Project.items)
            ).filter(Project.id == recipe_id)
            return session.execute(query).scalar()

    def update_recipe_items(self, recipe_id: int, items: List[Dict[str, Any]]) -> Project:
        """
        Update recipe items (replace existing items).

        Args:
            recipe_id: Project ID
            items: New list of recipe items

        Returns:
            Updated Project instance

        Raises:
            DatabaseError: If recipe not found or validation fails
        """
        with self.session_scope() as session:
            recipe = session.get(Project, recipe_id)
            if not recipe:
                raise DatabaseError(f"Project {recipe_id} not found")

            # Remove existing items
            for item in recipe.items:
                session.delete(item)

            # Add new items
            for item_data in items:
                if not all(k in item_data for k in ['item_type', 'item_id', 'quantity']):
                    raise DatabaseError("Invalid recipe item data")

                recipe_item = ProjectComponent(
                    recipe_id=recipe_id,
                    **item_data
                )
                session.add(recipe_item)

            recipe.modified_at = datetime.utcnow()
            return recipe

    def add_recipe_item(self, recipe_id: int, item_data: Dict[str, Any]) -> ProjectComponent:
        """
        Add a single item to a recipe.

        Args:
            recipe_id: Project ID
            item_data: Dictionary containing item data

        Returns:
            Created ProjectComponent instance
        """
        with self.session_scope() as session:
            recipe = session.get(Project, recipe_id)
            if not recipe:
                raise DatabaseError(f"Project {recipe_id} not found")

            if not all(k in item_data for k in ['item_type', 'item_id', 'quantity']):
                raise DatabaseError("Invalid recipe item data")

            recipe_item = ProjectComponent(
                recipe_id=recipe_id,
                **item_data
            )
            session.add(recipe_item)
            recipe.modified_at = datetime.utcnow()
            return recipe_item

    def remove_recipe_item(self, recipe_id: int, item_id: int) -> bool:
        """
        Remove an item from a recipe.

        Args:
            recipe_id: Project ID
            item_id: Project Item ID

        Returns:
            True if item was removed, False otherwise
        """
        with self.session_scope() as session:
            item = session.query(ProjectComponent).filter(
                and_(
                    ProjectComponent.recipe_id == recipe_id,
                    ProjectComponent.id == item_id
                )
            ).first()

            if item:
                session.delete(item)
                return True
            return False

    def update_recipe_item_quantity(self, recipe_id: int, item_id: int, quantity: float) -> ProjectComponent:
        """
        Update the quantity of a recipe item.

        Args:
            recipe_id: Project ID
            item_id: Project Item ID
            quantity: New quantity

        Returns:
            Updated ProjectComponent instance
        """
        with self.session_scope() as session:
            item = session.query(ProjectComponent).filter(
                and_(
                    ProjectComponent.recipe_id == recipe_id,
                    ProjectComponent.id == item_id
                )
            ).first()

            if not item:
                raise DatabaseError(f"Project item {item_id} not found")

            item.quantity = quantity
            return item

    def check_materials_availability(self, recipe_id: int, quantity: int = 1) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check if all materials for a recipe are available in sufficient quantity.

        Args:
            recipe_id: Project ID
            quantity: Number of items to produce

        Returns:
            Tuple of (bool, list of missing items)
        """
        with self.session_scope() as session:
            recipe = self.get_recipe_with_items(recipe_id)
            if not recipe:
                raise DatabaseError(f"Project {recipe_id} not found")

            missing_items = []

            for item in recipe.items:
                required_quantity = item.quantity * quantity

                if item.item_type == 'part':
                    part = session.get(Part, item.item_id)
                    if not part or part.current_stock < required_quantity:
                        missing_items.append({
                            'item_type': 'part',
                            'item_id': item.item_id,
                            'name': part.name if part else 'Unknown',
                            'required': required_quantity,
                            'available': part.current_stock if part else 0
                        })
                elif item.item_type == 'leather':
                    leather = session.get(Leather, item.item_id)
                    if not leather or leather.available_area_sqft < required_quantity:
                        missing_items.append({
                            'item_type': 'leather',
                            'item_id': item.item_id,
                            'name': leather.name if leather else 'Unknown',
                            'required': required_quantity,
                            'available': leather.available_area_sqft if leather else 0
                        })

            return len(missing_items) == 0, missing_items

    def get_recipes_by_type(self, recipe_type: str) -> List[Project]:
        """
        Get all recipes of a specific type.

        Args:
            recipe_type: Type of recipe to filter by

        Returns:
            List of matching Project instances
        """
        query = select(Project).filter(Project.type == recipe_type)
        with self.session_scope() as session:
            return list(session.execute(query).scalars())

    def get_recipes_by_collection(self, collection: str) -> List[Project]:
        """
        Get all recipes in a specific collection.

        Args:
            collection: Collection name

        Returns:
            List of matching Project instances
        """
        query = select(Project).filter(Project.collection == collection)
        with self.session_scope() as session:
            return list(session.execute(query).scalars())

    def search_recipes(self, search_term: str) -> List[Project]:
        """
        Search recipes by various fields.

        Args:
            search_term: Term to search for

        Returns:
            List of matching Project instances
        """
        query = select(Project).filter(
            or_(
                Project.name.ilike(f"%{search_term}%"),
                Project.type.ilike(f"%{search_term}%"),
                Project.collection.ilike(f"%{search_term}%"),
                Project.notes.ilike(f"%{search_term}%")
            )
        )
        with self.session_scope() as session:
            return list(session.execute(query).scalars())

    def duplicate_recipe(self, recipe_id: int, new_name: str) -> Project:
        """
        Create a duplicate of an existing recipe.

        Args:
            recipe_id: Source recipe ID
            new_name: Name for the new recipe

        Returns:
            New Project instance
        """
        with self.session_scope() as session:
            source_recipe = self.get_recipe_with_items(recipe_id)
            if not source_recipe:
                raise DatabaseError(f"Project {recipe_id} not found")

            # Create new recipe
            new_recipe = Project(
                name=new_name,
                type=source_recipe.type,
                collection=source_recipe.collection,
                notes=source_recipe.notes,
                production_time=source_recipe.production_time,
                difficulty_level=source_recipe.difficulty_level
            )
            session.add(new_recipe)
            session.flush()

            # Copy items
            for item in source_recipe.items:
                new_item = ProjectComponent(
                    recipe_id=new_recipe.id,
                    item_type=item.item_type,
                    item_id=item.item_id,
                    quantity=item.quantity,
                    notes=item.notes
                )
                session.add(new_item)

            return new_recipe

    def calculate_recipe_cost(self, recipe_id: int) -> float:
        """
        Calculate the total cost of materials for a recipe.

        Args:
            recipe_id: Project ID

        Returns:
            Total cost of all materials
        """
        with self.session_scope() as session:
            recipe = self.get_recipe_with_items(recipe_id)
            if not recipe:
                raise DatabaseError(f"Project {recipe_id} not found")

            total_cost = 0.0
            for item in recipe.items:
                if item.item_type == 'part':
                    part = session.get(Part, item.item_id)
                    if part:
                        total_cost += part.price * item.quantity
                elif item.item_type == 'leather':
                    leather = session.get(Leather, item.item_id)
                    if leather:
                        total_cost += leather.price_per_sqft * item.quantity

            return total_cost