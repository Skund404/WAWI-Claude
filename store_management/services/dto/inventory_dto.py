# services/dto/inventory_dto.py
# Data Transfer Object for Inventory

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class InventoryDTO:
    """Data Transfer Object for Inventory."""

    id: int
    item_type: str
    item_id: int
    quantity: float
    status: str
    storage_location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    item_name: Optional[str] = None
    item_details: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(cls, model, include_item_details=False):
        """Create DTO from model instance.

        Args:
            model: Inventory model instance
            include_item_details: Whether to include item details

        Returns:
            InventoryDTO instance
        """
        dto = cls(
            id=model.id,
            item_type=model.item_type,
            item_id=model.item_id,
            quantity=model.quantity,
            status=model.status,
            storage_location=model.storage_location if hasattr(model, 'storage_location') else None,
            created_at=model.created_at if hasattr(model, 'created_at') else None,
            updated_at=model.updated_at if hasattr(model, 'updated_at') else None
        )

        # Add item details if requested and available
        if include_item_details:
            if model.item_type == 'material' and hasattr(model, 'material') and model.material:
                dto.item_name = model.material.name
                dto.item_details = {
                    'material_type': model.material.material_type,
                    'unit': model.material.unit if hasattr(model.material, 'unit') else None,
                    'supplier_id': model.material.supplier_id if hasattr(model.material, 'supplier_id') else None
                }
            elif model.item_type == 'product' and hasattr(model, 'product') and model.product:
                dto.item_name = model.product.name
                dto.item_details = {
                    'price': model.product.price if hasattr(model.product, 'price') else None,
                    'description': model.product.description if hasattr(model.product, 'description') else None
                }
            elif model.item_type == 'tool' and hasattr(model, 'tool') and model.tool:
                dto.item_name = model.tool.name
                dto.item_details = {
                    'tool_type': model.tool.tool_type if hasattr(model.tool, 'tool_type') else None,
                    'description': model.tool.description if hasattr(model.tool, 'description') else None
                }

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class InventoryTransactionDTO:
    """Data Transfer Object for Inventory Transaction."""

    id: int
    inventory_id: int
    item_type: str
    item_id: int
    quantity: float
    type: str
    timestamp: datetime
    notes: Optional[str] = None
    item_name: Optional[str] = None
    user_id: Optional[int] = None

    @classmethod
    def from_model(cls, model):
        """Create DTO from model instance.

        Args:
            model: InventoryTransaction model instance

        Returns:
            InventoryTransactionDTO instance
        """
        dto = cls(
            id=model.id,
            inventory_id=model.inventory_id if hasattr(model, 'inventory_id') else None,
            item_type=model.item_type,
            item_id=model.item_id,
            quantity=model.quantity,
            type=model.type,
            timestamp=model.timestamp,
            notes=model.notes if hasattr(model, 'notes') else None,
            user_id=model.user_id if hasattr(model, 'user_id') else None
        )

        # Add item name if available
        if hasattr(model, 'inventory') and model.inventory:
            if model.item_type == 'material' and hasattr(model.inventory, 'material') and model.inventory.material:
                dto.item_name = model.inventory.material.name
            elif model.item_type == 'product' and hasattr(model.inventory, 'product') and model.inventory.product:
                dto.item_name = model.inventory.product.name
            elif model.item_type == 'tool' and hasattr(model.inventory, 'tool') and model.inventory.tool:
                dto.item_name = model.inventory.tool.name

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LocationHistoryDTO:
    """Data Transfer Object for Location History."""

    id: int
    inventory_id: int
    previous_location: Optional[str]
    new_location: str
    timestamp: datetime
    notes: Optional[str] = None

    @classmethod
    def from_model(cls, model):
        """Create DTO from model instance.

        Args:
            model: LocationHistory model instance

        Returns:
            LocationHistoryDTO instance
        """
        return cls(
            id=model.id,
            inventory_id=model.inventory_id,
            previous_location=model.previous_location if hasattr(model, 'previous_location') else None,
            new_location=model.new_location,
            timestamp=model.timestamp,
            notes=model.notes if hasattr(model, 'notes') else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}