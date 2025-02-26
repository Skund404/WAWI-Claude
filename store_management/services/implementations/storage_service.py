# services/implementations/storage_service.py
"""
Implementation of the storage service interface.
Provides functionality for managing storage locations for leatherworking materials.
"""

import logging
from typing import Any, Dict, List, Optional

from services.interfaces.storage_service import IStorageService

# Configure logger
logger = logging.getLogger(__name__)


class StorageService(IStorageService):
    """Implementation of the storage service interface."""

    def __init__(self):
        """Initialize the storage service."""
        logger.info("StorageService initialized")

    def get_storage_location(self, storage_id: int) -> Dict[str, Any]:
        """
        Get details of a specific storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            Dictionary with storage location details

        Raises:
            NotFoundError: If storage location not found
        """
        logger.debug(f"Get storage location with ID: {storage_id}")

        # Return dummy data for now
        return {
            "id": storage_id,
            "name": f"Storage Location {storage_id}",
            "location": f"Room {storage_id // 10 + 1}, Shelf {storage_id % 10 + 1}",
            "type": "SHELF",
            "capacity": 100,
            "used_capacity": 30,
            "notes": f"Sample storage location {storage_id}"
        }

    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """
        Get all storage locations.

        Returns:
            List of dictionaries with storage location details
        """
        logger.debug("Get all storage locations")

        # Return dummy data for now
        storage_types = ["SHELF", "BIN", "DRAWER", "CABINET", "RACK", "BOX"]
        locations = []

        for i in range(1, 6):
            location = {
                "id": i,
                "name": f"Storage Location {i}",
                "location": f"Room {i // 3 + 1}, Section {i % 3 + 1}",
                "type": storage_types[i % len(storage_types)],
                "capacity": 100,
                "used_capacity": 20 * i,
                "notes": f"Sample storage location {i}"
            }
            locations.append(location)

        logger.info(f"Retrieved {len(locations)} storage locations")
        return locations

    def create_storage_location(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new storage location.

        Args:
            storage_data: Dictionary with storage location data

        Returns:
            Dictionary with created storage location details

        Raises:
            ValidationError: If storage data is invalid
        """
        logger.debug(f"Create storage location with data: {storage_data}")

        # Return dummy data with a new ID
        new_data = {
            "id": 999,
            **storage_data
        }

        logger.info(f"Created storage location: {new_data['id']} - {new_data.get('name', 'Unnamed')}")
        return new_data

    def update_storage_location(self, storage_id: int, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing storage location.

        Args:
            storage_id: ID of the storage location to update
            storage_data: Dictionary with updated storage location data

        Returns:
            Dictionary with updated storage location details

        Raises:
            NotFoundError: If storage location not found
            ValidationError: If storage data is invalid
        """
        logger.debug(f"Update storage location {storage_id} with data: {storage_data}")

        # Get current data and update it
        current = self.get_storage_location(storage_id)
        updated = {**current, **storage_data}

        logger.info(f"Updated storage location: {storage_id}")
        return updated

    def delete_storage_location(self, storage_id: int) -> bool:
        """
        Delete a storage location.

        Args:
            storage_id: ID of the storage location to delete

        Returns:
            True if deletion was successful

        Raises:
            NotFoundError: If storage location not found
        """
        logger.debug(f"Delete storage location with ID: {storage_id}")

        # Pretend it was deleted
        logger.info(f"Deleted storage location: {storage_id}")
        return True

    def assign_item_to_storage(self, storage_id: int, item_id: int, item_type: str) -> Dict[str, Any]:
        """
        Assign an item to a storage location.

        Args:
            storage_id: ID of the storage location
            item_id: ID of the item to assign
            item_type: Type of item ('material', 'tool', etc.)

        Returns:
            Dictionary with storage assignment details

        Raises:
            NotFoundError: If storage location or item not found
            ValidationError: If assignment is not valid
        """
        logger.debug(f"Assign {item_type} {item_id} to storage {storage_id}")

        # Return dummy assignment data
        assignment = {
            "storage_id": storage_id,
            "item_id": item_id,
            "item_type": item_type,
            "assignment_id": 1,
            "date_assigned": "2025-02-26T01:00:00"
        }

        logger.info(f"Assigned {item_type} {item_id} to storage {storage_id}")
        return assignment

    def remove_item_from_storage(self, storage_id: int, item_id: int, item_type: str) -> bool:
        """
        Remove an item from a storage location.

        Args:
            storage_id: ID of the storage location
            item_id: ID of the item to remove
            item_type: Type of item ('material', 'tool', etc.)

        Returns:
            True if removal was successful

        Raises:
            NotFoundError: If storage location or item not found
        """
        logger.debug(f"Remove {item_type} {item_id} from storage {storage_id}")

        # Pretend it was removed
        logger.info(f"Removed {item_type} {item_id} from storage {storage_id}")
        return True

    def get_items_in_storage(self, storage_id: int) -> List[Dict[str, Any]]:
        """
        Get all items in a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            List of dictionaries with item details

        Raises:
            NotFoundError: If storage location not found
        """
        logger.debug(f"Get items in storage {storage_id}")

        # Return dummy items
        items = []
        for i in range(1, 4):
            item = {
                "id": i,
                "name": f"Item {i}",
                "type": ["material", "tool", "hardware"][i % 3],
                "size": 10,
                "quantity": i * 5
            }
            items.append(item)

        logger.info(f"Retrieved {len(items)} items in storage {storage_id}")
        return items

    def get_storage_utilization(self, storage_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get utilization statistics for storage locations.

        Args:
            storage_id: Optional ID to get stats for a specific location

        Returns:
            Dictionary with utilization statistics
        """
        logger.debug(f"Get storage utilization for storage ID: {storage_id}")

        if storage_id:
            # Get utilization for a specific storage location
            storage = self.get_storage_location(storage_id)
            capacity = storage["capacity"]
            used = storage["used_capacity"]

            return {
                "storage_id": storage_id,
                "name": storage["name"],
                "capacity": capacity,
                "used_capacity": used,
                "available_capacity": capacity - used,
                "utilization_percentage": (used / capacity * 100) if capacity > 0 else 0,
                "item_count": 3  # Dummy value
            }
        else:
            # Get overall utilization statistics
            locations = self.get_all_storage_locations()

            total_capacity = sum(loc["capacity"] for loc in locations)
            total_used = sum(loc["used_capacity"] for loc in locations)

            return {
                "total_locations": len(locations),
                "total_capacity": total_capacity,
                "total_used_capacity": total_used,
                "total_available_capacity": total_capacity - total_used,
                "overall_utilization_percentage": (total_used / total_capacity * 100) if total_capacity > 0 else 0
            }