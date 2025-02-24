# Path: store_management/database/models/storage_resolver.py
"""
Circular Import Resolver for Storage Model.

Provides a mechanism to lazily load and resolve model relationships
to prevent circular import issues.
"""

from typing import TYPE_CHECKING, Any, Optional, List, Dict
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from datetime import datetime

from .base import BaseModel
from .mixins import TimestampMixin, ValidationMixin

if TYPE_CHECKING:
    from .product import Product


class StorageModelResolver:
    """
    A resolver class to handle lazy loading of storage-related models.
    """

    _product_model: Optional[Any] = None

    @classmethod
    def set_product_model(cls, product_model: Any) -> None:
        """Set the Product model class for lazy loading."""
        cls._product_model = product_model

    @classmethod
    def get_products_relationship(cls):
        """Get the products relationship with lazy loading."""
        if cls._product_model is None:
            from .product import Product
            cls._product_model = Product

        return relationship(
            cls._product_model,
            back_populates="storage",
            lazy='subquery'
        )


def create_storage_model(base_classes):
    """
    Dynamically create the Storage model with resolved relationships.

    Args:
        base_classes (tuple): Base classes for the model.

    Returns:
        type: Dynamically created Storage model class.
    """

    class Storage(*base_classes):
        """
        Represents a storage location in the inventory system.
        """
        __tablename__ = 'storage_locations'

        # Basic storage information
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        location: Mapped[str] = mapped_column(String(200))
        description: Mapped[Optional[str]] = mapped_column(String(500))

        # Capacity and occupancy tracking
        capacity: Mapped[float] = mapped_column(Float, nullable=False)
        current_occupancy: Mapped[float] = mapped_column(Float, default=0.0)

        # Timestamps
        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Relationships using resolver
        products = StorageModelResolver.get_products_relationship()

        def __init__(self,
                     name: str,
                     location: str,
                     capacity: float,
                     description: Optional[str] = None):
            """
            Initialize a Storage instance.

            Args:
                name (str): Name of the storage location.
                location (str): Specific location details.
                capacity (float): Total storage capacity.
                description (Optional[str], optional): Additional description.
            """
            self.name = name
            self.location = location
            self.capacity = capacity
            self.description = description

            # Default initializations
            self.current_occupancy = 0.0
            self.products = []

        def occupancy_percentage(self) -> float:
            """
            Calculate the storage occupancy percentage.

            Returns:
                float: Percentage of storage capacity used.
            """
            return (self.current_occupancy / self.capacity) * 100 if self.capacity > 0 else 0.0

        def add_product(self, product, quantity: float) -> None:
            """
            Add a product to the storage location.

            Args:
                product: Product to be stored.
                quantity (float): Quantity of the product to store.

            Raises:
                ValueError: If adding the product would exceed storage capacity.
            """
            if self.current_occupancy + quantity > self.capacity:
                raise ValueError("Storage capacity would be exceeded")

            self.current_occupancy += quantity
            if product not in self.products:
                self.products.append(product)

        def remove_product(self, product, quantity: float) -> None:
            """
            Remove a product from the storage location.

            Args:
                product: Product to be removed.
                quantity (float): Quantity of the product to remove.

            Raises:
                ValueError: If removing more than stored quantity.
            """
            if quantity > self.current_occupancy:
                raise ValueError("Cannot remove more than stored quantity")

            self.current_occupancy -= quantity

            # Optionally remove product from list if no quantity remains
            if self.current_occupancy == 0:
                self.products.remove(product)

        def to_dict(self,
                    exclude_fields: Optional[List[str]] = None,
                    include_relationships: bool = False) -> Dict[str, Any]:
            """
            Convert Storage to dictionary representation.

            Args:
                exclude_fields (Optional[List[str]], optional): Fields to exclude.
                include_relationships (bool, optional): Whether to include related entities.

            Returns:
                Dict[str, Any]: Dictionary of storage attributes.
            """
            exclude_fields = exclude_fields or []

            storage_dict = {
                'id': self.id,
                'name': self.name,
                'location': self.location,
                'description': self.description,
                'capacity': self.capacity,
                'current_occupancy': self.current_occupancy,
                'occupancy_percentage': self.occupancy_percentage(),
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat()
            }

            # Remove excluded fields
            for field in exclude_fields:
                storage_dict.pop(field, None)

            # Optionally include relationships
            if include_relationships and self.products:
                storage_dict['products'] = [
                    product.to_dict() for product in self.products
                ]

            return storage_dict

    return Storage


# Create the Storage model with resolved base classes
Storage = create_storage_model((BaseModel, TimestampMixin, ValidationMixin))