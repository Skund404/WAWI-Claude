# database/models/product_pattern.py
"""
Comprehensive Product Pattern Model for Leatherworking Management System

This module defines the ProductPattern model with proper validation,
relationship management, and circular import resolution.

Implements the junction table between Product and Pattern entities
from the ER diagram, managing the many-to-many relationship.
"""

import logging
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    apply_mixins
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    CircularImportResolver
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')


class ProductPattern(Base, apply_mixins(TimestampMixin, ValidationMixin)):
    """
    ProductPattern model representing the many-to-many relationship between
    Product and Pattern entities.

    This implements the junction table for managing which patterns are associated
    with which products in the leatherworking management system.
    """
    __tablename__ = 'product_patterns'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign keys
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    pattern_id: Mapped[int] = mapped_column(Integer, ForeignKey('patterns.id'), nullable=False, index=True)

    # Additional relationship metadata
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sequence_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    product = relationship(
        "Product",
        back_populates="patterns",
        lazy="select"
    )

    pattern = relationship(
        "Pattern",
        back_populates="products",
        lazy="select"
    )

    def __init__(self, **kwargs):
        """
        Initialize a ProductPattern instance with proper validation.

        Args:
            **kwargs: Keyword arguments for relationship attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_product_pattern_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ProductPattern initialization failed: {e}")
            raise ModelValidationError(f"Failed to create ProductPattern: {str(e)}") from e

    @classmethod
    def _validate_product_pattern_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate product pattern relationship data.

        Args:
            data: Relationship data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'product_id', 'Product ID is required')
        validate_not_empty(data, 'pattern_id', 'Pattern ID is required')

        # Validate sequence_order if provided
        if 'sequence_order' in data and data['sequence_order'] is not None:
            if not isinstance(data['sequence_order'], int) or data['sequence_order'] < 0:
                raise ValidationError("Sequence order must be a non-negative integer", "sequence_order")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert product pattern relationship to a dictionary.

        Returns:
            Dictionary representation of the relationship
        """
        return {
            'id': self.id,
            'product_id': self.product_id,
            'pattern_id': self.pattern_id,
            'is_primary': self.is_primary,
            'sequence_order': self.sequence_order,
            'notes': self.notes,
            'product_name': getattr(self.product, 'name', None) if hasattr(self, 'product') and self.product else None,
            'pattern_name': getattr(self.pattern, 'name', None) if hasattr(self, 'pattern') and self.pattern else None
        }

    def __repr__(self) -> str:
        """
        String representation of the ProductPattern.

        Returns:
            Detailed relationship representation
        """
        primary_indicator = " (primary)" if hasattr(self, 'is_primary') and self.is_primary else ""
        sequence_info = f", order={self.sequence_order}" if hasattr(self,
                                                                    'sequence_order') and self.sequence_order is not None else ""

        return (
            f"<ProductPattern(id={self.id}, "
            f"product_id={self.product_id}, "
            f"pattern_id={self.pattern_id}{primary_indicator}{sequence_info})>"
        )


def initialize_relationships() -> None:
    """
    Initialize relationships between Product and Pattern models.

    This function resolves potential circular dependencies by setting up
    the relationship properties after all models have been loaded.
    """
    try:
        # Import models directly to avoid circular import issues
        from database.models.product import Product
        from database.models.pattern import Pattern

        # Ensure Product has a relationship to ProductPattern
        if not hasattr(Product, 'patterns') or Product.patterns is None:
            Product.patterns = relationship(
                'ProductPattern',
                back_populates='product',
                cascade='all, delete-orphan'
            )

        # Ensure Pattern has a relationship to ProductPattern
        if not hasattr(Pattern, 'products') or Pattern.products is None:
            Pattern.products = relationship(
                'ProductPattern',
                back_populates='pattern',
                cascade='all, delete-orphan'
            )

        logger.info("ProductPattern relationships initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing ProductPattern relationships: {e}")


# Register for lazy import resolution
register_lazy_import('ProductPattern', 'database.models.product_pattern', 'ProductPattern')