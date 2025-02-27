# store_management/services/implementations/inventory_service.py
"""
Inventory Service Implementation for Leatherworking Store Management.

Provides concrete implementation of inventory-related operations.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from services.base_service import Service
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import MaterialType
from database.repositories.inventory_repository import InventoryRepository
from database.sqlalchemy.core.manager_factory import get_manager
from database.models.inventory import Inventory

class InventoryService(Service[Dict[str, Any]], IInventoryService):
    """
    Concrete implementation of the Inventory Service.

    Manages inventory-related operations for leatherworking materials and products.
    """

    def __init__(self, inventory_repository: Optional[InventoryRepository] = None):
        """
        Initialize the Inventory Service.

        Args:
            inventory_repository (Optional[InventoryRepository]): Repository for inventory operations
        """
        self._repository = inventory_repository or get_manager(Inventory)
        self._logger = logging.getLogger(__name__)

    def get_by_id(
            self,
            id_value: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an inventory item by its unique identifier.

        Args:
            id_value (str): Unique identifier for the inventory item

        Returns:
            Optional[Dict[str, Any]]: Retrieved inventory item or None if not found
        """
        try:
            self.log_operation("Retrieving inventory item", {"id": id_value})

            # Use repository to fetch the item
            item = self._repository.get_by_id(id_value)

            if item:
                self._logger.info(f"Successfully retrieved inventory item {id_value}")
                return self._convert_to_dict(item)

            self._logger.warning(f"No inventory item found with ID {id_value}")
            return None
        except Exception as e:
            self._logger.error(f"Error retrieving inventory item {id_value}: {e}")
            raise

    def get_all(
            self,
            filters: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all inventory items, with optional filtering and pagination.

        Args:
            filters (Optional[Dict[str, Any]], optional): Filtering criteria
            limit (Optional[int], optional): Maximum number of items to retrieve
            offset (Optional[int], optional): Number of items to skip

        Returns:
            List[Dict[str, Any]]: List of retrieved inventory items
        """
        try:
            self.log_operation("Retrieving inventory items", {
                "filters": filters,
                "limit": limit,
                "offset": offset
            })

            # Use repository to fetch items
            items = self._repository.search(
                filter_criteria=filters or {},
                limit=limit,
                offset=offset
            )

            # Convert items to dictionaries
            inventory_items = [self._convert_to_dict(item) for item in items]

            self._logger.info(f"Retrieved {len(inventory_items)} inventory items")
            return inventory_items
        except Exception as e:
            self._logger.error(f"Error retrieving inventory items: {e}")
            raise

    def create(
            self,
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new inventory item.

        Args:
            data (Dict[str, Any]): Data for creating the inventory item

        Returns:
            Dict[str, Any]: Created inventory item
        """
        try:
            # Validate required fields
            self.validate_data(data, [
                'material_type',
                'quantity',
                'unit_of_measurement'
            ])

            # Add timestamp
            data['created_at'] = datetime.now()

            self.log_operation("Creating inventory item", {"data": data})

            # Use repository to create item
            created_item = self._repository.create(**data)

            # Convert and return
            inventory_item = self._convert_to_dict(created_item)

            self._logger.info(f"Created inventory item: {inventory_item}")
            return inventory_item
        except Exception as e:
            self._logger.error(f"Error creating inventory item: {e}")
            raise

    def update(
            self,
            id_value: str,
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing inventory item.

        Args:
            id_value (str): Unique identifier of the inventory item to update
            data (Dict[str, Any]): Updated data

        Returns:
            Dict[str, Any]: Updated inventory item
        """
        try:
            # Add update timestamp
            data['updated_at'] = datetime.now()

            self.log_operation("Updating inventory item", {
                "id": id_value,
                "data": data
            })

            # Use repository to update item
            updated_item = self._repository.update(id_value, **data)

            # Convert and return
            inventory_item = self._convert_to_dict(updated_item)

            self._logger.info(f"Updated inventory item {id_value}")
            return inventory_item
        except Exception as e:
            self._logger.error(f"Error updating inventory item {id_value}: {e}")
            raise

    def delete(
            self,
            id_value: str
    ) -> bool:
        """
        Delete an inventory item.

        Args:
            id_value (str): Unique identifier of the inventory item to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.log_operation("Deleting inventory item", {"id": id_value})

            # Use repository to delete item
            self._repository.delete(id_value)

            self._logger.info(f"Deleted inventory item {id_value}")
            return True
        except Exception as e:
            self._logger.error(f"Error deleting inventory item {id_value}: {e}")
            return False

    def get_low_stock_items(
            self,
            threshold: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve items with stock below a specified threshold.

        Args:
            threshold (float, optional): Minimum stock level. Defaults to 10.0.

        Returns:
            List[Dict[str, Any]]: List of low stock items
        """
        try:
            self.log_operation("Retrieving low stock items", {"threshold": threshold})

            # Use repository to find low stock items
            low_stock_items = self._repository.search(
                filter_criteria={'quantity__lt': threshold}
            )

            # Convert items to dictionaries
            inventory_items = [self._convert_to_dict(item) for item in low_stock_items]

            self._logger.info(f"Found {len(inventory_items)} low stock items")
            return inventory_items
        except Exception as e:
            self._logger.error(f"Error retrieving low stock items: {e}")
            return []

    def adjust_stock(
            self,
            item_id: str,
            quantity_change: float,
            reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adjust the stock of an inventory item.

        Args:
            item_id (str): Unique identifier of the inventory item
            quantity_change (float): Amount to add or subtract from current stock
            reason (Optional[str], optional): Reason for stock adjustment

        Returns:
            Dict[str, Any]: Updated inventory item
        """
        try:
            self.log_operation("Adjusting stock", {
                "item_id": item_id,
                "quantity_change": quantity_change,
                "reason": reason
            })

            # Retrieve current item
            current_item = self._repository.get_by_id(item_id)

            if not current_item:
                raise ValueError(f"Inventory item {item_id} not found")

            # Calculate new quantity
            current_quantity = getattr(current_item, 'quantity', 0)
            new_quantity = current_quantity + quantity_change

            # Update with new quantity and track adjustment
            update_data = {
                'quantity': new_quantity,
                'last_adjusted_at': datetime.now(),
                'last_adjustment_reason': reason
            }

            # Use repository to update
            updated_item = self._repository.update(item_id, **update_data)

            # Convert and return
            inventory_item = self._convert_to_dict(updated_item)

            self._logger.info(f"Adjusted stock for item {item_id}: {quantity_change}")
            return inventory_item
        except Exception as e:
            self._logger.error(f"Error adjusting stock for item {item_id}: {e}")
            raise

    def get_stock_by_material_type(
            self,
            material_type: MaterialType
    ) -> List[Dict[str, Any]]:
        """
        Retrieve inventory items of a specific material type.

        Args:
            material_type (MaterialType): Type of material to filter by

        Returns:
            List[Dict[str, Any]]: List of inventory items of the specified type
        """
        try:
            self.log_operation("Retrieving stock by material type", {
                "material_type": material_type
            })

            # Use repository to find items by material type
            items = self._repository.search(
                filter_criteria={'material_type': material_type}
            )

            # Convert items to dictionaries
            inventory_items = [self._convert_to_dict(item) for item in items]

            self._logger.info(f"Found {len(inventory_items)} items of type {material_type}")
            return inventory_items
        except Exception as e:
            self._logger.error(f"Error retrieving stock for material type {material_type}: {e}")
            return []

    def _convert_to_dict(self, item: Any) -> Dict[str, Any]:
        """
        Convert an inventory item to a dictionary representation.

        Args:
            item (Any): Inventory item to convert

        Returns:
            Dict[str, Any]: Dictionary representation of the item
        """
        try:
            # If item is already a dictionary, return it
            if isinstance(item, dict):
                return item

            # Convert SQLAlchemy model to dictionary
            return {
                'id': getattr(item, 'id', None),
                'material_type': getattr(item, 'material_type', None),
                'quantity': getattr(item, 'quantity', 0),
                'unit_of_measurement': getattr(item, 'unit_of_measurement', None),
                'created_at': getattr(item, 'created_at', None),
                'updated_at': getattr(item, 'updated_at', None)
            }
        except Exception as e:
            self._logger.error(f"Error converting item to dictionary: {e}")
            return {}