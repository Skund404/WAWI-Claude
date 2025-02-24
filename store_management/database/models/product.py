# Path: database/models/product.py
"""
Product model definition with support for order items.
"""

from sqlalchemy import Column, Integer, String, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel
from .enums import MaterialType


class Product(BaseModel):
    """
    Represents a product in the inventory system.

    Attributes:
        id (int): Primary key for the product.
        name (str): Name of the product.
        price (float): Selling price of the product.
        cost_price (float): Cost price of the product.
        description (str): Product description.
        sku (str): Stock Keeping Unit identifier.
        material_type (MaterialType): Type of material used in the product.
        stock_quantity (float): Current stock quantity.
        minimum_stock_level (float): Minimum stock level before reordering.
        created_at (datetime): Timestamp of product creation.
        updated_at (datetime): Timestamp of last product update.
        order_items (list): List of order items associated with this product.
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    description = Column(String(255))
    sku = Column(String(50), unique=True)
    material_type = Column(Enum(MaterialType))
    stock_quantity = Column(Float, default=0)
    minimum_stock_level = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with OrderItem
    order_items = relationship("OrderItem", back_populates="product",
                               cascade="all, delete-orphan",
                               lazy='subquery')

    def __init__(self, name: str, price: float, cost_price: float,
                 description: str = None, sku: str = None,
                 material_type: MaterialType = None):
        """
        Initialize a Product.

        Args:
            name (str): Name of the product.
            price (float): Selling price of the product.
            cost_price (float): Cost price of the product.
            description (str, optional): Product description. Defaults to None.
            sku (str, optional): Stock Keeping Unit identifier. Defaults to None.
            material_type (MaterialType, optional): Type of material. Defaults to None.
        """
        self.name = name
        self.price = price
        self.cost_price = cost_price
        self.description = description
        self.sku = sku
        self.material_type = material_type

    def __repr__(self) -> str:
        """
        String representation of the Product.

        Returns:
            str: Formatted string describing the product.
        """
        return (f"<Product(id={self.id}, "
                f"name='{self.name}', "
                f"price={self.price}, "
                f"stock_quantity={self.stock_quantity})>")

    def update_stock(self, quantity_change: float, transaction_type: str = None) -> None:
        """
        Update the stock quantity of the product.

        Args:
            quantity_change (float): Amount to change stock by (positive or negative).
            transaction_type (str, optional): Type of stock transaction. Defaults to None.
        """
        self.stock_quantity += quantity_change

    def is_low_stock(self) -> bool:
        """
        Check if the product is below its minimum stock level.

        Returns:
            bool: True if stock is low, False otherwise.
        """
        return self.stock_quantity <= self.minimum_stock_level

    def calculate_profit_margin(self) -> float:
        """
        Calculate the profit margin of the product.

        Returns:
            float: Profit margin percentage.
        """
        return ((self.price - self.cost_price) / self.price) * 100 if self.price > 0 else 0

    def activate(self) -> None:
        """
        Activate the product (placeholder for potential future implementation).
        """
        # Future implementation might include setting an active flag
        pass

    def deactivate(self) -> None:
        """
        Deactivate the product (placeholder for potential future implementation).
        """
        # Future implementation might include setting an inactive flag
        pass

    def to_dict(self, include_details: bool = False) -> dict:
        """
        Convert Product to dictionary representation.

        Args:
            include_details (bool, optional): Whether to include additional details. Defaults to False.

        Returns:
            dict: Dictionary containing Product attributes.
        """
        product_dict = {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'cost_price': self.cost_price,
            'description': self.description,
            'sku': self.sku,
            'material_type': self.material_type.value if self.material_type else None,
            'stock_quantity': self.stock_quantity,
            'minimum_stock_level': self.minimum_stock_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_details:
            product_dict.update({
                'profit_margin': self.calculate_profit_margin(),
                'is_low_stock': self.is_low_stock()
            })

        return product_dict