

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class OrderValidator:

        @staticmethod
    def validate_order(data: Dict[str, Any]) ->Tuple[bool, str]:
        """Validate order data"""
        try:
            if not data.get('order_number'):
                return False, 'Order number is required'
            if not data.get('supplier'):
                return False, 'Supplier is required'
            try:
                datetime.strptime(data.get('date_of_order', ''), '%Y-%m-%d')
            except ValueError:
                return False, 'Invalid date format (YYYY-MM-DD)'
            try:
                amount = float(data.get('total_amount', 0))
                if amount < 0:
                    return False, 'Total amount must be non-negative'
            except ValueError:
                return False, 'Invalid total amount'
            return True, ''
        except Exception as e:
            return False, str(e)

        @staticmethod
    def validate_order_detail(data: Dict[str, Any]) ->Tuple[bool, str]:
        """Validate order detail data"""
        try:
            if not data.get('article'):
                return False, 'Article is required'
            try:
                price = float(data.get('price', 0))
                if price < 0:
                    return False, 'Price must be non-negative'
            except ValueError:
                return False, 'Invalid price'
            try:
                amount = int(data.get('amount', 0))
                if amount < 1:
                    return False, 'Amount must be at least 1'
            except ValueError:
                return False, 'Invalid amount'
            return True, ''
        except Exception as e:
            return False, str(e)
