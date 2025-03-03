# database/models/production.py
from database.models.base import Base
from sqlalchemy import Column, Date, Float, Integer, String, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, date
from typing import Optional
from utils.validators import validate_not_empty


class Production(Base):
    """
    Model representing production records for leatherworking items.
    """
    # Production specific fields
    production_date = Column(Date, default=date.today, nullable=False)
    batch_number = Column(String(50), nullable=True)

    product_name = Column(String(255), nullable=False)
    quantity_produced = Column(Integer, default=0, nullable=False)

    labor_hours = Column(Float, default=0.0, nullable=False)
    material_cost = Column(Float, default=0.0, nullable=False)
    labor_cost = Column(Float, default=0.0, nullable=False)
    overhead_cost = Column(Float, default=0.0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)

    notes = Column(Text, nullable=True)

    # Foreign keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="production_records")
    project = relationship("Project", back_populates="production_records")

    def __init__(self, **kwargs):
        """Initialize a Production instance with validation.

        Args:
            **kwargs: Keyword arguments with production attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)

        # Set default production date if not provided
        if 'production_date' not in kwargs:
            kwargs['production_date'] = date.today()

        super().__init__(**kwargs)

        # Calculate total cost if not provided
        if 'total_cost' not in kwargs:
            self.calculate_total_cost()

    @classmethod
    def _validate_creation(cls, data):
        """Validate production data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'product_name', 'Product name is required')

        # Validate numeric fields
        for field in ['quantity_produced', 'labor_hours', 'material_cost', 'labor_cost', 'overhead_cost']:
            if field in data and data[field] < 0:
                raise ValueError(f"{field.replace('_', ' ').title()} cannot be negative")

    def calculate_total_cost(self):
        """Calculate the total production cost.

        Returns:
            float: The calculated total cost
        """
        self.total_cost = self.material_cost + self.labor_cost + self.overhead_cost
        return self.total_cost

    def get_unit_cost(self):
        """Calculate the per-unit production cost.

        Returns:
            float: The per-unit cost, or None if quantity is zero
        """
        if self.quantity_produced > 0:
            return self.total_cost / self.quantity_produced
        return None

    def __repr__(self):
        """String representation of the production record.

        Returns:
            str: String representation
        """
        return f"<Production(id={self.id}, date={self.production_date}, product='{self.product_name}', quantity={self.quantity_produced})>"