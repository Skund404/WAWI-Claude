# services/implementations/material_service_debug.py
"""
Simplified debug version of the material service implementation to help identify issues.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from services.interfaces.material_service import IMaterialService, MaterialType

# Configure logger
logger = logging.getLogger(__name__)


class MaterialService(IMaterialService):
    """Simplified implementation of the material service interface for debugging."""

    def __init__(self):
        """Initialize the Material Service."""
        logger.info("Debug MaterialService initialized")

    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material."""
        logger.debug(f"Debug create_material called with: {material_data}")
        return {"id": 1, "name": "Debug Material", **material_data}

    def get_material(self, material_id: Union[int, str]) -> Dict[str, Any]:
        """Get a material by ID."""
        logger.debug(f"Debug get_material called with ID: {material_id}")
        return {"id": material_id, "name": f"Debug Material {material_id}"}

    def update_material(self, material_id: Union[int, str], material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a material."""
        logger.debug(f"Debug update_material called with ID: {material_id}, data: {material_data}")
        return {"id": material_id, "name": f"Updated Debug Material {material_id}", **material_data}

    def delete_material(self, material_id: Union[int, str]) -> bool:
        """Delete a material."""
        logger.debug(f"Debug delete_material called with ID: {material_id}")
        return True

    def list_materials(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """List all materials, optionally filtered by type."""
        logger.debug(f"Debug list_materials called with type: {material_type}")

        # Return some dummy data
        materials = []
        for i in range(1, 6):
            material = {
                "id": i,
                "name": f"Debug Leather {i}",
                "material_type": MaterialType.LEATHER.value,
                "color": f"Color {i}",
                "thickness": 1.0 + (i * 0.5),
                "size": 10 + i,
                "quantity": 5 * i,
                "cost_per_unit": 10.0 + i,
                "supplier_code": f"SUP-{i:03d}"
            }
            materials.append(material)

        # Filter by type if specified
        if material_type:
            materials = [m for m in materials if m["material_type"] == material_type.value]

        return materials

    def search_materials(self, query: str) -> List[Dict[str, Any]]:
        """Search for materials."""
        logger.debug(f"Debug search_materials called with query: {query}")
        materials = self.list_materials()
        return [m for m in materials if query.lower() in m["name"].lower()]

    def get_material_inventory(self, material_id: Union[int, str]) -> Dict[str, Any]:
        """Get inventory for a material."""
        logger.debug(f"Debug get_material_inventory called with ID: {material_id}")
        return {
            "material_id": material_id,
            "current_quantity": 10,
            "last_updated": "2025-02-26T01:00:00",
            "transactions": []
        }

    def update_material_inventory(self, material_id: Union[int, str], quantity_change: float,
                                  notes: Optional[str] = None) -> Dict[str, Any]:
        """Update inventory for a material."""
        logger.debug(f"Debug update_material_inventory called with ID: {material_id}, change: {quantity_change}")
        return {
            "material_id": material_id,
            "current_quantity": 10 + quantity_change,
            "last_updated": "2025-02-26T01:00:00",
            "transactions": []
        }

    def get_low_stock_materials(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get materials with low stock."""
        logger.debug(f"Debug get_low_stock_materials called with threshold: {threshold}")
        materials = self.list_materials()
        return [m for m in materials if m["quantity"] < (threshold or 5)]