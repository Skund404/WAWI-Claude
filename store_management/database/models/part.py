# database/models/part.py
from typing import Dict, Any, Optional

from database.models.base import Base
from database.models.enums import InventoryStatus
from database.models.product import Product  # Explicit import
from database.models.supplier import Supplier  # Explicit import
from database.models.storage import Storage  # Explicit import

from sqlalchemy import Column, Enum, String, Text, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from utils.validators import validate_not_empty, validate_positive_number


class Part(Base):
    """
    Model representing individual parts used in leatherworking projects.

    Manages inventory tracking, relationships with products, suppliers,
    and storage locations with robust validation and error handling.
    """
    __tablename__ = 'parts'

    # Part specific fields
    name = Column(String(255), nullable=False, index=True)
    part_number = Column(String(50), nullable=True, unique=True)
    description = Column(Text, nullable=True)

    dimensions = Column(String(100), nullable=True)  # Format: "LxWxH"
    weight = Column(Float, nullable=True)

    quantity = Column(Integer, default=0, nullable=False)
    min_quantity = Column(Integer, default=0, nullable=False)

    cost = Column(Float, default=0.0, nullable=False)
    msrp = Column(Float, default=0.0, nullable=False)

    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    storage_id = Column(Integer, ForeignKey("storages.id"), nullable=True)

    # Relationships with explicit back_populates
    product = relationship(
        "Product",
        back_populates="parts",
        lazy='select',
        cascade='save-update'
    )
    supplier = relationship(
        "Supplier",
        back_populates="parts",
        lazy='select',
        cascade='save-update'
    )
    storage = relationship(
        "Storage",
        back_populates="parts",
        lazy='select',
        cascade='save-update'
    )

    def __init__(self, **kwargs):
        """
        Initialize a Part instance with robust validation.

        Args:
            **kwargs: Keyword arguments with part attributes

        Raises:
            ValueError: If validation fails for any field
            TypeError: If invalid data types are provided
        """
        try:
            self._validate_creation(kwargs)
            super().__init__(**kwargs)
        except (ValueError, TypeError) as e:
            self._handle_initialization_error(e, kwargs)

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation for part creation data.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
            TypeError: If data types are incorrect
        """
        if not isinstance(data, dict):
            raise TypeError("Input must be a dictionary")

        validate_not_empty(data, 'name', 'Part name is required')

        validation_rules = [
            ('quantity', False),
            ('min_quantity', False),
            ('cost', False),
            ('msrp', False)
        ]

        for field, allow_none in validation_rules:
            if field in data:
                try:
                    validate_positive_number(data, field, allow_zero=True, allow_none=allow_none)
                except ValueError as e:
                    raise ValueError(f"Invalid {field}: {str(e)}")

        # Optional: Additional custom validations
        if data.get('part_number') and len(data['part_number']) > 50:
            raise ValueError("Part number cannot exceed 50 characters")

    def _handle_initialization_error(self, error: Exception, data: Dict[str, Any]) -> None:
        """
        Handle initialization errors with detailed logging.

        Args:
            error (Exception): The caught exception
            data (dict): The input data that caused the error

        Raises:
            ValueError: Re-raises the original error with additional context
        """
        error_context = {
            'input_data': data,
            'error_type': type(error).__name__,
            'error_message': str(error)
        }

        # Log the error (replace with your logging mechanism)
        print(f"Part Initialization Error: {error_context}")

        # Re-raise with more context
        raise ValueError(f"Failed to create Part: {str(error)}") from error

    def adjust_quantity(self, quantity_change: int) -> None:
        """
        Adjust the part quantity with robust error checking.

        Args:
            quantity_change (int): The quantity to add (positive) or remove (negative)

        Raises:
            ValueError: If quantity adjustment is invalid
            TypeError: If quantity_change is not an integer
        """
        if not isinstance(quantity_change, int):
            raise TypeError("Quantity change must be an integer")

        try:
            new_quantity = self.quantity + quantity_change

            if new_quantity < 0:
                raise ValueError(
                    f"Cannot adjust quantity to {new_quantity}. "
                    f"Current quantity is {self.quantity}."
                )

            self.quantity = new_quantity

            # Sophisticated status management
            if self.quantity == 0:
                self.status = InventoryStatus.OUT_OF_STOCK
            elif 0 < self.quantity <= self.min_quantity:
                self.status = InventoryStatus.LOW_STOCK
            else:
                self.status = InventoryStatus.IN_STOCK

        except Exception as e:
            print(f"Quantity Adjustment Error: {e}")
            raise

    def __repr__(self) -> str:
        """
        Detailed string representation of the part.

        Returns:
            str: Comprehensive string representation
        """
        return (
            f"<Part(id={self.id}, name='{self.name}', "
            f"quantity={self.quantity}, status={self.status}, "
            f"part_number='{self.part_number or 'N/A'}')>"
        )