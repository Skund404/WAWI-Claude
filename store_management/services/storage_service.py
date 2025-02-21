from typing import List, Optional, Dict, Any
from store_management.database.sqlalchemy.models.storage import Storage
from store_management.database.sqlalchemy.models.product import Product
from store_management.database.sqlalchemy.manager_factory import get_manager


class StorageService:
    """Service for storage and product placement operations"""

    def __init__(self):
        """Initialize with appropriate managers"""
        self.storage_manager = get_manager(Storage)
        self.product_manager = get_manager(Product)

    def assign_product_to_storage(self, product_id: int, storage_id: int) -> bool:
        """Assign a product to a storage location.

        Args:
            product_id: Product ID
            storage_id: Storage location ID

        Returns:
            True if assignment succeeded, False otherwise
        """
        try:
            # Check if product exists
            product = self.product_manager.get(product_id)
            if not product:
                return False

            # Check if storage location exists
            storage = self.storage_manager.get(storage_id)
            if not storage:
                return False

            # Update product with storage location
            self.product_manager.update(product_id, {"storage_id": storage_id})

            return True
        except Exception as e:
            # Log error
            print(f"Error assigning product to storage: {str(e)}")
            return False

    def get_storage_utilization(self) -> List[Dict[str, Any]]:
        """Get utilization metrics for all storage locations.

        Returns:
            List of dictionaries with utilization metrics
        """
        try:
            utilization = []
            storage_locations = self.storage_manager.get_all()

            for storage in storage_locations:
                # Get products in this storage location
                products = self.product_manager.filter_by(storage_id=storage.id)

                # Calculate capacity and utilization
                product_count = len(products)
                capacity = storage.capacity or 0
                used_space = sum(1 for _ in products)  # Simple count, could be more complex
                utilization_percent = (used_space / capacity * 100) if capacity > 0 else 0

                utilization.append({
                    "id": storage.id,
                    "location": storage.location,
                    "capacity": capacity,
                    "used_space": used_space,
                    "available_space": capacity - used_space,
                    "utilization_percent": utilization_percent,
                    "product_count": product_count
                })

            return utilization
        except Exception as e:
            # Log error and return empty list
            print(f"Error getting storage utilization: {str(e)}")
            return []

    def create_storage_location(self, data: Dict[str, Any]) -> Optional[Storage]:
        """Create a new storage location.

        Args:
            data: Storage location data

        Returns:
            Created storage location or None if failed
        """
        try:
            # Validate required fields
            if 'location' not in data:
                return None

            # Create storage location
            storage = self.storage_manager.create(data)

            return storage
        except Exception as e:
            # Log error
            print(f"Error creating storage location: {str(e)}")
            return None