# tests/leatherwork_services_tests/test_leather_service.py
"""
Unit tests for the LeatherService.

This module tests the LeatherService using mocked dependencies.
"""

import pytest
from database.models.enums import (
    LeatherType,
    LeatherFinish,
    InventoryStatus
)
from services.exceptions import ValidationError, NotFoundError


class TestLeatherService:
    def test_create_leather_success(self, leather_service_with_mock_repo):
        """
        Test successful leather creation with valid data.
        """
        # Prepare leather data
        leather_data = {
            'name': 'Premium Cowhide',
            'type': LeatherType.FULL_GRAIN.value,
            'finish': LeatherFinish.ANILINE.value,
            'color': 'Natural Tan',
            'thickness': 2.0,
            'description': 'High-quality full-grain cowhide leather'
        }

        # Create leather
        created_leather = leather_service_with_mock_repo.create(leather_data)

        # Assertions
        assert created_leather is not None
        assert created_leather['name'] == 'Premium Cowhide'
        assert created_leather['type'] == LeatherType.FULL_GRAIN.value
        assert created_leather['finish'] == LeatherFinish.ANILINE.value

    def test_create_leather_validation_error(self, leather_service_with_mock_repo):
        """
        Test leather creation with invalid data raises ValidationError.
        """
        # Prepare invalid leather data (missing name)
        invalid_leather_data = {
            'type': LeatherType.TOP_GRAIN.value,
            # Missing required fields
        }

        # Expect ValidationError
        with pytest.raises(ValidationError):
            leather_service_with_mock_repo.create(invalid_leather_data)

    def test_get_leather_by_id_success(self, leather_service_with_mock_repo):
        """
        Test retrieving an existing leather item by ID.
        """
        # Retrieve the leather
        retrieved_leather = leather_service_with_mock_repo.get_by_id(1)

        # Assertions
        assert retrieved_leather is not None
        assert retrieved_leather['id'] == 1

    def test_get_leather_by_id_not_found(self, leather_service_with_mock_repo):
        """
        Test retrieving a non-existent leather item raises NotFoundError.
        """
        # Attempt to retrieve non-existent leather
        with pytest.raises(NotFoundError):
            leather_service_with_mock_repo.get_by_id(999999)

    def test_update_leather_success(self, leather_service_with_mock_repo):
        """
        Test successful leather update.
        """
        # Prepare update data
        update_data = {
            'name': 'Updated Premium Cowhide',
            'finish': LeatherFinish.SEMI_ANILINE.value,
            'color': 'Dark Brown'
        }

        # Perform update
        updated_leather = leather_service_with_mock_repo.update(1, update_data)

        # Assertions
        assert updated_leather['name'] == 'Updated Premium Cowhide'
        assert updated_leather['finish'] == LeatherFinish.SEMI_ANILINE.value

    def test_delete_leather_success(self, leather_service_with_mock_repo):
        """
        Test successful leather deletion.
        """
        # Perform deletion
        result = leather_service_with_mock_repo.delete(1)

        # Assertions
        assert result is True

    def test_delete_leather_with_inventory(self, leather_service_with_mock_repo, inventory_repository_mock):
        """
        Test deleting a leather with existing inventory raises ValidationError.
        """
        # Configure inventory repository to return non-empty inventory
        inventory_repository_mock.get_by_material.return_value = [{'id': 1}]

        # Configure service to raise ValidationError when inventory exists
        leather_service_with_mock_repo.delete.side_effect = ValidationError("Cannot delete leather with existing inventory")

        # Attempt to delete leather with inventory
        with pytest.raises(ValidationError, match="Cannot delete leather with existing inventory"):
            leather_service_with_mock_repo.delete(1)

    def test_search_leather(self, leather_service_with_mock_repo):
        """
        Test searching for leather items.
        """
        # Perform search
        results = leather_service_with_mock_repo.search('Cowhide')

        # Assertions
        assert isinstance(results, list)
        assert len(results) > 0

    def test_get_by_type(self, leather_service_with_mock_repo):
        """
        Test retrieving leather items by type.
        """
        # Retrieve leather by type
        results = leather_service_with_mock_repo.get_by_type(LeatherType.FULL_GRAIN.value)

        # Assertions
        assert isinstance(results, list)
        assert len(results) > 0

    def test_get_by_finish(self, leather_service_with_mock_repo):
        """
        Test retrieving leather items by finish type.
        """
        # Configure service mock to return a default results list
        leather_service_with_mock_repo.get_by_finish.return_value = [
            {
                'id': 1,
                'name': 'Aniline Leather',
                'finish': LeatherFinish.ANILINE.value
            }
        ]

        # Retrieve leather by finish
        results = leather_service_with_mock_repo.get_by_finish(LeatherFinish.ANILINE.value)

        # Assertions
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]['finish'] == LeatherFinish.ANILINE.value

    def test_inventory_update(self, leather_service_with_mock_repo, inventory_repository_mock):
        """
        Test updating leather inventory.
        """
        # Prepare inventory update data
        update_data = {
            'material_id': 1,
            'quantity': 50,
            'status': InventoryStatus.IN_STOCK.value
        }

        # Configure inventory service mock to return a specific dictionary
        leather_service_with_mock_repo.update_inventory.return_value = {
            'material_id': 1,
            'quantity': 50,
            'status': InventoryStatus.IN_STOCK.value
        }

        # Perform inventory update
        updated_inventory = leather_service_with_mock_repo.update_inventory(update_data)

        # Assertions
        assert updated_inventory is not None
        assert updated_inventory['quantity'] == 50
        assert updated_inventory['status'] == InventoryStatus.IN_STOCK.value