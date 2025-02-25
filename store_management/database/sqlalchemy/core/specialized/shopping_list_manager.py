# shopping_list_manager.py
"""
Shopping List Manager module for handling shopping list operations.

This module provides a specialized manager for ShoppingList model operations,
with comprehensive methods for creating, retrieving, and managing shopping lists.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from models.shopping_list import ShoppingList, ShoppingListItem
from core.managers.base_manager import BaseManager
from core.exceptions import DatabaseError

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ShoppingListManager(BaseManager):
    """
    Specialized manager for ShoppingList model operations.

    This class extends BaseManager with shopping list-specific operations,
    providing methods for creating, retrieving, and managing shopping lists.
    """

    @inject(MaterialService)
    def __init__(self, session_factory, material_service: MaterialService):
        """
        Initialize the ShoppingListManager.

        Args:
            session_factory: Database session factory
            material_service (MaterialService): Service for material-related operations
        """
        super().__init__(ShoppingList, session_factory)
        self._material_service = material_service

    def get_shopping_list_with_items(self, list_id: int) -> Optional[ShoppingList]:
        """
        Retrieve a shopping list with all its items.

        Args:
            list_id (int): Shopping list ID

        Returns:
            Optional[ShoppingList]: Shopping list with loaded items or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = (
                    select(ShoppingList)
                    .options(joinedload(ShoppingList.items))
                    .filter(ShoppingList.id == list_id)
                )
                result = session.execute(query)
                shopping_list = result.scalar_one_or_none()
                return shopping_list
        except SQLAlchemyError as e:
            logger.error(f'Error getting shopping list with items: {e}')
            raise DatabaseError(f'Error getting shopping list with items: {e}') from e

    def create_shopping_list(
            self,
            data: Dict[str, Any],
            items: Optional[List[Dict[str, Any]]] = None
    ) -> ShoppingList:
        """
        Create a new shopping list with optional items.

        Args:
            data (Dict[str, Any]): Shopping list data (name, description, etc.)
            items (Optional[List[Dict[str, Any]]], optional): Optional list of shopping list items

        Returns:
            ShoppingList: Created shopping list instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self.session_scope() as session:
                # Create shopping list
                shopping_list = ShoppingList(**data)
                session.add(shopping_list)
                session.commit()
                session.refresh(shopping_list)

                # Add items if provided
                if items:
                    for item_data in items:
                        item = ShoppingListItem(
                            **item_data,
                            shopping_list_id=shopping_list.id
                        )
                        session.add(item)
                    session.commit()
                    session.refresh(shopping_list)

                return shopping_list
        except SQLAlchemyError as e:
            logger.error(f'Error creating shopping list: {e}')
            raise DatabaseError(f'Error creating shopping list: {e}') from e

    def mark_item_purchased(
            self,
            item_id: int,
            purchase_data: Dict[str, Any]
    ) -> None:
        """
        Mark a shopping list item as purchased.

        Args:
            item_id (int): Shopping list item ID
            purchase_data (Dict[str, Any]): Purchase details (date, price)

        Raises:
            DatabaseError: If item update fails
            ValueError: If item not found
        """
        try:
            with self.session_scope() as session:
                item = session.get(ShoppingListItem, item_id)
                if item:
                    # Update item attributes dynamically
                    for key, value in purchase_data.items():
                        setattr(item, key, value)
                    item.purchased = True
                    session.commit()
                else:
                    raise ValueError(f'Shopping list item with ID {item_id} not found')
        except (ValueError, SQLAlchemyError) as e:
            logger.error(f'Error marking item purchased: {e}')
            raise DatabaseError(f'Error marking item purchased: {e}') from e

    def get_pending_items(self) -> List[ShoppingListItem]:
        """
        Retrieve all unpurchased shopping list items.

        Returns:
            List[ShoppingListItem]: List of unpurchased shopping list items

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(ShoppingListItem).where(ShoppingListItem.purchased == False)
                result = session.execute(query)
                pending_items = result.scalars().all()
                return pending_items
        except SQLAlchemyError as e:
            logger.error(f'Error getting pending items: {e}')
            raise DatabaseError(f'Error getting pending items: {e}') from e

    def get_items_by_supplier(self, supplier_id: int) -> List[ShoppingListItem]:
        """
        Retrieve shopping list items for a specific supplier.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            List[ShoppingListItem]: List of shopping list items for the supplier

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                # TODO: Implement proper supplier-based item retrieval
                # This is a placeholder implementation
                query = (
                    select(ShoppingListItem)
                    .join(ShoppingList)  # Add appropriate joins
                    .where(ShoppingList.supplier_id == supplier_id)
                )
                result = session.execute(query)
                supplier_items = result.scalars().all()
                return supplier_items
        except SQLAlchemyError as e:
            logger.error(f'Error getting supplier items: {e}')
            raise DatabaseError(f'Error getting supplier items: {e}') from e

    def get_shopping_list_summary(self, list_id: int) -> Dict[str, Any]:
        """
        Retrieve a summary of a shopping list.

        Args:
            list_id (int): ID of the list to summarize

        Returns:
            Dict[str, Any]: Dictionary with summary information

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                # Calculate total items and total quantity
                query = (
                    select(
                        func.count(ShoppingListItem.id).label('total_items'),
                        func.sum(ShoppingListItem.quantity).label('total_quantity')
                    )
                    .where(ShoppingListItem.shopping_list_id == list_id)
                )
                result = session.execute(query).one()
                total_items, total_quantity = result

                return {
                    'total_items': total_items or 0,
                    'total_quantity': total_quantity or 0
                }
        except SQLAlchemyError as e:
            logger.error(f'Error getting shopping list summary: {e}')
            raise DatabaseError(f'Error getting shopping list summary: {e}') from e