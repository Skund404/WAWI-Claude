

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class OrderValidator:

    pass
@staticmethod
def validate_order(data: Dict[str, Any]) ->Tuple[bool, str]:
"""Validate order data"""
try:
    pass
if not data.get('order_number'):
    pass
return False, 'Order number is required'
if not data.get('supplier'):
    pass
return False, 'Supplier is required'
try:
    pass
datetime.strptime(data.get('date_of_order', ''), '%Y-%m-%d')
except ValueError:
    pass
return False, 'Invalid date format (YYYY-MM-DD)'
try:
    pass
amount = float(data.get('total_amount', 0))
if amount < 0:
    pass
return False, 'Total amount must be non-negative'
except ValueError:
    pass
return False, 'Invalid total amount'
return True, ''
except Exception as e:
    pass
return False, str(e)

@staticmethod
def validate_order_detail(data: Dict[str, Any]) ->Tuple[bool, str]:
"""Validate order detail data"""
try:
    pass
if not data.get('article'):
    pass
return False, 'Article is required'
try:
    pass
price = float(data.get('price', 0))
if price < 0:
    pass
return False, 'Price must be non-negative'
except ValueError:
    pass
return False, 'Invalid price'
try:
    pass
amount = int(data.get('amount', 0))
if amount < 1:
    pass
return False, 'Amount must be at least 1'
except ValueError:
    pass
return False, 'Invalid amount'
return True, ''
except Exception as e:
    pass
return False, str(e)
