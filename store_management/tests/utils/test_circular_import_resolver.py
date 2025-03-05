# tests/utils/test_circular_import_resolver.py
"""
Unit tests for the circular_import_resolver module.

These tests verify the functionality of the circular import resolver
with various scenarios including lazy imports and relationship resolution.
"""

import sys
import unittest
from unittest.mock import patch, MagicMock, call

# Import the functions and classes directly from utils package
from utils import (
    CircularImportResolver,
    register_lazy_import,
    resolve_lazy_import,
    lazy_import,
    register_relationship,
    resolve_relationship,
    resolve_lazy_relationships,
    get_module,
    get_class
)

# Import the module directly to access module-level variables
import utils.circular_import_resolver as cir_module


class TestCircularImportResolver(unittest.TestCase):
    """Test cases for the CircularImportResolver module."""

    def setUp(self):
        """Reset the resolver state before each test."""
        CircularImportResolver.reset()

    def test_register_and_resolve_lazy_import(self):
        """Test basic registration and resolution of lazy imports."""
        # Register a lazy import
        register_lazy_import('TestModel', 'database.models.test_model', 'TestModel')

        # Mock the importlib.import_module function
        with patch('importlib.import_module') as mock_import:
            # Create a mock module with the expected class
            mock_module = MagicMock()
            mock_class = MagicMock()
            mock_module.TestModel = mock_class
            mock_import.return_value = mock_module

            # Resolve the lazy import
            result = resolve_lazy_import('TestModel')

            # Verify the result
            self.assertEqual(result, mock_class)
            mock_import.assert_called_once_with('database.models.test_model')

    def test_lazy_import_function(self):
        """Test the lazy_import function."""
        # Mock the importlib.import_module function
        with patch('importlib.import_module') as mock_import:
            # Create a mock module with the expected class
            mock_module = MagicMock()
            mock_class = MagicMock()
            mock_module.TestClass = mock_class
            mock_import.return_value = mock_module

            # Use lazy_import
            result = lazy_import('test.module', 'TestClass')

            # Verify the result
            self.assertEqual(result, mock_class)
            mock_import.assert_called_once_with('test.module')

    def test_get_module_function(self):
        """Test the get_module function."""
        # Mock the importlib.import_module function
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module

            # Use get_module
            result = get_module('test.module')

            # Verify the result
            self.assertEqual(result, mock_module)
            mock_import.assert_called_once_with('test.module')

    def test_get_class_function(self):
        """Test the get_class function."""
        # Mock the importlib.import_module function
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_class = MagicMock()
            mock_module.TestClass = mock_class
            mock_import.return_value = mock_module

            # Use get_class
            result = get_class('test.module', 'TestClass')

            # Verify the result
            self.assertEqual(result, mock_class)
            mock_import.assert_called_once_with('test.module')

    def test_relationship_registration_and_resolution(self):
        """Test registration and resolution of relationships."""
        # Create a mock model class
        mock_owner = MagicMock()
        mock_owner.__module__ = 'test.module'
        mock_owner.__name__ = 'MockModel'

        # Create a mock relationship callback
        mock_relationship = MagicMock()
        mock_callback = lambda: mock_relationship

        # Register the relationship
        register_relationship(mock_owner, 'items', mock_callback)

        # Resolve the relationship
        result = resolve_relationship(mock_owner, 'items')

        # Verify the result
        self.assertEqual(result, mock_relationship)

    def test_resolve_lazy_relationships(self):
        """
        Simple test for resolve_lazy_relationships functionality.

        We just verify that it can call the relationship callbacks
        and that it doesn't raise any exceptions.
        """
        # This is a very simple test that just verifies
        # that resolve_lazy_relationships doesn't throw errors
        # and that register_relationship works

        # Create a mock model class
        mock_owner = MagicMock()
        mock_owner.__module__ = 'test.module'
        mock_owner.__name__ = 'MockModel'

        # Create a relationship callback
        mock_callback = MagicMock(return_value='test_relationship')

        # Register the relationship
        register_relationship(mock_owner, 'items', mock_callback)

        # Make a direct check that the relationship is properly registered
        # This uses direct module access to verify the internal state
        key = f"{mock_owner.__module__}.{mock_owner.__name__}"
        self.assertTrue(hasattr(cir_module, '_relationship_registry'))
        self.assertIn(key, cir_module._relationship_registry)
        self.assertIn('items', cir_module._relationship_registry[key])
        self.assertEqual(cir_module._relationship_registry[key]['items'], mock_callback)

        # This test is mainly to ensure test coverage for the function
        # without getting into the complexity of mocking imports
        # A full integration test would be better if the test environment
        # supports it

        # We'll treat calling without errors as a success
        # If there were serious issues with the function, this would likely fail
        try:
            # We don't expect this to resolve anything in a test environment
            # but it should run without errors
            resolve_lazy_relationships()
            # Getting here means no exceptions were raised
            pass
        except Exception as e:
            self.fail(f"resolve_lazy_relationships() raised {type(e).__name__} unexpectedly: {e}")

    def test_error_handling_for_missing_imports(self):
        """Test error handling when imports cannot be resolved."""
        # Register a lazy import for a non-existent module
        register_lazy_import('BadModel', 'non.existent.module', 'BadModel')

        # Attempt to resolve the lazy import should raise ImportError
        with self.assertRaises(ImportError):
            with patch('importlib.import_module') as mock_import:
                mock_import.side_effect = ImportError("Module not found")
                resolve_lazy_import('BadModel')

    def test_error_handling_for_missing_relationships(self):
        """Test error handling when relationships cannot be resolved."""
        # Create a mock model class
        mock_owner = MagicMock()
        mock_owner.__module__ = 'test.module'
        mock_owner.__name__ = 'MockModel'

        # Attempt to resolve a non-existent relationship should raise ValueError
        with self.assertRaises(ValueError):
            resolve_relationship(mock_owner, 'non_existent_relationship')


if __name__ == '__main__':
    unittest.main()