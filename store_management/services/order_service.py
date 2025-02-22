from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from database.sqlalchemy.models.order import Order, OrderItem
from database.sqlalchemy.models.supplier import Supplier
from database.sqlalchemy.models.part import Part
from database.sqlalchemy.models.leather import Leather
from database.sqlalchemy.models.enums import OrderStatus, PaymentStatus
from database.sqlalchemy.manager_factory import get_manager


class OrderService:
    """Service for order management operations"""

    def __init__(self):
        """Initialize with appropriate managers"""
        self.order_manager = get_manager(Order)
        self.order_item_manager = get_manager(OrderItem)
        self.supplier_manager = get_manager(Supplier)
        self.part_manager = get_manager(Part)
        self.leather_manager = get_manager(Leather)

    def create_order(self, order_data: Dict[str, Any], items: List[Dict[str, Any]]) -> Tuple[Optional[Order], str]:
        """Create a new order with items.

        Args:
            order_data: Dictionary with order data
            items: List of dictionaries with item data

        Returns:
            Tuple of (created order or None, result message)
        """
        try:
            # Validate supplier exists
            supplier_id = order_data.get('supplier_id')
            if supplier_id and not self.supplier_manager.get(supplier_id):
                return None, f"Supplier with ID {supplier_id} not found"

            # Create order
            order = self.order_manager.create(order_data)

            # Create order items
            for item_data in items:
                item_data['order_id'] = order.id
                self.order_item_manager.create(item_data)

            return order, "Order created successfully"
        except Exception as e:
            return None, f"Error creating order: {str(e)}"

    def update_order_status(self, order_id: int, status: OrderStatus) -> Tuple[bool, str]:
        """Update order status with validation of status transitions.

        Args:
            order_id: Order ID
            status: New status

        Returns:
            Tuple of (success, message)
        """
        try:
            order = self.order_manager.get(order_id)
            if not order:
                return False, f"Order with ID {order_id} not found"

            # Validate status transition
            if not self._is_valid_status_transition(order.status, status):
                return False, f"Invalid status transition from {order.status} to {status}"

            # Update order status
            self.order_manager.update(order_id, {"status": status})

            return True, f"Order status updated to {status}"
        except Exception as e:
            return False, f"Error updating order status: {str(e)}"

    def _is_valid_status_transition(self, current_status: OrderStatus, new_status: OrderStatus) -> bool:
        """Validate if a status transition is allowed.

        Args:
            current_status: Current order status
            new_status: New order status

        Returns:
            True if transition is valid, False otherwise
        """
        # Define valid transitions (simplified example)
        valid_transitions = {
            OrderStatus.NEW: [OrderStatus.PENDING, OrderStatus.CANCELLED],
            OrderStatus.PENDING: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
            OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.RETURNED],
            OrderStatus.DELIVERED: [OrderStatus.RETURNED],
            # No transitions from final states
            OrderStatus.CANCELLED: [],
            OrderStatus.RETURNED: []
        }

        return new_status in valid_transitions.get(current_status, [])