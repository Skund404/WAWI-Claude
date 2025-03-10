from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ProductDTO:
    """Data Transfer Object for Product."""

    id: int
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    sku: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Optional related data
    inventory_status: Optional[Dict[str, Any]] = None
    patterns: Optional[List[Dict[str, Any]]] = None
    sales_stats: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(cls, model, include_inventory=False, include_patterns=False, include_sales=False):
        """Create DTO from model instance.

        Args:
            model: Product model instance
            include_inventory: Whether to include inventory information
            include_patterns: Whether to include patterns information
            include_sales: Whether to include sales statistics

        Returns:
            ProductDTO instance
        """
        dto = cls(
            id=model.id,
            name=model.name,
            description=getattr(model, 'description', None),
            price=getattr(model, 'price', None),
            cost_price=getattr(model, 'cost_price', None),
            sku=getattr(model, 'sku', None),
            is_active=getattr(model, 'is_active', True),
            created_at=getattr(model, 'created_at', None),
            updated_at=getattr(model, 'updated_at', None)
        )

        # Add inventory information if requested
        if include_inventory and hasattr(model, 'inventory') and model.inventory:
            dto.inventory_status = {
                'quantity': model.inventory.quantity,
                'status': model.inventory.status,
                'storage_location': model.inventory.storage_location
            }

        # Add patterns if requested
        if include_patterns and hasattr(model, 'patterns') and model.patterns:
            dto.patterns = [
                {
                    'id': pattern.id,
                    'name': pattern.name,
                    'description': getattr(pattern, 'description', None),
                    'skill_level': getattr(pattern, 'skill_level', None)
                }
                for pattern in model.patterns
            ]

        # Add sales statistics if requested
        if include_sales and hasattr(model, 'sales_items') and model.sales_items:
            total_sold = sum(item.quantity for item in model.sales_items)
            total_revenue = sum(item.quantity * item.price for item in model.sales_items)

            dto.sales_stats = {
                'total_sold': total_sold,
                'total_revenue': total_revenue,
                'average_price': total_revenue / total_sold if total_sold > 0 else 0
            }

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}