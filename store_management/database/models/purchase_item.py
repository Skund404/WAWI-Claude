# database/models/purchase_item.py
"""
Purchase Item Model

This module defines the PurchaseItem model which implements
the PurchaseItem entity from the ER diagram.
"""

import logging
from typing import Dict, Any, Optional, Union

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, validate_positive_number, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports
Purchase = lazy_import('database.models.purchase', 'Purchase')
Material = lazy_import('database.models.material', 'Material')
Leather = lazy_import('database.models.leather', 'Leather')
Hardware = lazy_import('database.models.hardware', 'Hardware')
Tool = lazy_import('database.models.tool', 'Tool')

# Register lazy imports
register_lazy_import('database.models.purchase.Purchase', 'database.models.purchase', 'Purchase')
register_lazy_import('database.models.material.Material', 'database.models.material', 'Material')
register_lazy_import('database.models.leather.Leather', 'database.models.leather', 'Leather')
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('database.models.tool.Tool', 'database.models.tool', 'Tool')


class PurchaseItem(Base):
    """
    PurchaseItem model representing items in a purchase order.
    This corresponds to the PurchaseItem entity in the ER diagram.
    """
    __tablename__ = 'purchase_items'

    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    # References to purchasable items - only one should be set
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), nullable=True)
    hardware_id = Column(Integer, ForeignKey('hardwares.id'), nullable=True)
    tool_id = Column(Integer, ForeignKey('tools.id'), nullable=True)

    # Additional fields
    description = Column(String(255), nullable=True)

    # Relationships
    purchase = relationship("Purchase", back_populates="items")
    material = relationship("Material", lazy="select")
    leather = relationship("Leather", lazy="select")
    hardware = relationship("Hardware", lazy="select")
    tool = relationship("Tool", lazy="select")

    def __init__(self, purchase_id: int, quantity: int, price: float,
                 material_id: Optional[int] = None, leather_id: Optional[int] = None,
                 hardware_id: Optional[int] = None, tool_id: Optional[int] = None,
                 description: Optional[str] = None, **kwargs):
        """
        Initialize a PurchaseItem instance.

        Args:
            purchase_id: ID of the purchase
            quantity: Quantity ordered
            price: Price per unit
            material_id: Optional ID of the material
            leather_id: Optional ID of the leather
            hardware_id: Optional ID of the hardware
            tool_id: Optional ID of the tool
            description: Optional description
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'purchase_id': purchase_id,
                'quantity': quantity,
                'price': price,
                'material_id': material_id,
                'leather_id': leather_id,
                'hardware_id': hardware_id,
                'tool_id': tool_id,
                'description': description
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PurchaseItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create purchase item: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate purchase item creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'purchase_id', 'Purchase ID is required')
        validate_not_empty(data, 'quantity', 'Quantity is required')
        validate_not_empty(data, 'price', 'Price is required')

        # Validate numeric fields
        validate_positive_number(data, 'quantity', allow_zero=False, message="Quantity must be positive")
        validate_positive_number(data, 'price', allow_zero=False, message="Price must be positive")

        # Validate that at least one item type is specified
        if not any([data.get('material_id'), data.get('leather_id'),
                    data.get('hardware_id'), data.get('tool_id')]):
            raise ValidationError("At least one item type (material, leather, hardware, or tool) must be specified")

    def get_total(self) -> float:
        """
        Calculate the total price for this item.

        Returns:
            float: Total price (quantity * price)
        """
        return self.quantity * self.price

    def get_item_name(self) -> str:
        """
        Get the name of the purchased item.

        Returns:
            str: Name of the item or a descriptive string
        """
        if self.material_id and self.material:
            return f"Material: {self.material.name}"
        elif self.leather_id and self.leather:
            return f"Leather: {self.leather.name}"
        elif self.hardware_id and self.hardware:
            return f"Hardware: {self.hardware.name}"
        elif self.tool_id and self.tool:
            return f"Tool: {self.tool.name}"
        else:
            return self.description or "Unknown item"

    def __repr__(self) -> str:
        """String representation of the purchase item."""
        return f"<PurchaseItem(id={self.id}, purchase_id={self.purchase_id}, quantity={self.quantity}, price={self.price})>"


# Final registration
register_lazy_import('database.models.purchase_item.PurchaseItem', 'database.models.purchase_item', 'PurchaseItem')