# services/implementations/shopping_list_service.py
"""Implementation of the Shopping List Service interface."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.shopping_list_service import IShoppingListService, ShoppingListStatus


class ShoppingListService(BaseService, IShoppingListService):
    """Concrete implementation of the Shopping List Service interface.

    Provides operations for managing shopping lists in the leatherworking application.
    """

    def __init__(self):
        """Initialize the Shopping List Service."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._shopping_lists = {}
        self._shopping_list_items = {}
        self._next_list_id = 1
        self._next_item_id = 1

        self.logger.info("ShoppingListService initialized")

    def get_all_shopping_lists(self) -> List[Dict[str, Any]]:
        """Get all shopping lists.

        Returns:
            List[Dict[str, Any]]: List of all shopping list data dictionaries
        """
        self.logger.info("Retrieving all shopping lists")
        return list(self._shopping_lists.values())

    def get_shopping_list_by_id(self, shopping_list_id: int) -> Dict[str, Any]:
        """Get a shopping list by its ID.

        Args:
            shopping_list_id (int): The shopping list ID to retrieve

        Returns:
            Dict[str, Any]: Shopping list data dictionary

        Raises:
            NotFoundError: If the shopping list doesn't exist
        """
        self.logger.info(f"Retrieving shopping list with ID {shopping_list_id}")

        if shopping_list_id not in self._shopping_lists:
            self.logger.warning(f"Shopping list with ID {shopping_list_id} not found")
            raise NotFoundError(f"Shopping list with ID {shopping_list_id} not found")

        return self._shopping_lists[shopping_list_id]

    def create_shopping_list(self, shopping_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shopping list.

        Args:
            shopping_list_data (Dict[str, Any]): Shopping list data to create

        Returns:
            Dict[str, Any]: Created shopping list data

        Raises:
            ValidationError: If the shopping list data is invalid
        """
        self.logger.info("Creating new shopping list")

        # Validate required fields
        if 'name' not in shopping_list_data:
            self.logger.warning("Missing required field: name")
            raise ValidationError("Shopping list name is required")

        # Set default values
        shopping_list_id = self._next_list_id
        self._next_list_id += 1

        # Create shopping list
        shopping_list = {
            'id': shopping_list_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'status': ShoppingListStatus.DRAFT.name,
            'items': [],
            **shopping_list_data
        }

        self._shopping_lists[shopping_list_id] = shopping_list
        self.logger.info(f"Created shopping list with ID {shopping_list_id}")

        return shopping_list

    def update_shopping_list(self, shopping_list_id: int, shopping_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list to update
            shopping_list_data (Dict[str, Any]): New shopping list data

        Returns:
            Dict[str, Any]: Updated shopping list data

        Raises:
            NotFoundError: If the shopping list doesn't exist
            ValidationError: If the shopping list data is invalid
        """
        self.logger.info(f"Updating shopping list with ID {shopping_list_id}")

        # Check if shopping list exists
        if shopping_list_id not in self._shopping_lists:
            self.logger.warning(f"Shopping list with ID {shopping_list_id} not found")
            raise NotFoundError(f"Shopping list with ID {shopping_list_id} not found")

        # Get current shopping list
        shopping_list = self._shopping_lists[shopping_list_id]

        # Update fields
        for key, value in shopping_list_data.items():
            if key not in ['id', 'created_at', 'items']:
                shopping_list[key] = value

        # Update timestamp
        shopping_list['updated_at'] = datetime.now()

        self.logger.info(f"Updated shopping list with ID {shopping_list_id}")
        return shopping_list

    def delete_shopping_list(self, shopping_list_id: int) -> bool:
        """Delete a shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the shopping list doesn't exist
        """
        self.logger.info(f"Deleting shopping list with ID {shopping_list_id}")

        # Check if shopping list exists
        if shopping_list_id not in self._shopping_lists:
            self.logger.warning(f"Shopping list with ID {shopping_list_id} not found")
            raise NotFoundError(f"Shopping list with ID {shopping_list_id} not found")

        # Get shopping list
        shopping_list = self._shopping_lists[shopping_list_id]

        # Delete items
        for item_id in shopping_list.get('items', []):
            self._shopping_list_items.pop(item_id, None)

        # Delete shopping list
        del self._shopping_lists[shopping_list_id]

        self.logger.info(f"Deleted shopping list with ID {shopping_list_id}")
        return True

    def get_shopping_lists_by_status(self, status: ShoppingListStatus) -> List[Dict[str, Any]]:
        """Get shopping lists by their status.

        Args:
            status (ShoppingListStatus): The status to filter by

        Returns:
            List[Dict[str, Any]]: List of shopping list data dictionaries with the specified status
        """
        self.logger.info(f"Retrieving shopping lists with status {status}")

        # Convert enum to string for comparison if needed
        status_str = status.name if hasattr(status, 'name') else str(status)

        return [
            shopping_list for shopping_list in self._shopping_lists.values()
            if shopping_list.get('status') == status_str
        ]

    def change_shopping_list_status(self, shopping_list_id: int, new_status: ShoppingListStatus) -> Dict[str, Any]:
        """Change a shopping list's status.

        Args:
            shopping_list_id (int): ID of the shopping list to update
            new_status (ShoppingListStatus): New status for the shopping list

        Returns:
            Dict[str, Any]: Updated shopping list data

        Raises:
            NotFoundError: If the shopping list doesn't exist
        """
        self.logger.info(f"Changing shopping list {shopping_list_id} status to {new_status}")

        # Check if shopping list exists
        if shopping_list_id not in self._shopping_lists:
            self.logger.warning(f"Shopping list with ID {shopping_list_id} not found")
            raise NotFoundError(f"Shopping list with ID {shopping_list_id} not found")

        # Get current shopping list
        shopping_list = self._shopping_lists[shopping_list_id]

        # Update status
        shopping_list['status'] = new_status.name if hasattr(new_status, 'name') else str(new_status)
        shopping_list['updated_at'] = datetime.now()

        self.logger.info(f"Changed shopping list {shopping_list_id} status to {new_status}")
        return shopping_list

    def add_item_to_shopping_list(self, shopping_list_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list to add the item to
            item_data (Dict[str, Any]): Item data to add

        Returns:
            Dict[str, Any]: Added shopping list item data

        Raises:
            NotFoundError: If the shopping list doesn't exist
            ValidationError: If the item data is invalid
        """
        self.logger.info(f"Adding item to shopping list {shopping_list_id}")

        # Check if shopping list exists
        if shopping_list_id not in self._shopping_lists:
            self.logger.warning(f"Shopping list with ID {shopping_list_id} not found")
            raise NotFoundError(f"Shopping list with ID {shopping_list_id} not found")

        # Validate item data
        if 'name' not in item_data:
            self.logger.warning("Missing required field: name")
            raise ValidationError("Item name is required")

        if 'quantity' not in item_data:
            self.logger.warning("Missing required field: quantity")
            raise ValidationError("Item quantity is required")

        # Create item
        item_id = self._next_item_id
        self._next_item_id += 1

        item = {
            'id': item_id,
            'shopping_list_id': shopping_list_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'purchased': False,
            **item_data
        }

        self._shopping_list_items[item_id] = item

        # Add item to shopping list
        shopping_list = self._shopping_lists[shopping_list_id]
        shopping_list['items'].append(item_id)
        shopping_list['updated_at'] = datetime.now()

        self.logger.info(f"Added item {item_id} to shopping list {shopping_list_id}")
        return item

    def remove_item_from_shopping_list(self, shopping_list_id: int, item_id: int) -> bool:
        """Remove an item from a shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list to remove the item from
            item_id (int): ID of the item to remove

        Returns:
            bool: True if removal was successful

        Raises:
            NotFoundError: If the shopping list or item doesn't exist
        """
        self.logger.info(f"Removing item {item_id} from shopping list {shopping_list_id}")

        # Check if shopping list exists
        if shopping_list_id not in self._shopping_lists:
            self.logger.warning(f"Shopping list with ID {shopping_list_id} not found")
            raise NotFoundError(f"Shopping list with ID {shopping_list_id} not found")

        # Check if item exists and belongs to the shopping list
        if item_id not in self._shopping_list_items:
            self.logger.warning(f"Item with ID {item_id} not found")
            raise NotFoundError(f"Item with ID {item_id} not found")

        item = self._shopping_list_items[item_id]
        if item.get('shopping_list_id') != shopping_list_id:
            self.logger.warning(f"Item with ID {item_id} does not belong to shopping list {shopping_list_id}")
            raise NotFoundError(f"Item with ID {item_id} not found in shopping list {shopping_list_id}")

        # Remove item from shopping list
        shopping_list = self._shopping_lists[shopping_list_id]
        if 'items' in shopping_list and item_id in shopping_list['items']:
            shopping_list['items'].remove(item_id)
            shopping_list['updated_at'] = datetime.now()

        # Delete item
        del self._shopping_list_items[item_id]

        self.logger.info(f"Removed item {item_id} from shopping list {shopping_list_id}")
        return True

    def get_shopping_list_items(self, shopping_list_id: int) -> List[Dict[str, Any]]:
        """Get all items in a shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list to get items for

        Returns:
            List[Dict[str, Any]]: List of shopping list item data dictionaries

        Raises:
            NotFoundError: If the shopping list doesn't exist
        """
        self.logger.info(f"Retrieving items for shopping list {shopping_list_id}")

        # Check if shopping list exists
        if shopping_list_id not in self._shopping_lists:
            self.logger.warning(f"Shopping list with ID {shopping_list_id} not found")
            raise NotFoundError(f"Shopping list with ID {shopping_list_id} not found")

        # Get shopping list
        shopping_list = self._shopping_lists[shopping_list_id]

        # Get items
        items = []
        for item_id in shopping_list.get('items', []):
            if item_id in self._shopping_list_items:
                items.append(self._shopping_list_items[item_id])

        return items

    # IBaseService implementation methods

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shopping list.

        Args:
            data (Dict[str, Any]): Data for creating the shopping list

        Returns:
            Dict[str, Any]: Created shopping list

        Raises:
            ValidationError: If data is invalid
        """
        return self.create_shopping_list(data)

    def get_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """Retrieve a shopping list by its identifier.

        Args:
            entity_id (Any): Unique identifier for the shopping list

        Returns:
            Optional[Dict[str, Any]]: Retrieved shopping list or None if not found
        """
        try:
            return self.get_shopping_list_by_id(int(entity_id))
        except NotFoundError:
            return None

    def update(self, entity_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing shopping list.

        Args:
            entity_id (Any): Unique identifier for the shopping list
            data (Dict[str, Any]): Updated data for the shopping list

        Returns:
            Dict[str, Any]: Updated shopping list

        Raises:
            NotFoundError: If shopping list doesn't exist
            ValidationError: If update data is invalid
        """
        return self.update_shopping_list(int(entity_id), data)

    def delete(self, entity_id: Any) -> bool:
        """Delete a shopping list by its identifier.

        Args:
            entity_id (Any): Unique identifier for the shopping list

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        return self.delete_shopping_list(int(entity_id))

    def update_shopping_list_item(self, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a shopping list item.

        Args:
            item_id (int): ID of the item to update
            item_data (Dict[str, Any]): Updated item data

        Returns:
            Dict[str, Any]: Updated shopping list item data

        Raises:
            NotFoundError: If the item doesn't exist
        """
        self.logger.info(f"Updating shopping list item {item_id}")

        # Check if item exists
        if item_id not in self._shopping_list_items:
            self.logger.warning(f"Item with ID {item_id} not found")
            raise NotFoundError(f"Item with ID {item_id} not found")

        # Get item
        item = self._shopping_list_items[item_id]

        # Update fields
        for key, value in item_data.items():
            if key not in ['id', 'shopping_list_id', 'created_at']:
                item[key] = value

        # Update timestamp
        item['updated_at'] = datetime.now()

        # Update shopping list timestamp
        shopping_list_id = item.get('shopping_list_id')
        if shopping_list_id in self._shopping_lists:
            self._shopping_lists[shopping_list_id]['updated_at'] = datetime.now()

        self.logger.info(f"Updated shopping list item {item_id}")
        return item

    def mark_item_as_purchased(self, item_id: int, purchased: bool = True) -> Dict[str, Any]:
        """Mark a shopping list item as purchased or not purchased.

        Args:
            item_id (int): ID of the item to mark
            purchased (bool): Whether the item has been purchased

        Returns:
            Dict[str, Any]: Updated shopping list item data

        Raises:
            NotFoundError: If the item doesn't exist
        """
        self.logger.info(f"Marking shopping list item {item_id} as {'purchased' if purchased else 'not purchased'}")

        # Check if item exists
        if item_id not in self._shopping_list_items:
            self.logger.warning(f"Item with ID {item_id} not found")
            raise NotFoundError(f"Item with ID {item_id} not found")

        # Get item
        item = self._shopping_list_items[item_id]

        # Update purchased status
        item['purchased'] = purchased
        item['updated_at'] = datetime.now()

        # Update purchase date if marked as purchased
        if purchased:
            item['purchased_at'] = datetime.now()
        else:
            item.pop('purchased_at', None)

        # Update shopping list timestamp
        shopping_list_id = item.get('shopping_list_id')
        if shopping_list_id in self._shopping_lists:
            self._shopping_lists[shopping_list_id]['updated_at'] = datetime.now()

        self.logger.info(f"Marked shopping list item {item_id} as {'purchased' if purchased else 'not purchased'}")
        return item

    def list_shopping_lists(self) -> List[Dict[str, Any]]:
        """List all shopping lists.

        Returns:
            List[Dict[str, Any]]: List of all shopping lists
        """
        return self.get_all_shopping_lists()

    def get_shopping_list(self, shopping_list_id: int) -> Dict[str, Any]:
        """Get a shopping list by its ID.

        Args:
            shopping_list_id (int): The ID of the shopping list to retrieve

        Returns:
            Dict[str, Any]: The shopping list data

        Raises:
            NotFoundError: If the shopping list doesn't exist
        """
        return self.get_shopping_list_by_id(shopping_list_id)

    def search_shopping_lists(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for shopping lists by name or content.

        Args:
            search_term (str): The search term to filter by

        Returns:
            List[Dict[str, Any]]: List of matching shopping lists
        """
        self.logger.info(f"Searching shopping lists with term '{search_term}'")

        search_term = search_term.lower()
        results = []

        for shopping_list in self._shopping_lists.values():
            # Search in name
            if search_term in shopping_list.get('name', '').lower():
                results.append(shopping_list)
                continue

            # Search in items
            for item_id in shopping_list.get('items', []):
                if item_id in self._shopping_list_items:
                    item = self._shopping_list_items[item_id]
                    if search_term in item.get('name', '').lower() or search_term in item.get('notes', '').lower():
                        results.append(shopping_list)
                        break

        return results

    def generate_purchase_order(self, shopping_list_id: int) -> Dict[str, Any]:
        """Generate a purchase order from a shopping list.

        Args:
            shopping_list_id (int): The ID of the shopping list

        Returns:
            Dict[str, Any]: Generated purchase order data

        Raises:
            NotFoundError: If the shopping list doesn't exist
        """
        self.logger.info(f"Generating purchase order from shopping list {shopping_list_id}")

        # Check if shopping list exists
        if shopping_list_id not in self._shopping_lists:
            self.logger.warning(f"Shopping list with ID {shopping_list_id} not found")
            raise NotFoundError(f"Shopping list with ID {shopping_list_id} not found")

        # Get shopping list
        shopping_list = self._shopping_lists[shopping_list_id]

        # Get items
        items = []
        for item_id in shopping_list.get('items', []):
            if item_id in self._shopping_list_items:
                item = self._shopping_list_items[item_id]
                if not item.get('purchased', False):
                    items.append(item)

        # Create purchase order
        purchase_order = {
            'id': f"PO-{shopping_list_id}-{datetime.now().strftime('%Y%m%d')}",
            'shopping_list_id': shopping_list_id,
            'shopping_list_name': shopping_list.get('name', ''),
            'created_at': datetime.now(),
            'items': items,
            'total_items': len(items)
        }

        self.logger.info(f"Generated purchase order with {len(items)} items")
        return purchase_order
