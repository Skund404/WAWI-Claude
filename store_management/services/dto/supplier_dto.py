from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class SupplierDTO:
    """Data Transfer Object for Supplier."""

    id: int
    name: str
    status: str
    contact_email: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    minimum_order: Optional[float] = None
    tax_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    material_count: Optional[int] = None
    tool_count: Optional[int] = None

    @classmethod
    def from_model(cls, model, include_metrics=False, include_counts=False):
        """Create DTO from model instance.

        Args:
            model: Supplier model instance
            include_metrics: Whether to include performance metrics
            include_counts: Whether to include material and tool counts

        Returns:
            SupplierDTO instance
        """
        dto = cls(
            id=model.id,
            name=model.name,
            status=model.status,
            contact_email=getattr(model, 'contact_email', None),
            contact_person=getattr(model, 'contact_person', None),
            phone=getattr(model, 'phone', None),
            address=getattr(model, 'address', None),
            website=getattr(model, 'website', None),
            notes=getattr(model, 'notes', None),
            payment_terms=getattr(model, 'payment_terms', None),
            minimum_order=getattr(model, 'minimum_order', None),
            tax_id=getattr(model, 'tax_id', None),
            created_at=getattr(model, 'created_at', None),
            updated_at=getattr(model, 'updated_at', None)
        )

        # Add performance metrics if requested
        if include_metrics and hasattr(model, 'purchases') and model.purchases:
            on_time_delivery = sum(
                1 for p in model.purchases if p.status == 'DELIVERED' and p.delivery_date <= p.expected_delivery_date)
            on_time_rate = on_time_delivery / len(model.purchases) if model.purchases else 0

            dto.performance_metrics = {
                'on_time_delivery_rate': on_time_rate,
                'average_delivery_days': sum(
                    (p.delivery_date - p.order_date).days for p in model.purchases if p.delivery_date) / len(
                    model.purchases) if model.purchases else 0,
                'total_purchases': len(model.purchases),
                'total_spent': sum(p.total_amount for p in model.purchases)
            }

        # Add counts if requested
        if include_counts:
            dto.material_count = len(model.materials) if hasattr(model, 'materials') else 0
            dto.tool_count = len(model.tools) if hasattr(model, 'tools') else 0

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}