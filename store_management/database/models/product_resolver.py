# Path: store_management/database/models/product_resolver.py
"""
Circular Import Resolver for Product Model.

Provides a mechanism to lazily load and resolve model relationships
to prevent circular import issues.
"""

from typing import TYPE_CHECKING, Any, Optional, List, Dict
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, Float, Enum, DateTime
from datetime import datetime

from .base import BaseModel
from .enums import MaterialType
from .mixins import TimestampMixin, ValidationMixin

if TYPE_CHECKING:
    from .supplier import Supplier
    from .order import OrderItem
    from .storage import Storage


class ProductModelResolver:
    """
    A resolver class to handle lazy loading of product-related models.
    """

    _supplier_model: Optional[Any] = None
    _order_item_model: Optional[Any] = None
    _storage_model: Optional[Any] = None

    @classmethod
    def set_supplier_model(cls, supplier_model: Any) -> None:
        """Set the Supplier model class for lazy loading."""
        cls._supplier_model = supplier_model

    @classmethod
    def set_order_item_model(cls, order_item_model: Any) -> None:
        """Set the OrderItem model class for lazy loading."""
        cls._order_item_model = order_item_model

    @classmethod
    def set_storage_model(cls, storage_model: Any) -> None:
        """Set the Storage model class for lazy loading."""
        cls._storage_model = storage_model

    @classmethod
    def get_supplier_relationship(cls):
        """Get the supplier relationship with lazy loading."""
        if cls._supplier_model is None:
            from .supplier import Supplier
            cls._supplier_model = Supplier

        return relationship(
            cls._supplier_model,
            back_populates="products",
            lazy='subquery'
        )

    @classmethod
    def get_order_items_relationship(cls):
        """Get the order items relationship with lazy loading."""
        if cls._order_item_model is None:
            from .order_item import OrderItem
            cls._order_item_model = OrderItem

        return relationship(
            cls._order_item_model,
            back_populates="product",
            lazy='subquery'
        )

    @classmethod
    def get_storage_relationship(cls):
        """Get the storage relationship with lazy loading."""
        if cls._storage_model is None:
            from .storage import Storage
            cls._storage_model = Storage

        return relationship(
            cls._storage_model,
            back_populates="products",
            lazy='subquery'
        )


def create_product_model(base_classes):
    """
    Dynamically create the Product model with resolved relationships.

    Args:
        base_classes (tuple): Base classes for the model.

    Returns:
        type: Dynamically created Product model class.
    """

    class Product(*base_classes):
        """
        Represents a product in the inventory system.
        """
        __tablename__ = 'products'

        # Basic product information
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        description: Mapped[Optional[str]] = mapped_column(String(500))
        sku: Mapped[Optional[str]] = mapped_column(String(50), unique=True)

        # Pricing and costing
        price: Mapped[float] = mapped_column(Float, nullable=False)
        cost_price: Mapped[float] = mapped_column(Float, nullable=False)

        # Inventory tracking
        stock_quantity: Mapped[float] = mapped_column(Float, default=0.0)
        minimum_stock_level: Mapped[float] = mapped_column(Float, default=0.0)

        # Categorization
        material_type: Mapped[MaterialType] = mapped_column(Enum(MaterialType))

        # Timestamps
        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Relationships using resolver
        supplier_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
        supplier = ProductModelResolver.get_supplier_relationship()
        order_items = ProductModelResolver.get_order_items_relationship()
        storage = ProductModelResolver.get_storage_relationship()

        def __init__(self,
                     name: str,
                     price: float,
                     cost_price: float,
                     material_type: MaterialType,
                     description: Optional[str] = None,
                     sku: Optional[str] = None):
            """
            Initialize a Product instance.

            Args:
                name (str): Name of the product.
                price (float): Selling price of the product.
                cost_price (float): Cost price of the product.
                material_type (MaterialType): Type of material.
                description (Optional[str], optional): Product description.
                sku (Optional[str], optional): Stock Keeping Unit.
            """
            self.name = name
            self.price = price
            self.cost_price = cost_price
            self.material_type = material_type
            self.description = description
            self.sku = sku

            # Default initializations
            self.stock_quantity = 0.0
            self.minimum_stock_level = 0.0

        def update_stock(self, quantity_change: float) -> None:
            """
            Update the stock quantity.

            Args:
                quantity_change (float): Amount to change stock by.
            """
            self.stock_quantity += quantity_change

        def is_low_stock(self) -> bool:
            """
            Check if product is below minimum stock level.

            Returns:
                bool: True if stock is low, False otherwise.
            """
            return self.stock_quantity <= self.minimum_stock_level

        def calculate_profit_margin(self) -> float:
            """
            Calculate the profit margin percentage.

            Returns:
                float: Profit margin percentage.
            """
            return ((self.price - self.cost_price) / self.price) * 100 if self.price > 0 else 0.0

        def to_dict(self,
                    exclude_fields: Optional[List[str]] = None,
                    include_relationships: bool = False) -> Dict[str, Any]:
            """
            Convert Product to dictionary representation.

            Args:
                exclude_fields (Optional[List[str]], optional): Fields to exclude.
                include_relationships (bool, optional): Whether to include related entities.

            Returns:
                Dict[str, Any]: Dictionary of product attributes.
            """
            exclude_fields = exclude_fields or []

            product_dict = {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'sku': self.sku,
                'price': self.price,
                'cost_price': self.cost_price,
                'stock_quantity': self.stock_quantity,
                'minimum_stock_level': self.minimum_stock_level,
                'material_type': self.material_type.value,
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat(),
                'profit_margin': self.calculate_profit_margin(),
                'is_low_stock': self.is_low_stock()
            }

            # Remove excluded fields
            for field in exclude_fields:
                product_dict.pop(field, None)

            # Optionally include relationships
            if include_relationships:
                if self.supplier:
                    product_dict['supplier'] = self.supplier.to_dict()

                if self.order_items:
                    product_dict['order_items'] = [
                        item.to_dict() for item in self.order_items
                    ]

                if self.storage:
                    product_dict['storage'] = self.storage.to_dict()

            return product_dict

    return Product


# Create the Product model with resolved base classes
Product = create_product_model((BaseModel, TimestampMixin, ValidationMixin))