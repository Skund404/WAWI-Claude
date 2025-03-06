# database/models/picking_list.py
"""
Picking List Models

This module defines the PickingList and PickingListItem models which implement
the PickingList and PickingListItem entities from the ER diagram.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import PickingListStatus
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, validate_positive_number, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports
Sales = lazy_import('database.models.sales', 'Sales')
Component = lazy_import('database.models.components', 'Component')
Material = lazy_import('database.models.material', 'Material')
Leather = lazy_import('database.models.leather', 'Leather')
Hardware = lazy_import('database.models.hardware', 'Hardware')
ProjectComponent = lazy_import('database.models.components', 'ProjectComponent')

# Register lazy imports
register_lazy_import('database.models.sales.Sales', 'database.models.sales', 'Sales')
register_lazy_import('database.models.components.Component', 'database.models.components', 'Component')
register_lazy_import('database.models.material.Material', 'database.models.material', 'Material')
register_lazy_import('database.models.leather.Leather', 'database.models.leather', 'Leather')
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('database.models.components.ProjectComponent', 'database.models.components', 'ProjectComponent')


class PickingList(Base):
    """
    PickingList model representing material and hardware picking lists for sales.
    This corresponds to the PickingList entity in the ER diagram.
    """
    __tablename__ = 'picking_lists'

    id = Column(Integer, primary_key=True)
    sales_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    status = Column(Enum(PickingListStatus), nullable=False, default=PickingListStatus.DRAFT)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    sales = relationship("Sales", back_populates="picking_list")
    items = relationship("PickingListItem", back_populates="picking_list", cascade="all, delete-orphan")

    def __init__(self, sales_id: int, status: PickingListStatus = PickingListStatus.DRAFT, **kwargs):
        """
        Initialize a PickingList instance.

        Args:
            sales_id: ID of the sales record
            status: Picking list status
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'sales_id': sales_id,
                'status': status,
                'created_at': datetime.utcnow()
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PickingList initialization failed: {e}")
            raise ModelValidationError(f"Failed to create picking list: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate picking list creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'sales_id', 'Sales ID is required')

    def mark_as_completed(self) -> None:
        """
        Mark the picking list as completed.
        """
        try:
            self.status = PickingListStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            logger.info(f"PickingList {self.id} marked as completed")
        except Exception as e:
            logger.error(f"Error marking picking list as completed: {e}")
            raise ModelValidationError(f"Failed to update picking list status: {str(e)}") from e

    def __repr__(self) -> str:
        """String representation of the picking list."""
        return f"<PickingList(id={self.id}, sales_id={self.sales_id}, status={self.status})>"


class PickingListItem(Base):
    """
    PickingListItem model representing an item in a picking list.
    This corresponds to the PickingListItem entity in the ER diagram.
    """
    __tablename__ = 'picking_list_items'

    id = Column(Integer, primary_key=True)
    picking_list_id = Column(Integer, ForeignKey('picking_lists.id'), nullable=False)

    # References to different item types - only one should be set
    component_id = Column(Integer, ForeignKey('components.id'), nullable=True)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leathers.id'), nullable=True)
    hardware_id = Column(Integer, ForeignKey('hardwares.id'), nullable=True)

    # Quantities
    quantity_ordered = Column(Integer, nullable=False, default=0)
    quantity_picked = Column(Integer, nullable=False, default=0)

    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    component = relationship("Component", foreign_keys=[component_id])
    material = relationship("Material", foreign_keys=[material_id])
    leather = relationship("Leather", foreign_keys=[leather_id])
    hardware = relationship("Hardware", foreign_keys=[hardware_id])
    project_component = relationship("ProjectComponent", back_populates="picking_list_item")

    def __init__(self, picking_list_id: int, quantity_ordered: int,
                 component_id: Optional[int] = None, material_id: Optional[int] = None,
                 leather_id: Optional[int] = None, hardware_id: Optional[int] = None, **kwargs):
        """
        Initialize a PickingListItem instance.

        Args:
            picking_list_id: ID of the picking list
            quantity_ordered: Quantity to pick
            component_id: Optional ID of the component
            material_id: Optional ID of the material
            leather_id: Optional ID of the leather
            hardware_id: Optional ID of the hardware
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'picking_list_id': picking_list_id,
                'quantity_ordered': quantity_ordered,
                'quantity_picked': 0,  # Initially nothing is picked
                'component_id': component_id,
                'material_id': material_id,
                'leather_id': leather_id,
                'hardware_id': hardware_id
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"PickingListItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create picking list item: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate picking list item creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'picking_list_id', 'Picking list ID is required')
        validate_not_empty(data, 'quantity_ordered', 'Quantity ordered is required')

        # Validate quantity
        validate_positive_number(data, 'quantity_ordered', allow_zero=False,
                                 message="Quantity ordered must be positive")

        # Validate that at least one item type is specified
        if not any([data.get('component_id'), data.get('material_id'),
                    data.get('leather_id'), data.get('hardware_id')]):
            raise ValidationError(
                "At least one item type (component, material, leather, or hardware) must be specified")

    def update_picked_quantity(self, quantity: int) -> None:
        """
        Update the quantity picked.

        Args:
            quantity: New picked quantity

        Raises:
            ModelValidationError: If quantity is invalid
        """
        try:
            # Validate
            if quantity < 0:
                raise ValidationError("Picked quantity cannot be negative")

            if quantity > self.quantity_ordered:
                raise ValidationError("Picked quantity cannot exceed ordered quantity")

            # Update
            self.quantity_picked = quantity

            logger.info(f"PickingListItem {self.id} picked quantity updated to {self.quantity_picked}")

        except Exception as e:
            logger.error(f"Error updating picked quantity: {e}")
            raise ModelValidationError(f"Failed to update picked quantity: {str(e)}") from e

    def is_fully_picked(self) -> bool:
        """
        Check if the item is fully picked.

        Returns:
            bool: True if quantity_picked equals quantity_ordered
        """
        return self.quantity_picked >= self.quantity_ordered

    def __repr__(self) -> str:
        """String representation of the picking list item."""
        return f"<PickingListItem(id={self.id}, picking_list_id={self.picking_list_id}, ordered={self.quantity_ordered}, picked={self.quantity_picked})>"


# Initialize relationships function
def initialize_relationships():
    """
    Initialize relationships after all models are loaded.
    """
    try:
        logger.info("Initializing PickingList model relationships")

        # Import necessary models directly to avoid circular import issues
        from database.models.sales import Sales
        from database.models.components import Component, ProjectComponent

        logger.info("PickingList relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing picking list relationships: {e}")


# Final registration
register_lazy_import('database.models.picking_list.PickingList', 'database.models.picking_list', 'PickingList')
register_lazy_import('database.models.picking_list.PickingListItem', 'database.models.picking_list', 'PickingListItem')