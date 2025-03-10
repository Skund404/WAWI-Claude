from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class PatternComponentDTO:
    """Data Transfer Object for Pattern-Component relationship."""

    component_id: int
    pattern_id: int
    quantity: Optional[int] = 1
    component_name: Optional[str] = None
    component_type: Optional[str] = None

    @classmethod
    def from_relationship(cls, relationship, include_component_details=False):
        """Create DTO from a pattern-component relationship."""
        dto = cls(
            component_id=relationship.component_id,
            pattern_id=relationship.pattern_id,
            quantity=getattr(relationship, 'quantity', 1)
        )

        # Add component details if requested
        if include_component_details and hasattr(relationship, 'component') and relationship.component:
            dto.component_name = relationship.component.name
            dto.component_type = relationship.component.component_type

        return dto


@dataclass
class PatternDTO:
    """Data Transfer Object for Pattern."""

    id: int
    name: str
    description: Optional[str] = None
    skill_level: Optional[str] = None
    project_type: Optional[str] = None
    version: Optional[str] = None
    designer: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Optional related data
    components: Optional[List[Dict[str, Any]]] = None
    products: Optional[List[Dict[str, Any]]] = None
    material_requirements: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_model(cls, model, include_components=False, include_products=False, include_materials=False):
        """Create DTO from model instance.

        Args:
            model: Pattern model instance
            include_components: Whether to include component information
            include_products: Whether to include product information
            include_materials: Whether to include material requirements

        Returns:
            PatternDTO instance
        """
        dto = cls(
            id=model.id,
            name=model.name,
            description=getattr(model, 'description', None),
            skill_level=getattr(model, 'skill_level', None),
            project_type=getattr(model, 'project_type', None),
            version=getattr(model, 'version', None),
            designer=getattr(model, 'designer', None),
            created_at=getattr(model, 'created_at', None),
            updated_at=getattr(model, 'updated_at', None)
        )

        # Add components if requested
        if include_components and hasattr(model, 'components') and model.components:
            dto.components = []
            for component_relationship in model.components:
                component = getattr(component_relationship, 'component', None)
                if component:
                    dto.components.append({
                        'id': component.id,
                        'name': component.name,
                        'component_type': getattr(component, 'component_type', None),
                        'description': getattr(component, 'description', None),
                        'quantity': getattr(component_relationship, 'quantity', 1)
                    })

        # Add products if requested
        if include_products and hasattr(model, 'products') and model.products:
            dto.products = []
            for product in model.products:
                dto.products.append({
                    'id': product.id,
                    'name': product.name,
                    'description': getattr(product, 'description', None),
                    'price': getattr(product, 'price', None)
                })

        # Add material requirements if requested
        if include_materials and hasattr(model, 'components') and model.components:
            material_map = {}  # Used to combine quantities for the same material

            for component_relationship in model.components:
                component = getattr(component_relationship, 'component', None)
                component_quantity = getattr(component_relationship, 'quantity', 1)

                if component and hasattr(component, 'materials') and component.materials:
                    for material_relationship in component.materials:
                        material = getattr(material_relationship, 'material', None)
                        material_quantity = getattr(material_relationship, 'quantity', 0)

                        if material:
                            # Calculate total quantity needed
                            total_quantity = component_quantity * material_quantity

                            # Group by material ID
                            material_id = material.id
                            if material_id not in material_map:
                                material_map[material_id] = {
                                    'id': material_id,
                                    'name': material.name,
                                    'material_type': getattr(material, 'material_type', None),
                                    'unit': getattr(material, 'unit', None),
                                    'quantity': 0
                                }

                            # Add quantity to existing entry
                            material_map[material_id]['quantity'] += total_quantity

            # Convert map to list
            dto.material_requirements = list(material_map.values())

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}