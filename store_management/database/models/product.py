# database/models/product.py
from database.models.base import Base
from sqlalchemy import Column, String, Text, Float, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from utils.validators import validate_not_empty, validate_positive_number
import uuid


class Product(Base):
    """
    Model representing products sold in leatherworking business.
    """
    # Product specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=True, unique=True)

    category = Column(String(100), nullable=True)
    tags = Column(String(255), nullable=True)  # Comma-separated tags

    price = Column(Float, default=0.0, nullable=False)
    cost = Column(Float, default=0.0, nullable=False)

    stock_quantity = Column(Integer, default=0, nullable=False)
    min_stock_quantity = Column(Integer, default=0, nullable=False)

    weight = Column(Float, nullable=True)
    dimensions = Column(String(100), nullable=True)  # Format: "LxWxH"

    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)

    metadata = Column(JSON, nullable=True)

    # Foreign keys
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storage.id"), nullable=True)

    # Relationships
    pattern = relationship("Pattern", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    storage = relationship("Storage", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    parts = relationship("Part", back_populates="product")
    production_records = relationship("Production", back_populates="product")
    sales = relationship("Sales", back_populates="product")

    def __init__(self, **kwargs):
        """Initialize a Product instance with validation.

        Args:
            **kwargs: Keyword arguments for product attributes

        Raises:
            ValueError: If validation fails for any attribute
        """
        # Generate SKU if not provided
        if 'sku' not in kwargs and 'name' in kwargs:
            kwargs['sku'] = self._generate_sku(kwargs['name'])

        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate product attributes before saving.

        Raises:
            ValueError: If any validation check fails
        """
        validate_not_empty(data, 'name', 'Product name is required')

        if 'price' in data:
            validate_positive_number(data, 'price', allow_zero=True)
        if 'cost' in data:
            validate_positive_number(data, 'cost', allow_zero=True)
        if 'stock_quantity' in data:
            validate_positive_number(data, 'stock_quantity', allow_zero=True)
        if 'min_stock_quantity' in data:
            validate_positive_number(data, 'min_stock_quantity', allow_zero=True)

    def _generate_sku(self, name):
        """Generate a SKU for the product based on name.

        Args:
            name (str): Product name

        Returns:
            str: Generated SKU
        """
        # Take first 3 letters of name (uppercase) + 8 chars of a UUID
        name_part = ''.join(c for c in name if c.isalnum())[:3].upper()
        uuid_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"{name_part}-{uuid_part}"

    def adjust_stock(self, quantity_change):
        """Adjust the stock quantity.

        Args:
            quantity_change (int): The quantity to add (positive) or remove (negative)

        Raises:
            ValueError: If the resulting quantity would be negative
        """
        new_quantity = self.stock_quantity + quantity_change
        if new_quantity < 0:
            raise ValueError(f"Cannot adjust stock to {new_quantity}. Current stock is {self.stock_quantity}.")

        self.stock_quantity = new_quantity

    def calculate_profit_margin(self):
        """Calculate the product's profit margin.

        Returns:
            float: Profit margin as a percentage, or None if price is zero
        """
        if self.price > 0:
            return ((self.price - self.cost) / self.price) * 100
        return None

    def needs_restock(self):
        """Check if the product needs to be restocked.

        Returns:
            bool: True if the stock quantity is below the minimum stock quantity
        """
        return self.stock_quantity <= self.min_stock_quantity

    def soft_delete(self):
        """Soft delete the product by marking it as inactive."""
        self.is_active = False

    def restore(self):
        """Restore a soft-deleted product."""
        self.is_active = True

    def __repr__(self):
        """String representation of the product.

        Returns:
            str: Descriptive string of the product
        """
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}', stock={self.stock_quantity})>"