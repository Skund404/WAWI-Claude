# Path: services/implementations/inventory_service.py
"""Inventory Service Implementation for Leatherworking Store Management."""

from typing import Any, Dict, List, Optional

from services.interfaces.material_service import MaterialType
from services.interfaces.inventory_service import IInventoryService
from services.base_service import Service
from database.repositories.material_repository import MaterialRepository
from database.sqlalchemy.core.manager_factory import get_manager


class InventoryService(Service[Any], IInventoryService):
    """
    Inventory Service implementation for managing leatherworking materials and parts.

    This service provides comprehensive methods for tracking and managing
    inventory in the leatherworking store management system.
    """

    def __init__(self, material_repository: Optional[MaterialRepository] = None):
        """
        Initialize the Inventory Service.

        Args:
            material_repository (Optional[MaterialRepository]): Repository for material operations
        """
        self._material_repository = material_repository or get_manager('Material')
        super().__init__()

    def get_material_by_id(self, material_id: int) -> Any:
        """
        Retrieve a material by its ID.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            Any: Material object
        """
        try:
            return self._material_repository.get_by_id(material_id)
        except Exception as e:
            self.logger.error(f"Error retrieving material {material_id}: {str(e)}")
            raise

    def update_material(self, material_id: int, update_data: Dict[str, Any]) -> Any:
        """
        Update an existing material.

        Args:
            material_id (int): ID of the material to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Any: Updated material object
        """
        try:
            return self._material_repository.update(material_id, update_data)
        except Exception as e:
            self.logger.error(f"Error updating material {material_id}: {str(e)}")
            raise

    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material from the system.

        Args:
            material_id (int): ID of the material to delete

        Returns:
            bool: True if deletion was successful
        """
        try:
            self._material_repository.delete(material_id)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting material {material_id}: {str(e)}")
            return False

    def list_materials(
            self,
            filter_criteria: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[Any]:
        """
        List materials with optional filtering and sorting.

        Args:
            filter_criteria (Optional[Dict[str, Any]], optional): Filters to apply
            sort_by (Optional[str], optional): Field to sort by
            limit (Optional[int], optional): Maximum number of results

        Returns:
            List[Any]: List of material objects
        """
        try:
            return self._material_repository.list(
                filter_criteria=filter_criteria,
                sort_by=sort_by,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Error listing materials: {str(e)}")
            return []

    def get_low_stock_materials(self, material_type: Optional[MaterialType] = None) -> List[Any]:
        """
        Retrieve materials with low stock.

        Args:
            material_type (Optional[MaterialType], optional): Filter by specific material type

        Returns:
            List[Any]: List of low stock material objects
        """
        try:
            filter_criteria = {
                "stock_level": {"$lt": 10}  # Adjust threshold as needed
            }
            if material_type:
                filter_criteria["type"] = material_type

            return self.list_materials(filter_criteria)
        except Exception as e:
            self.logger.error(f"Error retrieving low stock materials: {str(e)}")
            return []

    def add_material(self, material_data: Dict[str, Any]) -> Any:
        """
        Add a new material to the inventory.

        Args:
            material_data (Dict[str, Any]): Data for the new material

        Returns:
            Any: Created material object
        """
        try:
            # Validate and set default values
            material_data.setdefault('type', MaterialType.LEATHER)

            # Use repository to create material
            material = self._material_repository.create(material_data)
            return material
        except Exception as e:
            self.logger.error(f"Error adding material: {str(e)}")
            raise


# Export for easier importing
InventoryServiceImpl = InventoryService