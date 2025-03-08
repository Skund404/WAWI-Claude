from database.models.base import metadata
from sqlalchemy.orm import declarative_base
# database/models/hardware.py
"""
Hardware Model for Leatherworking Management System

Represents hardware components used in leatherworking projects.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, ModelValidationError, metadata
from database.models.enums import (
    HardwareType,
    HardwareMaterial,
    HardwareFinish,
    InventoryStatus
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    TrackingMixin,
    apply_mixins
)
from utils.circular_import_resolver import (
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_positive_number,
    validate_not_empty
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports
register_lazy_import('HardwareInventory', 'database.models.hardware_inventory', 'HardwareInventory')
register_lazy_import('ComponentHardware', 'database.models.components', 'ComponentHardware')
register_lazy_import('HardwareTransaction', 'database.models.transaction', 'HardwareTransaction')

from sqlalchemy.orm import declarative_base
HardwareBase = declarative_base()
HardwareBase.metadata = metadata
HardwareBase.metadata = metadata

class Hardware(HardwareBase):
    """
    Hardware model representing hardware items used in leatherworking.

    Tracks comprehensive details about hardware components, including
    type, material, finish, and inventory information.
    """
    __tablename__ = 'hardware'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Core hardware attributes
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hardware classification
    hardware_type: Mapped[HardwareType] = mapped_column(
        Enum(HardwareType),
        nullable=False
    )
    material: Mapped[Optional[HardwareMaterial]] = mapped_column(
        Enum(HardwareMaterial),
        nullable=True
    )
    finish: Mapped[Optional[HardwareFinish]] = mapped_column(
        Enum(HardwareFinish),
        nullable=True
    )

    # Physical attributes
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Inventory attributes
    sku: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    inventory_status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus),
        default=InventoryStatus.IN_STOCK,
        nullable=False
    )

    # Supply chain information
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('suppliers.id'),
        nullable=True
    )
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_discontinued: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    inventory_entries: Mapped[List['HardwareInventory']] = relationship(
        "HardwareInventory",
        back_populates="hardware",
        cascade="all, delete-orphan"
    )

    component_uses: Mapped[List['ComponentHardware']] = relationship(
        "ComponentHardware",
        back_populates="hardware",
        cascade="all, delete-orphan"
    )

    transactions: Mapped[List['HardwareTransaction']] = relationship(
        "HardwareTransaction",
        back_populates="hardware",
        cascade="all, delete-orphan"
    )

    supplier: Mapped['Supplier'] = relationship(
        "Supplier",
        back_populates="hardware_items"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Hardware instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for hardware attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_hardware_data(kwargs)

            # Initialize base models
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Hardware initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Hardware: {str(e)}") from e

    @classmethod
    def _validate_hardware_data(cls, data: Dict[str, Any]) -> None:
        """
        Validate hardware data before initialization.

        Args:
            data: Hardware data to validate

        Raises:
            ValidationError: If data validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Hardware name is required')
        validate_not_empty(data, 'hardware_type', 'Hardware type is required')

        # Validate enum fields
        if 'hardware_type' in data:
            cls._validate_hardware_type(data['hardware_type'])

        if 'material' in data and data['material']:
            cls._validate_hardware_material(data['material'])

        if 'finish' in data and data['finish']:
            cls._validate_hardware_finish(data['finish'])

        if 'inventory_status' in data:
            cls._validate_inventory_status(data['inventory_status'])

        # Validate numeric fields
        if 'weight' in data and data['weight'] is not None:
            validate_positive_number(data, 'weight', allow_zero=False)

    @classmethod
    def _validate_hardware_type(cls, hardware_type: Union[str, HardwareType]) -> HardwareType:
        """
        Validate hardware type.

        Args:
            hardware_type: Hardware type to validate

        Returns:
            Validated HardwareType

        Raises:
            ValidationError: If hardware type is invalid
        """
        if isinstance(hardware_type, str):
            try:
                return HardwareType[hardware_type.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid hardware type. Must be one of {[t.name for t in HardwareType]}",
                    "hardware_type"
                )

        if not isinstance(hardware_type, HardwareType):
            raise ValidationError("Invalid hardware type", "hardware_type")

        return hardware_type

    @classmethod
    def _validate_hardware_material(cls, material: Union[str, HardwareMaterial]) -> HardwareMaterial:
        """
        Validate hardware material.

        Args:
            material: Hardware material to validate

        Returns:
            Validated HardwareMaterial

        Raises:
            ValidationError: If material is invalid
        """
        if isinstance(material, str):
            try:
                return HardwareMaterial[material.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid hardware material. Must be one of {[m.name for m in HardwareMaterial]}",
                    "material"
                )

        if not isinstance(material, HardwareMaterial):
            raise ValidationError("Invalid hardware material", "material")

        return material

    @classmethod
    def _validate_hardware_finish(cls, finish: Union[str, HardwareFinish]) -> HardwareFinish:
        """
        Validate hardware finish.

        Args:
            finish: Hardware finish to validate

        Returns:
            Validated HardwareFinish

        Raises:
            ValidationError: If finish is invalid
        """
        if isinstance(finish, str):
            try:
                return HardwareFinish[finish.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid hardware finish. Must be one of {[f.name for f in HardwareFinish]}",
                    "finish"
                )

        if not isinstance(finish, HardwareFinish):
            raise ValidationError("Invalid hardware finish", "finish")

        return finish

    @classmethod
    def _validate_inventory_status(cls, status: Union[str, InventoryStatus]) -> InventoryStatus:
        """
        Validate inventory status.

        Args:
            status: Inventory status to validate

        Returns:
            Validated InventoryStatus

        Raises:
            ValidationError: If status is invalid
        """
        if isinstance(status, str):
            try:
                return InventoryStatus[status.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid inventory status. Must be one of {[s.name for s in InventoryStatus]}",
                    "inventory_status"
                )

        if not isinstance(status, InventoryStatus):
            raise ValidationError("Invalid inventory status", "inventory_status")

        return status

    def _post_init_processing(self) -> None:
        """
        Perform post-initialization processing.

        Sets defaults and performs any necessary data transformations.
        """
        # Set default inventory status if not provided
        if not hasattr(self, 'inventory_status') or self.inventory_status is None:
            self.inventory_status = InventoryStatus.IN_STOCK

        # Set default active status
        if not hasattr(self, 'is_active'):
            self.is_active = True

        # Set default discontinued status
        if not hasattr(self, 'is_discontinued'):
            self.is_discontinued = False

    def update_inventory_status(self, new_status: Union[str, InventoryStatus]) -> None:
        """
        Update the inventory status.

        Args:
            new_status: New inventory status

        Raises:
            ValidationError: If status is invalid
        """
        validated_status = self._validate_inventory_status(new_status)
        self.inventory_status = validated_status
        logger.info(f"Hardware {self.id} inventory status updated to {validated_status.name}")

    def discontinue(self) -> None:
        """
        Mark the hardware as discontinued.
        """
        self.is_discontinued = True
        self.is_active = False
        logger.info(f"Hardware {self.id} marked as discontinued")

    def reactivate(self) -> None:
        """
        Reactivate a discontinued hardware.
        """
        self.is_discontinued = False
        self.is_active = True
        logger.info(f"Hardware {self.id} reactivated")

    def get_current_stock_level(self) -> int:
        """
        Get current stock level by summing inventory entries.

        Returns:
            int: Current stock level
        """
        if not hasattr(self, 'inventory_entries') or not self.inventory_entries:
            return 0

        return sum(entry.quantity for entry in self.inventory_entries if entry.quantity > 0)

    def __repr__(self) -> str:
        """
        String representation of the hardware.

        Returns:
            str: Hardware representation
        """
        return (
            f"Hardware("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"type={self.hardware_type.name if hasattr(self, 'hardware_type') else 'Unknown'}, "
            f"status={self.inventory_status.name if hasattr(self, 'inventory_status') else 'Unknown'}"
            f")"
        )


# Register for lazy import resolution
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')