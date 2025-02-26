# services/implementations/material_service.py
"""
Implementation of the MaterialService interface. Provides functionality
for managing materials in the leatherworking store.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from services.interfaces.material_service import IMaterialService, MaterialType

# Configure logger
logger = logging.getLogger(__name__)


class MaterialService(IMaterialService):
    """Implementation of the material service interface."""

    def __init__(self):
        """
        Initialize the Material Service.
        """
        logger.info("MaterialService initialized")

    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new material.

        Args:
            material_data: Dictionary with material properties

        Returns:
            Dictionary representing the created material

        Raises:
            ValidationError: If material data is invalid
        """
        try:
            logger.debug(f"Creating material with data: {material_data}")

            # Return dummy data for now
            return {"id": 1, "name": "Dummy Material", **material_data}
        except Exception as e:
            logger.error(f"Error creating material: {str(e)}")
            raise

    def get_material(self, material_id: Union[int, str]) -> Dict[str, Any]:
        """
        Retrieve a material by ID.

        Args:
            material_id: ID of the material to retrieve

        Returns:
            Dictionary representing the material

        Raises:
            NotFoundError: If material is not found
        """
        try:
            logger.debug(f"Getting material with ID: {material_id}")

            # Return dummy data for now
            return {
                "id": material_id,
                "name": f"Dummy Material {material_id}",
                "material_type": MaterialType.LEATHER.value,
                "color": "Brown",
                "thickness": 1.5,
                "size": 10,
                "quantity": 5,
                "cost_per_unit": 15.0,
                "supplier_code": "SUP-001"
            }
        except Exception as e:
            logger.error(f"Error getting material: {str(e)}")
            raise

    def update_material(self, material_id: Union[int, str], material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing material.

        Args:
            material_id: ID of the material to update
            material_data: Dictionary with updated material properties

        Returns:
            Dictionary representing the updated material

        Raises:
            NotFoundError: If material is not found
            ValidationError: If material data is invalid
        """
        try:
            logger.debug(f"Updating material {material_id} with data: {material_data}")

            # Return dummy data for now
            return {"id": material_id, **material_data}
        except Exception as e:
            logger.error(f"Error updating material: {str(e)}")
            raise

    def delete_material(self, material_id: Union[int, str]) -> bool:
        """
        Delete a material.

        Args:
            material_id: ID of the material to delete

        Returns:
            True if deletion was successful

        Raises:
            NotFoundError: If material is not found
        """
        try:
            logger.debug(f"Deleting material with ID: {material_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting material: {str(e)}")
            raise

    def list_materials(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """
        List all materials, optionally filtered by type.

        Args:
            material_type: Optional filter for material type

        Returns:
            List of dictionaries representing materials
        """
        try:
            logger.debug(f"Listing materials with type filter: {material_type}")

            # Return dummy data for now
            materials = []
            for i in range(1, 6):
                material = {
                    "id": i,
                    "name": f"Dummy Leather {i}",
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

            logger.info(f"Listed {len(materials)} materials")
            return materials
        except Exception as e:
            logger.error(f"Error listing materials: {str(e)}")
            # Return empty list instead of raising to avoid UI disruption
            return []

    def search_materials(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for materials by name or description.

        Args:
            query: Search query string

        Returns:
            List of dictionaries representing matching materials
        """
        try:
            logger.debug(f"Searching materials with query: {query}")

            # Get all materials and filter by query
            materials = self.list_materials()
            filtered = [m for m in materials if query.lower() in m["name"].lower()]

            logger.info(f"Found {len(filtered)} materials matching '{query}'")
            return filtered
        except Exception as e:
            logger.error(f"Error searching materials: {str(e)}")
            return []

    def get_material_inventory(self, material_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get inventory information for a material.

        Args:
            material_id: ID of the material

        Returns:
            Dictionary with inventory information

        Raises:
            NotFoundError: If material is not found
        """
        try:
            logger.debug(f"Getting inventory for material ID: {material_id}")

            # Return dummy data for now
            return {
                "material_id": material_id,
                "current_quantity": 10,
                "last_updated": datetime.now().isoformat(),
                "transactions": []
            }
        except Exception as e:
            logger.error(f"Error getting material inventory: {str(e)}")
            raise

    def update_material_inventory(self,
                                  material_id: Union[int, str],
                                  quantity_change: float,
                                  notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Update inventory quantities for a material.

        Args:
            material_id: ID of the material
            quantity_change: Amount to add (positive) or remove (negative)
            notes: Optional notes about the inventory change

        Returns:
            Dictionary with updated inventory information

        Raises:
            NotFoundError: If material is not found
            ValidationError: If quantity change is invalid
        """
        try:
            logger.debug(f"Updating inventory for material {material_id}: {quantity_change}")

            # Return dummy data for now
            return {
                "material_id": material_id,
                "current_quantity": 10 + quantity_change,
                "last_updated": datetime.now().isoformat(),
                "transactions": []
            }
        except Exception as e:
            logger.error(f"Error updating material inventory: {str(e)}")
            raise

    def get_low_stock_materials(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get a list of materials with low stock levels.

        Args:
            threshold: Optional custom threshold for low stock

        Returns:
            List of dictionaries representing low stock materials
        """
        try:
            logger.debug(f"Getting low stock materials with threshold: {threshold}")

            # Get all materials and filter for low stock
            materials = self.list_materials()
            low_stock = [m for m in materials if m["quantity"] < (threshold or 5)]

            logger.info(f"Found {len(low_stock)} materials with low stock")
            return low_stock
        except Exception as e:
            logger.error(f"Error getting low stock materials: {str(e)}")
            return []