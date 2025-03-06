# database/models/product_pattern.py
"""
ProductPattern Model

Represents the many-to-many relationship between Product and Pattern
in the leatherworking application.
"""

import logging
from typing import Optional

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.models.base import Base
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Setup logger
logger = logging.getLogger(__name__)

# Explicitly import SQLAlchemy types to ensure they're available for lazy imports
Integer  # Ensure this type is explicitly referenced

# Lazy imports
Product = lazy_import('database.models.product', 'Product')
Pattern = lazy_import('database.models.pattern', 'Pattern')

# Register lazy imports to help resolve circular dependencies
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')
register_lazy_import('ProductPattern', 'database.models.product_pattern', 'ProductPattern')


class ProductPattern(Base):
    """
    Junction table for the many-to-many relationship between Product and Pattern.

    Corresponds to the ER diagram relationship:
    Product }|--o{ ProductPattern : associated_with
    ProductPattern }o--|| Pattern : follows
    """
    __tablename__ = 'product_patterns'

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign keys
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False)
    pattern_id: Mapped[int] = mapped_column(ForeignKey('patterns.id'), nullable=False)

    # Relationships
    product = relationship(
        'Product',
        back_populates='patterns',
        lazy='select'
    )

    pattern = relationship(
        'Pattern',
        back_populates='products',
        lazy='select'
    )

    def __init__(self, product_id: int, pattern_id: int):
        """
        Initialize a ProductPattern instance.

        Args:
            product_id: ID of the associated product
            pattern_id: ID of the associated pattern
        """
        self.product_id = product_id
        self.pattern_id = pattern_id

    def __repr__(self) -> str:
        """
        String representation of the ProductPattern.

        Returns:
            str: Descriptive string of the ProductPattern
        """
        return f"<ProductPattern(product_id={self.product_id}, pattern_id={self.pattern_id})>"


def setup_relationships():
    """
    Initialize relationships to resolve potential circular imports.
    """
    try:
        from .product import Product
        from .pattern import Pattern

        # Ensure Product has a relationship to ProductPattern
        if not hasattr(Product, 'patterns'):
            Product.patterns = relationship(
                'ProductPattern',
                back_populates='product',
                cascade='all, delete-orphan'
            )

        # Ensure Pattern has a relationship to ProductPattern
        if not hasattr(Pattern, 'products'):
            Pattern.products = relationship(
                'ProductPattern',
                back_populates='pattern',
                cascade='all, delete-orphan'
            )

        logger.info("ProductPattern relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing ProductPattern relationships: {e}")


# Final registration of lazy import
register_lazy_import('database.models.product_pattern.ProductPattern', 'database.models.product_pattern',
                     'ProductPattern')