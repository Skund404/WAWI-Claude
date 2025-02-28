"""
Order Service Implementation.

This module provides a concrete implementation of the Order Service interface
for managing orders in the leatherworking store management application.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

# Try to import the interface
try:
    from services.interfaces.order_service import IOrderService, OrderStatus, PaymentStatus
except ImportError:
    # Create placeholder classes if imports fail
    import enum

    class OrderStatus(enum.Enum):
        """Possible statuses for an order."""
        PENDING = "pending"
        PROCESSING = "processing"
        SHIPPED = "shipped"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"

    class PaymentStatus(enum.Enum):
        """Possible payment statuses for an order."""
        UNPAID = "unpaid"
        PARTIALLY_PAID = "partially_paid"
        PAID = "paid"
        REFUNDED = "refunded"

    class IOrderService:
        """Placeholder for IOrderService interface."""
        pass

class OrderService(IOrderService):
    """
    Implementation of the Order Service interface.

    This service manages customer orders, including creation, updates,
    and tracking of order status and payment information.
    """

    def __init__(self):
        """Initialize the Order Service."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("OrderService initialized")

        # For demonstration purposes, we'll use in-memory dictionaries
        self._orders = {}
        self._order_items = {}
        self._next_order_id = 1
        self._next_item_id = 1

    def _create_sample_orders(self):
        """Create sample orders for testing."""
        # Sample order 1
        order1 = self.create_order({
            "customer_name": "John Doe",
            "customer_email": "john.doe@example.com",
            "order_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "status": OrderStatus.DELIVERED.name,
            "payment_status": PaymentStatus.PAID.name,
            "shipping_address": "123 Main St, Anytown, CA 12345"
        })

        # Add items to order 1
        self.add_order_item(order1["id"], {
            "product_id": 1,
            "product_name": "Leather Wallet",
            "quantity": 1,
            "unit_price": 49.99
        })

        self.add_order_item(order1["id"], {
            "product_id": 5,
            "product_name": "Leather Care Kit",
            "quantity": 1,
            "unit_price": 24.99
        })

        # Sample order 2
        order2 = self.create_order({
            "customer_name": "Jane Smith",
            "customer_email": "jane.smith@example.com",
            "order_date": datetime.now().strftime("%Y-%m-%d"),
            "status": OrderStatus.PROCESSING.name,
            "payment_status": PaymentStatus.PAID.name,
            "shipping_address": "456 Oak Ave, Othertown, NY 67890"
        })

        # Add items to order 2
        self.add_order_item(order2["id"], {
            "product_id": 2,
            "product_name": "Leather Belt",
            "quantity": 1,
            "unit_price": 39.99
        })

        # Sample order 3
        order3 = self.create_order({
            "customer_name": "Robert Johnson",
            "customer_email": "robert.johnson@example.com",
            "order_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "status": OrderStatus.PENDING.name,
            "payment_status": PaymentStatus.UNPAID.name,
            "shipping_address": "789 Pine Rd, Somewhere, TX 54321"
        })

        # Add items to order 3
        self.add_order_item(order3["id"], {
            "product_id": 3,
            "product_name": "Leather Bag",
            "quantity": 1,
            "unit_price": 129.99
        })

        self.add_order_item(order3["id"], {
            "product_id": 4,
            "product_name": "Leather Keychain",
            "quantity": 2,
            "unit_price": 9.99
        })

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order.

        Args:
            order_data: Dictionary with order information

        Returns:
            Dict[str, Any]: Created order
        """
        self.logger.info("Creating new order")

        # Set default values if not provided
        order = {
            "id": self._next_order_id,
            "reference_number": order_data.get("reference_number", f"ORD-{self._next_order_id:04d}"),
            "customer_name": order_data.get("customer_name", ""),
            "customer_email": order_data.get("customer_email", ""),
            "customer_phone": order_data.get("customer_phone", ""),
            "order_date": order_data.get("order_date", datetime.now().strftime("%Y-%m-%d")),
            "status": order_data.get("status", OrderStatus.PENDING.name),
            "payment_status": order_data.get("payment_status", PaymentStatus.UNPAID.name),
            "total_amount": order_data.get("total_amount", 0.0),
            "shipping_address": order_data.get("shipping_address", ""),
            "notes": order_data.get("notes", ""),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Add order to storage
        self._orders.append(order)
        self._order_items[self._next_order_id] = []
        self._next_order_id += 1

        return order

    def get_order_items(self, order_id: int) -> List[Dict[str, Any]]:
        """Get items for an order.

        Args:
            order_id: ID of the order to get items for

        Returns:
            List[Dict[str, Any]]: List of order items
        """
        self.logger.info(f"Getting items for order {order_id}")

        return self._order_items.get(order_id, [])

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get an order by ID.

        Args:
            order_id: ID of the order to retrieve

        Returns:
            Optional[Dict[str, Any]]: Order data or None if not found
        """
        self.logger.info(f"Getting order with ID {order_id}")

        for order in self._orders:
            if order["id"] == order_id:
                return order

        return None

    def get_orders_by_status(self, status: Union[OrderStatus, str]) -> List[Dict[str, Any]]:
        """Get orders by status.

        Args:
            status: Order status to filter by (enum or string)

        Returns:
            List[Dict[str, Any]]: List of orders with the specified status
        """
        self.logger.info(f"Getting orders with status {status}")

        # Convert string status to enum name if needed
        if isinstance(status, OrderStatus):
            status_name = status.name
        else:
            status_name = status

        return [order for order in self._orders if order["status"] == status_name]

    def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders.

        Returns:
            List[Dict[str, Any]]: List of all orders
        """
        self.logger.info("Getting all orders")
        return self._orders

    def get_order(self, order_id: int) -> Dict[str, Any]:
        """
        Retrieve an order by its ID.

        Args:
            order_id: Unique identifier of the order

        Returns:
            Dictionary containing order details

        Raises:
            ValueError: If order with given ID doesn't exist
        """
        self.logger.debug(f"Getting order with ID: {order_id}")

        if order_id not in self._orders:
            raise ValueError(f"Order with ID {order_id} not found")

        return self._orders[order_id]

    def get_orders(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a list of orders with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip for pagination

        Returns:
            List of dictionaries containing order details
        """
        self.logger.debug(f"Getting orders with limit: {limit}, offset: {offset}")

        orders = list(self._orders.values())
        return orders[offset:offset + limit]

    def update_payment_status(self, order_id: int, status: Union[PaymentStatus, str]) -> Optional[Dict[str, Any]]:
        """Update an order's payment status.

        Args:
            order_id: ID of the order to update
            status: New payment status (enum or string)

        Returns:
            Optional[Dict[str, Any]]: Updated order data or None if not found
        """
        self.logger.info(f"Updating payment status of order {order_id} to {status}")

        # Convert enum to string if needed
        if isinstance(status, PaymentStatus):
            status_name = status.name
        else:
            status_name = status

        return self.update_order(order_id, {"payment_status": status_name})

    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing order.

        Args:
            order_id: ID of the order to update
            order_data: Updated order data

        Returns:
            Optional[Dict[str, Any]]: Updated order data or None if not found
        """
        self.logger.info(f"Updating order with ID {order_id}")

        for i, order in enumerate(self._orders):
            if order["id"] == order_id:
                # Update order fields
                for key, value in order_data.items():
                    if key != "id":  # Don't update the ID
                        order[key] = value

                # Update the updated_at timestamp
                order["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Recalculate total amount if there are items
                if order_id in self._order_items:
                    total = sum(item["total_price"] for item in self._order_items[order_id])
                    order["total_amount"] = total

                return order

        return None

    def update_order_item(self, order_id: int, item_id: int, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an order item.

        Args:
            order_id: ID of the order containing the item
            item_id: ID of the item to update
            item_data: Updated item data

        Returns:
            Optional[Dict[str, Any]]: Updated item data or None if not found
        """
        self.logger.info(f"Updating item {item_id} in order {order_id}")

        # Check if order exists and has items
        if order_id not in self._order_items:
            return None

        # Find and update the item
        for i, item in enumerate(self._order_items[order_id]):
            if item["id"] == item_id:
                # Update item fields
                for key, value in item_data.items():
                    if key != "id" and key != "order_id":  # Don't update ID or order_id
                        item[key] = value

                # Recalculate total price
                if "quantity" in item_data or "unit_price" in item_data:
                    item["total_price"] = item["unit_price"] * item["quantity"]

                # Update order total
                total = sum(item["total_price"] for item in self._order_items[order_id])
                self.update_order(order_id, {"total_amount": total})

                return item

        return None

    def update_order_status(self, order_id: int, status: Union[OrderStatus, str]) -> Optional[Dict[str, Any]]:
        """Update an order's status.

        Args:
            order_id: ID of the order to update
            status: New order status (enum or string)

        Returns:
            Optional[Dict[str, Any]]: Updated order data or None if not found
        """
        self.logger.info(f"Updating status of order {order_id} to {status}")

        # Convert enum to string if needed
        if isinstance(status, OrderStatus):
            status_name = status.name
        else:
            status_name = status

        return self.update_order(order_id, {"status": status_name})

    def process_payment(self, order_id: int, amount: float, payment_method: str) -> Dict[str, Any]:
        """
        Process a payment for an order.

        Args:
            order_id: Unique identifier of the order
            amount: Payment amount
            payment_method: Method of payment (e.g., credit card, cash)

        Returns:
            Dictionary containing payment details

        Raises:
            ValueError: If order with given ID doesn't exist
        """
        self.logger.debug(f"Processing payment of {amount} for order {order_id}")

        if order_id not in self._orders:
            raise ValueError(f"Order with ID {order_id} not found")

        order = self._orders[order_id]

        # Calculate total order value
        total = self.calculate_order_total(order_id)

        # Determine new payment status based on amount
        if amount >= total:
            payment_status = PaymentStatus.PAID
        elif amount > 0:
            payment_status = PaymentStatus.PARTIALLY_PAID
        else:
            payment_status = PaymentStatus.UNPAID

        # Update payment status
        order['payment_status'] = payment_status.value

        # Create payment record
        payment = {
            'order_id': order_id,
            'amount': amount,
            'payment_method': payment_method,
            'payment_status': payment_status.value
        }

        self.logger.info(f"Processed payment of {amount} for order {order_id}")
        return payment

    def delete_order(self, order_id: int) -> bool:
        """Delete an order.

        Args:
            order_id: ID of the order to delete

        Returns:
            bool: True if deleted, False if not found
        """
        self.logger.info(f"Deleting order with ID {order_id}")

        for i, order in enumerate(self._orders):
            if order["id"] == order_id:
                self._orders.pop(i)
                if order_id in self._order_items:
                    del self._order_items[order_id]
                return True

        return False

    def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add an item to an order.

        Args:
            order_id: ID of the order to add the item to
            item_data: Item data including product_id, quantity, etc.

        Returns:
            Optional[Dict[str, Any]]: Added item data or None if order not found
        """
        self.logger.info(f"Adding item to order {order_id}")

        # Check if order exists
        order = self.get_order_by_id(order_id)
        if not order:
            return None

        # Prepare item data
        item = {
            "id": self._next_item_id,
            "order_id": order_id,
            "product_id": item_data.get("product_id"),
            "product_name": item_data.get("product_name", "Unknown Product"),
            "quantity": item_data.get("quantity", 1),
            "unit_price": item_data.get("unit_price", 0.0),
            "total_price": item_data.get("unit_price", 0.0) * item_data.get("quantity", 1),
            "notes": item_data.get("notes", "")
        }

        # Add item to order
        if order_id not in self._order_items:
            self._order_items[order_id] = []

        self._order_items[order_id].append(item)
        self._next_item_id += 1

        # Update order total
        total = sum(item["total_price"] for item in self._order_items[order_id])
        self.update_order(order_id, {"total_amount": total})

        return item

    def remove_order_item(self, order_id: int, item_id: int) -> bool:
        """Remove an item from an order.

        Args:
            order_id: ID of the order containing the item
            item_id: ID of the item to remove

        Returns:
            bool: True if removed, False if not found
        """
        self.logger.info(f"Removing item {item_id} from order {order_id}")

        # Check if order exists and has items
        if order_id not in self._order_items:
            return False

        # Find and remove the item
        for i, item in enumerate(self._order_items[order_id]):
            if item["id"] == item_id:
                self._order_items[order_id].pop(i)

                # Update order total
                total = sum(item["total_price"] for item in self._order_items[order_id])
                self.update_order(order_id, {"total_amount": total})

                return True

        return False

    def list_orders(self, status: Optional[OrderStatus] = None) -> List[Dict[str, Any]]:
        """
        List orders optionally filtered by status.

        Args:
            status: Optional filter by order status

        Returns:
            List of dictionaries containing matching order details
        """
        self.logger.debug(f"Listing orders with status: {status}")

        # Filter by status if specified
        if status:
            status_value = status.value
            return [order for order in self._orders.values() if order.get('status') == status_value]

        return list(self._orders.values())

    def search_orders(self, field: str, search_text: str, exact_match: bool = False) -> List[Dict[str, Any]]:
        """Search orders based on criteria.

        Args:
            field: Field to search in
            search_text: Text to search for
            exact_match: Whether to use exact matching

        Returns:
            List[Dict[str, Any]]: List of matching orders
        """
        self.logger.info(f"Searching orders for '{search_text}' in field '{field}'")

        results = []

        for order in self._orders:
            if field in order:
                field_value = str(order[field])

                if exact_match:
                    if field_value == search_text:
                        results.append(order)
                else:
                    if search_text.lower() in field_value.lower():
                        results.append(order)

        return results

    def calculate_order_total(self, order_id: int) -> float:
        """
        Calculate the total amount for an order.

        Args:
            order_id: Unique identifier of the order

        Returns:
            Calculated order total

        Raises:
            ValueError: If order with given ID doesn't exist
        """
        self.logger.debug(f"Calculating total for order ID {order_id}")

        if order_id not in self._orders:
            raise ValueError(f"Order with ID {order_id} not found")

        order = self._orders[order_id]
        total = 0.0

        # Sum up item costs
        for item_id in order.get('items', []):
            if item_id in self._order_items:
                item = self._order_items[item_id]
                quantity = item.get('quantity', 0)
                unit_price = item.get('unit_price', 0)
                total += quantity * unit_price

        return total

    def generate_order_report(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a report of orders within a date range.

        Args:
            start_date: Optional start date for filtering orders
            end_date: Optional end date for filtering orders

        Returns:
            Dictionary containing the order report
        """
        self.logger.debug(f"Generating order report from {start_date} to {end_date}")

        # In this simple implementation, we just return basic statistics
        total_orders = len(self._orders)
        total_revenue = sum(self.calculate_order_total(order_id) for order_id in self._orders)

        report = {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'average_order_value': total_revenue / total_orders if total_orders > 0 else 0
        }

        return report