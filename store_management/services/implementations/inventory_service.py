from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logger = logging.getLogger(__name__)


class InventoryService(Service, IInventoryService):
    pass
"""
Service for managing inventory items, tracking stock levels,
and handling inventory transactions.
"""

@inject(MaterialService)
def __init__(self, container) -> None:
"""
Initialize the inventory service.

Args:
container: Dependency injection container
"""
super().__init__(container)
self.part_repository = self.get_dependency('PartRepository')
self.leather_repository = self.get_dependency('LeatherRepository')
self.transaction_repository = self.get_dependency(
'TransactionRepository')

@inject(MaterialService)
def update_part_stock(self, part_id: int, quantity_change: float,
transaction_type: TransactionType, notes: str) -> None:
"""
Update the stock level for a part and record the transaction.

Args:
part_id: ID of the part to update
quantity_change: Amount to change stock by (positive or negative)
transaction_type: Type of transaction
notes: Transaction notes

Raises:
ValueError: If resulting quantity would be negative
"""
try:
    pass
part = self.part_repository.get_with_transactions(part_id)
if not part:
    pass
raise ValueError(f'Part not found with ID: {part_id}')
new_quantity = part.quantity + quantity_change
if new_quantity < 0:
    pass
raise ValueError(
f'Cannot reduce stock below zero. Current stock: {part.quantity}'
)
part.quantity = new_quantity
self.transaction_repository.create_part_transaction(
part_id=part_id, quantity_change=quantity_change, transaction_type=transaction_type, notes=notes)
self._update_part_status(part)
logger.info(
f'Updated stock for part {part_id} by {quantity_change}')
except Exception as e:
    pass
logger.error(f'Error updating part stock: {str(e)}')
raise

@inject(MaterialService)
def update_leather_area(self, leather_id: int, area_change: float,
transaction_type: TransactionType, notes: str, wastage: Optional[
float] = None) -> None:
"""
Update the available area for a leather piece and record the transaction.

Args:
leather_id: ID of the leather to update
area_change: Amount to change area by (positive or negative)
transaction_type: Type of transaction
notes: Transaction notes
wastage: Optional wastage amount

Raises:
ValueError: If resulting area would be negative
"""
try:
    pass
leather = self.leather_repository.get_with_transactions(leather_id)
if not leather:
    pass
raise ValueError(f'Leather not found with ID: {leather_id}')
new_area = leather.area + area_change
if new_area < 0:
    pass
raise ValueError(
f'Cannot reduce area below zero. Current area: {leather.area}'
)
leather.area = new_area
self.transaction_repository.create_leather_transaction(
leather_id=leather_id, area_change=area_change, transaction_type=transaction_type, notes=notes, wastage=wastage)
self._update_leather_status(leather)
logger.info(
f'Updated area for leather {leather_id} by {area_change}')
except Exception as e:
    pass
logger.error(f'Error updating leather area: {str(e)}')
raise

@inject(MaterialService)
def get_low_stock_parts(self, include_out_of_stock: bool = False) -> List[Dict
[str, Any]]:
"""
Get list of parts with low stock levels.

Args:
include_out_of_stock: Whether to include out of stock items

Returns:
List[Dict[str, Any]]: List of parts with low stock
"""
try:
    pass
parts = self.part_repository.get_low_stock()
if not include_out_of_stock:
    pass
parts = [p for p in parts if p.quantity > 0]
return [self._part_to_dict(p) for p in parts]
except Exception as e:
    pass
logger.error(f'Error getting low stock parts: {str(e)}')
return []

@inject(MaterialService)
def get_low_stock_leather(self, include_out_of_stock: bool = False) -> List[
Dict[str, Any]]:
"""
Get list of leather pieces with low area remaining.

Args:
include_out_of_stock: Whether to include out of stock items

Returns:
List[Dict[str, Any]]: List of leather pieces with low stock
"""
try:
    pass
leather = self.leather_repository.get_low_stock()
if not include_out_of_stock:
    pass
leather = [l for l in leather if l.area > 0]
return [self._leather_to_dict(l) for l in leather]
except Exception as e:
    pass
logger.error(f'Error getting low stock leather: {str(e)}')
return []

@inject(MaterialService)
def _update_part_status(self, part: Any) -> None:
"""
Update the status of a part based on its current stock level.

Args:
part: Part to update
"""
if part.quantity <= 0:
    pass
part.status = InventoryStatus.OUT_OF_STOCK
elif part.quantity <= part.reorder_point:
    pass
part.status = InventoryStatus.LOW_STOCK
else:
part.status = InventoryStatus.IN_STOCK

@inject(MaterialService)
def _update_leather_status(self, leather: Any) -> None:
"""
Update the status of a leather piece based on its current area.

Args:
leather: Leather piece to update
"""
if leather.area <= 0:
    pass
leather.status = InventoryStatus.OUT_OF_STOCK
elif leather.area <= leather.minimum_area:
    pass
leather.status = InventoryStatus.LOW_STOCK
else:
leather.status = InventoryStatus.IN_STOCK

@inject(MaterialService)
def _part_to_dict(self, part: Any) -> Dict[str, Any]:
"""
Convert a part to a dictionary representation.

Args:
part: Part to convert

Returns:
Dict[str, Any]: Dictionary representation of the part
"""
return {'id': part.id, 'name': part.name, 'quantity': part.quantity,
'reorder_point': part.reorder_point, 'status': part.status.
value, 'location': part.location, 'supplier': part.supplier.
name if part.supplier else None}

@inject(MaterialService)
def _leather_to_dict(self, leather: Any) -> Dict[str, Any]:
"""
Convert a leather piece to a dictionary representation.

Args:
leather: Leather piece to convert

Returns:
Dict[str, Any]: Dictionary representation of the leather piece
"""
return {'id': leather.id, 'name': leather.name, 'area': leather.
area, 'minimum_area': leather.minimum_area, 'leather_type':
leather.leather_type.value, 'quality_grade': leather.
quality_grade.value, 'status': leather.status.value, 'location':
leather.location, 'supplier': leather.supplier.name if leather.
supplier else None}
