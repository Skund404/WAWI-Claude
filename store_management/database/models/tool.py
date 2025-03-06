# database/models/tool.py
"""
Tool Model

This module defines the Tool model which implements
the Tool entity from the ER diagram.
"""

import logging
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Enum, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import ToolCategory
from utils.circular_import_resolver import lazy_import, register_lazy_import
from utils.enhanced_model_validator import validate_not_empty, ValidationError

# Setup logger
logger = logging.getLogger(__name__)

# Lazy imports
Supplier = lazy_import('database.models.supplier', 'Supplier')

# Register lazy imports
register_lazy_import('database.models.supplier.Supplier', 'database.models.supplier', 'Supplier')


class Tool(Base):
    """
    Tool model representing tools used in leatherworking.
    This corresponds to the Tool entity in the ER diagram.
    """
    __tablename__ = 'tools'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(ToolCategory), nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)

    # Additional attributes
    is_active = Column(Boolean, default=True, nullable=False)
    model_number = Column(String(100), nullable=True)
    maintenance_notes = Column(Text, nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="tools")
    inventories = relationship("ToolInventory", back_populates="tool")
    tool_list_items = relationship("ToolListItem", back_populates="tool")
    component_tools = relationship("ComponentTool", back_populates="tool")

    def __init__(self, name: str, type: ToolCategory, supplier_id: Optional[int] = None,
                 description: Optional[str] = None, model_number: Optional[str] = None,
                 maintenance_notes: Optional[str] = None, **kwargs):
        """
        Initialize a Tool instance.

        Args:
            name: Name of the tool
            type: Tool category
            supplier_id: Optional supplier ID
            description: Optional description
            model_number: Optional model number
            maintenance_notes: Optional maintenance notes
            **kwargs: Additional attributes
        """
        try:
            # Prepare data
            kwargs.update({
                'name': name,
                'type': type,
                'supplier_id': supplier_id,
                'description': description,
                'model_number': model_number,
                'maintenance_notes': maintenance_notes
            })

            # Validate
            self._validate_creation(kwargs)

            # Initialize
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Tool initialization failed: {e}")
            raise ModelValidationError(f"Failed to create tool: {str(e)}") from e

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate tool creation data.

        Args:
            data: Data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Tool name is required')
        validate_not_empty(data, 'type', 'Tool type is required')

    def mark_inactive(self) -> None:
        """
        Mark the tool as inactive.
        """
        self.is_active = False
        logger.info(f"Tool {self.id} marked as inactive")

    def __repr__(self) -> str:
        """String representation of the tool."""
        return f"<Tool(id={self.id}, name='{self.name}', type={self.type})>"


# Final registration
register_lazy_import('database.models.tool.Tool', 'database.models.tool', 'Tool')