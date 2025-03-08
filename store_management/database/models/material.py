from database.models.base import metadata
from sqlalchemy.orm import declarative_base
# database/models/material.py
"""
Comprehensive Material Model for Leatherworking Management System

Implements the Material entity with robust validation,
relationship management, and inventory tracking.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError, metadata
from database.models.enums import (
    MaterialType,
    InventoryStatus,
    TransactionType,
    MeasurementUnit,
    QualityGrade
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    TrackingMixin,
    apply_mixins
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
register_lazy_import('MaterialInventory', 'database.models.material_inventory', 'MaterialInventory')
register_lazy_import('ComponentMaterial', 'database.models.components', 'ComponentMaterial')
register_lazy_import('ProjectComponent', 'database.models.components', 'ProjectComponent')

from sqlalchemy.orm import declarative_base
MaterialBase = declarative_base()
MaterialBase.metadata = metadata
MaterialBase.metadata = metadata
MaterialBase.metadata = metadata

class Material(MaterialBase):
    """
    Material model representing various materials used in leatherworking projects.
    """
    __tablename__ = 'materials'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

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
    material_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="materials")
    purchase_items = relationship("PurchaseItem", back_populates="material")
    component_materials = relationship("ComponentMaterial", back_populates="material")
    project_components = relationship("ProjectComponent", back_populates="material")
    inventories = relationship("MaterialInventory", back_populates="material", cascade="all, delete-orphan")
    picking_list_items = relationship("PickingListItem", back_populates="material")

    def __init__(self, **kwargs):
        """
        Initialize a Material instance with comprehensive validation.
        """
        try:
            # Handle metadata renaming consistently
            if 'metadata' in kwargs:
                kwargs['material_metadata'] = kwargs.pop('metadata')

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
        """
        # Initialize inventory status if not set
        if not hasattr(self, 'status') or self.status is None:
            self.status = InventoryStatus.OUT_OF_STOCK

        # Generate SKU if not provided
        if not hasattr(self, 'sku') or not self.sku:
            self._generate_sku()

        # Initialize metadata if not provided
        if not hasattr(self, 'material_metadata') or self.material_metadata is None:
            self.material_metadata = {}

    def _generate_sku(self) -> None:
        """
        Generate a unique SKU for the material.
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        type_prefix = self.material_type.name[:3].upper()
        self.sku = f"MAT-{type_prefix}-{timestamp}"
        logger.debug(f"Generated SKU for material {self.id}: {self.sku}")

    def adjust_quantity(self, quantity_change: float, transaction_type: Union[str, TransactionType],
                        notes: Optional[str] = None) -> None:
        """
        Adjust the inventory quantity for this material.
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

    def update_inventory(self, quantity: float, location: str) -> Any:
        """
        Update or create an inventory record for this material.
        """
        try:
            MaterialInventory = lazy_import('database.models.material_inventory', 'MaterialInventory')

            # Find or create inventory record
            inventory = next(
                (inv for inv in self.inventories if inv.storage_location == location),
                None
            )

            if inventory:
                # Update existing inventory
                inventory.quantity = quantity
                if hasattr(inventory, '_update_status'):
                    inventory._update_status()
                logger.info(f"Updated inventory for material {self.id} at {location}")
            else:
                # Create new inventory at target location
                inventory = MaterialInventory(
                    material_id=self.id,
                    quantity=quantity,
                    storage_location=location
                )
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
        """
        try:
            return sum(inv.quantity for inv in self.inventories) if self.inventories else 0.0
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

    def get_stock_value(self) -> float:
        """
        Calculate the total stock value.
        """
        try:
            total_quantity = self.calculate_total_inventory()
            return total_quantity * self.price_per_unit
        except Exception as e:
            logger.error(f"Failed to calculate stock value: {e}")
            raise ModelValidationError(f"Stock value calculation failed: {str(e)}")

    def needs_reorder(self) -> bool:
        """
        Check if the material needs to be reordered.
        """
        total_quantity = self.calculate_total_inventory()
        return (
            total_quantity <= self.min_quantity and
            self.is_active and
            self.status != InventoryStatus.DISCONTINUED
        )

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate the material instance.
        """
        errors = {}

        try:
            # Validate required fields
            if not self.name:
                errors['name'] = ["Name is required"]

            if not self.material_type:
                errors['material_type'] = ["Material type is required"]

            # Validate numeric fields
            if self.price_per_unit < 0:
                errors['price_per_unit'] = ["Price per unit cannot be negative"]

            if self.min_quantity < 0:
                errors['min_quantity'] = ["Minimum quantity cannot be negative"]

        except Exception as e:
            errors['general'] = [f"Validation error: {str(e)}"]

        return errors

    def is_valid(self) -> bool:
        """
        Check if the material instance is valid.
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
        """
        return (
            f"<Material(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.material_type.name}, "
            f"status={self.status.name})>"
        )


# Register for lazy import resolution
register_lazy_import('Material', 'database.models.material', 'Material')