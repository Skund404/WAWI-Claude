"""
MOCK IMPLEMENTATION FOR TESTING

This is a temporary mock implementation used for testing and development.
Replace with a real implementation in the appropriate services module.

DO NOT USE IN PRODUCTION.
"""

from di.tests.mock_implementations.base_service import MockBaseService


class MockInventoryService(MockBaseService):
    """Mock implementation of IInventoryService."""

    def get_low_stock_items(self):
        """Get low stock items."""
        return [
            {
                "id": 1,
                "name": "[MOCK] Low Stock Item 1",
                "quantity": 2,
                "threshold": 5,
                "mock": True
            },
            {
                "id": 2,
                "name": "[MOCK] Low Stock Item 2",
                "quantity": 3,
                "threshold": 10,
                "mock": True
            }
        ]

    def get_inventory_item(self, item_id, item_type=None):
        """Get inventory item by ID and type."""
        return {
            "id": item_id,
            "name": f"[MOCK] Inventory Item {item_id}",
            "type": item_type or "MATERIAL",
            "quantity": 25,
            "location": "Shelf A",
            "mock": True
        }

    def update_inventory_quantity(self, item_id, quantity, item_type=None):
        """Update quantity for an inventory item."""
        return {
            "id": item_id,
            "type": item_type or "MATERIAL",
            "previous_quantity": 25,
            "new_quantity": quantity,
            "mock_updated": True
        }

    def adjust_inventory(self, item_id, adjustment, reason=None, item_type=None):
        """Adjust inventory by a certain amount."""
        return {
            "id": item_id,
            "type": item_type or "MATERIAL",
            "previous_quantity": 25,
            "adjustment": adjustment,
            "new_quantity": 25 + adjustment,
            "reason": reason or "Mock adjustment",
            "mock_updated": True
        }

    def get_inventory_transactions(self, item_id=None, item_type=None,
                                   transaction_type=None, date_from=None, date_to=None):
        """Get inventory transactions with optional filtering."""
        return [
            {
                "id": 1,
                "item_id": item_id or 1,
                "item_type": item_type or "MATERIAL",
                "transaction_type": transaction_type or "ADJUSTMENT",
                "quantity": 5,
                "date": "2025-03-10",
                "mock": True
            },
            {
                "id": 2,
                "item_id": item_id or 1,
                "item_type": item_type or "MATERIAL",
                "transaction_type": transaction_type or "ADJUSTMENT",
                "quantity": -2,
                "date": "2025-03-09",
                "mock": True
            }
        ]

    def get_inventory_summary(self, item_type=None):
        """Get inventory summary with optional filtering by type."""
        return {
            "total_items": 125,
            "total_value": 15650.75,
            "low_stock_count": 12,
            "item_type_counts": {
                "MATERIAL": 75,
                "TOOL": 30,
                "PRODUCT": 20
            },
            "mock": True
        }

    def find_items_by_location(self, location):
        """Find inventory items by storage location."""
        return [
            {
                "id": 1,
                "name": f"[MOCK] Item in {location} 1",
                "type": "MATERIAL",
                "quantity": 10,
                "location": location,
                "mock": True
            },
            {
                "id": 2,
                "name": f"[MOCK] Item in {location} 2",
                "type": "TOOL",
                "quantity": 5,
                "location": location,
                "mock": True
            }
        ]