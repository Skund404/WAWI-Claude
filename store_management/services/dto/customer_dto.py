# services/dto/customer_dto.py
# Data Transfer Object for Customer

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class CustomerDTO:
    """Data Transfer Object for Customer."""

    id: int
    name: str
    email: str
    status: str
    tier: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    contact_phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    sales_count: Optional[int] = None
    project_count: Optional[int] = None
    total_spent: Optional[float] = None

    @classmethod
    def from_model(cls, model, include_statistics=False):
        """Create DTO from model instance.

        Args:
            model: Customer model instance
            include_statistics: Whether to include sales statistics

        Returns:
            CustomerDTO instance
        """
        dto = cls(
            id=model.id,
            name=model.name,
            email=model.email,
            status=model.status,
            tier=model.tier if hasattr(model, 'tier') else None,
            source=model.source if hasattr(model, 'source') else None,
            created_at=model.created_at if hasattr(model, 'created_at') else None,
            updated_at=model.updated_at if hasattr(model, 'updated_at') else None,
            contact_phone=model.contact_phone if hasattr(model, 'contact_phone') else None,
            address=model.address if hasattr(model, 'address') else None,
            notes=model.notes if hasattr(model, 'notes') else None
        )

        # Add statistics if requested and available
        if include_statistics:
            if hasattr(model, 'sales') and model.sales:
                dto.sales_count = len(model.sales)
                dto.total_spent = sum(sale.total_amount for sale in model.sales if hasattr(sale, 'total_amount'))

            if hasattr(model, 'projects') and model.projects:
                dto.project_count = len(model.projects)

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}