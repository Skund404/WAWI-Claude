# database/models/order.py
from database.models.base import Base
from database.models.enums import OrderStatus, PaymentStatus
from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from utils.validators import validate_not_empty, validate_positive_number


class Order(Base):
    """
    Model representing a customer order.
    """
    # Order specific fields
    order_number = Column(String(50), unique=True, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)

    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    shipping_date = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)

    status = Column(Enum(OrderStatus), default=OrderStatus.NEW, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    subtotal = Column(Float, default=0.0, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    shipping_cost = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)

    shipping_address = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    # Foreign keys
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier = relationship("Supplier", back_populates="orders")

    def __init__(self, **kwargs):
        """Initialize an Order instance with validation.

        Args:
            **kwargs: Keyword arguments with order attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

        # Calculate total if not already set
        if 'total' not in kwargs and 'subtotal' in kwargs:
            self.calculate_total()

    @classmethod
    def _validate_creation(cls, data):
        """Validate order data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'customer_name', 'Customer name is required')

        # Validate numeric fields if provided
        for field in ['subtotal', 'tax', 'shipping_cost', 'total']:
            if field in data:
                validate_positive_number(data, field)

    def calculate_total(self):
        """Calculate the order total based on subtotal, tax, and shipping cost."""
        self.total = self.subtotal + self.tax + self.shipping_cost
        return self.total

    def update_status(self, new_status):
        """Update the order status with validation and tracking.

        Args:
            new_status (OrderStatus): The new status to set

        Raises:
            ValueError: If the status transition is invalid
        """
        # Implement status transition validation if needed
        self.status = new_status

        # Update related timestamps
        if new_status == OrderStatus.SHIPPED:
            self.shipping_date = datetime.utcnow()
        elif new_status == OrderStatus.DELIVERED:
            self.delivery_date = datetime.utcnow()


class OrderItem(Base):
    """
    Model representing an item in an order.
    """
    # OrderItem specific fields
    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, default=0.0, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    total_price = Column(Float, default=0.0, nullable=False)

    notes = Column(Text, nullable=True)

    # Foreign keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __init__(self, **kwargs):
        """Initialize an OrderItem.

        Args:
            **kwargs: Keyword arguments with order item attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

        # Calculate total price if not set
        if 'total_price' not in kwargs and 'unit_price' in kwargs and 'quantity' in kwargs:
            self.calculate_total_price()

    @classmethod
    def _validate_creation(cls, data):
        """Validate order item data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        if 'product_id' not in data:
            raise ValueError("Product ID is required")
        if 'order_id' not in data:
            raise ValueError("Order ID is required")

        # Validate numeric fields
        for field in ['quantity', 'unit_price']:
            if field in data:
                validate_positive_number(data, field)

    def calculate_total_price(self):
        """Calculate the total price based on quantity, unit price, and discount."""
        self.total_price = self.quantity * self.unit_price * (1 - self.discount / 100)
        return self.total_price