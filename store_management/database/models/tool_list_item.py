# database/models/tool_list_item.py
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Any, Dict, List, Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import TransactionType


class ToolListItem(AbstractBase, ValidationMixin):
    """
    ToolListItem represents an individual tool in a tool list.

    Attributes:
        tool_list_id: Foreign key to the tool list
        tool_id: Foreign key to the tool
        quantity: Quantity needed
        is_checked_out: Whether the tool is currently checked out
    """
    __tablename__ = 'tool_list_items'

    tool_list_id: Mapped[int] = mapped_column(Integer, ForeignKey('tool_lists.id'), nullable=False)
    tool_id: Mapped[int] = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_checked_out: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0"
    )

    # Relationships
    tool_list: Mapped["ToolList"] = relationship(back_populates="items")
    tool: Mapped["Tool"] = relationship(back_populates="tool_list_items")

    def __init__(self, **kwargs):
        """Initialize a ToolListItem instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate tool list item data."""
        if self.quantity <= 0:
            raise ModelValidationError("Quantity must be positive")

    def check_out(self, user: Optional[str] = None) -> None:
        """
        Check out tools from inventory for use in a project.

        Args:
            user: User checking out the tools

        Raises:
            ValueError: If tools are already checked out or not available in inventory
        """
        if self.is_checked_out:
            raise ValueError("Tools are already checked out")

        # Verify tool is available in inventory
        if hasattr(self, 'tool') and self.tool and hasattr(self.tool, 'inventory') and self.tool.inventory:
            if self.tool.inventory.quantity < self.quantity:
                raise ValueError(f"Only {self.tool.inventory.quantity} units available, but {self.quantity} requested")

            # Get reference information
            project_id = self.tool_list.project_id if hasattr(self.tool_list, 'project_id') else None

            # Prepare notes for the inventory transaction
            notes = f"Checked out for tool list #{self.tool_list_id}"
            if project_id:
                notes += f" (Project #{project_id})"

            try:
                # Update inventory
                self.tool.inventory.update_quantity(
                    change=-self.quantity,
                    transaction_type=TransactionType.USAGE,
                    reference_type='tool_list',
                    reference_id=self.tool_list_id,
                    notes=notes
                )

                # Mark as checked out
                self.is_checked_out = True
                self.updated_at = datetime.now()
                if user:
                    self.updated_by = user

            except ModelValidationError as e:
                raise ValueError(f"Cannot check out tool: {str(e)}")
        else:
            raise ValueError("Tool has no inventory record")

    def return_to_inventory(self, user: Optional[str] = None) -> None:
        """
        Return checked out tools to inventory.

        Args:
            user: User returning the tools

        Raises:
            ValueError: If tools are not checked out
        """
        if not self.is_checked_out:
            raise ValueError("Tools are not checked out")

        if hasattr(self, 'tool') and self.tool and hasattr(self.tool, 'inventory') and self.tool.inventory:
            # Get reference information
            project_id = self.tool_list.project_id if hasattr(self.tool_list, 'project_id') else None

            # Prepare notes for the inventory transaction
            notes = f"Returned from tool list #{self.tool_list_id}"
            if project_id:
                notes += f" (Project #{project_id})"

            # Update inventory
            self.tool.inventory.update_quantity(
                change=self.quantity,
                transaction_type=TransactionType.RETURN,
                reference_type='tool_list',
                reference_id=self.tool_list_id,
                notes=notes
            )

            # Mark as returned
            self.is_checked_out = False
            self.updated_at = datetime.now()
            if user:
                self.updated_by = user
        else:
            # Even if there's no inventory record, mark as returned anyway
            self.is_checked_out = False
            self.updated_at = datetime.now()
            if user:
                self.updated_by = user