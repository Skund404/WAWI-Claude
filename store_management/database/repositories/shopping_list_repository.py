# store_management/database/repositories/shopping_list_repository.py
"""
Repository for managing shopping list related database operations.

Provides specialized methods for retrieving, creating, and managing
shopping lists with advanced querying capabilities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces import InventoryService
from models.shopping_list import ShoppingList, ShoppingListItem
from models.part import Part
from models.leather import Leather

# Configure logging
logger = logging.getLogger(__name__)


class ShoppingListRepository:
    """
    Repository for ShoppingList model operations.

    Provides methods to interact with shopping lists, including 
    retrieval, filtering, and advanced querying.
    """

    @inject(InventoryService)
    def __init__(self, session):
        """
        Initialize the ShoppingListRepository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_with_items(self, list_id: int) -> Optional[ShoppingList]:
        """
        Retrieve a shopping list with all its items.

        Args:
            list_id (int): Unique identifier of the shopping list

        Returns:
            Optional[ShoppingList]: Shopping list with loaded items or None
        """
        try:
            return (
                self.session.query(ShoppingList)
                .options(joinedload(ShoppingList.items))
                .filter(ShoppingList.id == list_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving shopping list with items for ID {list_id}: {e}')
            raise

    def get_pending_items(self) -> List[ShoppingListItem]:
        """
        Retrieve all unpurchased shopping list items.

        Returns:
            List[ShoppingListItem]: List of unpurchased shopping list items
        """
        try:
            return (
                self.session.query(ShoppingListItem)
                .filter(ShoppingListItem.purchased == False)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving pending shopping list items: {e}')
            raise

    def get_items_by_supplier(self, supplier_id: int) -> List[ShoppingListItem]:
        """
        Retrieve shopping list items for a specific supplier.

        This method joins through parts and leather to find items 
        associated with a particular supplier.

        Args:
            supplier_id (int): Unique identifier of the supplier

        Returns:
            List[ShoppingListItem]: Shopping list items for the supplier
        """
        try:
            # Query items through parts
            part_items = (
                self.session.query(ShoppingListItem)
                .join(Part, ShoppingListItem.part_id == Part.id)
                .filter(Part.supplier_id == supplier_id)
                .all()
            )

            # Query items through leather
            leather_items = (
                self.session.query(ShoppingListItem)
                .join(Leather, ShoppingListItem.leather_id == Leather.id)
                .filter(Leather.supplier_id == supplier_id)
                .all()
            )

            # Combine and return unique items
            return list(set(part_items + leather_items))
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving shopping list items for supplier {supplier_id}: {e}')
            raise

    def create_shopping_list(self, shopping_list_data: Dict[str, Any]) -> ShoppingList:
        """
        Create a new shopping list with items.

        Args:
            shopping_list_data (Dict[str, Any]): Shopping list creation data

        Returns:
            ShoppingList: Created shopping list instance

        Raises:
            ValueError: If shopping list validation fails
        """
        try:
            # Validate required fields
            if 'items' not in shopping_list_data or not shopping_list_data['items']:
                raise ValueError("Shopping list must have at least one item")

            # Separate items from shopping list data
            items_data = shopping_list_data.pop('items', [])

            # Create shopping list instance
            shopping_list = ShoppingList(**shopping_list_data)

            # Add shopping list to session
            self.session.add(shopping_list)

            # Add shopping list items
            for item_data in items_data:
                item = ShoppingListItem(**item_data)
                item.shopping_list = shopping_list
                self.session.add(item)

            # Commit transaction
            self.session.commit()

            return shopping_list
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error creating shopping list: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error creating shopping list: {e}')
            raise

    def update_shopping_list(
            self,
            list_id: int,
            shopping_list_data: Dict[str, Any]
    ) -> ShoppingList:
        """
        Update an existing shopping list.

        Args:
            list_id (int): ID of the shopping list to update
            shopping_list_data (Dict[str, Any]): Updated shopping list data

        Returns:
            ShoppingList: Updated shopping list instance

        Raises:
            ValueError: If shopping list validation fails
        """
        try:
            # Retrieve existing shopping list
            existing_list = self.get_with_items(list_id)

            if not existing_list:
                raise ValueError(f'Shopping list with ID {list_id} not found')

            # Validate required fields
            if 'items' not in shopping_list_data or not shopping_list_data['items']:
                raise ValueError("Shopping list must have at least one item")

            # Separate items from shopping list data
            items_data = shopping_list_data.pop('items', [])

            # Update shopping list attributes
            for key, value in shopping_list_data.items():
                if hasattr(existing_list, key):
                    setattr(existing_list, key, value)

            # Clear existing items
            existing_list.items.clear()

            # Add new items
            for item_data in items_data:
                item = ShoppingListItem(**item_data)
                item.shopping_list = existing_list
                self.session.add(item)

            # Commit transaction
            self.session.commit()

            return existing_list
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error updating shopping list: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error updating shopping list: {e}')
            raise

    def delete_shopping_list(self, list_id: int) -> bool:
        """
        Delete a shopping list and its associated items.

        Args:
            list_id (int): ID of the shopping list to delete

        Returns:
            bool: True if deletion was successful
        """
        try:
            # Retrieve shopping list
            shopping_list = self.get_with_items(list_id)

            if not shopping_list:
                raise ValueError(f'Shopping list with ID {list_id} not found')

            # Delete associated items first
            for item in shopping_list.items:
                self.session.delete(item)

            # Delete shopping list
            self.session.delete(shopping_list)

            # Commit transaction
            self.session.commit()

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error deleting shopping list: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error deleting shopping list: {e}')
            raise