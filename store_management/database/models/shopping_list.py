# database/models/shopping_list.py
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.models.base import Base, BaseModel, ModelValidationError
from database.models.enums import Priority, ShoppingListStatus
from database.models.mixins import TimestampMixin, ValidationMixin, TrackingMixin

import logging
import re
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime


class ShoppingList(Base, BaseModel, TimestampMixin, ValidationMixin, TrackingMixin):
    """
    Represents a shopping list in the leatherworking inventory management system.

    Attributes:
        name (str): Name of the shopping list
        description (Optional[str]): Detailed description of the shopping list
        status (ShoppingListStatus): Current status of the shopping list
        priority (Priority): Priority level of the shopping list
        target_date (Optional[datetime]): Target date for completing the shopping list
        is_completed (bool): Whether the shopping list is completed
        items (List[ShoppingListItem]): List of items in the shopping list

    Validation Rules:
        - Name must be non-empty and between 2-100 characters
        - Target date must be in the future if provided
        - Must have at least one item or allow empty list
    """
    __tablename__ = 'shopping_lists'

    # Basic shopping list information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(ShoppingListStatus, nullable=False, default=ShoppingListStatus.DRAFT)
    priority = Column(Priority, nullable=False, default=Priority.LOW)

    # Additional metadata
    target_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)

    # Relationships
    items = relationship('ShoppingListItem',
                         back_populates='shopping_list',
                         cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        """
        Initialize a ShoppingList instance with validation.

        Args:
            **kwargs: Keyword arguments for shopping list attributes

        Raises:
            ModelValidationError: If validation fails for any attribute
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """
        Validate shopping list attributes before saving.

        Raises:
            ModelValidationError: If any validation check fails
        """
        # Validate name
        if not self.name or len(self.name) < 2 or len(self.name) > 100:
            raise ModelValidationError(
                "Shopping list name must be between 2 and 100 characters",
                {"name": self.name}
            )

        # Validate target date
        if self.target_date and self.target_date < datetime.now():
            raise ModelValidationError(
                "Target date must be in the future",
                {"target_date": self.target_date}
            )

        # Validate status
        if not isinstance(self.status, ShoppingListStatus):
            raise ModelValidationError(
                "Invalid shopping list status",
                {"status": self.status}
            )

        # Validate priority
        if not isinstance(self.priority, Priority):
            raise ModelValidationError(
                "Invalid priority",
                {"priority": self.priority}
            )

    def update(self, **kwargs):
        """
        Update shopping list attributes with validation.

        Args:
            **kwargs: Keyword arguments with shopping list attributes to update

        Returns:
            ShoppingList: Updated shopping list instance

        Raises:
            ModelValidationError: If validation fails for any field
        """
        for key, value in kwargs.items():
            # Handle enum conversions
            if key == 'status':
                value = ShoppingListStatus(value)
            elif key == 'priority':
                value = Priority(value)

            setattr(self, key, value)

        self.validate()
        return self

    def add_item(self, item_data: Dict[str, Any]) -> 'ShoppingListItem':
        """
        Add a new item to the shopping list.

        Args:
            item_data (Dict[str, Any]): Data for the new shopping list item

        Returns:
            ShoppingListItem: The newly created item

        Raises:
            ModelValidationError: If item data is invalid
        """
        from database.models.shopping_list import ShoppingListItem

        # Create item and link to this shopping list
        item_data['shopping_list_id'] = self.id
        item = ShoppingListItem(**item_data)

        # Add to items collection
        self.items.append(item)

        return item

    def remove_item(self, item_id: int) -> None:
        """
        Remove an item from the shopping list.

        Args:
            item_id (int): ID of the item to remove

        Raises:
            ModelValidationError: If item not found
        """
        for item in self.items[:]:
            if item.id == item_id:
                self.items.remove(item)
                return

        raise ModelValidationError(
            "Item not found in shopping list",
            {"item_id": item_id}
        )

    def mark_completed(self):
        """
        Mark the shopping list as completed.
        """
        self.is_completed = True
        self.status = ShoppingListStatus.COMPLETED

        logging.info(f"Shopping list {self.id} marked as completed", extra={
            "shopping_list_id": self.id,
            "name": self.name
        })

    def reset(self):
        """
        Reset the shopping list to draft status.
        """
        self.is_completed = False
        self.status = ShoppingListStatus.DRAFT

        logging.info(f"Shopping list {self.id} reset to draft", extra={
            "shopping_list_id": self.id,
            "name": self.name
        })

    def __repr__(self):
        """
        String representation of the shopping list.

        Returns:
            str: Descriptive string of the shopping list
        """
        return (f"<ShoppingList(id={self.id}, name='{self.name}', "
                f"status={self.status}, priority={self.priority})>")


class ShoppingListItem(Base, BaseModel, TimestampMixin):
    """
    Represents an individual item within a shopping list.

    Attributes:
        name (str): Name of the item
        quantity (float): Quantity of the item
        estimated_price (Optional[float]): Estimated price per unit
        is_purchased (bool): Whether the item has been purchased
        shopping_list_id (int): Foreign key to the parent shopping list
        shopping_list (ShoppingList): Relationship to the parent shopping list

    Validation Rules:
        - Name must be non-empty
        - Quantity must be positive
        - Estimated price must be non-negative if provided
    """
    __tablename__ = 'shopping_list_items'

    # Item details
    name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    estimated_price = Column(Float, nullable=True)
    is_purchased = Column(Boolean, default=False)

    # Relationship to shopping list
    shopping_list_id = Column(Integer, ForeignKey('shopping_lists.id'), nullable=False)
    shopping_list = relationship('ShoppingList', back_populates='items')

    def __init__(self, **kwargs):
        """
        Initialize a ShoppingListItem instance with validation.

        Args:
            **kwargs: Keyword arguments for shopping list item attributes

        Raises:
            ModelValidationError: If validation fails for any attribute
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """
        Validate shopping list item attributes before saving.

        Raises:
            ModelValidationError: If any validation check fails
        """
        # Validate name
        if not self.name or len(self.name.strip()) == 0:
            raise ModelValidationError(
                "Item name cannot be empty",
                {"name": self.name}
            )

        # Validate quantity
        if self.quantity <= 0:
            raise ModelValidationError(
                "Quantity must be positive",
                {"quantity": self.quantity}
            )

        # Validate estimated price
        if self.estimated_price is not None and self.estimated_price < 0:
            raise ModelValidationError(
                "Estimated price cannot be negative",
                {"estimated_price": self.estimated_price}
            )

    def update(self, **kwargs):
        """
        Update shopping list item attributes with validation.

        Args:
            **kwargs: Keyword arguments with item attributes to update

        Returns:
            ShoppingListItem: Updated item instance

        Raises:
            ModelValidationError: If validation fails for any field
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.validate()
        return self

    def mark_purchased(self):
        """
        Mark the item as purchased.
        """
        self.is_purchased = True

        logging.info(f"Shopping list item {self.id} marked as purchased", extra={
            "item_id": self.id,
            "name": self.name
        })

    def reset_purchase_status(self):
        """
        Reset the purchase status of the item.
        """
        self.is_purchased = False

        logging.info(f"Shopping list item {self.id} purchase status reset", extra={
            "item_id": self.id,
            "name": self.name
        })

    def __repr__(self):
        """
        String representation of the shopping list item.

        Returns:
            str: Descriptive string of the shopping list item
        """
        return (f"<ShoppingListItem(id={self.id}, name='{self.name}', "
                f"quantity={self.quantity}, purchased={self.is_purchased})>")