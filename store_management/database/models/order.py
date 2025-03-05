# database/models/order.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Float, Enum, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.models.base import Base, ModelValidationError
from database.models.enums import OrderStatus, PaymentStatus
from utils import register_lazy_import
import logging

# Forward declarations for circular imports
OrderItem = None
Customer = None

class Order(Base):
    """Represents a customer order with comprehensive tracking and validation."""
    __tablename__ = 'orders'

    # Customer fields
    customer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True
    )
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    register_lazy_import('Sales', 'database.models.sales', 'Sales')
    # Relationship with Customer model
    customer: Mapped[Optional['Customer']] = relationship(
        'Customer',
        back_populates='orders',
        lazy='selectin'
    )

    sales: Mapped[List["Sales"]] = relationship(
        "Sales",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Order details
    order_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    shipping_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Address information
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    billing_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tracking
    tracking_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status tracking
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.QUOTE_REQUEST,
        nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )

    # Financial tracking
    subtotal: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tax: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, info={"alias": "tax_amount"})
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, info={"alias": "total_amount"})

    # Foreign key for supplier orders
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Supplier relationship
    supplier: Mapped[Optional['Supplier']] = relationship(
        'Supplier',
        back_populates='orders',
        lazy='selectin'
    )

    def __init__(self, **kwargs):
        """Initialize the Order instance."""
        super().__init__(**kwargs)
        self.calculate_total()

    def calculate_total(self):
        """Calculate the total order amount."""
        if hasattr(self, 'items'):
            # Calculate subtotal from items
            items_subtotal = sum(getattr(item, 'subtotal', 0) for item in self.items)
            self.subtotal = items_subtotal

        self.total = self.subtotal + self.tax + self.shipping_cost
        return self.total

    def add_item(self, order_item):
        """Add an item to the order and update total."""
        if not hasattr(self, 'items'):
            self.items = []

        # Set the order reference
        order_item.order = self
        self.items.append(order_item)

        # Recalculate totals
        self.calculate_total()

    def remove_item(self, order_item):
        """Remove an item from the order and update total."""
        if hasattr(self, 'items') and order_item in self.items:
            self.items.remove(order_item)
            # Recalculate totals
            self.calculate_total()


# Set up relationship later to avoid circular imports
def setup_relationships():
    global OrderItem, Customer

    # Set up OrderItem relationship
    if OrderItem is None:
        try:
            from database.models.order_item import OrderItem as OI
            OrderItem = OI

            # Set up relationship if not already set
            if not hasattr(Order, 'items'):
                Order.items = relationship(
                    'OrderItem',
                    back_populates='order',
                    cascade='all, delete-orphan',
                    lazy='selectin'
                )
        except ImportError:
            logger.warning("Could not import OrderItem")

    # Set up Customer relationship
    if Customer is None:
        try:
            from database.models.customer import Customer as C
            Customer = C
            # Relationship is already defined in class attribute
        except ImportError:
            logger.warning("Could not import Customer")

    # Try to import Supplier 
    try:
        from database.models.supplier import Supplier
        # Relationship is already defined in class attribute
    except ImportError:
        logger.warning("Could not import Supplier")

# Try to setup relationships immediately
setup_relationships()
