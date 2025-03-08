from database.models.base import metadata
from sqlalchemy.orm import declarative_base
# database/models/leather.py
"""
Comprehensive Leather Model for Leatherworking Management System

This module defines the Leather model with extensive validation,
relationship management, and circular import resolution.

Implements the Leather entity from the ER diagram with all its
relationships and attributes.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError, metadata
from database.models.enums import (
    LeatherType,
    LeatherFinish,
    MaterialQualityGrade,
    InventoryStatus,
    TransactionType,
    MeasurementUnit
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    TrackingMixin,
    apply_mixins  # Import apply_mixins function
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Supplier', 'database.models.supplier', 'Supplier')
register_lazy_import('PurchaseItem', 'database.models.purchase', 'PurchaseItem')
register_lazy_import('PickingListItem', 'database.models.picking_list', 'PickingListItem')
register_lazy_import('LeatherInventory', 'database.models.leather_inventory', 'LeatherInventory')
register_lazy_import('ComponentLeather', 'database.models.components', 'ComponentLeather')
register_lazy_import('ProjectComponent', 'database.models.components', 'ProjectComponent')

from sqlalchemy.orm import declarative_base
LeatherBase = declarative_base()
LeatherBase.metadata = metadata
LeatherBase.metadata = metadata

class Leather(LeatherBase):
    """
    Leather model representing leather materials used in leatherworking projects.

    This implements the Leather entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'leathers'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Basic attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Leather-specific attributes
    leather_type: Mapped[LeatherType] = mapped_column(Enum(LeatherType), nullable=False)
    finish: Mapped[Optional[LeatherFinish]] = mapped_column(Enum(LeatherFinish), nullable=True)
    tannage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Physical properties
    thickness_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    size_sqft: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    area_available_sqft: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Inventory attributes
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)
    cost_per_sqft: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    price_per_sqft: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Quality tracking
    quality_grade: Mapped[Optional[MaterialQualityGrade]] = mapped_column(Enum(MaterialQualityGrade), nullable=True)

    # Status tracking
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus),
        default=InventoryStatus.IN_STOCK,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Supplier relationship
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=True)

    # Measurement unit
    unit: Mapped[MeasurementUnit] = mapped_column(
        Enum(MeasurementUnit),
        default=MeasurementUnit.SQUARE_FOOT,
        nullable=False
    )

    # Relationships - following the ER diagram
    supplier = relationship("Supplier", back_populates="leathers")
    purchase_items = relationship("PurchaseItem", back_populates="leather")
    component_leathers = relationship("ComponentLeather", back_populates="leather")
    project_components = relationship("ProjectComponent", back_populates="leather")
    inventories = relationship("LeatherInventory", back_populates="leather")
    picking_list_items = relationship("PickingListItem", back_populates="leather")

    def __init__(self, **kwargs):
        """
        Initialize a Leather instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for leather attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_leather_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Leather initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Leather: {str(e)}") from e

    @classmethod
    def _validate_leather_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of leather creation data.

        Args:
            data: Leather creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Leather name is required')
        validate_not_empty(data, 'leather_type', 'Leather type is required')

        # Validate leather type
        if 'leather_type' in data:
            ModelValidator.validate_enum(
                data['leather_type'],
                LeatherType,
                'leather_type'
            )

        # Validate leather finish if provided
        if 'finish' in data and data['finish'] is not None:
            ModelValidator.validate_enum(
                data['finish'],
                LeatherFinish,
                'finish'
            )

        # Validate quality grade if provided
        if 'quality_grade' in data and data['quality_grade'] is not None:
            ModelValidator.validate_enum(
                data['quality_grade'],
                MaterialQualityGrade,
                'quality_grade'
            )

        # Validate unit if provided
        if 'unit' in data:
            ModelValidator.validate_enum(
                data['unit'],
                MeasurementUnit,
                'unit'
            )

        # Validate physical properties
        for field in ['thickness_mm', 'size_sqft', 'area_available_sqft']:
            if field in data and data[field] is not None:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} cannot be negative"
                )

        # Validate cost and price fields
        for field in ['cost_per_sqft', 'price_per_sqft', 'min_quantity']:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=True,
                    message=f"{field.replace('_', ' ').title()} cannot be negative"
                )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Initialize inventory status if not set
        if not hasattr(self, 'status') or self.status is None:
            self.status = InventoryStatus.OUT_OF_STOCK if (
                    not hasattr(self, 'area_available_sqft') or
                    self.area_available_sqft is None or
                    self.area_available_sqft <= 0
            ) else InventoryStatus.IN_STOCK

        # Generate SKU if not provided
        if not hasattr(self, 'sku') or not self.sku:
            self._generate_sku()

    def _generate_sku(self) -> None:
        """
        Generate a unique SKU for the leather.
        """
        # Simple implementation - in practice would have more complexity
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        type_prefix = self.leather_type.name[:3].upper()
        self.sku = f"LTH-{type_prefix}-{timestamp}"
        logger.debug(f"Generated SKU for leather {self.id}: {self.sku}")

    def update_inventory(self, quantity: float, location: str) -> "LeatherInventory":
        """
        Update or create an inventory record for this leather.

        Args:
            quantity: The quantity to set (in square feet)
            location: The storage location

        Returns:
            The updated or created inventory record
        """
        try:
            # Import the LeatherInventory model
            LeatherInventory = lazy_import('database.models.leather_inventory', 'LeatherInventory')

            # Find or create inventory record
            inventory = None
            if hasattr(self, 'inventories') and self.inventories:
                # Find inventory by location if it exists
                for inv in self.inventories:
                    if inv.storage_location == location:
                        inventory = inv
                        break

            if inventory:
                # Update existing inventory
                inventory.quantity = quantity
                inventory._update_status()
                logger.info(f"Updated inventory for leather {self.id} at {location}")
            else:
                # Create new inventory at target location
                inventory = LeatherInventory(
                    leather_id=self.id,
                    quantity=quantity,
                    storage_location=location
                )
                if hasattr(self, 'inventories'):
                    self.inventories.append(inventory)
                logger.info(f"Created new inventory for leather {self.id} at {location}")

            # Update the main leather record's available area
            self._update_available_area()

            return inventory

        except Exception as e:
            logger.error(f"Failed to update inventory: {e}")
            raise ModelValidationError(f"Inventory update failed: {str(e)}")

    def _update_available_area(self) -> None:
        """
        Update the available area based on all inventory records.
        """
        try:
            total = 0.0
            if hasattr(self, 'inventories') and self.inventories:
                total = sum(inv.quantity for inv in self.inventories)

            self.area_available_sqft = total

            # Update status based on available area
            if total <= 0:
                self.status = InventoryStatus.OUT_OF_STOCK
            elif total < self.min_quantity:
                self.status = InventoryStatus.LOW_STOCK
            else:
                self.status = InventoryStatus.IN_STOCK

            logger.debug(f"Updated available area for leather {self.id} to {total} sqft")

        except Exception as e:
            logger.error(f"Failed to update available area: {e}")
            raise ModelValidationError(f"Available area update failed: {str(e)}")

    def calculate_total_value(self) -> float:
        """
        Calculate the total value of the leather based on available area.

        Returns:
            Total value in currency units
        """
        try:
            total_value = (self.area_available_sqft or 0.0) * self.price_per_sqft
            return total_value
        except Exception as e:
            logger.error(f"Failed to calculate total value: {e}")
            raise ModelValidationError(f"Value calculation failed: {str(e)}")

    def mark_as_inactive(self) -> None:
        """
        Mark the leather as inactive.
        """
        self.is_active = False
        self.status = InventoryStatus.DISCONTINUED
        logger.info(f"Leather {self.id} marked as inactive")

    def restore(self) -> None:
        """
        Restore an inactive leather.
        """
        self.is_active = True
        # Restore status based on available area
        self._update_available_area()
        logger.info(f"Leather {self.id} restored")

    def __repr__(self) -> str:
        """
        String representation of the Leather.

        Returns:
            Detailed leather representation
        """
        return (
            f"<Leather(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.leather_type.name if self.leather_type else 'None'}, "
            f"area={self.area_available_sqft or 0.0} sqft, "
            f"status={self.status.name if self.status else 'None'})>"
        )


# Register for lazy import resolution
register_lazy_import('Leather', 'database.models.leather', 'Leather')