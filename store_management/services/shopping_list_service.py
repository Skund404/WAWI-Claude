from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from store_management.database.sqlalchemy.models.shopping_list import ShoppingList, ShoppingListItem
from store_management.database.sqlalchemy.models.part import Part
from store_management.database.sqlalchemy.models.leather import Leather
from store_management.database.sqlalchemy.manager_factory import get_manager


class ShoppingListService:
    """Service for shopping list management operations"""

    def __init__(self):
        """Initialize with appropriate managers"""
        self.shopping_list_manager = get_manager(ShoppingList)
        self.shopping_list_item_manager = get_manager(ShoppingListItem)
        self.part_manager = get_manager(Part)
        self.leather_manager = get_manager(Leather)

    def create_shopping_list(self, list_data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Tuple[
        Optional[ShoppingList], str]:
        """Create a new shopping list with optional items.

        Args:
            list_data: Shopping list data
            items: Optional list of item data

        Returns:
            Tuple of (created shopping list or None, result message)
        """
        try:
            # Create shopping list
            if 'created_at' not in list_data:
                list_data['created_at'] = datetime.now()

            shopping_list = self.shopping_list_manager.create(list_data)

            # Create shopping list items if provided
            if items:
                for item_data in items:
                    item_data['shopping_list_id'] = shopping_list.id
                    if 'purchased' not in item_data:
                        item_data['purchased'] = False
                    self.shopping_list_item_manager.create(item_data)

            return shopping_list, "Shopping list created successfully"
        except Exception as e:
            return None, f"Error creating shopping list: {str(e)}"

    def add_item_to_list(self, list_id: int, item_data: Dict[str, Any]) -> Tuple[Optional[ShoppingListItem], str]:
        """Add an item to a shopping list.

        Args:
            list_id: Shopping list ID
            item_data: Item data

        Returns:
            Tuple of (created item or None, result message)
        """
        try:
            # Check if shopping list exists
            shopping_list = self.shopping_list_manager.get(list_id)
            if not shopping_list:
                return None, f"Shopping list with ID {list_id} not found"

            # Add shopping list ID to item data
            item_data['shopping_list_id'] = list_id
            if 'purchased' not in item_data:
                item_data['purchased'] = False

            # Create shopping list item
            item = self.shopping_list_item_manager.create(item_data)

            return item, "Item added to shopping list successfully"
        except Exception as e:
            return None, f"Error adding item to shopping list: {str(e)}"

    def mark_item_purchased(self, item_id: int, purchase_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Mark a shopping list item as purchased with purchase details.

        Args:
            item_id: Shopping list item ID
            purchase_data: Purchase details (date, price)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get shopping list item
            item = self.shopping_list_item_manager.get(item_id)
            if not item:
                return False, f"Shopping list item with ID {item_id} not found"

            # Update purchase details
            update_data = {
                'purchased': True,
                'purchase_date': purchase_data.get('purchase_date', datetime.now()),
                'purchase_price': purchase_data.get('purchase_price')
            }

            self.shopping_list_item_manager.update(item_id, update_data)

            return True, "Item marked as purchased successfully"
        except Exception as e:
            return False, f"Error marking item as purchased: {str(e)}"

    def get_pending_items_by_supplier(self) -> Dict[int, List[ShoppingListItem]]:
        """Get pending items grouped by supplier.

        Returns:
            Dictionary mapping supplier IDs to lists of pending items
        """
        try:
            # Get all unpurchased items
            unpurchased_items = self.shopping_list_item_manager.filter_by(purchased=False)

            # Group by supplier
            supplier_items = {}
            for item in unpurchased_items:
                # Get the supplier ID based on the part or leather
                supplier_id = None

                if item.part_id:
                    part = self.part_manager.get(item.part_id)
                    if part:
                        supplier_id = part.supplier_id

                if item.leather_id:
                    leather = self.leather_manager.get(item.leather_id)
                    if leather:
                        supplier_id = leather.supplier_id

                if supplier_id:
                    if supplier_id not in supplier_items:
                        supplier_items[supplier_id] = []
                    supplier_items[supplier_id].append(item)

            return supplier_items
        except Exception as e:
            # Log error and return empty dictionary
            print(f"Error getting pending items by supplier: {str(e)}")
            return {}