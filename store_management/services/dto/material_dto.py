# services/dto/material_dto.py
# Data Transfer Object for Material

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class MaterialDTO:
    """Data Transfer Object for Material."""

    id: int
    name: str
    material_type: str
    unit: str
    supplier_id: Optional[int] = None
    description: Optional[str] = None
    quality: Optional[str] = None
    cost_price: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    attributes: Optional[Dict[str, Any]] = None
    inventory_status: Optional[Dict[str, Any]] = None
    supplier_info: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(cls, model, include_inventory=False, include_supplier=False):
        """Create DTO from model instance.

        Args:
            model: Material model instance
            include_inventory: Whether to include inventory information
            include_supplier: Whether to include supplier information

        Returns:
            MaterialDTO instance
        """
        dto = cls(
            id=model.id,
            name=model.name,
            material_type=model.material_type,
            unit=model.unit,
            supplier_id=model.supplier_id if hasattr(model, 'supplier_id') else None,
            description=model.description if hasattr(model, 'description') else None,
            quality=model.quality if hasattr(model, 'quality') else None,
            cost_price=model.cost_price if hasattr(model, 'cost_price') else None,
            created_at=model.created_at if hasattr(model, 'created_at') else None,
            updated_at=model.updated_at if hasattr(model, 'updated_at') else None,
            attributes=model.attributes if hasattr(model, 'attributes') else None
        )

        # Add inventory information if requested and available
        if include_inventory and hasattr(model, 'inventory') and model.inventory:
            dto.inventory_status = {
                'quantity': model.inventory.quantity,
                'status': model.inventory.status,
                'storage_location': model.inventory.storage_location
            }

        # Add supplier information if requested and available
        if include_supplier and hasattr(model, 'supplier') and model.supplier:
            dto.supplier_info = {
                'id': model.supplier.id,
                'name': model.supplier.name,
                'status': model.supplier.status
            }

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LeatherDTO(MaterialDTO):
    """Data Transfer Object for Leather (extends MaterialDTO)."""

    leather_type: Optional[str] = None
    thickness: Optional[float] = None
    area: Optional[float] = None
    is_full_hide: Optional[bool] = None
    color: Optional[str] = None
    finish: Optional[str] = None

    @classmethod
    def from_model(cls, model, include_inventory=False, include_supplier=False):
        """Create DTO from model instance.

        Args:
            model: Leather model instance
            include_inventory: Whether to include inventory information
            include_supplier: Whether to include supplier information

        Returns:
            LeatherDTO instance
        """
        dto = super().from_model(model, include_inventory, include_supplier)

        # Add leather-specific properties
        dto.leather_type = model.leather_type if hasattr(model, 'leather_type') else None
        dto.thickness = model.thickness if hasattr(model, 'thickness') else None
        dto.area = model.area if hasattr(model, 'area') else None
        dto.is_full_hide = model.is_full_hide if hasattr(model, 'is_full_hide') else None
        dto.color = model.color if hasattr(model, 'color') else None
        dto.finish = model.finish if hasattr(model, 'finish') else None

        return dto


@dataclass
class HardwareDTO(MaterialDTO):
    """Data Transfer Object for Hardware (extends MaterialDTO)."""

    hardware_type: Optional[str] = None
    hardware_material: Optional[str] = None
    finish: Optional[str] = None
    size: Optional[str] = None

    @classmethod
    def from_model(cls, model, include_inventory=False, include_supplier=False):
        """Create DTO from model instance.

        Args:
            model: Hardware model instance
            include_inventory: Whether to include inventory information
            include_supplier: Whether to include supplier information

        Returns:
            HardwareDTO instance
        """
        dto = super().from_model(model, include_inventory, include_supplier)

        # Add hardware-specific properties
        dto.hardware_type = model.hardware_type if hasattr(model, 'hardware_type') else None
        dto.hardware_material = model.hardware_material if hasattr(model, 'hardware_material') else None
        dto.finish = model.finish if hasattr(model, 'finish') else None
        dto.size = model.size if hasattr(model, 'size') else None

        return dto


@dataclass
class SuppliesDTO(MaterialDTO):
    """Data Transfer Object for Supplies (extends MaterialDTO)."""

    color: Optional[str] = None
    thickness: Optional[str] = None
    material_composition: Optional[str] = None

    @classmethod
    def from_model(cls, model, include_inventory=False, include_supplier=False):
        """Create DTO from model instance.

        Args:
            model: Supplies model instance
            include_inventory: Whether to include inventory information
            include_supplier: Whether to include supplier information

        Returns:
            SuppliesDTO instance
        """
        dto = super().from_model(model, include_inventory, include_supplier)

        # Add supplies-specific properties
        dto.color = model.color if hasattr(model, 'color') else None
        dto.thickness = model.thickness if hasattr(model, 'thickness') else None
        dto.material_composition = model.material_composition if hasattr(model, 'material_composition') else None

        return dto


def create_material_dto(model, include_inventory=False, include_supplier=False):
    """Factory function to create the appropriate DTO for a material.

    Args:
        model: Material model instance
        include_inventory: Whether to include inventory information
        include_supplier: Whether to include supplier information

    Returns:
        MaterialDTO or a subclass instance
    """
    material_type = getattr(model, 'material_type', None)

    if hasattr(model, 'leather_type'):
        return LeatherDTO.from_model(model, include_inventory, include_supplier)
    elif hasattr(model, 'hardware_type'):
        return HardwareDTO.from_model(model, include_inventory, include_supplier)
    elif hasattr(model, 'material_composition'):
        return SuppliesDTO.from_model(model, include_inventory, include_supplier)
    else:
        return MaterialDTO.from_model(model, include_inventory, include_supplier)