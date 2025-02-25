#!/usr/bin/env python3
# Path: shopping_list_service.py
"""
Shopping List Service Implementation

Provides functionality for managing shopping lists, including creation,
modification, and tracking of purchased items.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from models.shopping_list import ShoppingList, ShoppingListItem, ShoppingListStatus
from exceptions import ValidationError, ApplicationError

logger = logging.getLogger(__name__)


class ShoppingListService(IShoppingListService):
    """
    Implementation of shopping list management service.

    Provides operations for creating and managing shopping lists and items.
    """

    def __init__(self, session_factory):
        """
        Initialize with session factory.

        Args:
            session_factory: SQLAlchemy session factory for database access
        """
        self.session_factory = session_factory

    def get_all_shopping_lists(self) -> List[ShoppingList]:
        """
        Get all shopping lists.

        Returns:
            List[ShoppingList]: All shopping lists in the system

        Raises:
            ApplicationError: If retrieval fails
        """
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).all()
        except Exception as e:
            logger.error(f'Failed to get shopping lists: {str(e)}')
            raise ApplicationError('Failed to retrieve shopping lists', str(e))

    def get_shopping_list_by_id(self, list_id: int) -> Optional[ShoppingList]:
        """
        Get shopping list by ID.

        Args:
            list_id (int): ID of the shopping list to retrieve

        Returns:
            Optional[ShoppingList]: The shopping list if found, None otherwise

        Raises:
            ApplicationError: If retrieval fails
        """
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).filter(ShoppingList.id == list_id).first()
        except Exception as e:
            logger.error(f'Failed to get shopping list {list_id}: {str(e)}')
            raise ApplicationError(f'Failed to retrieve shopping list {list_id}', str(e))

    def create_shopping_list(self, list_data: Dict[str, Any]) -> ShoppingList:
        """
        Create new shopping list.

        Args:
            list_data (Dict[str, Any]): Data for the new shopping list

        Returns:
            ShoppingList: The newly created shopping list

        Raises:
            ValidationError: If shopping list data is invalid
            ApplicationError: If creation fails
        """
        try:
            with self.session_factory() as session:
                self._validate_shopping_list_data(list_data)

                shopping_list = ShoppingList()
                for key, value in list_data.items():
                    if hasattr(shopping_list, key):
                        setattr(shopping_list, key, value)

                shopping_list.created_at = datetime.now()
                shopping_list.updated_at = datetime.now()
                shopping_list.status = ShoppingListStatus.ACTIVE

                session.add(shopping_list)
                session.commit()
                return shopping_list

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f'Failed to create shopping list: {str(e)}')
            raise ApplicationError('Failed to create shopping list', str(e))

    def update_shopping_list(self, list_id: int, list_data: Dict[str, Any]) -> Optional[ShoppingList]:
        """
        Update existing shopping list.

        Args:
            list_id (int): ID of the shopping list to update
            list_data (Dict[str, Any]): Updated shopping list data

        Returns:
            Optional[ShoppingList]: The updated shopping list or None if not found

        Raises:
            ValidationError: If shopping list data is invalid
            ApplicationError: If update fails
        """
        try:
            with self.session_factory() as session:
                shopping_list = session.query(ShoppingList).filter(ShoppingList.id == list_id).first()
                if not shopping_list:
                    return None

                self._validate_shopping_list_data(list_data)
                for key, value in list_data.items():
                    if hasattr(shopping_list, key):
                        setattr(shopping_list, key, value)

                shopping_list.updated_at = datetime.now()
                session.commit()
                return shopping_list

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f'Failed to update shopping list {list_id}: {str(e)}')
            raise ApplicationError(f'Failed to update shopping list {list_id}', str(e))

    def delete_shopping_list(self, list_id: int) -> bool:
        """
        Delete shopping list.

        Args:
            list_id (int): ID of the shopping list to delete

        Returns:
            bool: True if deletion was successful, False if list not found

        Raises:
            ApplicationError: If deletion fails
        """
        try:
            with self.session_factory() as session:
                shopping_list = session.query(ShoppingList).filter(ShoppingList.id == list_id).first()
                if not shopping_list:
                    return False

                session.delete(shopping_list)
                session.commit()
                return True

        except Exception as e:
            logger.error(f'Failed to delete shopping list {list_id}: {str(e)}')
            raise ApplicationError(f'Failed to delete shopping list {list_id}', str(e))

    def add_item_to_list(self, list_id: int, item_data: Dict[str, Any]) -> ShoppingListItem:
        """
        Add item to shopping list.

        Args:
            list_id (int): ID of the shopping list
            item_data (Dict[str, Any]): Data for the new item

        Returns:
            ShoppingListItem: The newly created shopping list item

        Raises:
            ValidationError: If item data is invalid
            ApplicationError: If addition fails
        """
        try:
            with self.session_factory() as session:
                shopping_list = session.query(ShoppingList).filter(ShoppingList.id == list_id).first()
                if not shopping_list:
                    raise ValidationError(f'Shopping list {list_id} not found')

                self._validate_item_data(item_data)

                item = ShoppingListItem()
                item.shopping_list_id = list_id

                for key, value in item_data.items():
                    if hasattr(item, key):
                        setattr(item, key, value)

                session.add(item)
                session.commit()
                return item

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f'Failed to add item to list {list_id}: {str(e)}')
            raise ApplicationError(f'Failed to add item to list', str(e))

    def remove_item_from_list(self, list_id: int, item_id: int) -> bool:
        """
        Remove item from shopping list.

        Args:
            list_id (int): ID of the shopping list
            item_id (int): ID of the item to remove

        Returns:
            bool: True if removal was successful, False if item not found

        Raises:
            ApplicationError: If removal fails
        """
        try:
            with self.session_factory() as session:
                item = session.query(ShoppingListItem).filter(
                    ShoppingListItem.id == item_id,
                    ShoppingListItem.shopping_list_id == list_id
                ).first()

                if not item:
                    return False

                session.delete(item)
                session.commit()
                return True

        except Exception as e:
            logger.error(f'Failed to remove item {item_id} from list {list_id}: {str(e)}')
            raise ApplicationError('Failed to remove item from list', str(e))

    def mark_item_purchased(self, list_id: int, item_id: int, quantity: float) -> bool:
        """
        Mark item as purchased.

        Args:
            list_id (int): ID of the shopping list
            item_id (int): ID of the item to mark as purchased
            quantity (float): Quantity purchased

        Returns:
            bool: True if update was successful, False if item not found

        Raises:
            ApplicationError: If update fails
        """
        try:
            with self.session_factory() as session:
                item = session.query(ShoppingListItem).filter(
                    ShoppingListItem.id == item_id,
                    ShoppingListItem.shopping_list_id == list_id
                ).first()

                if not item:
                    return False

                item.purchased_quantity = quantity
                item.purchase_date = datetime.now()
                session.commit()
                return True

        except Exception as e:
            logger.error(f'Failed to mark item {item_id} as purchased: {str(e)}')
            raise ApplicationError('Failed to mark item as purchased', str(e))

    def get_active_lists(self) -> List[ShoppingList]:
        """
        Get active shopping lists.

        Returns:
            List[ShoppingList]: List of active shopping lists

        Raises:
            ApplicationError: If retrieval fails
        """
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).filter(
                    ShoppingList.status == ShoppingListStatus.ACTIVE
                ).all()

        except Exception as e:
            logger.error(f'Failed to get active shopping lists: {str(e)}')
            raise ApplicationError('Failed to retrieve active lists', str(e))

    def get_pending_items(self) -> List[ShoppingListItem]:
        """
        Get pending items.

        Returns:
            List[ShoppingListItem]: List of items not yet purchased

        Raises:
            ApplicationError: If retrieval fails
        """
        try:
            with self.session_factory() as session:
                return session.query(ShoppingListItem).filter(
                    ShoppingListItem.purchase_date.is_(None)
                ).all()

        except Exception as e:
            logger.error(f'Failed to get pending items: {str(e)}')
            raise ApplicationError('Failed to retrieve pending items', str(e))

    def get_lists_by_status(self, status: str) -> List[ShoppingList]:
        """
        Get lists by status.

        Args:
            status (str): Status to filter by

        Returns:
            List[ShoppingList]: List of shopping lists with the specified status

        Raises:
            ApplicationError: If retrieval fails
        """
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).filter(
                    ShoppingList.status == status
                ).all()

        except Exception as e:
            logger.error(f'Failed to get lists by status {status}: {str(e)}')
            raise ApplicationError(f'Failed to retrieve lists with status {status}', str(e))

    def search_shopping_lists(self, search_term: str) -> List[ShoppingList]:
        """
        Search shopping lists.

        Args:
            search_term (str): Term to search for

        Returns:
            List[ShoppingList]: List of shopping lists matching the search term

        Raises:
            ApplicationError: If search fails
        """
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).filter(
                    ShoppingList.name.ilike(f'%{search_term}%')
                ).all()

        except Exception as e:
            logger.error(f'Failed to search shopping lists: {str(e)}')
            raise ApplicationError('Failed to search shopping lists', str(e))

    def _validate_shopping_list_data(self, list_data: Dict[str, Any]) -> None:
        """
        Validate shopping list data.

        Args:
            list_data (Dict[str, Any]): Shopping list data to validate

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        if 'name' not in list_data or not list_data['name']:
            errors.append('Shopping list name is required')

        if errors:
            raise ValidationError('Shopping list validation failed', errors)

    def _validate_item_data(self, item_data: Dict[str, Any]) -> None:
        """
        Validate shopping list item data.

        Args:
            item_data (Dict[str, Any]): Shopping list item data to validate

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        if 'name' not in item_data or not item_data['name']:
            errors.append('Item name is required')

        if 'quantity' in item_data:
            try:
                quantity = float(item_data['quantity'])
                if quantity <= 0:
                    errors.append('Quantity must be positive')
            except ValueError:
                errors.append('Invalid quantity value')

        if errors:
            raise ValidationError('Shopping list item validation failed', errors)