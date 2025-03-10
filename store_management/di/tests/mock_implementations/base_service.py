"""
MOCK IMPLEMENTATION FOR TESTING

This is a temporary mock implementation used for testing and development.
Replace with a real implementation in the appropriate services module.

DO NOT USE IN PRODUCTION.
"""


class MockBaseService:
    """Generic mock service for other interfaces."""

    def __init__(self, session=None):
        self.session = session

    def get_all(self):
        """Get all items."""
        return [{"id": 1, "name": "[MOCK] Test Item"}]

    def get_by_id(self, id):
        """Get an item by ID."""
        return {"id": id, "name": f"[MOCK] Test Item {id}"}

    def create(self, data):
        """Create a new item."""
        return {"id": 999, **data, "mock_generated": True}

    def update(self, id, data):
        """Update an item."""
        return {"id": id, **data, "mock_updated": True}

    def delete(self, id):
        """Delete an item."""
        return True