# database/models/tool.py
"""
Comprehensive Tool Model for Leatherworking Management System

This module defines the Tool model with extensive validation,
relationship management, and circular import resolution.

Implements the Tool entity from the ER diagram with all its
relationships and attributes.
"""

import logging
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import ToolCategory
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    TrackingMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Supplier', 'database.models.supplier', 'Supplier')
register_lazy_import('ToolInventory', 'database.models.tool_inventory', 'ToolInventory')
register_lazy_import('ComponentTool', 'database.models.components', 'ComponentTool')
register_lazy_import('ToolListItem', 'database.models.tool_list', 'ToolListItem')
register_lazy_import('PurchaseItem', 'database.models.purchase_item', 'PurchaseItem')


class Tool(Base, TimestampMixin, ValidationMixin, TrackingMixin):
    """
    Tool model representing tools used in leatherworking projects.

    This implements the Tool entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'tools'

    # Basic attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[ToolCategory] = mapped_column(Enum(ToolCategory), nullable=False)

    # Additional attributes
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    model_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    maintenance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign keys
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="tools")
    inventories = relationship("ToolInventory", back_populates="tool", cascade="all, delete-orphan")
    tool_list_items = relationship("ToolListItem", back_populates="tool")
    component_tools = relationship("ComponentTool", back_populates="tool")
    purchase_items = relationship("PurchaseItem", back_populates="tool")

    def __init__(self, **kwargs):
        """
        Initialize a Tool instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for tool attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_tool_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Tool initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Tool: {str(e)}") from e

    @classmethod
    def _validate_tool_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of tool creation data.

        Args:
            data: Tool creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'name', 'Tool name is required')
        validate_not_empty(data, 'type', 'Tool type is required')

        # Validate tool type
        if 'type' in data:
            ModelValidator.validate_enum(
                data['type'],
                ToolCategory,
                'type'
            )

    def mark_as_inactive(self) -> None:
        """
        Mark the tool as inactive.
        """
        self.is_active = False
        logger.info(f"Tool {self.id} marked as inactive")

    def mark_as_active(self) -> None:
        """
        Mark the tool as active.
        """
        self.is_active = True
        logger.info(f"Tool {self.id} marked as active")

    def update_maintenance_notes(self, notes: str) -> None:
        """
        Update the maintenance notes for the tool.

        Args:
            notes: Maintenance notes to add
        """
        if self.maintenance_notes:
            self.maintenance_notes += f"\n\n{notes}"
        else:
            self.maintenance_notes = notes

        logger.info(f"Maintenance notes updated for tool {self.id}")

    def total_inventory_quantity(self) -> int:
        """
        Calculate the total quantity of this tool in inventory.

        Returns:
            Total quantity across all inventories
        """
        try:
            total = 0
            if hasattr(self, 'inventories') and self.inventories:
                total = sum(inv.quantity for inv in self.inventories)
            return total
        except Exception as e:
            logger.error(f"Failed to calculate total inventory: {e}")
            return 0

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

        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Handle enum values
                if isinstance(value, ToolCategory):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        # Add computed fields
        result['total_inventory'] = self.total_inventory_quantity()

        return result

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate the tool instance.

        Returns:
            Dictionary mapping field names to validation errors,
            or an empty dictionary if validation succeeds
        """
        errors = {}

        try:
            # Validate required fields
            if not self.name:
                errors.setdefault('name', []).append("Name is required")

            if not self.type:
                errors.setdefault('type', []).append("Tool type is required")

        except Exception as e:
            errors.setdefault('general', []).append(f"Validation error: {str(e)}")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the tool instance is valid.

        Returns:
            True if the instance is valid, False otherwise
        """
        return len(self.validate()) == 0

    def __repr__(self) -> str:
        """
        String representation of the Tool.

        Returns:
            Detailed tool representation
        """
        return (
            f"<Tool(id={self.id}, "
            f"name='{self.name}', "
            f"type={self.type.name if self.type else 'None'}, "
            f"active={self.is_active})>"
        )


# Register for lazy import resolution
register_lazy_import('Tool', 'database.models.tool', 'Tool')