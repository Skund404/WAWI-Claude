# database/models/customer.py
from sqlalchemy import Column, Enum, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
import re

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError
from database.models.enums import CustomerStatus, CustomerTier, CustomerSource


class Customer(AbstractBase, ValidationMixin):
    """
    Customer represents a person or organization that purchases products.

    Attributes:
        name: Customer name
        email: Contact email
        phone: Contact phone number
        address: Physical address
        status: Customer status
        tier: Customer loyalty tier
        source: How the customer was acquired
        notes: Additional notes
    """
    __tablename__ = 'customers'

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[CustomerStatus] = mapped_column(Enum(CustomerStatus), nullable=False, default=CustomerStatus.ACTIVE)
    tier: Mapped[CustomerTier] = mapped_column(Enum(CustomerTier), nullable=False, default=CustomerTier.STANDARD)
    source: Mapped[Optional[CustomerSource]] = mapped_column(Enum(CustomerSource), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_business: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    sales = relationship("Sales", back_populates="customer")

    def __init__(self, **kwargs):
        """Initialize a Customer instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate customer data."""
        if not self.name:
            raise ModelValidationError("Customer name cannot be empty")

        if len(self.name) > 255:
            raise ModelValidationError("Customer name cannot exceed 255 characters")

        if self.email and not self._is_valid_email(self.email):
            raise ModelValidationError("Invalid email format")

    def _is_valid_email(self, email: str) -> bool:
        """Check if the email is valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def upgrade_tier(self, new_tier: CustomerTier, reason: Optional[str] = None) -> None:
        """
        Upgrade customer to a higher tier.

        Args:
            new_tier: New customer tier
            reason: Optional reason for the upgrade
        """
        # Ensure new tier is an upgrade
        tier_order = {
            CustomerTier.NEW: 0,
            CustomerTier.STANDARD: 1,
            CustomerTier.PREMIUM: 2,
            CustomerTier.VIP: 3
        }

        current_tier_value = tier_order.get(self.tier, 0)
        new_tier_value = tier_order.get(new_tier, 0)

        if new_tier_value <= current_tier_value:
            raise ValueError(f"New tier ({new_tier.name}) is not an upgrade from current tier ({self.tier.name})")

        self.tier = new_tier

        if reason:
            if self.notes:
                self.notes += f"\n[TIER UPGRADE] {reason}"
            else:
                self.notes = f"[TIER UPGRADE] {reason}"