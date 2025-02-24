

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class IMaterialRepository(IBaseRepository[Material]):
    pass
"""
Interface defining the contract for Material Repository operations.

Extends the base repository interface with material-specific methods.
"""

@abstractmethod
@inject(MaterialService)
def update_stock(self, material_id: Any, quantity_change: float,
transaction_type: str, notes: Optional[str] = None) -> Material:
"""
Update the stock of a material.

Args:
material_id (Any): ID of the material
quantity_change (float): Quantity to add or subtract
transaction_type (str): Type of stock transaction
notes (Optional[str], optional): Additional notes for the transaction

Returns:
Material: Updated material
"""
pass

@abstractmethod
@inject(MaterialService)
def get_low_stock_materials(self, include_zero_stock: bool = False) -> List[
Material]:
"""
Retrieve materials with low stock.

Args:
include_zero_stock (bool, optional): Whether to include materials
with zero stock. Defaults to False.

Returns:
List[Material]: List of low stock materials
"""
pass

@abstractmethod
@inject(MaterialService)
def search_materials(self, search_params: Dict[str, Any]) -> List[Material]:
"""
Search materials based on multiple criteria.

Args:
search_params (Dict[str, Any]): Search criteria

Returns:
List[Material]: List of matching materials
"""
pass

@abstractmethod
@inject(MaterialService)
def generate_material_usage_report(self, start_date: Optional[str] = None,
end_date: Optional[str] = None) -> Dict[str, Any]:
"""
Generate a comprehensive material usage report.

Args:
start_date (Optional[str], optional): Start date for the report
end_date (Optional[str], optional): End date for the report

Returns:
Dict[str, Any]: Material usage report
"""
pass

@abstractmethod
@inject(MaterialService)
def validate_material_substitution(self, original_material_id: Any,
substitute_material_id: Any) -> bool:
"""
Check if one material can be substituted for another.

Args:
original_material_id (Any): ID of the original material
substitute_material_id (Any): ID of the potential substitute material

Returns:
bool: True if substitution is possible, False otherwise
"""
pass
