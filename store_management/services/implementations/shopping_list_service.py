# store_management/services/implementations/shopping_list_service.py
from typing import List, Dict, Any, Optional, Tuple, cast
from datetime import datetime

from di.service import Service
from di.container import DependencyContainer
from services.interfaces.shopping_list_service import IShoppingListService
from database.sqlalchemy.base_manager import BaseManager
from database.models.shopping_list import ShoppingList, ShoppingListItem
from database.models.part import Part
from database.models.leather import Leather
from database.models.supplier import Supplier


class ShoppingListService(Service, IShoppingListService):
    """Service for shopping list management operations"""

    def __init__(self, container: DependencyContainer):
        """Initialize with appropriate managers"""
        super().__init__(container)
        self._shopping_list_manager = self.get_dependency(BaseManager[ShoppingList])
        self._shopping_list_item_manager = self.get_dependency(BaseManager[ShoppingListItem])
        self._supplier_manager = self.get_dependency(BaseManager[Supplier])
        self._part_manager = self.get_dependency(BaseManager[Part])
        self._leather_manager = self.get_dependency(BaseManager[Leather])

    def create_shopping_list(self, list_data: Dict[str, Any],
                             items: Optional[List[Dict[str, Any]]] = None) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Create a new shopping list with optional items.

        Args:
            list_data: Shopping list data
            items: Optional list of item data

        Returns:
            Tuple of (created shopping list or None, result message)
        """
        try:
            # Validate list data
            if not list_data.get('name'):
                return None, "Shopping list name is required"

            # Prepare shopping list data
            shopping_list_data = {
                'name': list_data.get('name'),
                'description': list_data.get('description', ''),
                'date_created': datetime.now(),
                'created_by': list_data.get('created_by', 'system'),
                'priority': list_data.get('priority', 'NORMAL')
            }

            # Create shopping list
            shopping_list = self._shopping_list_manager.create(shopping_list_data)

            # Create shopping list items if provided
            if items:
                for item_data in items:
                    # Add shopping_list_id to item data
                    item_data['shopping_list_id'] = shopping_list.id

                    # Create item
                    self._shopping_list_item_manager.create(item_data)

            # Get created shopping list with items
            created_list = self._get_shopping_list_with_items(shopping_list.id)
            if not created_list:
                return None, "Shopping list created but failed to retrieve"

            return created_list, "Shopping list created successfully"

        except Exception as e:
            return None, f"Error creating shopping list: {str(e)}"

    def add_item_to_list(self, list_id: int,
                         item_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Add an item to a shopping list.

        Args:
            list_id: Shopping list ID
            item_data: Item data

        Returns:
            Tuple of (created item or None, result message)
        """
        try:
            # Get the shopping list
            shopping_list = self._shopping_list_manager.get(list_id)
            if not shopping_list:
                return None, f"Shopping list with ID {list_id} not found"

            # Validate item data
            if not (item_data.get('part_id') or item_data.get('leather_id')):
                return None, "Either part_id or leather_id is required"

            if not item_data.get('quantity'):
                return None, "Quantity is required"

            # Check if the part or leather exists
            if item_data.get('part_id'):
                part = self._part_manager.get(item_data.get('part_id'))
                if not part:
                    return None, f"Part with ID {item_data.get('part_id')} not found"

            if item_data.get('leather_id'):
                leather = self._leather_manager.get(item_data.get('leather_id'))
                if not leather:
                    return None, f"Leather with ID {item_data.get('leather_id')} not found"

            # Add shopping_list_id to item data
            item_data['shopping_list_id'] = list_id

            # Set default values
            if 'date_added' not in item_data:
                item_data['date_added'] = datetime.now()

            if 'is_purchased' not in item_data:
                item_data['is_purchased'] = False

            # Create item
            shopping_list_item = self._shopping_list_item_manager.create(item_data)

            return self._shopping_list_item_to_dict(shopping_list_item), "Item added to shopping list"

        except Exception as e:
            return None, f"Error adding item to shopping list: {str(e)}"

    def mark_item_purchased(self, item_id: int,
                            purchase_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Mark a shopping list item as purchased with purchase details.

        Args:
            item_id: Shopping list item ID
            purchase_data: Purchase details (date, price)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get the shopping list item
            item = self._shopping_list_item_manager.get(item_id)
            if not item:
                return False, f"Shopping list item with ID {item_id} not found"

            # Validate purchase data
            if not purchase_data.get('price'):
                return False, "Purchase price is required"

            # Prepare update data
            update_data = {
                'is_purchased': True,
                'purchase_date': purchase_data.get('date', datetime.now()),
                'purchase_price': purchase_data.get('price'),
                'purchase_notes': purchase_data.get('notes', '')
            }

            # Update the item
            self._shopping_list_item_manager.update(item_id, update_data)

            return True, "Item marked as purchased"

        except Exception as e:
            return False, f"Error marking item as purchased: {str(e)}"

    def get_pending_items_by_supplier(self) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get pending items grouped by supplier.

        Returns:
            Dictionary mapping supplier IDs to lists of pending items
        """
        try:
            # Get all shopping list items
            all_items = self._shopping_list_item_manager.get_all()

            # Filter pending items
            pending_items = [item for item in all_items if not item.is_purchased]

            # Group by supplier
            supplier_items = {}

            for item in pending_items:
                # Determine supplier ID
                supplier_id = None

                if item.part_id:
                    part = self._part_manager.get(item.part_id)
                    if part:
                        supplier_id = part.supplier_id

                elif item.leather_id:
                    leather = self._leather_manager.get(item.leather_id)
                    if leather:
                        supplier_id = leather.supplier_id

                # Skip if no supplier
                if not supplier_id:
                    continue

                # Add to supplier group
                if supplier_id not in supplier_items:
                    supplier_items[supplier_id] = []

                supplier_items[supplier_id].append(self._shopping_list_item_to_dict(item))

            return supplier_items

        except Exception as e:
            # Log the error
            print(f"Error getting pending items by supplier: {str(e)}")
            return {}

    def _get_shopping_list_with_items(self, list_id: int) -> Optional[Dict[str, Any]]:
        """
        Get shopping list with its items.

        Args:
            list_id: Shopping list ID

        Returns:
            Dictionary with shopping list and items or None if not found
        """
        try:
            # Get shopping list
            shopping_list = self._shopping_list_manager.get(list_id)
            if not shopping_list:
                return None

            # Get items
            all_items = self._shopping_list_item_manager.get_all()
            list_items = []

            for item in all_items:
                if item.shopping_list_id == list_id:
                    list_items.append(self._shopping_list_item_to_dict(item))

            # Create full shopping list dictionary
            shopping_list_dict = self._shopping_list_to_dict(shopping_list)
            shopping_list_dict['items'] = list_items

            return shopping_list_dict

        except Exception as e:
            # Log the error
            print(f"Error getting shopping list with items: {str(e)}")
            return None

    def _shopping_list_to_dict(self, shopping_list: ShoppingList) -> Dict[str, Any]:
        """Convert ShoppingList model to dictionary."""
        return {
            'id': shopping_list.id,
            'name': shopping_list.name,
            'description': shopping_list.description,
            'date_created': shopping_list.date_created,
            'created_by': shopping_list.created_by,
            'priority': shopping_list.priority
        }

    def _shopping_list_item_to_dict(self, item: ShoppingListItem) -> Dict[str, Any]:
        """Convert ShoppingListItem model to dictionary."""
        return {
            'id': item.id,
            'shopping_list_id': item.shopping_list_id,
            'part_id': item.part_id,
            'leather_id': item.leather_id,
            'quantity': item.quantity,
            'date_added': item.date_added,
            'is_purchased': item.is_purchased,
            'purchase_date': item.purchase_date,
            'purchase_price': item.purchase_price,
            'purchase_notes': item.purchase_notes,
            'notes': item.notes
        }