# database/models/tool_list.py
"""
Comprehensive Tool List Models for Leatherworking Management System

This module defines the ToolList and ToolListItem models with extensive validation,
relationship management, and circular import resolution.

Implements the ToolList and ToolListItem entities from the ER diagram with all their
relationships and attributes.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Column, Enum, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import ToolListStatus
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
    validate_not_empty,
    validate_positive_number
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Project', 'database.models.project', 'Project')
register_lazy_import('Tool', 'database.models.tool', 'Tool')


class ToolList(Base, TimestampMixin, ValidationMixin, TrackingMixin):
    """
    ToolList model representing a list of tools needed for a project.

    This implements the ToolList entity from the ER diagram with comprehensive
    attributes and relationship management.
    """
    __tablename__ = 'tool_lists'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    status: Mapped[ToolListStatus] = mapped_column(
        Enum(ToolListStatus),
        nullable=False,
        default=ToolListStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="tool_list")
    items = relationship("ToolListItem", back_populates="tool_list", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """
        Initialize a ToolList instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for tool list attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_tool_list_data(kwargs)

            # Set created_at if not provided
            if 'created_at' not in kwargs:
                kwargs['created_at'] = datetime.utcnow()

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ToolList initialization failed: {e}")
            raise ModelValidationError(f"Failed to create tool list: {str(e)}") from e

    @classmethod
    def _validate_tool_list_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of tool list creation data.

        Args:
            data: Tool list creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'project_id', 'Project ID is required')

        # Validate status if provided
        if 'status' in data:
            ModelValidator.validate_enum(
                data['status'],
                ToolListStatus,
                'status'
            )

    def add_tool(self, tool_id: int, quantity: int = 1) -> "ToolListItem":
        """
        Add a tool to the tool list.

        Args:
            tool_id: ID of the tool to add
            quantity: Quantity of the tool

        Returns:
            The created tool list item

        Raises:
            ModelValidationError: If adding fails
        """
        try:
            # Check if tool already exists in the list
            existing_item = None
            if hasattr(self, 'items'):
                for item in self.items:
                    if item.tool_id == tool_id:
                        existing_item = item
                        break

            if existing_item:
                # Update existing item
                existing_item.quantity += quantity
                logger.info(f"Updated quantity for tool {tool_id} in list {self.id} to {existing_item.quantity}")
                return existing_item
            else:
                # Create new item
                ToolListItem = lazy_import('database.models.tool_list', 'ToolListItem')
                new_item = ToolListItem(
                    tool_list_id=self.id,
                    tool_id=tool_id,
                    quantity=quantity
                )

                if hasattr(self, 'items'):
                    self.items.append(new_item)

                logger.info(f"Added tool {tool_id} to list {self.id}")
                return new_item

        except Exception as e:
            logger.error(f"Failed to add tool to list: {e}")
            raise ModelValidationError(f"Failed to add tool: {str(e)}") from e

    def remove_tool(self, tool_id: int) -> bool:
        """
        Remove a tool from the tool list.

        Args:
            tool_id: ID of the tool to remove

        Returns:
            True if successfully removed, False if not found

        Raises:
            ModelValidationError: If removal fails
        """
        try:
            # Find the item
            item_to_remove = None
            if hasattr(self, 'items'):
                for item in self.items:
                    if item.tool_id == tool_id:
                        item_to_remove = item
                        break

            if item_to_remove:
                # Remove the item
                self.items.remove(item_to_remove)
                logger.info(f"Removed tool {tool_id} from list {self.id}")
                return True
            else:
                logger.warning(f"Tool {tool_id} not found in list {self.id}")
                return False

        except Exception as e:
            logger.error(f"Failed to remove tool from list: {e}")
            raise ModelValidationError(f"Failed to remove tool: {str(e)}") from e

    def mark_as_completed(self) -> None:
        """
        Mark the tool list as completed.
        """
        try:
            self.status = ToolListStatus.COMPLETED
            logger.info(f"ToolList {self.id} marked as completed")
        except Exception as e:
            logger.error(f"Error marking tool list as completed: {e}")
            raise ModelValidationError(f"Failed to update tool list status: {str(e)}") from e

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

                # Handle special types
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                elif isinstance(value, ToolListStatus):
                    result[column.name] = value.name
                else:
                    result[column.name] = value

        # Add items if desired
        if hasattr(self, 'items') and self.items:
            result['items'] = [item.to_dict() for item in self.items]

        return result

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate the tool list instance.

        Returns:
            Dictionary mapping field names to validation errors,
            or an empty dictionary if validation succeeds
        """
        errors = {}

        try:
            # Validate required fields
            if not self.project_id:
                errors.setdefault('project_id', []).append("Project ID is required")

        except Exception as e:
            errors.setdefault('general', []).append(f"Validation error: {str(e)}")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the tool list instance is valid.

        Returns:
            True if the instance is valid, False otherwise
        """
        return len(self.validate()) == 0

    def __repr__(self) -> str:
        """
        String representation of the ToolList.

        Returns:
            Detailed tool list representation
        """
        item_count = len(self.items) if hasattr(self, 'items') else 0
        return (
            f"<ToolList(id={self.id}, "
            f"project_id={self.project_id}, "
            f"status={self.status.name if self.status else 'None'}, "
            f"items={item_count})>"
        )


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
register_lazy_import('ToolList', 'database.models.tool_list', 'ToolList')
register_lazy_import('ToolListItem', 'database.models.tool_list', 'ToolListItem')