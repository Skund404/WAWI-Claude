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

    def create_storage_location(self, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new storage location.

        Args:
            storage_data: Dictionary with storage location data

        Returns:
            Dict[str, Any]: Created storage location data
        """
        self.logger.info("Creating new storage location")

        # Generate ID if none provided
        if 'id' not in storage_data:
            storage_data['id'] = len(self._storage_locations) + 1

        # Convert type to enum if provided as string
        if 'location_type' in storage_data and isinstance(storage_data['location_type'], str):
            try:
                storage_data['location_type'] = StorageLocationType[storage_data['location_type']]
            except KeyError:
                storage_data['location_type'] = StorageLocationType.OTHER

        # Add to storage
        self._storage_locations.append(storage_data)

        return storage_data

    def get_storage_location(self, location_id: int) -> Optional[Dict[str, Any]]:
        """Get a storage location by ID.

        Args:
            location_id: ID of the storage location to retrieve

        Returns:
            Optional[Dict[str, Any]]: Storage location data or None if not found
        """
        self.logger.info(f"Getting storage location with ID {location_id}")

        # Find storage location
        for location in self._storage_locations:
            if location['id'] == location_id:
                return location

        return None

    def update_storage_location(self, location_id: int, storage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing storage location.

        Args:
            location_id: ID of the storage location to update
            storage_data: Updated storage location data

        Returns:
            Dict[str, Any]: Updated storage location data
        """
        self.logger.info(f"Updating storage location with ID {location_id}")

        # Find storage location
        for i, location in enumerate(self._storage_locations):
            if location['id'] == location_id:
                # Update data
                self._storage_locations[i].update(storage_data)
                return self._storage_locations[i]

        # If not found, create new
        storage_data['id'] = location_id
        return self.create_storage_location(storage_data)

    def delete_storage_location(self, location_id: int) -> bool:
        """Delete a storage location.

        Args:
            location_id: ID of the storage location to delete

        Returns:
            bool: True if deleted, False if not found
        """
        self.logger.info(f"Deleting storage location with ID {location_id}")

        # Find storage location
        for i, location in enumerate(self._storage_locations):
            if location['id'] == location_id:
                # Remove from storage
                self._storage_locations.pop(i)
                return True

        return False

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

    def assign_product_to_storage(self, product_id: int, storage_id: int, quantity: int = 1) -> bool:
        """Assign a product to a storage location.

        Args:
            product_id: ID of the product to assign
            storage_id: ID of the storage location
            quantity: Quantity to assign

        Returns:
            bool: True if successful
        """
        self.logger.info(f"Assigning product {product_id} to storage {storage_id}")

        # Check if storage location exists
        storage_location = self.get_storage_location(storage_id)
        if not storage_location:
            return False

        # Add product to storage
        if 'products' not in storage_location:
            storage_location['products'] = []

        # Check if product already in storage
        for i, item in enumerate(storage_location['products']):
            if item.get('product_id') == product_id:
                # Update quantity
                storage_location['products'][i]['quantity'] += quantity
                return True

        # Add new product entry
        storage_location['products'].append({
            'product_id': product_id,
            'quantity': quantity
        })

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

    def get_all_storage_locations(self, location_type: Optional[Union[StorageLocationType, str]] = None) -> List[
        Dict[str, Any]]:
        """Get all storage locations, optionally filtered by type.

        Args:
            location_type: Optional location type to filter by

        Returns:
            List[Dict[str, Any]]: List of storage locations
        """
        self.logger.info("Getting all storage locations")

        # Convert string type to enum if needed
        if isinstance(location_type, str):
            try:
                location_type = StorageLocationType[location_type]
            except KeyError:
                location_type = None

        # Filter by type if specified
        if location_type is not None:
            return [loc for loc in self._storage_locations
                    if loc.get('location_type') == location_type]

        return self._storage_locations

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

    def get_storage_capacity_status(self, storage_id: int) -> StorageCapacityStatus:
        """Get the capacity status of a storage location.

        Args:
            storage_id: ID of the storage location

        Returns:
            StorageCapacityStatus: Capacity status
        """
        self.logger.info(f"Getting capacity status for storage {storage_id}")

        # Get storage location
        storage_location = self.get_storage_location(storage_id)
        if not storage_location:
            return StorageCapacityStatus.EMPTY

        # Check if products exist
        if 'products' not in storage_location or not storage_location['products']:
            return StorageCapacityStatus.EMPTY

        # Get capacity information
        capacity = storage_location.get('capacity', 100)
        used_capacity = sum(item.get('quantity', 0) for item in storage_location['products'])
        percentage = (used_capacity / capacity) * 100

        # Determine status
        if percentage < 30:
            return StorageCapacityStatus.EMPTY
        elif percentage < 70:
            return StorageCapacityStatus.PARTIALLY_FILLED
        elif percentage < 90:
            return StorageCapacityStatus.NEARLY_FULL
        else:
            return StorageCapacityStatus.FULL