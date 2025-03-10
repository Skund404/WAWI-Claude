from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ComponentMaterialDTO:
    """Data Transfer Object for Component-Material relationship."""

    component_id: int
    material_id: int
    quantity: float
    material_name: Optional[str] = None
    material_type: Optional[str] = None
    unit: Optional[str] = None
    cost: Optional[float] = None

    @classmethod
    def from_relationship(cls, relationship, include_material_details=False):
        """Create DTO from component-material relationship."""
        dto = cls(
            component_id=relationship.component_id,
            material_id=relationship.material_id,
            quantity=relationship.quantity
        )

        # Add material details if requested
        if include_material_details and hasattr(relationship, 'material') and relationship.material:
            material = relationship.material
            dto.material_name = material.name
            dto.material_type = getattr(material, 'material_type', None)
            dto.unit = getattr(material, 'unit', None)
            dto.cost = getattr(material, 'cost_price', None)

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ComponentDTO:
    """Data Transfer Object for Component."""

    id: int
    name: str
    component_type: str
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Optional related data
    materials: Optional[List[Dict[str, Any]]] = None
    patterns: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_model(cls, model, include_materials=False, include_patterns=False):
        """Create DTO from model instance.

        Args:
            model: Component model instance
            include_materials: Whether to include material information
            include_patterns: Whether to include pattern information

        Returns:
            ComponentDTO instance
        """
        dto = cls(
            id=model.id,
            name=model.name,
            component_type=model.component_type,
            description=getattr(model, 'description', None),
            attributes=getattr(model, 'attributes', {}),
            created_at=getattr(model, 'created_at', None),
            updated_at=getattr(model, 'updated_at', None)
        )

        # Add materials if requested
        if include_materials and hasattr(model, 'materials') and model.materials:
            dto.materials = []
            for material_relationship in model.materials:
                material = getattr(material_relationship, 'material', None)
                if material:
                    material_data = {
                        'id': material.id,
                        'name': material.name,
                        'material_type': getattr(material, 'material_type', None),
                        'unit': getattr(material, 'unit', None),
                        'quantity': getattr(material_relationship, 'quantity', 0),
                        'cost_price': getattr(material, 'cost_price', None),
                        'total_cost': getattr(material, 'cost_price', 0) * getattr(material_relationship, 'quantity', 0)
                    }
                    dto.materials.append(material_data)

        # Add patterns if requested
        if include_patterns and hasattr(model, 'patterns') and model.patterns:
            dto.patterns = []
            for pattern_relationship in model.patterns:
                pattern = getattr(pattern_relationship, 'pattern', None)
                if pattern:
                    pattern_data = {
                        'id': pattern.id,
                        'name': pattern.name,
                        'skill_level': getattr(pattern, 'skill_level', None),
                        'project_type': getattr(pattern, 'project_type', None)
                    }
                    dto.patterns.append(pattern_data)

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}