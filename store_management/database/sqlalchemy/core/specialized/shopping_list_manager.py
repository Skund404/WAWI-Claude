from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy import select
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.sqlalchemy.core.base_manager import BaseManager
from database.models.shopping_list import ShoppingList
from database.models.shopping_list import ShoppingListItem
from database.models.supplier import Supplier
from utils.error_handling import DatabaseError

class ShoppingListManager(BaseManager):
    """Specialized manager for ShoppingList model operations.

    This class extends BaseManager with shopping list-specific operations.
    """

    def __init__(self, session_factory):
        super().__init__(ShoppingList, session_factory)

    def get_shopping_list_with_items(self, list_id: int) -> Optional[ShoppingList]:
        """Get shopping list with all its items.

        Args:
            list_id: Shopping list ID

        Returns:
            ShoppingList with loaded items or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(ShoppingList).options(joinedload(ShoppingList.items)).filter(ShoppingList.id == list_id)
                result = session.execute(query)
                shopping_list = result.scalar_one_or_none()
                return shopping_list
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting shopping list with items: {e}") from e

    def create_shopping_list(self, data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> ShoppingList:
        """Create a new shopping list with optional items.

        Args:
            data: Shopping list data (name, description, etc.)
            items: Optional list of shopping list items

        Returns:
            Created ShoppingList instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            with self.session_scope() as session:
                shopping_list = ShoppingList(**data)
                session.add(shopping_list)
                session.commit()
                session.refresh(shopping_list) # Refresh to get generated ID

                if items:
                    # Process and add items to the list if provided
                    for item_data in items:
                        item = ShoppingListItem(**item_data, shopping_list_id=shopping_list.id)
                        session.add(item)
                    session.commit()
                    session.refresh(shopping_list) # Refresh to load items

                return shopping_list
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error creating shopping list: {e}") from e

    def mark_item_purchased(self, item_id: int, purchase_data: Dict[str, Any]) -> None:
        """Mark a shopping list item as purchased.

        Args:
            item_id: Shopping list item ID
            purchase_data: Purchase details (date, price)

        Raises:
            DatabaseError: If item update fails
        """
        try:
            with self.session_scope() as session:
                item = session.get(ShoppingListItem, item_id)
                if item:
                    # Update item attributes from purchase_data
                    for key, value in purchase_data.items():
                        setattr(item, key, value)
                    session.commit()
                else:
                    raise ValueError(f"Shopping list item with ID {item_id} not found")
        except (ValueError, SQLAlchemyError) as e:
            raise DatabaseError(f"Error marking item purchased: {e}") from e

    def get_pending_items(self) -> List[ShoppingListItem]:
        """Get all unpurchased shopping list items.

        Returns:
            List of unpurchased ShoppingListItem instances

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(ShoppingListItem).where(ShoppingListItem.purchased == False) # noqa: E712
                result = session.execute(query)
                pending_items = result.scalars().all()
                return pending_items
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting pending items: {e}") from e

    def get_items_by_supplier(self, supplier_id: int) -> List[ShoppingListItem]:
        """Get shopping list items for a specific supplier.

        This is more complex as it needs to join through the part or leather
        to find items for a supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of shopping list items for the supplier

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                # This is just a placeholder as the actual query is highly dependent
                # on your data model, especially the relationships to parts, leather, and suppliers.
                # Adjust the relationships and column names as necessary.
                query = (
                    select(ShoppingListItem)
                    # Example: Assuming there is a direct relationship between item and supplier
                    # and that the supplier_id column is directly on a related table, such as Part or Leather
                    #   .join(Part, ShoppingListItem.part_id == Part.id)
                    #   .where(Part.supplier_id == supplier_id)
                    .limit(10)
                )
                result = session.execute(query)
                supplier_items = result.scalars().all()
                return supplier_items
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting supplier items: {e}") from e

    def get_shopping_list_summary(self, list_id: int) -> Dict[str, Any]:
        """Get a summary of a shopping list.

        Args:
            list_id: ID of the list to summarize

        Returns:
            Dictionary with summary information

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                # Example calculation of summary - adapt to your needs
                query = select(
                    func.count(ShoppingListItem.id).label('total_items'),
                    func.sum(ShoppingListItem.quantity).label('total_quantity')
                ).where(ShoppingListItem.shopping_list_id == list_id)

                result = session.execute(query).one()
                total_items, total_quantity = result

                return {
                    'total_items': total_items or 0,
                    'total_quantity': total_quantity or 0,
                    # Add more relevant summary information as needed
                }

        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting shopping list summary: {e}") from e