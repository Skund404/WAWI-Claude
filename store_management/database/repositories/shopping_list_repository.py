

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ShoppingListRepository(BaseRepository[ShoppingList]):
    pass
"""Repository for ShoppingList model operations"""

@inject(MaterialService)
def __init__(self, session: Session):
    pass
super().__init__(session, ShoppingList)

@inject(MaterialService)
def get_with_items(self, list_id: int) -> Optional[ShoppingList]:
"""
Get shopping list with all items.

Args:
list_id: Shopping list ID

Returns:
Shopping list with loaded items or None
"""
return self.session.query(ShoppingList).options(joinedload(
ShoppingList.items)).filter(ShoppingList.id == list_id).first()

@inject(MaterialService)
def get_pending_items(self) -> List[ShoppingListItem]:
"""
Get all unpurchased shopping list items.

Returns:
List of unpurchased shopping list items
"""
return self.session.query(ShoppingListItem).filter(ShoppingListItem
.purchased == False).all()

@inject(MaterialService)
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
part_items = self.session.query(ShoppingListItem).join(Part,
ShoppingListItem.part_id == Part.id).filter(Part.supplier_id ==
supplier_id).all()
leather_items = self.session.query(ShoppingListItem).join(Leather,
ShoppingListItem.leather_id == Leather.id).filter(Leather.
supplier_id == supplier_id).all()
return part_items + leather_items
