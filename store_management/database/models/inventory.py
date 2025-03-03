# database/models/inventory.py
from database.models.base import Base
from database.models.enums import MaterialType, MeasurementUnit
from sqlalchemy import Column, Enum, Float, String, Integer, ForeignKey
from sqlalchemy.orm import relationship


class Inventory(Base):
    """
    Model representing the inventory system.
    """
    # Inventory specific fields
    item_name = Column(String(255), nullable=False, index=True)
    item_type = Column(Enum(MaterialType), nullable=False)

    quantity = Column(Float, default=0.0, nullable=False)
    unit = Column(Enum(MeasurementUnit), nullable=False, default=MeasurementUnit.PIECE)

    reorder_point = Column(Float, default=0.0, nullable=False)
    reorder_quantity = Column(Float, default=0.0, nullable=False)

    # Foreign keys for item references
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)

    # Location reference
    storage_id = Column(Integer, ForeignKey("storage.id"), nullable=True)

    # Relationships
    material = relationship("Material", uselist=False, viewonly=True)
    leather = relationship("Leather", uselist=False, viewonly=True)
    hardware = relationship("Hardware", uselist=False, viewonly=True)
    product = relationship("Product", uselist=False, viewonly=True)
    storage = relationship("Storage", uselist=False)

    def __init__(self, **kwargs):
        """Initialize an Inventory instance with validation.

        Args:
            **kwargs: Keyword arguments with inventory attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_creation(cls, data):
        """Validate inventory data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        if 'item_name' not in data or not data['item_name']:
            raise ValueError("Item name is required")

        if 'item_type' not in data:
            raise ValueError("Item type is required")

        # Ensure at least one item reference is provided
        if not any(key in data for key in ['material_id', 'leather_id', 'hardware_id', 'product_id']):
            raise ValueError("At least one of material_id, leather_id, hardware_id, or product_id must be specified")

    def needs_reorder(self):
        """Check if the inventory item needs to be reordered.

        Returns:
            bool: True if the quantity is below the reorder point
        """
        return self.quantity <= self.reorder_point

    def __repr__(self):
        """String representation of the Inventory item.

        Returns:
            str: Descriptive string of the inventory item
        """
        return f"<Inventory(id={self.id}, name='{self.item_name}', type={self.item_type}, quantity={self.quantity})>"