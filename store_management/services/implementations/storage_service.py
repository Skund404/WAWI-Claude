# services/implementations/storage_service.py
import logging
from typing import Any, Dict, List, Optional, Union

from services.interfaces.storage_service import IStorageService, StorageLocationType, StorageCapacityStatus


class StorageService(IStorageService):
    """Implementation of the Storage Service for managing storage locations and their contents."""

    def __init__(self):
        """Initialize the storage service."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("StorageService initialized")

        # In-memory storage for demonstration purposes
        # In a real implementation, this would use the database
        self._storage_locations = {}
        self._storage_contents = {}

    def create_storage_location(self, name: str, location_type: StorageLocationType,
                                capacity: float, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new storage location.

        Args:
            name: Name of the storage location
            location_type: Type of the storage location
            capacity: Storage capacity
            description: Optional description

        Returns:
            Dict[str, Any]: Created storage location data
        """
        storage_id = f"ST{len(self._storage_locations) + 1:04d}"
        storage_location = {
            "id": storage_id,
            "name": name,
            "type": location_type,
            "capacity": capacity,
            "description": description,
            "used_capacity": 0.0,
        }

        self._storage_locations[storage_id] = storage_location
        self._storage_contents[storage_id] = []

        self.logger.info(f"Created storage location: {name} (ID: {storage_id})")
        return storage_location

    def get_storage_location(self, storage_id: str) -> Optional[Dict[str, Any]]:
        """Get storage location details by ID.

        Args:
            storage_id: ID of the storage location to retrieve

        Returns:
            Optional[Dict[str, Any]]: Storage location data or None if not found
        """
        storage_location = self._storage_locations.get(storage_id)
        if not storage_location:
            self.logger.warning(f"Storage location not found: {storage_id}")
            return None

        return storage_location

    def update_storage_location(self, storage_id: str,
                                updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a storage location.

        Args:
            storage_id: ID of the storage location to update
            updates: Dictionary of fields to update

        Returns:
            Optional[Dict[str, Any]]: Updated storage location data or None if not found
        """
        if storage_id not in self._storage_locations:
            self.logger.warning(f"Cannot update non-existent storage location: {storage_id}")
            return None

        storage = self._storage_locations[storage_id]

        # Update only valid fields
        valid_fields = ["name", "type", "capacity", "description"]
        for field, value in updates.items():
            if field in valid_fields:
                storage[field] = value

        self.logger.info(f"Updated storage location: {storage_id}")
        return storage

    def delete_storage_location(self, storage_id: str) -> bool:
        """Delete a storage location if it exists and is empty.

        Args:
            storage_id: ID of the storage location to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if storage_id not in self._storage_locations:
            self.logger.warning(f"Cannot delete non-existent storage location: {storage_id}")
            return False

        # Check if storage is empty
        if self._storage_contents.get(storage_id, []):
            self.logger.warning(f"Cannot delete non-empty storage location: {storage_id}")
            return False

        # Delete the storage location
        del self._storage_locations[storage_id]
        if storage_id in self._storage_contents:
            del self._storage_contents[storage_id]

        self.logger.info(f"Deleted storage location: {storage_id}")
        return True

    def list_storage_locations(self, location_type: Optional[StorageLocationType] = None) -> List[Dict[str, Any]]:
        """List all storage locations, optionally filtered by type.

        Args:
            location_type: Optional filter by location type

        Returns:
            List[Dict[str, Any]]: List of storage locations
        """
        if location_type:
            return [loc for loc in self._storage_locations.values() if loc["type"] == location_type]
        return list(self._storage_locations.values())

    def add_item_to_storage(self, storage_id: str, item_id: str, item_type: str,
                            quantity: float, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add an item to a storage location.

        Args:
            storage_id: ID of the storage location
            item_id: ID of the item to add
            item_type: Type of the item (e.g., 'PRODUCT', 'MATERIAL')
            quantity: Quantity to add
            metadata: Additional item metadata

        Returns:
            bool: True if successful, False otherwise
        """
        if storage_id not in self._storage_locations:
            self.logger.warning(f"Cannot add item to non-existent storage: {storage_id}")
            return False

        # Add the item to storage
        storage_item = {
            "item_id": item_id,
            "item_type": item_type,
            "quantity": quantity,
            "metadata": metadata or {}
        }

        self._storage_contents.setdefault(storage_id, []).append(storage_item)

        # Update used capacity (simplified calculation)
        self._storage_locations[storage_id]["used_capacity"] += quantity

        self.logger.info(f"Added item {item_id} to storage {storage_id}")
        return True

    def assign_item_to_storage(self, item_id: str, storage_id: str,
                               quantity: Optional[float] = None) -> bool:
        """Assign an item to a storage location.

        Args:
            item_id: ID of the item to assign
            storage_id: ID of the storage location
            quantity: Quantity to assign (if None, assigns all)

        Returns:
            bool: True if successful, False otherwise
        """
        if storage_id not in self._storage_locations:
            self.logger.warning(f"Cannot assign item to non-existent storage: {storage_id}")
            return False

        # This is a simplified implementation - in a real application,
        # you would need to track items in an inventory system and update their location

        # Check if the item already exists in the storage
        storage_contents = self._storage_contents.get(storage_id, [])

        for item in storage_contents:
            if item["item_id"] == item_id:
                # Item already exists in this storage, update quantity if specified
                if quantity is not None:
                    old_quantity = item["quantity"]
                    item["quantity"] = quantity

                    # Update used capacity
                    self._storage_locations[storage_id]["used_capacity"] += (quantity - old_quantity)

                    self.logger.info(f"Updated item {item_id} quantity in storage {storage_id}")
                    return True

        # Item doesn't exist in this storage yet
        # In a real implementation, you'd check if the item exists elsewhere and handle accordingly
        # For this demo, we'll create a new storage entry

        storage_item = {
            "item_id": item_id,
            "item_type": "UNKNOWN",  # In a real implementation, you'd look this up
            "quantity": quantity or 1.0,
            "metadata": {}
        }

        self._storage_contents.setdefault(storage_id, []).append(storage_item)

        # Update used capacity
        self._storage_locations[storage_id]["used_capacity"] += storage_item["quantity"]

        self.logger.info(f"Assigned item {item_id} to storage {storage_id}")
        return True

    def remove_item_from_storage(self, storage_id: str, item_id: str,
                                 quantity: Optional[float] = None) -> bool:
        """Remove an item from a storage location.

        Args:
            storage_id: ID of the storage location
            item_id: ID of the item to remove
            quantity: Quantity to remove (if None, removes all)

        Returns:
            bool: True if successful, False otherwise
        """
        if storage_id not in self._storage_locations:
            self.logger.warning(f"Cannot remove item from non-existent storage: {storage_id}")
            return False

        items = self._storage_contents.get(storage_id, [])
        for i, item in enumerate(items):
            if item["item_id"] == item_id:
                if quantity is None or quantity >= item["quantity"]:
                    # Remove the entire item
                    removed_qty = item["quantity"]
                    items.pop(i)
                else:
                    # Reduce the quantity
                    item["quantity"] -= quantity
                    removed_qty = quantity

                # Update used capacity
                self._storage_locations[storage_id]["used_capacity"] -= removed_qty
                self.logger.info(f"Removed {removed_qty} of item {item_id} from storage {storage_id}")
                return True

        self.logger.warning(f"Item {item_id} not found in storage {storage_id}")
        return False

    def get_storage_contents(self, storage_id: str) -> List[Dict[str, Any]]:
        """Get the contents of a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            List[Dict[str, Any]]: List of items in the storage
        """
        if storage_id not in self._storage_locations:
            self.logger.warning(f"Cannot retrieve contents of non-existent storage: {storage_id}")
            return []

        return self._storage_contents.get(storage_id, [])

    def move_item_between_storage(self, from_storage_id: str, to_storage_id: str,
                                  item_id: str, quantity: float) -> bool:
        """Move an item between storage locations.

        Args:
            from_storage_id: Source storage location ID
            to_storage_id: Destination storage location ID
            item_id: ID of the item to move
            quantity: Quantity to move

        Returns:
            bool: True if successful, False otherwise
        """
        # Check that both storage locations exist
        if from_storage_id not in self._storage_locations:
            self.logger.warning(f"Source storage location not found: {from_storage_id}")
            return False

        if to_storage_id not in self._storage_locations:
            self.logger.warning(f"Destination storage location not found: {to_storage_id}")
            return False

        # Find the item in the source storage
        source_items = self._storage_contents.get(from_storage_id, [])
        found_item = None
        for item in source_items:
            if item["item_id"] == item_id:
                found_item = item
                break

        if not found_item:
            self.logger.warning(f"Item {item_id} not found in source storage {from_storage_id}")
            return False

        if found_item["quantity"] < quantity:
            self.logger.warning(f"Insufficient quantity of item {item_id} in storage {from_storage_id}")
            return False

        # Remove from source storage
        if not self.remove_item_from_storage(from_storage_id, item_id, quantity):
            return False

        # Add to destination storage
        if not self.add_item_to_storage(
                to_storage_id,
                item_id,
                found_item["item_type"],
                quantity,
                found_item.get("metadata")
        ):
            # Rollback the removal if adding fails
            self.add_item_to_storage(
                from_storage_id,
                item_id,
                found_item["item_type"],
                quantity,
                found_item.get("metadata")
            )
            return False

        self.logger.info(f"Moved {quantity} of item {item_id} from {from_storage_id} to {to_storage_id}")
        return True

    def search_items_in_storage(self, query: str, location_type: Optional[StorageLocationType] = None) -> List[
        Dict[str, Any]]:
        """Search for items across all storage locations.

        Args:
            query: Search query string
            location_type: Optional filter by location type

        Returns:
            List[Dict[str, Any]]: List of matching items with their storage information
        """
        results = []

        # Get storage locations to search in
        storage_locations = self.list_storage_locations(location_type)

        for storage in storage_locations:
            storage_id = storage["id"]
            for item in self._storage_contents.get(storage_id, []):
                # Simple string matching on item ID and metadata
                item_matches = query.lower() in item["item_id"].lower()
                metadata_matches = any(
                    query.lower() in str(v).lower()
                    for v in item.get("metadata", {}).values()
                )

                if item_matches or metadata_matches:
                    results.append({
                        "storage_id": storage_id,
                        "storage_name": storage["name"],
                        "item": item
                    })

        return results

    def get_storage_capacity_status(self, storage_id: str) -> Optional[StorageCapacityStatus]:
        """Get the capacity status of a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            Optional[StorageCapacityStatus]: Capacity status or None if storage not found
        """
        if storage_id not in self._storage_locations:
            self.logger.warning(f"Storage location not found: {storage_id}")
            return None

        storage = self._storage_locations[storage_id]
        capacity = storage["capacity"]
        used_capacity = storage["used_capacity"]

        if used_capacity <= 0:
            return StorageCapacityStatus.EMPTY

        utilization = used_capacity / capacity

        if utilization < 0.33:
            return StorageCapacityStatus.PARTIALLY_FILLED
        elif utilization < 0.9:
            return StorageCapacityStatus.NEARLY_FULL
        else:
            return StorageCapacityStatus.FULL