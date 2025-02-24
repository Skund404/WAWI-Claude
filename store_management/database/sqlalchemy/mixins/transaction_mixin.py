from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
T = TypeVar('T')


class TransactionMixin:
    pass
"""Mixin providing transaction handling for complex operations.

This mixin provides methods to run operations in transactions and handle errors.
"""

@contextmanager
@inject(MaterialService)
def run_in_transaction(self):
    pass
"""Run operations in a transaction with error handling.

Usage:
with self.run_in_transaction() as session:
    pass
# Perform operations

Yields:
SQLAlchemy session
"""
with get_db_session() as session:
    pass
yield session

@inject(MaterialService)
def execute_with_result(self, operation: Callable, *args, **kwargs) -> Dict[
str, Any]:
"""Execute an operation in a transaction and return a standard result.

Args:
operation: Function to execute
*args: Arguments for the operation
**kwargs: Keyword arguments for the operation

Returns:
Dictionary with operation result:
    pass
{
'success': True/False,
'data': Result data (if successful),
'error': Error message (if failed)
}
"""
try:
    pass
with self.run_in_transaction() as session:
    pass
result = operation(session, *args, **kwargs)
return {'success': True, 'data': result}
except Exception as e:
    pass
return {'success': False, 'error': str(e)}
