# database/models/product.py
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4

from database.models.base import Base, BaseModel
from database.models.enums import MaterialType
from database.models.mixins import TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin
from database.models.base import ModelValidationError

import logging
import re
import uuid


class Product(Base, BaseModel, TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin):
    """
    Represents a product in the leatherworking inventory system.

    Attributes:
        name (str): Name of the product
        description (str): Detailed description of the product
        sku (str): Unique Stock Keeping Unit identifier
        material_type (MaterialType): Type of primary material used
        unit_cost (float): Cost to produce the product
        sale_price (float): Selling price of the product
        is_active (bool): Whether the product is currently available
        supplier_id (int): Reference to the supplier of the product

    Validation Rules:
        - Name must be non-empty and between 2-100 characters
        - SKU must follow a specific format
        - Prices must be non-negative
        - Material type must be a valid enum value
    """
    __tablename__ = 'products'

    # Basic product information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sku = Column(String(50), unique=True, nullable=False)
    material_type = Column(MaterialType, nullable=False)

    # Pricing and cost tracking
    unit_cost = Column(Float, nullable=False, default=0.0)
    sale_price = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True)

    # Relationships
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    supplier = relationship('Supplier', back_populates='products')

    def __init__(self, **kwargs):
        """
        Initialize a Product instance with validation.

        Args:
            **kwargs: Keyword arguments for product attributes

        Raises:
            ModelValidationError: If validation fails for any attribute
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """
        Validate product attributes before saving.

        Raises:
            ModelValidationError: If any validation check fails
        """
        # Validate name
        if not self.name or len(self.name) < 2 or len(self.name) > 100:
            raise ModelValidationError(
                "Product name must be between 2 and 100 characters",
                {"name": self.name}
            )

        # Validate SKU format (example: LTH-PRD-XXXX)
        if not re.match(r'^[A-Z]{3}-[A-Z]{3}-\d{4}$', self.sku):
            raise ModelValidationError(
                "SKU must follow format LTH-PRD-XXXX",
                {"sku": self.sku}
            )

        # Validate pricing
        if self.unit_cost < 0 or self.sale_price < 0:
            raise ModelValidationError(
                "Prices cannot be negative",
                {"unit_cost": self.unit_cost, "sale_price": self.sale_price}
            )

        # Validate material type
        if not isinstance(self.material_type, MaterialType):
            raise ModelValidationError(
                "Invalid material type",
                {"material_type": self.material_type}
            )

    def update(self, **kwargs):
        """
        Update product attributes with validation.

        Args:
            **kwargs: Keyword arguments with product attributes to update

        Returns:
            Product: Updated product instance

        Raises:
            ModelValidationError: If validation fails for any field
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.validate()
        return self

    def soft_delete(self):
        """
        Soft delete the product by marking it as inactive.
        """
        self.is_active = False
        logging.info(f"Product {self.id} soft deleted", extra={
            "product_id": self.id,
            "product_name": self.name
        })

    def restore(self):
        """
        Restore a soft-deleted product.
        """
        self.is_active = True
        logging.info(f"Product {self.id} restored", extra={
            "product_id": self.id,
            "product_name": self.name
        })

    def __repr__(self):
        """
        String representation of the product.

        Returns:
            str: Descriptive string of the product
        """
        return (f"<Product(id={self.id}, name='{self.name}', "
                f"sku='{self.sku}', material_type={self.material_type})>")