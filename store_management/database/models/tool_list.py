# database/models/tool_list.py
"""
Tool List Model

This module defines the ToolList and ToolListItem models which implement
the ToolList and ToolListItem entities from the ER diagram.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Enum, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import ToolListStatus
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, validate_positive_number, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports
Project = lazy_import('database.models.project', 'Project')
Tool = lazy_import('database.models.tool', 'Tool')

# Register lazy imports
register_lazy_import('database.models.project.Project', 'database.models.project', 'Project')
register_lazy_import('database.models.tool.Tool', 'database.models.tool', 'Tool')


class ToolList(Base):
    """
    ToolList model representing a list of tools needed for a project.
    This corresponds to the ToolList entity in the ER diagram.
    """
    __tablename__ = 'tool_lists'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    status = Column(Enum(ToolListStatus), nullable=False, default=ToolListStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="tool_list")
    items = relationship("ToolListItem", back_populates="tool_list", cascade="all, delete-orphan")

    def __init__(self, project_id: int, status: ToolListStatus = ToolListStatus.ACTIVE, **kwargs):
        """
        Initialize a ToolList instance.

        Args:
            project_id: ID of the project
            status: Status of the tool list
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'project_id': project_id,
                'status': status,
                'created_at': datetime.utcnow()
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ToolList initialization failed: {e}")
            raise ModelValidationError(f"Failed to create tool list: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate tool list creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'project_id', 'Project ID is required')

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

    def __repr__(self) -> str:
        """String representation of the tool list."""
        return f"<ToolList(id={self.id}, project_id={self.project_id}, status={self.status})>"


class ToolListItem(Base):
    """
    ToolListItem model representing an item in a tool list.
    This corresponds to the ToolListItem entity in the ER diagram.
    """
    __tablename__ = 'tool_list_items'

    id = Column(Integer, primary_key=True)
    tool_list_id = Column(Integer, ForeignKey('tool_lists.id'), nullable=False)
    tool_id = Column(Integer, ForeignKey('tools.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    # Relationships
    tool_list = relationship("ToolList", back_populates="items")
    tool = relationship("Tool", back_populates="tool_list_items")

    def __init__(self, tool_list_id: int, tool_id: int, quantity: int = 1, **kwargs):
        """
        Initialize a ToolListItem instance.

        Args:
            tool_list_id: ID of the tool list
            tool_id: ID of the tool
            quantity: Quantity needed
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'tool_list_id': tool_list_id,
                'tool_id': tool_id,
                'quantity': quantity
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"ToolListItem initialization failed: {e}")
            raise ModelValidationError(f"Failed to create tool list item: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate tool list item creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'tool_list_id', 'Tool list ID is required')
        validate_not_empty(data, 'tool_id', 'Tool ID is required')

        # Validate quantity
        validate_positive_number(data, 'quantity', allow_zero=False, message="Quantity must be positive")

    def __repr__(self) -> str:
        """String representation of the tool list item."""
        return f"<ToolListItem(id={self.id}, tool_list_id={self.tool_list_id}, tool_id={self.tool_id}, quantity={self.quantity})>"


# Final registration
register_lazy_import('database.models.tool_list.ToolList', 'database.models.tool_list', 'ToolList')
register_lazy_import('database.models.tool_list.ToolListItem', 'database.models.tool_list', 'ToolListItem')