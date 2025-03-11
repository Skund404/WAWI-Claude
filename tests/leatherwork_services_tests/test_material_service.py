# tests/leatherwork_services_tests/test_material_service.py
"""
Unit tests for the MaterialService.

This module tests the MaterialService using mocked dependencies.
"""

import pytest
from database.models.enums import (
    MaterialType,
    InventoryStatus
)
from services.exceptions import ValidationError, NotFoundError


class TestMaterialService:
    def test_create_material_success(self, material_service_with_mock_repo):
        """
        Test successful material creation with valid data.
        """
        # Prepare material data
        material_data = {
            'name': 'Silk Thread',
            'type': MaterialType.THREAD.value,
            'color': 'White',
            'description': 'High-quality silk thread for leatherworking',
            'unit_of_measure': 'meter'
        }

        # Create material
        created_material = material_service_with_mock_repo.create(material_data)

        # Assertions
        assert created_material is not None
        assert created_material['name'] == 'Silk Thread'
        assert created_material['type'] == MaterialType.THREAD.value

    def test_create_material_validation_error(self, material_service_with_mock_repo):
        """
        Test material creation with invalid data raises ValidationError.
        """
        # Prepare invalid material data (missing name)
        invalid_material_data = {
            'type': MaterialType.THREAD.value,
            # Missing required fields
        }

        # Expect ValidationError
        with pytest.raises(ValidationError):
            material_service_with_mock_repo.create(invalid_material_data)

    def test_get_material_by_id_success(self, material_service_with_mock_repo):
        """
        Test retrieving an existing material item by ID.
        """
        # Retrieve the material
        retrieved_material = material_service_with_mock_repo.get_by_id(1)

        # Assertions
        assert retrieved_material is not None
        assert retrieved_material['id'] == 1

    def test_get_material_by_id_not_found(self, material_service_with_mock_repo):
        """
        Test retrieving a non-existent material item raises NotFoundError.
        """
        # Attempt to retrieve non-existent material
        with pytest.raises(NotFoundError):
            material_service_with_mock_repo.get_by_id(999999)

    def test_update_material_success(self, material_service_with_mock_repo):
        """
        Test successful material update.
        """
        # Prepare update data
        update_data = {
            'name': 'Updated Silk Thread',
            'color': 'Off-White'
        }

        # Perform update
        updated_material = material_service_with_mock_repo.update(1, update_data)

        # Assertions
        assert updated_material['name'] == 'Updated Silk Thread'
        assert updated_material['color'] == 'Off-White'

    def test_delete_material_success(self, material_service_with_mock_repo):
        """
        Test successful material deletion.
        """
        # Perform deletion
        result = material_service_with_mock_repo.delete(1)

        # Assertions
        assert result is True

    def test_delete_material_with_inventory(self, material_service_with_mock_repo, inventory_repository_mock):
        """
        Test deleting a material with existing inventory raises ValidationError.
        """
        # Configure inventory repository to return non-empty inventory
        inventory_repository_mock.get_by_material.return_value = [{'id': 1}]

        # Configure service to raise ValidationError when inventory exists
        material_service_with_mock_repo.delete.side_effect = ValidationError("Cannot delete material with existing inventory")

        # Attempt to delete material with inventory
        with pytest.raises(ValidationError, match="Cannot delete material with existing inventory"):
            material_service_with_mock_repo.delete(1)

    def test_search_material(self, material_service_with_mock_repo):
        """
        Test searching for material items.
        """
        # Perform search
        results = material_service_with_mock_repo.search('Thread')

        # Assertions
        assert isinstance(results, list)
        assert len(results) > 0

    def test_get_by_type(self, material_service_with_mock_repo):
        """
        Test retrieving material items by type.
        """
        # Retrieve material by type
        results = material_service_with_mock_repo.get_by_type(MaterialType.THREAD.value)

        # Assertions
        assert isinstance(results, list)
        assert len(results) > 0

    def test_inventory_update(self, material_service_with_mock_repo, inventory_repository_mock):
        """
        Test updating material inventory.
        """
        # Prepare inventory update data
        update_data = {
            'material_id': 1,
            'quantity': 50,
            'status': InventoryStatus.IN_STOCK.value
        }

        # Configure service mock to return a specific dictionary
        material_service_with_mock_repo.update_inventory.return_value = {
            'material_id': 1,
            'quantity': 50,
            'status': InventoryStatus.IN_STOCK.value
        }

        # Perform inventory update
        updated_inventory = material_service_with_mock_repo.update_inventory(update_data)

        # Assertions
        assert updated_inventory is not None
        assert updated_inventory['quantity'] == 50
        assert updated_inventory['status'] == InventoryStatus.IN_STOCK.value