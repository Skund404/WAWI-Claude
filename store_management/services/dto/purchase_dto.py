from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class PurchaseItemDTO:
    """Data Transfer Object for Purchase Item."""

    id: int
    purchase_id: int
    item_type: str  # material/tool
    item_id: int
    quantity: float
    price: Optional[float] = None
    quantity_received: Optional[float] = 0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Optional related data
    item_name: Optional[str] = None
    item_details: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(cls, model, include_item_details=False):
        """Create DTO from model instance.

        Args:
            model: PurchaseItem model instance
            include_item_details: Whether to include detailed item information

        Returns:
            PurchaseItemDTO instance
        """
        dto = cls(
            id=model.id,
            purchase_id=model.purchase_id,
            item_type=model.item_type,
            item_id=model.item_id,
            quantity=model.quantity,
            price=getattr(model, 'price', None),
            quantity_received=getattr(model, 'quantity_received', 0),
            notes=getattr(model, 'notes', None),
            created_at=getattr(model, 'created_at', None),
            updated_at=getattr(model, 'updated_at', None)
        )

        # Add item name if available
        item = None
        if model.item_type == 'material' and hasattr(model, 'material') and model.material:
            item = model.material
            dto.item_name = item.name
        elif model.item_type == 'tool' and hasattr(model, 'tool') and model.tool:
            item = model.tool
            dto.item_name = item.name

        # Add detailed item information if requested and available
        if include_item_details and item:
            if model.item_type == 'material':
                dto.item_details = {
                    'id': item.id,
                    'name': item.name,
                    'material_type': getattr(item, 'material_type', None),
                    'unit': getattr(item, 'unit', None),
                    'supplier_id': getattr(item, 'supplier_id', None)
                }
            elif model.item_type == 'tool':
                dto.item_details = {
                    'id': item.id,
                    'name': item.name,
                    'tool_category': getattr(item, 'tool_category', None),
                    'brand': getattr(item, 'brand', None),
                    'model': getattr(item, 'model', None)
                }

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PurchaseDTO:
    """Data Transfer Object for Purchase."""

    id: int
    supplier_id: int
    status: str
    created_at: datetime
    total_amount: Optional[float] = None
    order_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    delivery_date: Optional[datetime] = None
    shipping_cost: Optional[float] = None
    tax_amount: Optional[float] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    updated_at: Optional[datetime] = None

    # Optional related data
    supplier_info: Optional[Dict[str, Any]] = None
    items: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_model(cls, model, include_supplier=False, include_items=False):
        """Create DTO from model instance.

        Args:
            model: Purchase model instance
            include_supplier: Whether to include supplier information
            include_items: Whether to include purchase items

        Returns:
            PurchaseDTO instance
        """
        dto = cls(
            id=model.id,
            supplier_id=model.supplier_id,
            status=model.status,
            created_at=model.created_at,
            total_amount=getattr(model, 'total_amount', None),
            order_date=getattr(model, 'order_date', None),
            expected_delivery_date=getattr(model, 'expected_delivery_date', None),
            delivery_date=getattr(model, 'delivery_date', None),
            shipping_cost=getattr(model, 'shipping_cost', None),
            tax_amount=getattr(model, 'tax_amount', None),
            payment_terms=getattr(model, 'payment_terms', None),
            notes=getattr(model, 'notes', None),
            reference_number=getattr(model, 'reference_number', None),
            updated_at=getattr(model, 'updated_at', None)
        )

        # Add supplier information if requested and available
        if include_supplier and hasattr(model, 'supplier') and model.supplier:
            supplier = model.supplier
            dto.supplier_info = {
                'id': supplier.id,
                'name': supplier.name,
                'status': getattr(supplier, 'status', None),
                'contact_email': getattr(supplier, 'contact_email', None),
                'contact_person': getattr(supplier, 'contact_person', None)
            }

        # Add items if requested and available
        if include_items and hasattr(model, 'items') and model.items:
            dto.items = []
            for item in model.items:
                item_dto = PurchaseItemDTO.from_model(item, include_item_details=True)
                dto.items.append(item_dto.to_dict())

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}