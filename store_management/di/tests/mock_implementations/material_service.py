"""
MOCK IMPLEMENTATION FOR TESTING

This is a temporary mock implementation used for testing and development.
Replace with a real implementation in the appropriate services module.

DO NOT USE IN PRODUCTION.
"""

from di.tests.mock_implementations.base_service import MockBaseService


class MockMaterialService(MockBaseService):
    """Mock implementation of IMaterialService."""

    def get_material(self, material_id):
        """Get material by ID."""
        return {
            "id": material_id,
            "name": f"[MOCK] Test Material {material_id}",
            "type": "LEATHER",
            "unit_price": 15.99,
            "mock": True
        }

    def get_all_materials(self, filters=None):
        """Get all materials."""
        return [
            {
                "id": 1,
                "name": "[MOCK] Test Leather",
                "type": "LEATHER",
                "unit_price": 15.99,
                "mock": True
            },
            {
                "id": 2,
                "name": "[MOCK] Test Hardware",
                "type": "HARDWARE",
                "unit_price": 5.99,
                "mock": True
            }
        ]

    def create_material(self, material_data):
        """Create a new material."""
        return {"id": 999, **material_data, "mock_generated": True}

    def update_material(self, material_id, material_data):
        """Update a material."""
        return {"id": material_id, **material_data, "mock_updated": True}

    def delete_material(self, material_id):
        """Delete a material."""
        return True

    def get_materials_by_type(self, material_type):
        """Get materials by type."""
        return [
            {
                "id": 1,
                "name": f"[MOCK] Test {material_type} 1",
                "type": material_type,
                "unit_price": 15.99,
                "mock": True
            },
            {
                "id": 2,
                "name": f"[MOCK] Test {material_type} 2",
                "type": material_type,
                "unit_price": 25.99,
                "mock": True
            }
        ]

    def get_materials_by_supplier(self, supplier_id):
        """Get materials by supplier."""
        return [
            {
                "id": 1,
                "name": "[MOCK] Supplier Material 1",
                "type": "LEATHER",
                "supplier_id": supplier_id,
                "unit_price": 15.99,
                "mock": True
            },
            {
                "id": 2,
                "name": "[MOCK] Supplier Material 2",
                "type": "HARDWARE",
                "supplier_id": supplier_id,
                "unit_price": 5.99,
                "mock": True
            }
        ]

    def update_inventory(self, material_id, quantity):
        """Update inventory for a material."""
        return {
            "material_id": material_id,
            "quantity": quantity,
            "previous_quantity": quantity - 5,
            "mock_updated": True
        }