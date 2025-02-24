# Path: store_management/database/models/order_item_resolver.py
"""
Circular Import Resolver for OrderItem Model.

Provides a mechanism to lazily load and resolve model relationships
to prevent circular import issues.
"""

from typing import TYPE_CHECKING, Any, Optional, List, Dict
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Column, Integer, Float, ForeignKey
from datetime import datetime

from .base import BaseModel
from .mixins import TimestampMixin, ValidationMixin

if TYPE_CHECKING:
    from .product import Product
    from .order import Order


class OrderItemModelResolver:
    """
    A resolver class to handle lazy loading of order item-related models.
    """

    _product_model: Optional[Any] = None
    _order_model: Optional[Any] = None

    @classmethod
    def set_product_model(cls, product_model: Any) -> None:
        """Set the Product model class for lazy loading."""
        cls._product_model = product_model

    @classmethod
    def set_order_model(cls, order_model: Any) -> None:
        """Set the Order model class for lazy loading."""
        cls._order_model = order_model

    @classmethod
    def get_product_relationship(cls):
        """Get the product relationship with lazy loading."""
        if cls._product_model is None:
            from .product import Product
            cls._product_model = Product

        return relationship(
            cls._product_model,
            back_populates="order_items",
            lazy='subquery'
        )

    @classmethod
    def get_order_relationship(cls):
        """Get the order relationship with lazy loading."""
        if cls._order_model is None:
            from .order import Order
            cls._order_model = Order

        return relationship(
            cls._order_model,
            back_populates="items",
            lazy='subquery'
        )


def create_order_item_model(base_classes):
    """
    Dynamically create the OrderItem model with resolved relationships.

    Args:
        base_classes (tuple): Base classes for the model.

    Returns:
        type: Dynamically created OrderItem model class.
    """

    class OrderItem(*base_classes):
        """
        Represents an individual item within an order.
        """
        __tablename__ = 'order_items'

        # Basic order item information
        id: Mapped[int] = mapped_column(Integer, primary_key=True)

        # Foreign keys
        order_id: Mapped[int] = mapped_column(Integer, ForeignKey('orders.id'))
        product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'))

        # Order item details
        quantity: Mapped[float] = mapped_column(Float, nullable=False)
        unit_price: Mapped[float] = mapped_column(Float, nullable=False)

        # Relationships using resolver
        product = OrderItemModelResolver.get_product_relationship()
        order = OrderItemModelResolver.get_order_relationship()

        def __init__(self,
                     product_id: int,
                     quantity: float,
                     unit_price: float):
            """
            Initialize an OrderItem instance.

            Args:
                product_id (int): ID of the product.
                quantity (float): Quantity of the product.
                unit_price (float): Price per unit.
            """
            self.product_id = product_id
            self.quantity = quantity
            self.unit_price = unit_price

        def calculate_total_price(self) -> float:
            """
            Calculate the total price for this order item.

            Returns:
                float: Total price (quantity * unit price).
            """
            return self.quantity * self.unit_price

        def update_quantity(self, new_quantity: float) -> None:
            """
            Update the quantity of the order item.

            Args:
                new_quantity (float): New quantity to set.
            """
            self.quantity = new_quantity

        def to_dict(self,
                    exclude_fields: Optional[List[str]] = None,
                    include_relationships: bool = False) -> Dict[str, Any]:
            """
            Convert OrderItem to dictionary representation.

            Args:
                exclude_fields (Optional[List[str]], optional): Fields to exclude.
                include_relationships (bool, optional): Whether to include related entities.

            Returns:
                Dict[str, Any]: Dictionary of order item attributes.
            """
            exclude_fields = exclude_fields or []

            order_item_dict = {
                'id': self.id,
                'order_id': self.order_id,
                'product_id': self.product_id,
                'quantity': self.quantity,
                'unit_price': self.unit_price,
                'total_price': self.calculate_total_price()
            }

            # Remove excluded fields
            for field in exclude_fields:
                order_item_dict.pop(field, None)

            # Optionally include relationships
            if include_relationships:
                if self.product:
                    order_item_dict['product'] = self.product.to_dict()

                if self.order:
                    order_item_dict['order'] = self.order.to_dict()

            return order_item_dict

    return OrderItem


# Create the OrderItem model with resolved base classes
OrderItem = create_order_item_model((BaseModel, TimestampMixin, ValidationMixin))