# database/models/material.py
"""
Comprehensive Material Model for Leatherworking Management System

This module defines the Material model with extensive validation,
relationship management, and circular import resolution.

Implements the Material entity from the ER diagram with all its
relationships and attributes.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    MaterialType,
    InventoryStatus,
    TransactionType,
    MeasurementUnit,
    QualityGrade
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    TrackingMixin
)
from database.models.interfaces import IInventoryItem
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    CircularImportResolver
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
register_lazy_import('MaterialInventory', 'database.models.material_inventory', 'MaterialInventory')
register_lazy_import('ComponentMaterial', 'database.models.components', 'ComponentMaterial')
register_lazy_import('ProjectComponent', 'database.models.components', 'ProjectComponent')


class Material(Base, TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin, IInventoryItem):
    """
    Material model representing various materials used in leatherworking projects.

    This implements the Material entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'materials'

    # Basic attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Material-specific attributes
    material_type: Mapped[MaterialType] = mapped_column(Enum(MaterialType), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    thickness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Inventory attributes
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)
    price_per_unit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min_quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Measurement attributes
    unit: Mapped[MeasurementUnit] = mapped_column(
        Enum(MeasurementUnit),
        default=MeasurementUnit.PIECE,
        nullable=False
    )

    # Quality tracking
    quality_grade: Mapped[Optional[QualityGrade]] = mapped_column(Enum(QualityGrade), nullable=True)

    # Status tracking
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus),
        default=InventoryStatus.IN_STOCK,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Supplier relationship
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=True)

    # Metadata attributes
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships - following the ER diagram
    supplier = relationship("Supplier", back_populates="materials")
    purchase_items = relationship("PurchaseItem", back_populates="material")
    component_materials = relationship("ComponentMaterial", back_populates="material")
    project_components = relationship("ProjectComponent", back_populates="material")
    inventories = relationship("MaterialInventory", back_populates="material", cascade="all, delete-orphan")
    picking_list_items = relationship("PickingListItem", back_populates="material")

    def __init__(self, **kwargs):
        """
        Initialize a Material instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for material attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_material_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Material initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Material: {str(e)}") from e

    @classmethod
    def _validate_material_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of material creation data.

        Args:
            data: Material creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Material name is required')
        validate_not_empty(data, 'material_type', 'Material type is required')

        # Validate material type
        if 'material_type' in data:
            ModelValidator.validate_enum(
                data['material_type'],
                MaterialType,
                'material_type'
            )

        # Validate quality grade if provided
        if 'quality_grade' in data and data['quality_grade'] is not None:
            ModelValidator.validate_enum(
                data['quality_grade'],
                QualityGrade,
                'quality_grade'
            )

        # Validate unit if provided
        if 'unit' in data:
            ModelValidator.validate_enum(
                data['unit'],
                MeasurementUnit,
                'unit'
            )

        # Validate numeric fields
        for field in ['thickness', 'price_per_unit', 'min_quantity']:
            if field in data and data[field] is not None:
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
            self.status = InventoryStatus.OUT_OF_STOCK

        # Generate SKU if not provided
        if not hasattr(self, 'sku') or not self.sku:
            self._generate_sku()

        # Initialize metadata if not provided
        if not hasattr(self, 'metadata') or self.metadata is None:
            self.metadata = {}

    def _generate_sku(self) -> None:
        """
        Generate a unique SKU for the material.
        """
        # Simple implementation - in practice would have more complexity
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        type_prefix = self.material_type.name[:3].upper()
        self.sku = f"MAT-{type_prefix}-{timestamp}"
        logger.debug(f"Generated SKU for material {self.id}: {self.sku}")

    def update_inventory(self, quantity: float, location: str) -> "MaterialInventory":
        """
        Update or create an inventory record for this material.

        Args:
            quantity: The quantity to set
            location: The storage location

        Returns:
            The updated or created inventory record
        """
        try:
            # Import the MaterialInventory model
            MaterialInventory = lazy_import('database.models.material_inventory', 'MaterialInventory')

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
                logger.info(f"Updated inventory for material {self.id} at {location}")
            else:
                # Create new inventory
                inventory = MaterialInventory(
                    material_id=self.id,
                    quantity=quantity,
                    storage_location=location
                )
                if hasattr(self, 'inventories'):
                    self.inventories.append(inventory)
                logger.info(f"Created new inventory for material {self.id} at {location}")

            # Update the main material status based on total inventory
            self._update_status_from_inventory()

            return inventory

        except Exception as e:
            logger.error(f"Failed to update inventory: {e}")
            raise ModelValidationError(f"Inventory update failed: {str(e)}")

    def calculate_total_inventory(self) -> float:
        """
        Calculate the total inventory quantity across all locations.

        Returns:
            Total quantity in inventory
        """
        try:
            total = 0.0
            if hasattr(self, 'inventories') and self.inventories:
                total = sum(inv.quantity for inv in self.inventories)
            return total
        except Exception as e:
            logger.error(f"Failed to calculate total inventory: {e}")
            raise ModelValidationError(f"Inventory calculation failed: {str(e)}")

    def _update_status_from_inventory(self) -> None:
        """
        Update status based on total inventory quantities.
        """
        try:
            total = self.calculate_total_inventory()

            if total <= 0:
                self.status = InventoryStatus.OUT_OF_STOCK
            elif total < self.min_quantity:
                self.status = InventoryStatus.LOW_STOCK
            else:
                self.status = InventoryStatus.IN_STOCK

            logger.info(f"Updated status for material {self.id} to {self.status}")

        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            raise ModelValidationError(f"Status update failed: {str(e)}")

    def adjust_quantity(self, quantity_change: float, transaction_type: Union[str, TransactionType],
                        notes: Optional[str] = None) -> None:
        """
        Adjust the quantity of the inventory item.

        Implementation of IInventoryItem interface method.

        Args:
            quantity_change: Amount to adjust (positive for addition, negative for reduction)
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Raises:
            ValueError: If the resulting quantity would be negative
        """
        try:
            # Process transaction type
            if isinstance(transaction_type, str):
                try:
                    transaction_type = TransactionType[transaction_type.upper()]
                except KeyError:
                    raise ValidationError(f"Invalid transaction type: {transaction_type}")

            # Create or update inventory at default location
            default_location = "Main Storage"

            # Find or create inventory
            inventory = None
            if hasattr(self, 'inventories') and self.inventories:
                for inv in self.inventories:
                    if inv.storage_location == default_location:
                        inventory = inv
                        break

            if inventory:
                # Update existing inventory
                inventory.update_quantity(quantity_change, notes)
            else:
                # Create new inventory with the quantity change (if positive)
                if quantity_change > 0:
                    self.update_inventory(quantity_change, default_location)
                else:
                    raise ValidationError("Cannot reduce quantity when no inventory exists")

            # Update material status
            self._update_status_from_inventory()

        except Exception as e:
            logger.error(f"Failed to adjust quantity: {e}")
            raise ModelValidationError(f"Quantity adjustment failed: {str(e)}")

    def get_stock_value(self) -> float:
        """
        Calculate the total stock value.

        Implementation of IInventoryItem interface method.

        Returns:
            Total value of the item in stock
        """
        try:
            total_quantity = self.calculate_total_inventory()
            stock_value = total_quantity * self.price_per_unit
            return stock_value
        except Exception as e:
            logger.error(f"Failed to calculate stock value: {e}")
            raise ModelValidationError(f"Stock value calculation failed: {str(e)}")

    def update_status(self, new_status: Union[str, InventoryStatus]) -> None:
        """
        Manually update the inventory status.

        Implementation of IInventoryItem interface method.

        Args:
            new_status: New status for the inventory item

        Raises:
            ValueError: If the status is invalid
        """
        try:
            # Process status value
            if isinstance(new_status, str):
                try:
                    new_status = InventoryStatus[new_status.upper()]
                except KeyError:
                    raise ValidationError(f"Invalid inventory status: {new_status}")

            # Validate status type
            if not isinstance(new_status, InventoryStatus):
                raise ValidationError("Status must be a valid InventoryStatus enum value")

            # Update status
            self.status = new_status
            logger.info(f"Manually updated status for material {self.id} to {new_status.name}")

        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            raise ModelValidationError(f"Status update failed: {str(e)}")

    def needs_reorder(self) -> bool:
        """
        Check if the material needs to be reordered.

        Implementation of IInventoryItem interface method.

        Returns:
            True if quantity is at or below reorder point
        """
        total_quantity = self.calculate_total_inventory()
        return total_quantity <= self.min_quantity

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the model
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude_fields
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Material':
        """
        Create a new Material instance from dictionary data.

        Args:
            data: Dictionary containing model attributes

        Returns:
            A new Material instance
        """
        return cls(**data)

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate the material instance.

        Returns:
            Dictionary mapping field names to validation errors,
            or an empty dictionary if validation succeeds
        """
        errors = {}

        try:
            # Validate required fields
            if not self.name:
                errors.setdefault('name', []).append("Name is required")

            if not self.material_type:
                errors.setdefault('material_type', []).append("Material type is required")

            # Validate numeric fields
            if hasattr(self, 'price_per_unit') and self.price_per_unit < 0:
                errors.setdefault('price_per_unit', []).append("Price per unit cannot be negative")

            if hasattr(self, 'min_quantity') and self.min_quantity < 0:
                errors.setdefault('min_quantity', []).append("Minimum quantity cannot be negative")

        except Exception as e:
            errors.setdefault('general', []).append(f"Validation error: {str(e)}")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the material instance is valid.

        Returns:
            True if the instance is valid, False otherwise
        """
        return len(self.validate()) == 0

    def mark_as_inactive(self) -> None:
        """
        Mark the material as inactive.
        """
        self.is_active = False
        self.status = InventoryStatus.DISCONTINUED
        logger.info(f"Material {self.id} marked as inactive")

    def restore(self) -> None:
        """
        Restore an inactive material.
        """
        self.is_active = True
        # Restore status based on inventory
        self._update_status_from_inventory()
        logger.info(f"Material {self.id} restored")

    def __repr__(self) -> str:
        """
        String representation of the Material.

        Returns:
            Detailed material representation
        """
        return (
            f"<Material(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.material_type.name if self.material_type else 'None'}, "
            f"status={self.status.name if self.status else 'None'})>"
        )


# Register for lazy import resolution
register_lazy_import('Material', 'database.models.material', 'Material')