# Path: store_management/services/implementations/order_service.py
from typing import List, Dict, Any, Optional, Tuple

from store_management.di.service import Service
from store_management.di.container import DependencyContainer
from store_management.services.interfaces.order_service import IOrderService
from store_management.database.sqlalchemy.core.specialized.order_manager import OrderManager

class OrderService(Service, IOrderService):
    """Service for order management operations"""

    def __init__(self, container: DependencyContainer):
        """
        Initialize with appropriate managers.

        Args:
            container: Dependency injection container
        """
        super().__init__(container)
        self.order_manager = self.get_dependency(OrderManager)

    def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Retrieve all orders.

        Returns:
            List of order dictionaries
        """
        try:
            orders = self.order_manager.get_all()
            return [self._to_dict(order) for order in orders]
        except Exception as e:
            print(f"Error retrieving orders: {e}")
            return []

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Get order details by ID.

        Args:
            order_id: Order ID

        Returns:
            Order details or None if not found
        """
        try:
            order = self.order_manager.get(order_id)
            return self._to_dict(order) if order else None
        except Exception as e:
            print(f"Error retrieving order {order_id}: {e}")
            return None

    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new order.

        Args:
            order_data: Dictionary with order data

        Returns:
            Created order or None
        """
        try:
            new_order = self.order_manager.create(order_data)
            return self._to_dict(new_order)
        except Exception as e:
            print(f"Error creating order: {e}")
            return None

    def update_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing order.

        Args:
            order_data: Dictionary with updated order information

        Returns:
            Updated order or None
        """
        try:
            order_id = order_data.get('id')
            if not order_id:
                print("Order ID is required for update")
                return None

            updated_order = self.order_manager.update(order_id, order_data)
            return self._to_dict(updated_order)
        except Exception as e:
            print(f"Error updating order: {e}")
            return None

    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order.

        Args:
            order_id: ID of the order to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            return self.order_manager.delete(order_id)
        except Exception as e:
            print(f"Error deleting order {order_id}: {e}")
            return False

    def _to_dict(self, order):
        """
        Convert order model to dictionary.

        Args:
            order: Order model instance

        Returns:
            Dictionary representation of the order
        """
        if not order:
            return {}

        return {
            'id': order.id,
            'order_number': getattr(order, 'order_number', ''),
            'supplier_id': getattr(order, 'supplier_id', None),
            'order_date': str(getattr(order, 'order_date', '')),
            'expected_delivery_date': str(getattr(order, 'expected_delivery_date', '')),
            'total_amount': getattr(order, 'total_amount', 0.0),
            'status': getattr(order, 'status', ''),
            'payment_status': getattr(order, 'payment_status', ''),
            'is_paid': getattr(order, 'is_paid', False),
            'notes': getattr(order, 'notes', '')
        }