# database/models/shopping_list.py
from database.models.base import Base
from database.models.enums import Priority, ShoppingListStatus
from sqlalchemy import Column, Enum, String, Text, Boolean, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from utils.validators import validate_not_empty


class ShoppingList(Base):
    """
    Model representing a shopping list for materials.
    """
    # Shopping list specific fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    status = Column(Enum(ShoppingListStatus), default=ShoppingListStatus.DRAFT, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False)

    due_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize a ShoppingList instance with validation.

        Args:
            **kwargs: Keyword arguments for shopping list attributes

        Raises:
            ValueError: If validation fails for any attribute
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate shopping list attributes before saving.

        Raises:
            ValueError: If any validation check fails
        """
        validate_not_empty(data, 'name', 'Shopping list name is required')

    def mark_completed(self):
        """Mark the shopping list as completed."""
        self.status = ShoppingListStatus.COMPLETED
        self.completion_date = datetime.utcnow()

    def reset(self):
        """Reset the shopping list to draft status."""
        self.status = ShoppingListStatus.DRAFT
        self.completion_date = None

    def __repr__(self):
        """String representation of the shopping list.

        Returns:
            str: Descriptive string of the shopping list
        """
        return f"<ShoppingList(id={self.id}, name='{self.name}', status={self.status})>"


class ShoppingListItem(Base):
    """
    Model representing an item in a shopping list.
    """
    # Shopping list item specific fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, nullable=True)
    estimated_total = Column(Float, nullable=True)

    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False)
    is_purchased = Column(Boolean, default=False, nullable=False)
    purchase_date = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Foreign keys
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    material = relationship("Material", uselist=False, viewonly=True)
    leather = relationship("Leather", uselist=False, viewonly=True)
    hardware = relationship("Hardware", uselist=False, viewonly=True)
    supplier = relationship("Supplier", uselist=False)

    def __init__(self, **kwargs):
        """Initialize a ShoppingListItem instance with validation.

        Args:
            **kwargs: Keyword arguments for shopping list item attributes

        Raises:
            ValueError: If validation fails for any attribute
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

        # Calculate estimated total if unit price is provided
        if 'unit_price' in kwargs and 'quantity' in kwargs and 'estimated_total' not in kwargs:
            self.estimated_total = self.unit_price * self.quantity

    @classmethod
    def _validate_creation(cls, data):
        """Validate shopping list item attributes before saving.

        Raises:
            ValueError: If any validation check fails
        """
        validate_not_empty(data, 'name', 'Item name is required')
        validate_not_empty(data, 'shopping_list_id', 'Shopping list ID is required')

        if 'quantity' in data and data['quantity'] <= 0:
            raise ValueError("Quantity must be greater than zero")

        if 'unit_price' in data and data['unit_price'] < 0:
            raise ValueError("Unit price cannot be negative")

    def mark_purchased(self):
        """Mark the item as purchased."""
        self.is_purchased = True
        self.purchase_date = datetime.utcnow()

    def reset_purchase_status(self):
        """Reset the purchase status of the item."""
        self.is_purchased = False
        self.purchase_date = None

    def __repr__(self):
        """String representation of the shopping list item.

        Returns:
            str: Descriptive string of the shopping list item
        """
        return f"<ShoppingListItem(id={self.id}, name='{self.name}', list_id={self.shopping_list_id}, purchased={self.is_purchased})>"