# Path: database/models/order_item.py
"""
Separate module for OrderItem to break circular import dependency.
"""

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class OrderItem(BaseModel):
    """
    Represents an individual item within an order.

    Attributes:
        id (int): Primary key for the order item.
        order_id (int): Foreign key referencing the parent order.
        product_id (int): Foreign key referencing the product.
        quantity (float): Quantity of the product in the order.
        unit_price (float): Price per unit of the product.
        order (relationship): Relationship to the parent Order.
        product (relationship): Relationship to the associated Product.
    """
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)

    # Use lazy='subquery' to optimize relationship loading
    order = relationship("Order", back_populates="items", lazy='subquery')
    product = relationship("Product", back_populates="order_items", lazy='subquery')

    def __init__(self, product_id: int, quantity: float, unit_price: float):
        """
        Initialize an OrderItem.

        Args:
            product_id (int): ID of the product.
            quantity (float): Quantity of the product.
            unit_price (float): Price per unit of the product.
        """
        self.product_id = product_id
        self.quantity = quantity
        self.unit_price = unit_price

    def __repr__(self) -> str:
        """
        String representation of the OrderItem.

        Returns:
            str: Formatted string describing the order item.
        """
        return (f"<OrderItem(id={self.id}, "
                f"product_id={self.product_id}, "
                f"quantity={self.quantity}, "
                f"unit_price={self.unit_price})>")

    def update_quantity(self, new_quantity: float) -> None:
        """
        Update the quantity of the order item.

        Args:
            new_quantity (float): New quantity to set.
        """
        self.quantity = new_quantity

    def calculate_total_price(self) -> float:
        """
        Calculate the total price for this order item.

        Returns:
            float: Total price (quantity * unit price).
        """
        return self.quantity * self.unit_price

    def to_dict(self) -> dict:
        """
        Convert OrderItem to dictionary representation.

        Returns:
            dict: Dictionary containing OrderItem attributes.
        """
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price
        }