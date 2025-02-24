

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ShoppingListManager(BaseManager[ShoppingList]):
    pass
"""Manager for handling shopping list operations and related functionality."""

@inject(MaterialService)
def __init__(self, session_factory):
    pass
"""Initialize ShoppingListManager with session factory."""
super().__init__(session_factory, ShoppingList)

@inject(MaterialService)
def create_shopping_list(self, data: Dict[str, Any], items: List[Dict[
str, Any]] = None) -> ShoppingList:
"""Create a new shopping list with optional items.

Args:
data: Shopping list data (name, description, etc.)
items: Optional list of shopping list items

Returns:
Created ShoppingList instance

Raises:
DatabaseError: If validation fails or database operation fails
"""
try:
    pass
with self.session_scope() as session:
    pass
shopping_list = ShoppingList(name=data['name'], description=data.get('description', ''), priority=data.get(
'priority', 'normal'), due_date=data.get('due_date'),
created_at=datetime.now(), modified_at=datetime.now())
session.add(shopping_list)
session.flush()
if items:
    pass
for item_data in items:
    pass
item = ShoppingListItem(shopping_list_id=shopping_list.id, supplier_id=item_data.get(
'supplier_id'), part_id=item_data.get('part_id'
), leather_id=item_data.get('leather_id'),
quantity=item_data['quantity'], notes=item_data
.get('notes', ''), created_at=datetime.now(),
modified_at=datetime.now())
session.add(item)
return shopping_list
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to create shopping list: {str(e)}')
raise DatabaseError(f'Failed to create shopping list: {str(e)}')

@inject(MaterialService)
def get_shopping_list_with_items(self, list_id: int) -> Optional[
ShoppingList]:
"""Get shopping list with all its items.

Args:
list_id: Shopping list ID

Returns:
ShoppingList instance with items loaded or None if not found
"""
try:
    pass
with self.session_scope() as session:
    pass
query = select(ShoppingList).options(joinedload(
ShoppingList.items).joinedload(ShoppingListItem.
supplier), joinedload(ShoppingList.items).joinedload(
ShoppingListItem.part), joinedload(ShoppingList.items).
joinedload(ShoppingListItem.leather)).where(
ShoppingList.id == list_id)
result = session.execute(query).scalar_one_or_none()
return result
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to get shopping list: {str(e)}')
raise DatabaseError(f'Failed to get shopping list: {str(e)}')

@inject(MaterialService)
def add_shopping_list_item(self, list_id: int, item_data: Dict[str, Any]
) -> ShoppingListItem:
"""Add an item to a shopping list.

Args:
list_id: Shopping list ID
item_data: Item data including quantity and supplier

Returns:
Created ShoppingListItem instance
"""
try:
    pass
with self.session_scope() as session:
    pass
shopping_list = session.get(ShoppingList, list_id)
if not shopping_list:
    pass
raise DatabaseError(f'Shopping list {list_id} not found')
item = ShoppingListItem(shopping_list_id=list_id,
supplier_id=item_data.get('supplier_id'), part_id=item_data.get('part_id'), leather_id=item_data.get(
'leather_id'), quantity=item_data['quantity'], notes=item_data.get('notes', ''), created_at=datetime.now(),
modified_at=datetime.now())
session.add(item)
return item
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to add shopping list item: {str(e)}')
raise DatabaseError(f'Failed to add shopping list item: {str(e)}')

@inject(MaterialService)
def update_shopping_list_status(self, list_id: int, status: str
) -> Optional[ShoppingList]:
"""Update shopping list status.

Args:
list_id: Shopping list ID
status: New status

Returns:
Updated ShoppingList instance or None if not found
"""
try:
    pass
with self.session_scope() as session:
    pass
shopping_list = session.get(ShoppingList, list_id)
if shopping_list:
    pass
shopping_list.status = status
shopping_list.modified_at = datetime.now()
return shopping_list
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to update shopping list status: {str(e)}')
raise DatabaseError(
f'Failed to update shopping list status: {str(e)}')

@inject(MaterialService)
def mark_item_purchased(self, list_id: int, item_id: int, purchase_data:
Dict[str, Any]) -> Optional[ShoppingListItem]:
"""Mark a shopping list item as purchased.

Args:
list_id: Shopping list ID
item_id: Shopping list item ID
purchase_data: Purchase details including date and price

Returns:
Updated ShoppingListItem instance or None if not found
"""
try:
    pass
with self.session_scope() as session:
    pass
item = session.query(ShoppingListItem).filter(
ShoppingListItem.id == item_id, ShoppingListItem.
shopping_list_id == list_id).first()
if item:
    pass
item.purchased = True
item.purchase_date = purchase_data.get('purchase_date',
datetime.now())
item.purchase_price = purchase_data.get('purchase_price')
item.modified_at = datetime.now()
return item
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to mark item as purchased: {str(e)}')
raise DatabaseError(f'Failed to mark item as purchased: {str(e)}')

@inject(MaterialService)
def get_pending_items(self) -> List[ShoppingListItem]:
"""Get all pending (unpurchased) items across all shopping lists.

Returns:
List of unpurchased ShoppingListItem instances
"""
try:
    pass
with self.session_scope() as session:
    pass
query = select(ShoppingListItem).options(joinedload(
ShoppingListItem.shopping_list), joinedload(
ShoppingListItem.supplier)).where(ShoppingListItem.
purchased == False).order_by(ShoppingListItem.created_at)
result = session.execute(query).scalars().all()
return result
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to get pending items: {str(e)}')
raise DatabaseError(f'Failed to get pending items: {str(e)}')

@inject(MaterialService)
def get_items_by_supplier(self, supplier_id: int) -> List[ShoppingListItem]:
"""Get all shopping list items for a specific supplier.

Args:
supplier_id: Supplier ID

Returns:
List of ShoppingListItem instances for the supplier
"""
try:
    pass
with self.session_scope() as session:
    pass
query = select(ShoppingListItem).options(joinedload(
ShoppingListItem.shopping_list)).where(ShoppingListItem
.supplier_id == supplier_id).order_by(ShoppingListItem.
created_at)
result = session.execute(query).scalars().all()
return result
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to get supplier items: {str(e)}')
raise DatabaseError(f'Failed to get supplier items: {str(e)}')

@inject(MaterialService)
def get_shopping_list_summary(self, list_id: int) -> Dict[str, Any]:
"""Get summary statistics for a shopping list.

Args:
list_id: Shopping list ID

Returns:
Dictionary containing summary statistics
"""
try:
    pass
with self.session_scope() as session:
    pass
stats = session.query(func.count(ShoppingListItem.id).label
('total_items'), func.sum(case((ShoppingListItem.
purchased == True, 1), else_=0)).label(
'purchased_items'), func.sum(ShoppingListItem.
purchase_price).label('total_spent')).filter(
ShoppingListItem.shopping_list_id == list_id).first()
return {'total_items': stats.total_items or 0,
'purchased_items': stats.purchased_items or 0,
'pending_items': (stats.total_items or 0) - (stats.
purchased_items or 0), 'total_spent': float(stats.
total_spent or 0), 'completion_percentage': (stats.
purchased_items or 0) / stats.total_items * 100 if
stats.total_items > 0 else 0}
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to get shopping list summary: {str(e)}')
raise DatabaseError(
f'Failed to get shopping list summary: {str(e)}')

@inject(MaterialService)
def search_shopping_lists(self, search_term: str) -> List[ShoppingList]:
"""Search shopping lists across name and description.

Args:
search_term: Term to search for

Returns:
    pass
List of matching ShoppingList instances
"""
try:
    pass
with self.session_scope() as session:
    pass
query = select(ShoppingList).where(or_(ShoppingList.name.
ilike(f'%{search_term}%'), ShoppingList.description.
ilike(f'%{search_term}%'))).order_by(ShoppingList.
created_at.desc())
result = session.execute(query).scalars().all()
return result
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to search shopping lists: {str(e)}')
raise DatabaseError(f'Failed to search shopping lists: {str(e)}')

@inject(MaterialService)
def filter_shopping_lists(self, status: Optional[str] = None, priority:
Optional[str] = None, date_range: Optional[Tuple[datetime, datetime]]
= None) -> List[ShoppingList]:
"""Filter shopping lists based on various criteria.

Args:
status: Optional status filter
priority: Optional priority filter
date_range: Optional tuple of (start_date, end_date)

Returns:
List of filtered ShoppingList instances
"""
try:
    pass
with self.session_scope() as session:
    pass
filters = []
if status:
    pass
filters.append(ShoppingList.status == status)
if priority:
    pass
filters.append(ShoppingList.priority == priority)
if date_range:
    pass
start_date, end_date = date_range
filters.append(ShoppingList.created_at.between(
start_date, end_date))
query = select(ShoppingList).where(and_(*filters) if
filters else True).order_by(ShoppingList.created_at.desc())
result = session.execute(query).scalars().all()
return result
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to filter shopping lists: {str(e)}')
raise DatabaseError(f'Failed to filter shopping lists: {str(e)}')

@inject(MaterialService)
def bulk_update_items(self, updates: List[Dict[str, Any]], list_id:
Optional[int] = None) -> int:
"""Bulk update shopping list items.

Args:
updates: List of dictionaries containing item updates
list_id: Optional shopping list ID to restrict updates to

Returns:
Number of items updated
"""
try:
    pass
with self.session_scope() as session:
    pass
updated_count = 0
for update_data in updates:
    pass
item_id = update_data.pop('id')
query = session.query(ShoppingListItem).filter(
ShoppingListItem.id == item_id)
if list_id:
    pass
query = query.filter(ShoppingListItem.
shopping_list_id == list_id)
item = query.first()
if item:
    pass
for key, value in update_data.items():
    pass
setattr(item, key, value)
item.modified_at = datetime.now()
updated_count += 1
return updated_count
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to bulk update items: {str(e)}')
raise DatabaseError(f'Failed to bulk update items: {str(e)}')

@inject(MaterialService)
def merge_shopping_lists(self, source_ids: List[int], target_id: int
) -> ShoppingList:
"""Merge multiple shopping lists into a target list.

Args:
source_ids: List of source shopping list IDs
target_id: Target shopping list ID

Returns:
Updated target ShoppingList instance

Raises:
DatabaseError: If any list is not found or merge fails
"""
try:
    pass
with self.session_scope() as session:
    pass
target_list = session.get(ShoppingList, target_id)
if not target_list:
    pass
raise DatabaseError(
f'Target shopping list {target_id} not found')
for source_id in source_ids:
    pass
source_list = session.get(ShoppingList, source_id)
if not source_list:
    pass
raise DatabaseError(
f'Source shopping list {source_id} not found')
for item in source_list.items:
    pass
item.shopping_list_id = target_id
item.modified_at = datetime.now()
source_list.status = 'merged'
source_list.modified_at = datetime.now()
target_list.modified_at = datetime.now()
target_list.description += (
f"\\nMerged with lists: {', '.join(map(str, source_ids))}")
return target_list
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to merge shopping lists: {str(e)}')
raise DatabaseError(f'Failed to merge shopping lists: {str(e)}')

@inject(MaterialService)
def get_overdue_items(self) -> List[ShoppingListItem]:
"""Get all overdue items from active shopping lists.

Returns:
List of overdue ShoppingListItem instances
"""
try:
    pass
with self.session_scope() as session:
    pass
current_date = datetime.now()
query = select(ShoppingListItem).join(ShoppingList).options(
joinedload(ShoppingListItem.shopping_list), joinedload(
ShoppingListItem.supplier)).where(and_(ShoppingList.
status == 'active', ShoppingList.due_date <
current_date, ShoppingListItem.purchased == False)
).order_by(ShoppingList.due_date)
result = session.execute(query).scalars().all()
return result
except SQLAlchemyError as e:
    pass
logger.error(f'Failed to get overdue items: {str(e)}')
raise DatabaseError(f'Failed to get overdue items: {str(e)}')
