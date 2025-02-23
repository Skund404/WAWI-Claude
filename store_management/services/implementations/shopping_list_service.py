# services/implementations/shopping_list_service.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.interfaces.shopping_list_service import IShoppingListService
from database.models.shopping_list import ShoppingList, ShoppingListItem
from di.service import Service


class ShoppingListService(Service, IShoppingListService):
    """
    Service implementation for managing shopping lists.

    Handles:
    - Shopping list CRUD operations
    - Item management
    - Purchase tracking
    - List status management
    """

    def __init__(self, container):
        """
        Initialize the shopping list service.

        Args:
            container: Dependency injection container
        """
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
        self.shopping_list_repository = self.get_dependency('shopping_list_repository')

    def get_all_shopping_lists(self) -> List[ShoppingList]:
        """
        Get all shopping lists from the database.

        Returns:
            List of all shopping lists, ordered by creation date
        """
        try:
            return self.shopping_list_repository.get_all()
        except Exception as e:
            self.logger.error(f"Error retrieving shopping lists: {str(e)}")
            raise

    def get_shopping_list_by_id(self, list_id: int) -> Optional[ShoppingList]:
        """
        Get a specific shopping list by ID.

        Args:
            list_id: Unique identifier of the shopping list

        Returns:
            Shopping list if found, None otherwise
        """
        try:
            return self.shopping_list_repository.get(list_id)
        except Exception as e:
            self.logger.error(f"Error retrieving shopping list {list_id}: {str(e)}")
            raise

    def create_shopping_list(self, list_data: Dict[str, Any]) -> ShoppingList:
        """
        Create a new shopping list with optional items.

        Args:
            list_data: Dictionary containing shopping list details

        Returns:
            Created shopping list
        """
        try:
            # Prepare shopping list data
            shopping_list_data = {
                'name': list_data['name'],
                'description': list_data.get('description', ''),
                'status': list_data.get('status', 'active')
            }

            # Create shopping list first
            shopping_list = self.shopping_list_repository.create(shopping_list_data)

            # Add items if provided
            if 'items' in list_data:
                for item_data in list_data['items']:
                    item_data['shopping_list_id'] = shopping_list.id
                    self._add_item_to_list(item_data)

            self.logger.info(f"Created shopping list: {shopping_list.name}")
            return shopping_list

        except Exception as e:
            self.logger.error(f"Error creating shopping list: {str(e)}")
            raise

    def update_shopping_list(self, list_id: int, list_data: Dict[str, Any]) -> ShoppingList:
        """
        Update an existing shopping list.

        Args:
            list_id: ID of the shopping list to update
            list_data: Dictionary of updated fields

        Returns:
            Updated shopping list
        """
        try:
            # Update basic list details
            update_data = {
                'name': list_data.get('name'),
                'description': list_data.get('description'),
                'status': list_data.get('status')
            }

            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            # Update the list
            shopping_list = self.shopping_list_repository.update(list_id, update_data)

            # Update items if provided
            if 'items' in list_data:
                # First, remove existing items
                self._remove_all_list_items(list_id)

                # Add new items
                for item_data in list_data['items']:
                    item_data['shopping_list_id'] = list_id
                    self._add_item_to_list(item_data)

            self.logger.info(f"Updated shopping list: {shopping_list.name}")
            return shopping_list

        except Exception as e:
            self.logger.error(f"Error updating shopping list {list_id}: {str(e)}")
            raise

    def delete_shopping_list(self, list_id: int) -> None:
        """
        Delete a shopping list by ID.

        Args:
            list_id: ID of the shopping list to delete
        """
        try:
            self.shopping_list_repository.delete(list_id)
            self.logger.info(f"Deleted shopping list with ID: {list_id}")
        except Exception as e:
            self.logger.error(f"Error deleting shopping list {list_id}: {str(e)}")
            raise

    def add_item_to_list(self, list_id: int, item_data: Dict[str, Any]) -> ShoppingList:
        """
        Add a new item to an existing shopping list.

        Args:
            list_id: ID of the shopping list
            item_data: Details of the item to add

        Returns:
            Updated shopping list
        """
        try:
            # Ensure the list exists
            shopping_list = self.get_shopping_list_by_id(list_id)
            if not shopping_list:
                raise ValueError(f"Shopping list {list_id} not found")

            # Add item to list
            item_data['shopping_list_id'] = list_id
            self._add_item_to_list(item_data)

            self.logger.info(f"Added item to shopping list: {item_data.get('item_name', 'Unknown')}")
            return shopping_list

        except Exception as e:
            self.logger.error(f"Error adding item to shopping list {list_id}: {str(e)}")
            raise

    def _add_item_to_list(self, item_data: Dict[str, Any]) -> ShoppingListItem:
        """
        Internal method to add an item to a shopping list.

        Args:
            item_data: Details of the item to add

        Returns:
            Created shopping list item
        """
        try:
            return self.shopping_list_repository.add_item(item_data)
        except Exception as e:
            self.logger.error(f"Error adding item to list: {str(e)}")
            raise

    def _remove_all_list_items(self, list_id: int) -> None:
        """
        Remove all items from a shopping list.

        Args:
            list_id: ID of the shopping list
        """
        try:
            self.shopping_list_repository.remove_all_items(list_id)
        except Exception as e:
            self.logger.error(f"Error removing items from list {list_id}: {str(e)}")
            raise

    def remove_item_from_list(self, list_id: int, item_id: int) -> ShoppingList:
        """
        Remove a specific item from a shopping list.

        Args:
            list_id: ID of the shopping list
            item_id: ID of the item to remove

        Returns:
            Updated shopping list
        """
        try:
            shopping_list = self.get_shopping_list_by_id(list_id)
            if not shopping_list:
                raise ValueError(f"Shopping list {list_id} not found")

            self.shopping_list_repository.remove_item(item_id)

            self.logger.info(f"Removed item {item_id} from shopping list {list_id}")
            return shopping_list

        except Exception as e:
            self.logger.error(f"Error removing item from shopping list {list_id}: {str(e)}")
            raise

    def mark_item_purchased(self, list_id: int, item_id: int, quantity: float) -> ShoppingList:
        """
        Mark an item as purchased with the specified quantity.

        Args:
            list_id: ID of the shopping list
            item_id: ID of the item to mark
            quantity: Quantity purchased

        Returns:
            Updated shopping list
        """
        try:
            shopping_list = self.get_shopping_list_by_id(list_id)
            if not shopping_list:
                raise ValueError(f"Shopping list {list_id} not found")

            # Update item purchase status
            self.shopping_list_repository.update_item_purchase(item_id, quantity)

            # Refresh the list to get updated status
            updated_list = self.get_shopping_list_by_id(list_id)

            # Check if entire list is complete
            if all(item.purchased >= item.quantity for item in updated_list.items):
                self.update_shopping_list(list_id, {'status': 'completed'})

            self.logger.info(f"Marked item {item_id} as purchased in list {list_id}")
            return updated_list

        except Exception as e:
            self.logger.error(f"Error marking item as purchased in list {list_id}: {str(e)}")
            raise

    def get_active_lists(self) -> List[ShoppingList]:
        """
        Get all active shopping lists.

        Returns:
            List of active shopping lists
        """
        try:
            return self.shopping_list_repository.get_lists_by_status('active')
        except Exception as e:
            self.logger.error(f"Error retrieving active shopping lists: {str(e)}")
            raise

    def get_lists_by_status(self, status: str) -> List[ShoppingList]:
        """
        Get shopping lists by specific status.

        Args:
            status: Status to filter lists by

        Returns:
            List of shopping lists with given status
        """
        try:
            return self.shopping_list_repository.get_lists_by_status(status)
        except Exception as e:
            self.logger.error(f"Error retrieving shopping lists with status {status}: {str(e)}")
            raise

    def search_shopping_lists(self, search_term: str) -> List[ShoppingList]:
        """
        Search shopping lists by name or description.

        Args:
            search_term: Term to search for

        Returns:
            List of matching shopping lists
        """
        try:
            return self.shopping_list_repository.search(search_term)
        except Exception as e:
            self.logger.error(f"Error searching shopping lists: {str(e)}")
            raise

    def get_pending_items(self) -> List[Dict[str, Any]]:
        """
        Get all unpurchased items across active lists.

        Returns:
            List of pending items with detailed information
        """
        try:
            return self.shopping_list_repository.get_pending_items()
        except Exception as e:
            self.logger.error(f"Error retrieving pending items: {str(e)}")
            raise

    def get_shopping_list_summary(self, list_id: int) -> Dict[str, Any]:
        """
        Get a summary of a shopping list.

        Args:
            list_id: ID of the list to summarize

        Returns:
            Dictionary with list summary information
        """
        try:
            return self.shopping_list_repository.get_list_summary(list_id)
        except Exception as e:
            self.logger.error(f"Error generating summary for list {list_id}: {str(e)}")
            raise

    def merge_shopping_lists(self, source_ids: List[int], target_id: int) -> ShoppingList:
        """
        Merge multiple shopping lists into a target list.

        Args:
            source_ids: List of source list IDs to merge
            target_id: ID of the target list to merge into

        Returns:
            Updated target shopping list
        """
        try:
            return self.shopping_list_repository.merge_lists(source_ids, target_id)
        except Exception as e:
            self.logger.error(f"Error merging shopping lists: {str(e)}")
            raise

    def cleanup(self) -> None:
        """
        Clean up service resources.
        """
        # Any necessary cleanup operations
        self.logger.info("Shopping List Service cleanup complete")