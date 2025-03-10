# services/dto/picking_list_dto.py
# Data Transfer Object for Picking List

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class PickingListItemDTO:
    """Data Transfer Object for Picking List Item."""

    id: int
    picking_list_id: int
    component_id: int
    material_id: int
    quantity_ordered: float
    quantity_picked: float
    component_name: Optional[str] = None
    material_name: Optional[str] = None
    material_type: Optional[str] = None
    storage_location: Optional[str] = None
    status: Optional[str] = None

    @classmethod
    def from_model(cls, model):
        """Create DTO from model instance.

        Args:
            model: PickingListItem model instance

        Returns:
            PickingListItemDTO instance
        """
        dto = cls(
            id=model.id,
            picking_list_id=model.picking_list_id,
            component_id=model.component_id,
            material_id=model.material_id,
            quantity_ordered=model.quantity_ordered,
            quantity_picked=model.quantity_picked,
            status="COMPLETE" if model.quantity_picked >= model.quantity_ordered else "PARTIAL" if model.quantity_picked > 0 else "PENDING"
        )

        # Add component information if available
        if hasattr(model, 'component') and model.component:
            dto.component_name = model.component.name

        # Add material information if available
        if hasattr(model, 'material') and model.material:
            dto.material_name = model.material.name
            dto.material_type = model.material.material_type

            # Add storage location if available from inventory
            if hasattr(model.material, 'inventory') and model.material.inventory:
                dto.storage_location = model.material.inventory.storage_location

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PickingListDTO:
    """Data Transfer Object for Picking List."""

    id: int
    project_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    project_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_model(cls, model, include_items=False, include_project=False):
        """Create DTO from model instance.

        Args:
            model: PickingList model instance
            include_items: Whether to include picking list items
            include_project: Whether to include project information

        Returns:
            PickingListDTO instance
        """
        dto = cls(
            id=model.id,
            project_id=model.project_id,
            status=model.status,
            created_at=model.created_at,
            completed_at=model.completed_at if hasattr(model, 'completed_at') and model.completed_at else None,
            notes=model.notes if hasattr(model, 'notes') else None
        )

        # Add items if requested and available
        if include_items and hasattr(model, 'items') and model.items:
            dto.items = [PickingListItemDTO.from_model(item).to_dict() for item in model.items]

        # Add project information if requested and available
        if include_project and hasattr(model, 'project') and model.project:
            dto.project_name = model.project.name

            # Add customer information if available
            if hasattr(model.project, 'customer') and model.project.customer:
                dto.customer_id = model.project.customer.id
                dto.customer_name = model.project.customer.name
            elif hasattr(model.project, 'sales') and model.project.sales and hasattr(model.project.sales,
                                                                                     'customer') and model.project.sales.customer:
                dto.customer_id = model.project.sales.customer.id
                dto.customer_name = model.project.sales.customer.name

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}