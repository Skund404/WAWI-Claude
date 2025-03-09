# database/models/tool_list_item.py
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError


class ToolListItem(AbstractBase, ValidationMixin):
    """
    ToolListItem represents an individual tool in a tool list.

    Attributes:
        tool_list_id: Foreign key to the tool list
        tool_id: Foreign key to the tool
        quantity: Quantity needed
    """
    __tablename__ = 'tool_list_items'

    tool_list_id: Mapped[int] = mapped_column(Integer, ForeignKey('tool_lists.id'), nullable=False)
    tool_id: Mapped[int] = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    tool_list = relationship("ToolList", back_populates="items")
    tool = relationship("Tool", back_populates="tool_list_items")

    def __init__(self, **kwargs):
        """Initialize a ToolListItem instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate tool list item data."""
        if self.quantity <= 0:
            raise ModelValidationError("Quantity must be positive")