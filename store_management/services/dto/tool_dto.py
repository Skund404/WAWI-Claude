from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ToolDTO:
    """Data Transfer Object for Tool."""

    id: int
    name: str
    tool_category: str
    description: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[float] = None
    supplier_id: Optional[int] = None
    maintenance_interval: Optional[int] = None
    last_maintenance: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Optional related data
    inventory_status: Optional[Dict[str, Any]] = None
    supplier_info: Optional[Dict[str, Any]] = None
    usage_stats: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(cls, model, include_inventory=False, include_supplier=False, include_usage=False):
        """Create DTO from model instance.

        Args:
            model: Tool model instance
            include_inventory: Whether to include inventory information
            include_supplier: Whether to include supplier information
            include_usage: Whether to include usage statistics

        Returns:
            ToolDTO instance
        """
        dto = cls(
            id=model.id,
            name=model.name,
            tool_category=model.tool_category,
            description=getattr(model, 'description', None),
            brand=getattr(model, 'brand', None),
            model=getattr(model, 'model', None),
            serial_number=getattr(model, 'serial_number', None),
            purchase_date=getattr(model, 'purchase_date', None),
            purchase_price=getattr(model, 'purchase_price', None),
            supplier_id=getattr(model, 'supplier_id', None),
            maintenance_interval=getattr(model, 'maintenance_interval', None),
            last_maintenance=getattr(model, 'last_maintenance', None),
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

        # Add supplier information if requested
        if include_supplier and hasattr(model, 'supplier') and model.supplier:
            dto.supplier_info = {
                'id': model.supplier.id,
                'name': model.supplier.name,
                'status': getattr(model.supplier, 'status', None)
            }

        # Add usage statistics if requested
        if include_usage and hasattr(model, 'tool_list_items') and model.tool_list_items:
            total_checkouts = len(model.tool_list_items)
            tool_lists = set(item.tool_list_id for item in model.tool_list_items if hasattr(item, 'tool_list_id'))

            dto.usage_stats = {
                'total_checkouts': total_checkouts,
                'unique_projects': len(tool_lists),
                'current_checkouts': sum(1 for item in model.tool_list_items
                                         if hasattr(item, 'tool_list') and
                                         hasattr(item.tool_list, 'status') and
                                         item.tool_list.status in ['IN_PROGRESS', 'PENDING'])
            }

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}