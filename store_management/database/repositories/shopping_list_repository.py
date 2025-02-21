# store_management/database/repositories/shopping_list_repository.py

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from ..interfaces.base_repository import BaseRepository
from ..models.shopping_list import ShoppingList, ShoppingListItem


class ShoppingListRepository(BaseRepository[ShoppingList]):
    """Repository for ShoppingList model operations"""

    def __init__(self, session: Session):
        super().__init__(session, ShoppingList)

    def get_with_items(self, list_id: int) -> Optional[ShoppingList]:
        """
        Get shopping list with all items.

        Args:
            list_id: Shopping list ID

        Returns:
            Shopping list with loaded items or None
        """
        return self.session.query(ShoppingList) \
            .options(joinedload(ShoppingList.items)) \
            .filter(ShoppingList.id == list_id) \
            .first()

    def get_pending_items(self) -> List[ShoppingListItem]:
        """
        Get all unpurchased shopping list items.

        Returns:
            List of unpurchased shopping list items
        """
        return self.session.query(ShoppingListItem) \
            .filter(ShoppingListItem.purchased == False) \
            .all()

    def get_items_by_supplier(self, supplier_id: int) -> List[ShoppingListItem]:
        """
        Get shopping list items for a supplier.

        This is more complex as it needs to join through the part or leather
        to find items for a supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of shopping list items for the supplier
        """
        from ..models.part import Part
        from ..models.leather import Leather

        # Get items where the part is from the supplier
        part_items = self.session.query(ShoppingListItem) \
            .join(Part, ShoppingListItem.part_id == Part.id) \
            .filter(Part.supplier_id == supplier_id) \
            .all()

        # Get items where the leather is from the supplier
        leather_items = self.session.query(ShoppingListItem) \
            .join(Leather, ShoppingListItem.leather_id == Leather.id) \
            .filter(Leather.supplier_id == supplier_id) \
            .all()

        # Combine and return
        return part_items + leather_items