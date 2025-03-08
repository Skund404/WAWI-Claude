from database.models.base import metadata
# database/models/tool_list_item.py
"""
Comprehensive ToolListItem Model for Leatherworking Management System

This module defines the ToolListItem model with extensive validation,
relationship management, and circular import resolution.

Implements the ToolListItem entity from the ER diagram with all its
relationships and attributes.
"""

import logging
from typing import Dict, Any, Optional, List

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError, metadata
from database.models.base import (
    ValidationMixin
)
from utils.circular_import_resolver import (
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('ToolList', 'database.models.tool_list', 'ToolList')
register_lazy_import('Tool', 'database.models.tool', 'Tool')

class ToolListItem(Base, ValidationMixin):
    """
    ToolListItem model representing an item in a tool list.

    This implements the ToolListItem entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'tool_list_items'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_list_id: Mapped[int] = mapped_column(Integer, ForeignKey('tool_lists.id'), nullable=False)
    tool_id: Mapped[int] = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    tool_list = relationship("ToolList", back_populates="items")
    tool = relationship("Tool", back_populates="tool_list_items")

    def __init__(self, **kwargs):
        """
        Initialize a ToolListItem instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for tool list item attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_tool_list_item_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ToolListItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create tool list item: {str(e)}") from e

    @classmethod
    def _validate_tool_list_item_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of tool list item creation data.

        Args:
            data: Tool list item creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'tool_list_id', 'Tool list ID is required')
        validate_not_empty(data, 'tool_id', 'Tool ID is required')

        # Validate quantity
        validate_positive_number(
            data,
            'quantity',
            allow_zero=False,
            message="Quantity must be positive"
        )

    def update_quantity(self, quantity: int) -> None:
        """
        Update the quantity of the tool.

        Args:
            quantity: New quantity value

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate quantity
            validate_positive_number(
                {'quantity': quantity},
                'quantity',
                allow_zero=False,
                message="Quantity must be positive"
            )

            # Update quantity
            self.quantity = quantity
            logger.info(f"Updated quantity for tool list item {self.id} to {quantity}")

        except Exception as e:
            logger.error(f"Failed to update quantity: {e}")
            raise ModelValidationError(f"Failed to update quantity: {str(e)}") from e

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
                result[column.name] = getattr(self, column.name)

        # Add tool info if available
        if hasattr(self, 'tool') and self.tool:
            result['tool_name'] = self.tool.name
            if hasattr(self.tool, 'type'):
                result['tool_type'] = self.tool.type.name if self.tool.type else None

        return result

    def __repr__(self) -> str:
        """
        String representation of the ToolListItem.

        Returns:
            Detailed tool list item representation
        """
        return (
            f"<ToolListItem(id={self.id}, "
            f"tool_list_id={self.tool_list_id}, "
            f"tool_id={self.tool_id}, "
            f"quantity={self.quantity})>"
        )


# Register for lazy import resolution
register_lazy_import('ToolListItem', 'database.models.tool_list_item', 'ToolListItem')