# database/sqlalchemy/core/specialized/shopping_list_manager.py
"""
database/sqlalchemy/core/specialized/shopping_list_manager.py
Specialized manager for ShoppingList models with additional capabilities.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload

from database.sqlalchemy.core.base_manager import BaseManager
from database.models import ShoppingList, ShoppingListItem, Supplier
from utils.error_handling import DatabaseError


class ShoppingListManager(BaseManager[ShoppingList]):
    """
    Specialized manager for ShoppingList model operations.

    Extends BaseManager with shopping list-specific operations.
    """

    def get_shopping_list_with_items(self, list_id: int) -> Optional[ShoppingList]:
        """
        Get shopping list with all its items.

        Args:
            list_id: Shopping list ID

        Returns:
            ShoppingList with items loaded or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(ShoppingList).options(
                    joinedload(ShoppingList.items)
                ).where(ShoppingList.id == list_id)

                result = session.execute(query)
                return result.scalars().first()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve shopping list with items", str(e))

    def create_shopping_list(self, data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Optional[
        ShoppingList]:
        """
        Create a new shopping list with optional items.

        Args:
            data: Shopping list data
            items: Optional list of item data

        Returns:
            Created ShoppingList instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self.session_scope() as session:
                # Create shopping list
                shopping_list = ShoppingList(**data)
                session.add(shopping_list)
                session.flush()  # Get shopping list ID

                # Create shopping list items if provided
                if items:
                    for item_data in items:
                        item_data['shopping_list_id'] = shopping_list.id
                        shopping_list_item = ShoppingListItem(**item_data)
                        session.add(shopping_list_item)

                session.flush()
                return shopping_list
        except Exception as e:
            raise DatabaseError(f"Failed to create shopping list", str(e))

    def add_shopping_list_item(self, list_id: int, item_data: Dict[str, Any]) -> Optional[ShoppingListItem]:
        """
        Add an item to a shopping list.

        Args:
            list_id: Shopping list ID
            item_data: Item data

        Returns:
            Created ShoppingListItem instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self.session_scope() as session:
                # Check if shopping list exists
                shopping_list = session.get(ShoppingList, list_id)
                if not shopping_list:
                    return None

                # Create shopping list item
                item_data['shopping_list_id'] = list_id
                shopping_list_item = ShoppingListItem(**item_data)
                session.add(shopping_list_item)

                session.flush()
                return shopping_list_item
        except Exception as e:
            raise DatabaseError(f"Failed to add item to shopping list", str(e))

    def mark_item_purchased(self, item_id: int, purchase_data: Dict[str, Any]) -> Optional[ShoppingListItem]:
        """
        Mark a shopping list item as purchased.

        Args:
            item_id: Shopping list item ID
            purchase_data: Purchase details

        Returns:
            Updated ShoppingListItem instance

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                # Get shopping list item
                item = session.get(ShoppingListItem, item_id)
                if not item:
                    return None

                # Update item with purchase data
                item.purchased = True
                item.purchase_date = purchase_data.get('purchase_date', datetime.now())
                item.purchase_price = purchase_data.get('purchase_price')

                if 'notes' in purchase_data:
                    item.notes = purchase_data['notes']

                session.flush()
                return item
        except Exception as e:
            raise DatabaseError(f"Failed to mark item as purchased", str(e))

    def get_pending_items(self) -> List[ShoppingListItem]:
        """
        Get all pending (unpurchased) items across all shopping lists.

        Returns:
            List of unpurchased ShoppingListItem instances

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(ShoppingListItem).where(
                    ShoppingListItem.purchased == False
                ).order_by(ShoppingListItem.priority.desc())

                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to get pending items", str(e))

    def get_items_by_supplier(self, supplier_id: int) -> List[ShoppingListItem]:
        """
        Get all shopping list items for a specific supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of ShoppingListItem instances for the supplier

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(ShoppingListItem).where(
                    ShoppingListItem.supplier_id == supplier_id
                )

                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to get items by supplier", str(e))

    def get_shopping_list_summary(self, list_id: int) -> Dict[str, Any]:
        """
        Get summary statistics for a shopping list.

        Args:
            list_id: Shopping list ID

        Returns:
            Dictionary containing summary statistics

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                # Get shopping list with items
                shopping_list = self.get_shopping_list_with_items(list_id)
                if not shopping_list:
                    raise ValueError(f"Shopping list not found with ID {list_id}")

                # Calculate statistics
                total_items = len(shopping_list.items)
                purchased_items = sum(1 for item in shopping_list.items if item.purchased)
                remaining_items = total_items - purchased_items

                # Calculate total cost
                total_estimated_cost = sum(item.estimated_price * item.quantity for item in shopping_list.items)
                total_actual_cost = sum(
                    item.purchase_price * item.quantity for item in shopping_list.items if item.purchased)

                # Create summary
                summary = {
                    'id': shopping_list.id,
                    'name': shopping_list.name,
                    'created_date': shopping_list.created_date,
                    'total_items': total_items,
                    'purchased_items': purchased_items,
                    'remaining_items': remaining_items,
                    'completion_percentage': (purchased_items / total_items * 100) if total_items > 0 else 0,
                    'total_estimated_cost': total_estimated_cost,
                    'total_actual_cost': total_actual_cost,
                    'estimated_remaining_cost': total_estimated_cost - total_actual_cost
                }

                return summary
        except Exception as e:
            raise DatabaseError(f"Failed to get shopping list summary", str(e))