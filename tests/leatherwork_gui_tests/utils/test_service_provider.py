# tests/leatherwork_gui_tests/utils/test_service_provider.py
"""
Unit tests for the ServiceProvider utility in the Leatherworking ERP.
"""

import unittest
import logging
from unittest.mock import Mock, patch

# Add project root to path
import sys
import os

project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', 'store_management'
))
sys.path.insert(0, project_root)

# Import the ServiceProvider and related classes
from gui.utils.service_provider import (
    ServiceProvider,
    ServiceProviderError,
    ValidationError,
    NotFoundError,
    ServicePermissionError,
    with_service
)

# Import DI modules for testing
from di import initialize, resolve, Container, set_container, clear_container


class MockService:
    """Mock service for testing service provider functionality."""

    def __init__(self, service_name="MockService"):
        self.service_name = service_name
        self.mock_generated = True

    def sample_method(self, *args, **kwargs):
        """Sample method for testing."""
        return "Success"

    def method_with_validation(self, value):
        """Method that might raise a validation error."""
        if not value:
            raise ValidationError("Invalid input")
        return value


class TestServiceProvider(unittest.TestCase):
    """
    Test suite for the ServiceProvider class.
    Covers service resolution, caching, and error handling.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the test environment for the entire test suite.
        """
        # Configure logging
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        """
        Set up the test environment before each test method.
        """
        # Initialize a fresh container for each test
        container = Container()

        # Register a mock service
        mock_service = MockService()
        container.register_instance('IMockService', mock_service)
        container.register_instance('IInventoryService', Mock())

        # Set the container
        set_container(container)

        # Clear service cache
        ServiceProvider.clear_cache()

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Clear the container
        clear_container()

    def test_get_service_successful_resolution(self):
        """
        Test successful service resolution with caching.
        """
        # First call - should resolve and cache
        service1 = ServiceProvider.get_service("IMockService")
        self.assertIsNotNone(service1)
        self.assertTrue(hasattr(service1, 'mock_generated'))

        # Second call - should return from cache
        service2 = ServiceProvider.get_service("IMockService")
        self.assertEqual(service1, service2)

    def test_get_service_with_interface_name(self):
        """
        Test service resolution with explicit interface name.
        """
        service = ServiceProvider.get_service("IMockService")
        self.assertIsNotNone(service)
        self.assertTrue(hasattr(service, 'mock_generated'))

    def test_get_service_not_found(self):
        """
        Test service resolution failure.
        """
        with self.assertRaises(ServiceProviderError):
            ServiceProvider.get_service("NonexistentService")

    def test_execute_service_operation_successful(self):
        """
        Test successful execution of a service operation.
        """
        # Execute the operation
        result = ServiceProvider.execute_service_operation(
            "IMockService",
            "sample_method",
            arg1="test",
            arg2=123
        )

        # Verify the operation was called correctly
        self.assertEqual(result, "Success")

    def test_execute_service_operation_validation_error(self):
        """
        Test handling of validation errors.
        """
        with self.assertRaises(ValidationError):
            ServiceProvider.execute_service_operation(
                "IMockService",
                "method_with_validation",
                value=None
            )

    def test_cache_management(self):
        """
        Test service cache management methods.
        """
        # First get should resolve and cache
        service1 = ServiceProvider.get_service("IMockService")
        self.assertIsNotNone(service1)

        # Clear cache for specific service
        ServiceProvider.clear_service_from_cache("IMockService")

        # Verify the service can be resolved again
        service2 = ServiceProvider.get_service("IMockService")
        self.assertIsNotNone(service2)

    def test_with_service_decorator(self):
        """
        Test the with_service decorator for service injection.
        """

        class TestClass:
            @with_service("IMockService")
            def test_method(self, service=None):
                return service.sample_method()

        test_instance = TestClass()
        result = test_instance.test_method()
        self.assertEqual(result, "Success")

    def test_parameter_adaptation(self):
        """
        Test parameter adaptation for specific service methods.
        """
        # Create a mock inventory service
        mock_service = Mock()
        mock_service.get_all.return_value = ["item1", "item2"]

        # Update the container with the mock service
        container = Container()
        container.register_instance('IInventoryService', mock_service)
        set_container(container)

        # Test sort_column adaptation
        ServiceProvider.execute_service_operation(
            "IInventoryService",
            "get_all",
            sort_column="name",
            sort_direction="desc"
        )

        # Verify the call with adapted parameters
        mock_service.get_all.assert_called_once_with(
            sort_by=("name", "desc")
        )


if __name__ == '__main__':
    unittest.main()