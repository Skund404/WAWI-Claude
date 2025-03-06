from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from typing import TYPE_CHECKING, Optional, Any, List, Dict
from datetime import datetime

"""
Circular Import Resolver for Order Model.

Provides a mechanism to lazily load and resolve model relationships
to prevent circular import issues.
"""
if TYPE_CHECKING:
    from .supplier import Supplier
    from .sale_item import SaleItem
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum


class OrderStatus(Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'


class PaymentStatus(Enum):
    UNPAID = 'unpaid'
    PAID = 'paid'
    REFUNDED = 'refunded'


class OrderModelResolver:
    """
    A resolver class to handle lazy loading of sale-related models.
    """
    _supplier_model: Optional[Any] = None
    _order_item_model: Optional[Any] = None

    @classmethod
    def set_supplier_model(cls, supplier_model: Any) -> None:
        """Set the Supplier model class for lazy loading."""
        cls._supplier_model = supplier_model

    @classmethod
    def set_order_item_model(cls, order_item_model: Any) -> None:
        """Set the OrderItem model class for lazy loading."""
        cls._order_item_model = order_item_model

    @classmethod
    def get_supplier_relationship(cls):
        """Get the supplier relationship with lazy loading."""
        if cls._supplier_model is None:
            from .supplier import Supplier
            cls._supplier_model = Supplier
        return relationship(cls._supplier_model, back_populates='orders',
                            lazy='subquery')

    @classmethod
    def get_order_items_relationship(cls):
        """Get the sale items relationship with lazy loading."""
        if cls._order_item_model is None:
            from .sale_item import SaleItem
            cls._order_item_model = SaleItem
        return relationship(cls._order_item_model, back_populates='sale',
                            cascade='all, delete-orphan', lazy='subquery')


def create_order_model(base_classes):
    """
    Dynamically create the Order model with resolved relationships.

    Args:
        base_classes (tuple): Base classes for the model.

    Returns:
        type: Dynamically created Order model class.
    """

    class Order(*base_classes):
        """
        Represents a customer sale in the system.
        """
        __tablename__ = 'orders'
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        order_number: Mapped[str] = mapped_column(String(50), unique=True,
                                                   nullable=False)
        customer_name: Mapped[Optional[str]] = mapped_column(String(100))
        status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus),
                                                     default=OrderStatus.PENDING)
        payment_status: Mapped[PaymentStatus] = mapped_column(Enum(
            PaymentStatus), default=PaymentStatus.UNPAID)
        total_amount: Mapped[float] = mapped_column(Float, default=0.0)
        created_at: Mapped[datetime] = mapped_column(
            DateTime, default=datetime.utcnow)
        updated_at: Mapped[datetime] = mapped_column(
            DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        supplier_id: Mapped[Optional[int]] = mapped_column(Integer,
                                                            nullable=True)
        supplier = OrderModelResolver.get_supplier_relationship()
        items = OrderModelResolver.get_order_items_relationship()

        @inject(MaterialService)
        def __init__(self, order_number: str, customer_name: Optional[str] = None
                     ):
            """
            Initialize an Order instance.

            Args:
                order_number (str): Unique sale identifier.
                customer_name (Optional[str], optional): Name of the customer.
            """
            self.order_number = order_number
            self.customer_name = customer_name
            self.status = OrderStatus.PENDING
            self.payment_status = PaymentStatus.UNPAID
            self.total_amount = 0.0
            self.items = []

        @inject(MaterialService)
        def add_item(self, order_item) -> None:
            """
            Add an item to the sale.

            Args:
                order_item: OrderItem to be added.
            """
            order_item.sale = self
            self.items.append(order_item)
            self.calculate_total_amount()

        @inject(MaterialService)
        def remove_item(self, order_item) -> None:
            """
            Remove an item from the sale.

            Args:
                order_item: OrderItem to be removed.
            """
            if order_item in self.items:
                self.items.remove(order_item)
                order_item.sale = None
                self.calculate_total_amount()

        @inject(MaterialService)
        def calculate_total_amount(self) -> float:
            """
            Calculate the total amount of the sale.

            Returns:
                float: Total sale amount.
            """
            self.total_amount = sum(item.calculate_total_price() for item in
                                     self.items)
            return self.total_amount

        @inject(MaterialService)
        def update_status(self, new_status: OrderStatus) -> None:
            """
            Update the sale status.

            Args:
                new_status (OrderStatus): New status to set.
            """
            self.status = new_status

        @inject(MaterialService)
        def update_payment_status(self, new_payment_status: PaymentStatus
                                 ) -> None:
            """
            Update the payment status of the sale.

            Args:
                new_payment_status (PaymentStatus): New payment status.
            """
            self.payment_status = new_payment_status

        @inject(MaterialService)
        def to_dict(self, exclude_fields: Optional[List[str]] = None,
                    include_relationships: bool = False) -> Dict[str, Any]:
            """
            Convert Order to dictionary representation.

            Args:
                exclude_fields (Optional[List[str]], optional): Fields to exclude.
                include_relationships (bool, optional): Whether to include related entities.

            Returns:
                Dict[str, Any]: Dictionary of sale attributes.
            """
            exclude_fields = exclude_fields or []
            order_dict = {'id': self.id, 'sale_number': self.order_number,
                          'customer_name': self.customer_name, 'status': self.status.
                          value, 'payment_status': self.payment_status.value,
                          'total_amount': self.total_amount, 'created_at': self.
                          created_at.isoformat(), 'updated_at': self.updated_at.
                          isoformat()}
            for field in exclude_fields:
                order_dict.pop(field, None)
            if include_relationships:
                if self.supplier:
                    order_dict['supplier'] = self.supplier.to_dict()
                if self.items:
                    order_dict['items'] = [item.to_dict() for item in self.
                                            items]
            return order_dict
    return Order


Sale = create_order_model((BaseModel, TimestampMixin, ValidationMixin))