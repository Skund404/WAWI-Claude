"""
MOCK IMPLEMENTATION FOR TESTING

This is a temporary mock implementation used for testing and development.
Replace with a real implementation in the appropriate services module.

DO NOT USE IN PRODUCTION.
"""

from di.tests.mock_implementations.base_service import MockBaseService


class MockToolListService:
    """Mock implementation of IToolListService."""

    def __init__(self, session=None):
        self.session = session

    def get_by_id(self, tool_list_id):
        """Retrieve a tool list by its ID."""
        return {"id": tool_list_id, "project_id": 1, "status": "PENDING", "mock": True}

    def get_all(self, filters=None):
        """Retrieve all tool lists with optional filtering."""
        return [
            {"id": 1, "project_id": 1, "status": "PENDING", "mock": True},
            {"id": 2, "project_id": 2, "status": "COMPLETED", "mock": True}
        ]

    def create_for_project(self, project_id, notes=None):
        """Create a new tool list for a project."""
        return {
            "id": 999,
            "project_id": project_id,
            "status": "PENDING",
            "notes": notes,
            "mock_generated": True
        }

    def update(self, tool_list_id, tool_list_data):
        """Update an existing tool list."""
        return {"id": tool_list_id, **tool_list_data, "mock_updated": True}

    def delete(self, tool_list_id):
        """Delete a tool list by its ID."""
        return True

    def get_by_project(self, project_id):
        """Get tool lists for a specific project."""
        return [{"id": 1, "project_id": project_id, "status": "PENDING", "mock": True}]

    def get_tool_list_items(self, tool_list_id):
        """Get all items in a tool list."""
        return [
            {"id": 1, "tool_list_id": tool_list_id, "tool_id": 1, "quantity": 2, "mock": True},
            {"id": 2, "tool_list_id": tool_list_id, "tool_id": 2, "quantity": 1, "mock": True}
        ]

    def add_tool(self, tool_list_id, tool_id, quantity=1):
        """Add a tool to a tool list."""
        return {
            "id": 999,
            "tool_list_id": tool_list_id,
            "tool_id": tool_id,
            "quantity": quantity,
            "mock_generated": True
        }

    def remove_tool(self, tool_list_id, tool_item_id):
        """Remove a tool from a tool list."""
        return True

    def update_tool_quantity(self, tool_list_id, tool_item_id, quantity):
        """Update the quantity of a tool in a tool list."""
        return {
            "id": tool_item_id,
            "tool_list_id": tool_list_id,
            "quantity": quantity,
            "mock_updated": True
        }

    def allocate_tools(self, tool_list_id, allocate_all=False, tool_item_ids=None):
        """Allocate tools from inventory to a tool list."""
        return {"success": True, "allocated": 3, "mock": True}

    def return_tools(self, tool_list_id, return_all=False, tool_item_ids=None, condition_notes=None):
        """Return allocated tools to inventory."""
        return {"success": True, "returned": 3, "mock": True}

    def complete_tool_list(self, tool_list_id, notes=None):
        """Mark a tool list as complete."""
        return {"id": tool_list_id, "status": "COMPLETED", "notes": notes, "mock_updated": True}

    def cancel_tool_list(self, tool_list_id, reason):
        """Cancel a tool list."""
        return {"id": tool_list_id, "status": "CANCELLED", "notes": reason, "mock_updated": True}

    def validate_tool_availability(self, tool_list_id):
        """Validate that sufficient tools are available for a tool list."""
        return {"available": True, "missing": [], "mock": True}
