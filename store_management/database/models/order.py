# database/models/order.py

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import logging

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.models.base import Base, BaseModel
from database.models.enums import OrderStatus, PaymentStatus
from utils.logger import get_logger
from utils.validators import (
    validate_string, validate_positive_number, validate_not_empty,
    validate_date, validate_email, validate_phone
)

logger = get_logger(__name__)


class Order(Base, BaseModel):
    """
    Enhanced Order model with comprehensive validation and logging.

    Represents a customer order in the leatherworking system, with relationships
    to order items, suppliers, and payment information.
    """
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    order_date = Column(DateTime, default=func.now(), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False)
    shipping_address = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    total_amount = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)

    # Timestamps and soft delete
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    supplier = relationship("Supplier", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """
        Initialize an Order instance with validation.

        Args:
            **kwargs: Keyword arguments with order attributes

        Raises:
            ValueError: If validation fails for any field
        """
        logger.debug(f"Initializing new Order with data: {kwargs}")

        # Validate required fields
        if 'order_number' in kwargs:
            validate_string(kwargs['order_number'], 'order_number', min_length=3, max_length=50)

        if 'customer_name' in kwargs:
            validate_string(kwargs['customer_name'], 'customer_name', min_length=2, max_length=100)

        if 'customer_email' in kwargs and kwargs['customer_email']:
            validate_email(kwargs['customer_email'], 'customer_email')

        if 'customer_phone' in kwargs and kwargs['customer_phone']:
            validate_phone(kwargs['customer_phone'], 'customer_phone')

        if 'order_date' in kwargs:
            validate_date(kwargs['order_date'], 'order_date')

        if 'total_amount' in kwargs:
            validate_positive_number(kwargs['total_amount'], 'total_amount')

        # Set defaults if not provided
        if 'status' not in kwargs:
            kwargs['status'] = OrderStatus.PENDING

        if 'payment_status' not in kwargs:
            kwargs['payment_status'] = PaymentStatus.UNPAID

        super().__init__(**kwargs)
        logger.info(f"Order initialized: {self.order_number}")

    def update(self, **kwargs) -> 'Order':
        """
        Update order attributes with validation.

        Args:
            **kwargs: Keyword arguments with order attributes to update

        Returns:
            Order: Self reference

        Raises:
            ValueError: If validation fails for any field
        """
        logger.debug(f"Updating Order {self.id} with data: {kwargs}")

        # Store original values for logging changes
        original_values = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                original_values[key] = getattr(self, key)

        # Validate fields
        if 'order_number' in kwargs:
            validate_string(kwargs['order_number'], 'order_number', min_length=3, max_length=50)

        if 'customer_name' in kwargs:
            validate_string(kwargs['customer_name'], 'customer_name', min_length=2, max_length=100)

        if 'customer_email' in kwargs and kwargs['customer_email']:
            validate_email(kwargs['customer_email'], 'customer_email')

        if 'customer_phone' in kwargs and kwargs['customer_phone']:
            validate_phone(kwargs['customer_phone'], 'customer_phone')

        if 'order_date' in kwargs:
            validate_date(kwargs['order_date'], 'order_date')

        if 'total_amount' in kwargs:
            validate_positive_number(kwargs['total_amount'], 'total_amount')

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Log changes
        for key, old_value in original_values.items():
            new_value = getattr(self, key)
            if old_value != new_value:
                logger.info(f"Order {self.id}: {key} changed from '{old_value}' to '{new_value}'")

        self.updated_at = func.now()
        return self

    def soft_delete(self) -> None:
        """
        Soft delete the order.

        This doesn't remove the order from the database but marks it as deleted.
        """
        logger.info(f"Soft deleting Order {self.id}")
        self.deleted = True
        self.deleted_at = datetime.now()

    def restore(self) -> None:
        """
        Restore a soft-deleted order.
        """
        logger.info(f"Restoring soft-deleted Order {self.id}")
        self.deleted = False
        self.deleted_at = None

    def calculate_total(self) -> float:
        """
        Calculate the total amount of the order based on its items.

        Returns:
            float: The total amount
        """
        total = sum(item.quantity * item.unit_price for item in self.items)
        logger.debug(f"Order {self.id}: calculated total: {total}")
        self.total_amount = total
        return total

    def add_item(self, product_id: int, quantity: float, unit_price: float) -> 'OrderItem':
        """
        Add an item to the order.

        Args:
            product_id: ID of the product
            quantity: Quantity of the product
            unit_price: Price per unit of the product

        Returns:
            OrderItem: The created order item
        """
        from database.models.order_item import OrderItem

        logger.debug(
            f"Adding item to Order {self.id}: product_id={product_id}, quantity={quantity}, unit_price={unit_price}")

        # Validate inputs
        validate_positive_number(quantity, 'quantity')
        validate_positive_number(unit_price, 'unit_price')

        # Create and add the item
        item = OrderItem(
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price
        )
        self.items.append(item)

        # Recalculate the total
        self.calculate_total()

        logger.info(f"Added item to Order {self.id}: {item}")
        return item

    def remove_item(self, item_id: int) -> None:
        """
        Remove an item from the order.

        Args:
            item_id: ID of the item to remove
        """
        logger.debug(f"Removing item {item_id} from Order {self.id}")

        # Find and remove the item
        for idx, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(idx)
                logger.info(f"Removed item {item_id} from Order {self.id}")

                # Recalculate the total
                self.calculate_total()
                return

        logger.warning(f"Item {item_id} not found in Order {self.id}")

    def __repr__(self) -> str:
        """
        String representation of the order.

        Returns:
            str: String representation
        """
        return f"<Order(id={self.id}, order_number='{self.order_number}', status={self.status}, total_amount={self.total_amount})>"


class OrderItem(Base, BaseModel):
    """
    Enhanced OrderItem model with validation and logging.

    Represents an item within an order, linked to a product.
    """
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    def __init__(self, **kwargs):
        """
        Initialize an OrderItem.

        Args:
            **kwargs: Keyword arguments with order item attributes

        Raises:
            ValueError: If validation fails for any field
        """
        logger.debug(f"Initializing new OrderItem with data: {kwargs}")

        # Validate required fields
        if 'quantity' in kwargs:
            validate_positive_number(kwargs['quantity'], 'quantity')

        if 'unit_price' in kwargs:
            validate_positive_number(kwargs['unit_price'], 'unit_price')

        super().__init__(**kwargs)
        logger.info(f"OrderItem initialized: order_id={kwargs.get('order_id')}, product_id={kwargs.get('product_id')}")

    def update(self, **kwargs) -> 'OrderItem':
        """
        Update order item attributes with validation.

        Args:
            **kwargs: Keyword arguments with order item attributes to update

        Returns:
            OrderItem: Self reference

        Raises:
            ValueError: If validation fails for any field
        """
        logger.debug(f"Updating OrderItem {self.id} with data: {kwargs}")

        # Store original values for logging changes
        original_values = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                original_values[key] = getattr(self, key)

        # Validate fields
        if 'quantity' in kwargs:
            validate_positive_number(kwargs['quantity'], 'quantity')

        if 'unit_price' in kwargs:
            validate_positive_number(kwargs['unit_price'], 'unit_price')

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Log changes
        for key, old_value in original_values.items():
            new_value = getattr(self, key)
            if old_value != new_value:
                logger.info(f"OrderItem {self.id}: {key} changed from '{old_value}' to '{new_value}'")

        # Update parent order total if quantity or price changed
        if ('quantity' in kwargs or 'unit_price' in kwargs) and self.order:
            self.order.calculate_total()

        self.updated_at = func.now()
        return self

    def get_total(self) -> float:
        """
        Calculate the total price for this item.

        Returns:
            float: Total price (quantity * unit_price)
        """
        return self.quantity * self.unit_price

    def __repr__(self) -> str:
        """
        String representation of the order item.

        Returns:
            str: String representation
        """
        return f"<OrderItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity}, unit_price={self.unit_price})>"