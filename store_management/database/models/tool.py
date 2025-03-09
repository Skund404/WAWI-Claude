# database/models/tool.py
from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import ToolCategory


class Tool(AbstractBase, ValidationMixin):
    """
    Tools used in leatherworking projects.

    Attributes:
        name: Name of the tool
        description: Detailed description of the tool
        tool_type: Category/type of the tool
        supplier_id: Foreign key to supplier
    """
    __tablename__ = 'tool'

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_type: Mapped[ToolCategory] = mapped_column(Enum(ToolCategory), nullable=False)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("supplier.id"), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="tools")
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Inventory.item_id==Tool.id, Inventory.item_type=='tool')",
        back_populates="tool",
        uselist=False
    )
    tool_list_items = relationship("ToolListItem", back_populates="tool")
    purchase_items = relationship(
        "PurchaseItem",
        primaryjoin="and_(PurchaseItem.item_id==Tool.id, PurchaseItem.item_type=='tool')",
        back_populates="tool"
    )

    def __init__(self, **kwargs):
        """Initialize a Tool instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate tool data."""
        if not self.name:
            raise ModelValidationError("Tool name is required")

        if len(self.name) > 100:
            raise ModelValidationError("Tool name cannot exceed 100 characters")