# database/models/tool.py
"""
This module defines the Tool model for the leatherworking application.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import ToolCategory


class Tool(AbstractBase, ValidationMixin):
    """
    Tool model representing leatherworking tools.

    Attributes:
        name (str): Tool name
        description (Optional[str]): Detailed description
        tool_category (ToolCategory): Category/type of tool
        supplier_id (Optional[int]): Foreign key to the supplier
        maintenance_notes (Optional[str]): Notes about maintenance
    """
    __tablename__ = 'tools'
    __table_args__ = {"extend_existing": True}

    # Basic attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tool_category: Mapped[ToolCategory] = mapped_column(Enum(ToolCategory), nullable=False)
    maintenance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign keys
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    supplier = relationship(
        "Supplier",
        back_populates="tools",
        lazy="selectin"
    )

    # Inventory relationship
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Tool.id==Inventory.item_id, Inventory.item_type=='tool')",
        foreign_keys="[Inventory.item_id]",
        back_populates="tool",
        uselist=False,
        lazy="selectin"
    )

    # ToolListItem relationship
    tool_list_items = relationship(
        "ToolListItem",
        back_populates="tool",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Purchase items relationship
    purchase_items = relationship(
        "PurchaseItem",
        primaryjoin="and_(Tool.id==PurchaseItem.item_id, PurchaseItem.item_type=='tool')",
        foreign_keys="[PurchaseItem.item_id]",
        back_populates="tool",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Tool instance with validation.

        Args:
            **kwargs: Keyword arguments for Tool initialization
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate tool data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Name validation
        if not self.name or not isinstance(self.name, str):
            raise ModelValidationError("Tool name must be a non-empty string")

        if len(self.name) > 255:
            raise ModelValidationError("Tool name cannot exceed 255 characters")

        # Description validation
        if self.description is not None:
            if not isinstance(self.description, str):
                raise ModelValidationError("Tool description must be a string")

            if len(self.description) > 500:
                raise ModelValidationError("Tool description cannot exceed 500 characters")

        # Tool category validation
        if not self.tool_category:
            raise ModelValidationError("Tool category must be specified")

        return self

    def get_stock_level(self) -> float:
        """
        Get the current stock level for this tool.

        Returns:
            float: Current quantity in stock, or 0 if no inventory record exists
        """
        if self.inventory:
            return self.inventory.quantity
        return 0.0

    def is_in_stock(self) -> bool:
        """
        Check if this tool is currently in stock.

        Returns:
            bool: True if tool is in stock (quantity > 0), False otherwise
        """
        return self.get_stock_level() > 0

    def update_inventory(self, change: float, transaction_type: str,
                         reference_type: Optional[str] = None,
                         reference_id: Optional[int] = None,
                         notes: Optional[str] = None) -> None:
        """
        Update the inventory for this tool.

        Creates an inventory record if one doesn't exist yet.

        Args:
            change: Quantity change (positive for additions, negative for reductions)
            transaction_type: Type of transaction
            reference_type: Optional reference type (e.g., 'purchase', 'maintenance')
            reference_id: Optional reference ID
            notes: Optional notes about the transaction
        """
        from database.models.enums import InventoryStatus, TransactionType
        from database.models.inventory import Inventory

        # Create inventory record if it doesn't exist
        if not self.inventory:
            self.inventory = Inventory(
                item_type='tool',
                item_id=self.id,
                quantity=0,
                status=InventoryStatus.OUT_OF_STOCK,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

        # Update the inventory
        self.inventory.update_quantity(
            change=change,
            transaction_type=TransactionType[transaction_type],
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes
        )