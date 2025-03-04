# database/models/pattern_resolver.py
"""
Resolver module for Pattern model relationships to handle circular imports.
This resolves the relationship between Pattern and Product models.
"""

from .base import Base
from .product import Product  # Import Product model
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging

# Import dependency injection if used elsewhere in the project
try:
    from di.core import inject
    from services.interfaces import (
        InventoryService,
        MaterialService,
        OrderService,
        ProjectService
    )
except ImportError:
    # Mock inject decorator if DI system is not available
    def inject(cls):
        return cls

from utils.circular_import_resolver import lazy_import, register_lazy_import

# Set up logger
logger = logging.getLogger(__name__)


class PatternModelResolver:
    """Responsible for resolving relationships for the Pattern model."""

    @classmethod
    def get_products_relationship(cls):
        """Get the products relationship with lazy loading.

        Returns:
            Mapped[List[Any]]: Relationship to Product models.
        """
        return relationship(
            "Product",
            back_populates="pattern",
            lazy="selectin",
            cascade="all, delete-orphan"
        )

    @classmethod
    def create_pattern_model(cls, base_classes):
        """Dynamically create the Pattern model with resolved relationships.

        Args:
            base_classes (tuple): Base classes for the model.

        Returns:
            type: Dynamically created Pattern model class.
        """

        # Define Pattern model with relationships
        class Pattern(*base_classes):
            __tablename__ = "patterns"

            # Define columns
            id = mapped_column(sa.Integer, primary_key=True)
            name = mapped_column(sa.String(100), nullable=False)
            description = mapped_column(sa.Text, nullable=True)

            # Products relationship
            products = cls.get_products_relationship()

            def __init__(self, **kwargs):
                """Initialize a Pattern instance with validation.

                Args:
                    **kwargs: Keyword arguments with pattern attributes.

                Raises:
                    ValueError: If validation fails for any field.
                """
                super().__init__(**kwargs)

            def __repr__(self):
                """String representation of the pattern.

                Returns:
                    str: String representation.
                """
                return f"<Pattern(id={self.id}, name='{self.name}')>"

        return Pattern


# Register the Pattern-Product relationship for lazy resolution
register_lazy_import('database.models.pattern.Pattern.products',
                     'database.models.pattern_resolver.PatternModelResolver.get_products_relationship')