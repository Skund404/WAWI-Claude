# database/models/sales.py
from database.models.base import Base
from sqlalchemy import Column, Date, Float, Integer, String, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import date
from utils.validators import validate_not_empty, validate_positive_number


class Sales(Base):
    """
    Model representing sales records for leatherworking items.
    """
    # Sales specific fields
    sale_date = Column(Date, default=date.today, nullable=False)
    invoice_number = Column(String(50), nullable=True, unique=True)

    product_name = Column(String(255), nullable=False)
    quantity_sold = Column(Integer, default=1, nullable=False)

    unit_price = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)

    payment_method = Column(String(50), nullable=True)
    is_paid = Column(Boolean, default=True, nullable=False)

    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)

    notes = Column(Text, nullable=True)

    # Foreign keys
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="sales")
    order = relationship("Order", back_populates="sales")

    def __init__(self, **kwargs):
        """Initialize a Sales instance with validation.

        Args:
            **kwargs: Keyword arguments with sales attributes

        Raises:
            ValueError: If validation fails for any field
        """
        self._validate_creation(kwargs)

        # Set default sale date if not provided
        if 'sale_date' not in kwargs:
            kwargs['sale_date'] = date.today()

        super().__init__(**kwargs)

        # Calculate total amount if not provided
        if 'total_amount' not in kwargs:
            self.calculate_total()

    @classmethod
    def _validate_creation(cls, data):
        """Validate sales data before creation.

        Args:
            data (dict): The data to validate

        Raises:
            ValueError: If validation fails
        """
        validate_not_empty(data, 'product_name', 'Product name is required')

        if 'quantity_sold' in data:
            validate_positive_number(data, 'quantity_sold')
        if 'unit_price' in data:
            validate_positive_number(data, 'unit_price', allow_zero=True)

    def calculate_total(self):
        """Calculate the total sales amount.

        Returns:
            float: The calculated total amount
        """
        subtotal = self.quantity_sold * self.unit_price
        self.total_amount = subtotal - self.discount_amount + self.tax_amount
        return self.total_amount

    def mark_as_paid(self, is_paid=True):
        """Mark the sale as paid or unpaid.

        Args:
            is_paid (bool): Whether the sale is paid
        """
        self.is_paid = is_paid

    def __repr__(self):
        """String representation of the sales record.

        Returns:
            str: String representation
        """
        return f"<Sales(id={self.id}, date={self.sale_date}, product='{self.product_name}', amount={self.total_amount})>"