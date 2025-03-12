# database/models/tool.py
"""
This module defines the Tool model for the leatherworking application.
"""
import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ModelValidationError, ValidationMixin
from database.models.enums import ToolCategory
from database.models.inventory import Inventory


class Tool(AbstractBase, ValidationMixin):
    """
    Tool model representing tools and equipment used in leatherworking.

    Tools can be associated with suppliers, included in tool lists, and
    tracked through maintenance and checkout records.
    """
    __tablename__ = 'tools'
    __table_args__ = {"extend_existing": True}

    # Basic information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_category: Mapped[ToolCategory] = mapped_column(Enum(ToolCategory), nullable=False)

    # Supplier relationship
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("suppliers.id", name="fk_tool_supplier", ondelete="SET NULL"),
        nullable=True
    )

    # Technical specifications
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    specifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Purchase information
    purchase_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    purchase_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="IN_STOCK")

    # Maintenance information
    last_maintenance_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    next_maintenance_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    maintenance_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in days

    # Relationships
    supplier = relationship(
        "Supplier",
        back_populates="tools",
        lazy="selectin"
    )

    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Tool.id==Inventory.item_id, Inventory.item_type=='tool')",
        foreign_keys="[Inventory.item_id]",
        back_populates="tool",
        uselist=False,
        lazy="selectin",
        overlaps="inventory,inventory,material,product"  # Add this parameter
    )

    tool_list_items = relationship(
        "ToolListItem",
        back_populates="tool",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # New relationships for tool management
    maintenance_records = relationship(
        "ToolMaintenance",
        back_populates="tool",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    checkouts = relationship(
        "ToolCheckout",
        back_populates="tool",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Tool instance with validation.

        Args:
            **kwargs: Keyword arguments for Tool initialization
        """
        # Set default status
        if "status" not in kwargs:
            kwargs["status"] = "IN_STOCK"

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

        # Category validation
        if not self.tool_category:
            raise ModelValidationError("Tool category must be specified")

        # Price validation
        if self.purchase_price is not None and self.purchase_price < 0:
            raise ModelValidationError("Purchase price cannot be negative")

        return self

    def is_available(self) -> bool:
        """Check if the tool is available for checkout.

        Returns:
            True if available, False otherwise
        """
        return self.status == "IN_STOCK"

    def is_checked_out(self) -> bool:
        """Check if the tool is currently checked out.

        Returns:
            True if checked out, False otherwise
        """
        return self.status == "CHECKED_OUT"

    def is_in_maintenance(self) -> bool:
        """Check if the tool is currently in maintenance.

        Returns:
            True if in maintenance, False otherwise
        """
        return self.status == "MAINTENANCE"

    def needs_maintenance(self) -> bool:
        """Check if the tool needs maintenance.

        Returns:
            True if maintenance is due, False otherwise
        """
        if not self.next_maintenance_date:
            return False

        return self.next_maintenance_date <= datetime.datetime.now()

    def days_until_maintenance(self) -> Optional[int]:
        """Calculate days until next maintenance is due.

        Returns:
            Number of days until maintenance is due, or None if no maintenance scheduled
        """
        if not self.next_maintenance_date:
            return None

        delta = self.next_maintenance_date - datetime.datetime.now()
        return delta.days