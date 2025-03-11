# tests/leatherwork_services_tests/test_hardware_service.py
"""
Unit tests for the HardwareService.

This module tests the HardwareService using mocked dependencies.
"""

import pytest
from database.models.enums import (
    HardwareType,
    HardwareMaterial,
    HardwareFinish
)
from services.exceptions import ValidationError, NotFoundError


class TestHardwareService:
    def test_create_hardware_success(self, hardware_service_with_mock_repo):
        """
        Test successful hardware creation with valid data.
        """
        # Prepare hardware data
        hardware_data = {
            'name': 'Brass Buckle',
            'type': HardwareType.BUCKLE.value,
            'material': HardwareMaterial.BRASS.value,
            'finish': HardwareFinish.POLISHED.value,
            'size': '25mm',
            'description': 'High-quality brass buckle for leather projects'
        }

        # Create hardware
        created_hardware = hardware_service_with_mock_repo.create(hardware_data)

        # Assertions
        assert created_hardware is not None
        assert created_hardware['name'] == 'Brass Buckle'
        assert created_hardware['type'] == HardwareType.BUCKLE.value
        assert created_hardware['material'] == HardwareMaterial.BRASS.value

    def test_create_hardware_validation_error(self, hardware_service_with_mock_repo):
        """
        Test hardware creation with invalid data raises ValidationError.
        """
        # Prepare invalid hardware data (missing name)
        invalid_hardware_data = {
            'type': HardwareType.BUCKLE.value,
            # Missing required fields
        }

        # Expect ValidationError
        with pytest.raises(ValidationError):
            hardware_service_with_mock_repo.create(invalid_hardware_data)

    def test_get_hardware_by_id_success(self, hardware_service_with_mock_repo):
        """
        Test retrieving an existing hardware item by ID.
        """
        # Retrieve the hardware
        retrieved_hardware = hardware_service_with_mock_repo.get_by_id(1)

        # Assertions
        assert retrieved_hardware is not None
        assert retrieved_hardware['id'] == 1

    def test_get_hardware_by_id_not_found(self, hardware_service_with_mock_repo):
        """
        Test retrieving a non-existent hardware item raises NotFoundError.
        """
        # Attempt to retrieve non-existent hardware
        with pytest.raises(NotFoundError):
            hardware_service_with_mock_repo.get_by_id(999999)

    def test_update_hardware_success(self, hardware_service_with_mock_repo):
        """
        Test successful hardware update.
        """
        # Prepare update data
        update_data = {
            'name': 'Updated Brass Buckle',
            'finish': HardwareFinish.BRUSHED.value
        }

        # Perform update
        updated_hardware = hardware_service_with_mock_repo.update(1, update_data)

        # Assertions
        assert updated_hardware['name'] == 'Updated Brass Buckle'
        assert updated_hardware['finish'] == HardwareFinish.BRUSHED.value

    def test_delete_hardware_success(self, hardware_service_with_mock_repo):
        """
        Test successful hardware deletion.
        """
        # Perform deletion
        result = hardware_service_with_mock_repo.delete(1)

        # Assertions
        assert result is True

    def test_search_hardware(self, hardware_service_with_mock_repo):
        """
        Test searching for hardware items.
        """
        # Perform search
        results = hardware_service_with_mock_repo.search('Buckle')

        # Assertions
        assert isinstance(results, list)

    def test_get_by_type(self, hardware_service_with_mock_repo):
        """
        Test retrieving hardware items by type.
        """
        # Retrieve hardware by type
        results = hardware_service_with_mock_repo.get_by_type(HardwareType.BUCKLE.value)

        # Assertions
        assert isinstance(results, list)