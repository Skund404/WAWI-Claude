# tests/utils/test_circular_import_resolver.py
"""
Tests for the circular_import_resolver module.

This module contains tests to verify that the circular import resolver
correctly handles lazy imports, relationship registration, and class aliases.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to the Python path for imports to work correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from store_management.utils.circular_import_resolver import (
    CircularImportResolver, lazy_import, register_lazy_import, resolve_lazy_import,
    register_module_alias, register_class_alias, sql_types,
    register_relationship, resolve_relationship,
    # Test direct access to SQLAlchemy types
    Integer, String, Boolean, Column, relationship
)


class TestCircularImportResolver(unittest.TestCase):
    """Test suite for the CircularImportResolver module."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset the resolver state before each test
        CircularImportResolver.reset()

    def test_sqlalchemy_types_availability(self):
        """Test that SQLAlchemy types are available directly."""
        self.assertIsNotNone(sql_types['Integer'])
        self.assertIsNotNone(sql_types['String'])
        self.assertIsNotNone(sql_types['relationship'])

    def test_direct_sqlalchemy_types_access(self):
        """Test direct access to SQLAlchemy types from module level."""
        self.assertIsNotNone(Integer)
        self.assertIsNotNone(String)
        self.assertIsNotNone(Boolean)
        self.assertIsNotNone(Column)
        self.assertIsNotNone(relationship)

        # Test that they match the types in the dictionary
        self.assertEqual(Integer, sql_types['Integer'])
        self.assertEqual(String, sql_types['String'])
        self.assertEqual(relationship, sql_types['relationship'])

    def test_lazy_import_sqlalchemy_types(self):
        """Test lazy importing of SQLAlchemy types."""
        imported_integer = lazy_import('sqlalchemy', 'Integer')
        self.assertEqual(imported_integer, Integer)
        self.assertEqual(imported_integer, sql_types['Integer'])

        imported_relationship = lazy_import('sqlalchemy.orm', 'relationship')
        self.assertEqual(imported_relationship, relationship)
        self.assertEqual(imported_relationship, sql_types['relationship'])

    def test_lazy_import_sqlalchemy_module(self):
        """Test lazy importing of entire SQLAlchemy module."""
        sqlalchemy_module = lazy_import('sqlalchemy')
        self.assertIsNotNone(sqlalchemy_module)
        self.assertTrue(hasattr(sqlalchemy_module, 'Integer'))
        self.assertEqual(sqlalchemy_module.Integer, Integer)

        orm_module = lazy_import('sqlalchemy.orm')
        self.assertIsNotNone(orm_module)
        self.assertTrue(hasattr(orm_module, 'relationship'))
        self.assertEqual(orm_module.relationship, relationship)

    @patch('importlib.import_module')
    def test_lazy_import_custom_class(self, mock_importlib):
        """Test lazy importing of a custom class."""
        # Mock the module with a class
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_module.TestClass = mock_class
        mock_importlib.return_value = mock_module

        # Test the lazy import
        result = lazy_import('test.module', 'TestClass')
        mock_importlib.assert_called_once_with('test.module')
        self.assertEqual(result, mock_class)

    @patch('importlib.import_module')
    def test_module_alias(self, mock_importlib):
        """Test module alias resolution."""
        # Setup an alias
        register_module_alias('alias.module', 'actual.module')

        # Mock the module
        mock_module = MagicMock()
        mock_importlib.return_value = mock_module

        # Test importing via alias
        lazy_import('alias.module')
        mock_importlib.assert_called_once_with('actual.module')

    @patch('importlib.import_module')
    def test_class_alias(self, mock_importlib):
        """Test class alias resolution."""
        # Setup module with class
        mock_orig_module = MagicMock()
        mock_orig_class = MagicMock()
        mock_orig_module.OriginalClass = mock_orig_class

        # Register a class alias
        register_class_alias('alias.module', 'AliasClass', 'original.module', 'OriginalClass')

        # Mock importlib to return our mock module
        mock_importlib.return_value = mock_orig_module

        # Test that the alias resolves correctly
        from store_management.utils.circular_import_resolver import get_class
        result = get_class('alias.module', 'AliasClass')

        # Verify that importlib was called with the correct module path
        mock_importlib.assert_called_with('original.module')

        # Verify that we got the expected class
        self.assertEqual(result, mock_orig_class)

    def test_register_and_resolve_lazy_import(self):
        """Test registering and resolving a lazy import."""
        # Register a mock lazy import
        mock_class = MagicMock()
        register_lazy_import('TestTarget', 'test.module', 'TestClass')

        # Mock the resolution
        with patch('importlib.import_module') as mock_importlib:
            mock_module = MagicMock()
            mock_module.TestClass = mock_class
            mock_importlib.return_value = mock_module

            # Resolve the lazy import
            result = resolve_lazy_import('TestTarget')
            self.assertEqual(result, mock_class)

            # Resolving again should return the cached result without a new import
            mock_importlib.reset_mock()
            result2 = resolve_lazy_import('TestTarget')
            self.assertEqual(result2, mock_class)
            mock_importlib.assert_not_called()

    def test_relationship_registration(self):
        """Test registering and resolving a relationship."""
        # Create a mock owner class with a module attribute
        mock_owner = type('MockOwner', (), {'__module__': 'test.module', '__name__': 'MockOwner'})

        # Create a mock callback
        mock_callback = MagicMock()
        mock_callback.return_value = 'resolved_relationship'

        # Register the relationship
        register_relationship(mock_owner, 'test_relationship', mock_callback)

        # Resolve the relationship
        result = resolve_relationship(mock_owner, 'test_relationship')

        # Verify the callback was called and the relationship was resolved
        mock_callback.assert_called_once()
        self.assertEqual(result, 'resolved_relationship')

    def test_circular_resolver_reset(self):
        """Test that the reset method clears all registries."""
        # Register some things
        register_module_alias('test.alias', 'test.actual')
        register_lazy_import('TestTarget', 'test.module', 'TestClass')

        # Reset the resolver
        CircularImportResolver.reset()

        # Check that registries are cleared
        from store_management.utils.circular_import_resolver import _lazy_imports, _module_aliases
        self.assertEqual(_lazy_imports, {})
        self.assertEqual(_module_aliases, {})

    def test_get_sqlalchemy_type(self):
        """Test getting a SQLAlchemy type by name."""
        Integer_type = CircularImportResolver.get_sqlalchemy_type('Integer')
        self.assertEqual(Integer_type, sql_types['Integer'])
        self.assertEqual(Integer_type, Integer)

        # Should raise for unknown types
        with self.assertRaises(ValueError):
            CircularImportResolver.get_sqlalchemy_type('NonExistentType')

    @patch('importlib.import_module')
    def test_resolve_lazy_relationships(self, mock_importlib):
        """Test resolving lazy relationships."""
        from store_management.utils.circular_import_resolver import resolve_lazy_relationships

        # Create mock owner class and module
        mock_owner = type('MockOwner', (), {})
        mock_module = MagicMock()
        mock_module.MockOwner = mock_owner
        mock_importlib.return_value = mock_module

        # Create mock relationship callback
        mock_rel = MagicMock()

        # Register a relationship
        register_relationship(mock_owner, 'test_rel', lambda: mock_rel)

        # Resolve relationships
        resolve_lazy_relationships()

        # Check that the relationship was set on the owner class
        self.assertEqual(getattr(mock_owner, 'test_rel', None), mock_rel)


if __name__ == '__main__':
    unittest.main()