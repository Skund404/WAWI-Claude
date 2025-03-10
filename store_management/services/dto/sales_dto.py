# services/dto/sales_dto.py
# Data Transfer Object for Sales

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class SalesItemDTO:
    """Data Transfer Object for Sales Item."""

    id: int
    sales_id: int
    product_id: int
    quantity: int
    price: float
    product_name: Optional[str] = None
    product_type: Optional[str] = None
    subtotal: Optional[float] = None

    @classmethod
    def from_model(cls, model):
        """Create DTO from model instance.

        Args:
            model: SalesItem model instance

        Returns:
            SalesItemDTO instance
        """
        dto = cls(
            id=model.id,
            sales_id=model.sales_id,
            product_id=model.product_id,
            quantity=model.quantity,
            price=model.price,
            subtotal=model.quantity * model.price
        )

        # Add product information if available
        if hasattr(model, 'product') and model.product:
            dto.product_name = model.product.name
            dto.product_type = model.product.type if hasattr(model.product, 'type') else None

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SalesDTO:
    """Data Transfer Object for Sales."""

    id: int
    created_at: datetime
    total_amount: float
    status: str
    payment_status: str
    customer_id: int
    updated_at: Optional[datetime] = None
    customer_name: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)
    discount: Optional[float] = None
    tax: Optional[float] = None
    notes: Optional[str] = None
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(cls, model, include_items=False, include_customer=False):
        """Create DTO from model instance.

        Args:
            model: Sales model instance
            include_items: Whether to include sales items
            include_customer: Whether to include customer information

        Returns:
            SalesDTO instance
        """
        dto = cls(
            id=model.id,
            created_at=model.created_at,
            total_amount=model.total_amount,
            status=model.status,
            payment_status=model.payment_status,
            customer_id=model.customer_id,
            updated_at=model.updated_at if hasattr(model, 'updated_at') else None,
            discount=model.discount if hasattr(model, 'discount') else None,
            tax=model.tax if hasattr(model, 'tax') else None,
            notes=model.notes if hasattr(model, 'notes') else None,
            shipping_address=model.shipping_address if hasattr(model, 'shipping_address') else None,
            billing_address=model.billing_address if hasattr(model, 'billing_address') else None
        )

        # Add items if requested and available
        if include_items and hasattr(model, 'items') and model.items:
            dto.items = [SalesItemDTO.from_model(item).to_dict() for item in model.items]

        # Add customer information if requested and available
        if include_customer and hasattr(model, 'customer') and model.customer:
            dto.customer_name = model.customer.name

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}