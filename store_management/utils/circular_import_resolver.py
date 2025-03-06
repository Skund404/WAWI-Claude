# utils/circular_import_resolver.py
"""
Utility for resolving circular import dependencies in the application.

This module provides a mechanism to handle circular dependencies between modules
by using lazy imports and resolving them at runtime. It's particularly useful
for SQLAlchemy models with complex relationships.
"""

import logging
import importlib
import inspect
import sys
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

# Setup logger
logger = logging.getLogger(__name__)

# Type definition for relationship configuration
T = TypeVar('T')
RelationshipCallback = Callable[[], Any]

# Global registries
_lazy_imports: Dict[str, Dict[str, str]] = {}
_resolved_imports: Dict[str, Any] = {}
_relationship_registry: Dict[str, Dict[str, RelationshipCallback]] = {}
_module_aliases: Dict[str, str] = {}
_class_aliases: Dict[str, Dict[str, tuple]] = {}
_registered_paths: set = set()

# First, try to import from SQLAlchemy directly
try:
    from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, MetaData
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

    HAS_SQLALCHEMY = True
except ImportError:
    # Create dummy types if SQLAlchemy is not available
    HAS_SQLALCHEMY = False


    # These types will be used if SQLAlchemy isn't installed
    class DummyType:
        def __init__(self, *args, **kwargs):
            pass


    Boolean = DummyType
    Column = DummyType
    DateTime = DummyType
    Enum = DummyType
    Float = DummyType
    ForeignKey = DummyType
    Integer = DummyType
    String = DummyType
    Text = DummyType
    MetaData = DummyType


    class DeclarativeBase:
        pass


    class Mapped:
        pass


    def mapped_column(*args, **kwargs):
        pass


    def relationship(*args, **kwargs):
        pass

# Make these available to sys.modules to help with imports
sys.modules['sqlalchemy.Integer'] = Integer
sys.modules['sqlalchemy.String'] = String
sys.modules['sqlalchemy.Boolean'] = Boolean
sys.modules['sqlalchemy.Float'] = Float
sys.modules['sqlalchemy.DateTime'] = DateTime
sys.modules['sqlalchemy.ForeignKey'] = ForeignKey
sys.modules['sqlalchemy.Column'] = Column
sys.modules['sqlalchemy.Text'] = Text
sys.modules['sqlalchemy.Enum'] = Enum
sys.modules['sqlalchemy.MetaData'] = MetaData
sys.modules['sqlalchemy.orm.DeclarativeBase'] = DeclarativeBase
sys.modules['sqlalchemy.orm.Mapped'] = Mapped
sys.modules['sqlalchemy.orm.mapped_column'] = mapped_column
sys.modules['sqlalchemy.orm.relationship'] = relationship

# Export all SQLAlchemy types at module level
__all__ = [
    'Boolean', 'Column', 'DateTime', 'Enum', 'Float', 'ForeignKey',
    'Integer', 'MetaData', 'String', 'Text', 'DeclarativeBase',
    'Mapped', 'mapped_column', 'relationship', 'HAS_SQLALCHEMY',
    'register_module_alias', 'register_class_alias', 'register_lazy_import',
    'resolve_lazy_import', 'lazy_import', 'register_relationship',
    'resolve_relationship', 'resolve_lazy_relationships', 'CircularImportResolver',
    'sql_types'
]

# Create a centralized dictionary for SQL types for easy reference
sql_types = {
    'Integer': Integer,
    'String': String,
    'Boolean': Boolean,
    'Float': Float,
    'DateTime': DateTime,
    'ForeignKey': ForeignKey,
    'MetaData': MetaData,
    'Column': Column,
    'Text': Text,
    'Enum': Enum,
    'DeclarativeBase': DeclarativeBase,
    'Mapped': Mapped,
    'mapped_column': mapped_column,
    'relationship': relationship
}

# Make all types available at the global level for direct imports from models
globals().update(sql_types)


def register_module_alias(alias_path: str, actual_path: str) -> None:
    """
    Register an alias for a module path.

    Args:
        alias_path: The alias path to register
        actual_path: The actual module path
    """
    global _module_aliases
    _module_aliases[alias_path] = actual_path
    logger.debug(f"Registered module alias: {alias_path} -> {actual_path}")


def register_class_alias(module_path: str, class_name: str,
                         actual_module_path: str, actual_class_name: Optional[str] = None) -> None:
    """
    Register an alias for a class within a module.

    Args:
        module_path: The module path where the class is expected
        class_name: The class name that is expected
        actual_module_path: The actual module path where the class exists
        actual_class_name: The actual class name (if different)
    """
    global _class_aliases

    if module_path not in _class_aliases:
        _class_aliases[module_path] = {}

    actual_class = actual_class_name or class_name
    _class_aliases[module_path][class_name] = (actual_module_path, actual_class)

    logger.debug(f"Registered class alias: {module_path}.{class_name} -> {actual_module_path}.{actual_class}")


def register_lazy_import(target_name: str, module_path: str, class_name: str) -> None:
    """
    Register a lazy import to be resolved at runtime.

    Args:
        target_name: A unique identifier for this import
        module_path: Import path to the module
        class_name: Name of the class to import from the module

    Example:
        register_lazy_import('Product', 'database.models.product', 'Product')
    """
    global _lazy_imports, _resolved_imports

    if target_name in _resolved_imports:
        logger.debug(f"Lazy import '{target_name}' already resolved, skipping registration")
        return

    if target_name not in _lazy_imports:
        _lazy_imports[target_name] = {}

    _lazy_imports[target_name]['module_path'] = module_path
    _lazy_imports[target_name]['class_name'] = class_name
    logger.debug(f"Registered lazy import: {target_name} -> {module_path}.{class_name}")


def get_module(module_path: str) -> ModuleType:
    """
    Get a module by path, handling aliases.

    Args:
        module_path: Path to the module

    Returns:
        The imported module

    Raises:
        ImportError: If module cannot be imported
    """
    global _module_aliases

    try:
        # Check for module alias
        if module_path in _module_aliases:
            actual_path = _module_aliases[module_path]
            logger.debug(f"Using module alias: {module_path} -> {actual_path}")
            module_path = actual_path

        # Attempt to import the module
        module = importlib.import_module(module_path)
        return module
    except ImportError as e:
        logger.error(f"Error importing module {module_path}: {e}")
        raise


def get_class(module_path: str, class_name: str) -> Type:
    """
    Get a class from a module, handling special cases.

    Args:
        module_path: Path to the module
        class_name: Name of the class

    Returns:
        The class

    Raises:
        ImportError: If module or class cannot be imported
    """
    global _class_aliases, sql_types

    # Direct SQLAlchemy type handling - check current module globals first
    if module_path == 'sqlalchemy' and class_name in sql_types:
        return sql_types[class_name]

    if module_path == 'sqlalchemy.orm' and class_name in ['DeclarativeBase', 'Mapped', 'mapped_column', 'relationship']:
        return sql_types[class_name]

    try:
        # Check for class alias
        if module_path in _class_aliases and class_name in _class_aliases[module_path]:
            actual_module_path, actual_class_name = _class_aliases[module_path][class_name]
            logger.debug(f"Using class alias: {module_path}.{class_name} -> {actual_module_path}.{actual_class_name}")

            try:
                actual_module = get_module(actual_module_path)
                if hasattr(actual_module, actual_class_name):
                    return getattr(actual_module, actual_class_name)
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to import aliased class {actual_module_path}.{actual_class_name}: {e}")
                # Continue with standard import attempt

        # Special case handling for SaleItem
        if class_name == "SaleItem" and module_path == "database.models.sale":
            try:
                # First try to import from dedicated sale_item module
                sale_item_module = get_module("database.models.sales_item")
                if hasattr(sale_item_module, "SalesItem"):
                    return getattr(sale_item_module, "SalesItem")
            except ImportError:
                pass

        # Special case handling for ProjectComponent
        if class_name == "ProjectComponent" and module_path == "database.models.project":
            try:
                # Try to import from components module
                components_module = get_module("database.models.components")
                if hasattr(components_module, "ProjectComponent"):
                    return getattr(components_module, "ProjectComponent")
            except ImportError:
                pass

        # Standard import
        module = get_module(module_path)

        if hasattr(module, class_name):
            return getattr(module, class_name)

        raise ImportError(f"Class {class_name} not found in module {module_path}")
    except ImportError as e:
        logger.error(f"Error getting class {class_name} from module {module_path}: {e}")
        raise


def resolve_lazy_import(target_name: str) -> Any:
    """
    Resolve a registered lazy import.

    Args:
        target_name: The unique identifier for the import to resolve

    Returns:
        The imported class or object

    Raises:
        ImportError: If the lazy import cannot be resolved
    """
    global _lazy_imports, _resolved_imports, sql_types

    # Special case for SQLAlchemy types - check first in this module
    if target_name in sql_types:
        return sql_types[target_name]

    if target_name in _resolved_imports:
        return _resolved_imports[target_name]

    if target_name not in _lazy_imports:
        logger.error(f"No lazy import registered for {target_name}")
        raise ImportError(f"No lazy import registered for {target_name}")

    try:
        import_info = _lazy_imports[target_name]
        module_path = import_info['module_path']
        class_name = import_info['class_name']

        # Special handling for SQLAlchemy imports
        if module_path == 'sqlalchemy' and class_name in sql_types:
            resolved = sql_types[class_name]
            _resolved_imports[target_name] = resolved
            return resolved

        if module_path == 'sqlalchemy.orm' and class_name in ['DeclarativeBase', 'Mapped', 'mapped_column',
                                                              'relationship']:
            resolved = sql_types[class_name]
            _resolved_imports[target_name] = resolved
            return resolved

        # Import the module
        module = importlib.import_module(module_path)

        # Get the class or object from the module
        if hasattr(module, class_name):
            resolved = getattr(module, class_name)
            _resolved_imports[target_name] = resolved
            logger.debug(f"Resolved lazy import: {target_name} -> {module_path}.{class_name}")
            return resolved
        else:
            logger.error(f"Class {class_name} not found in module {module_path}")
            raise ImportError(f"Class {class_name} not found in module {module_path}")
    except Exception as e:
        logger.error(f"Error resolving lazy import {target_name}: {e}")
        raise ImportError(f"Failed to resolve lazy import: {e}") from e


def lazy_import(module_path: str, class_name: Optional[str] = None) -> Any:
    """
    Lazily import a module or class.

    Args:
        module_path: Path to the module
        class_name: Optional name of the class to import

    Returns:
        The imported module or class
    """
    try:
        # Handle SQLAlchemy types directly from this module
        if module_path == 'sqlalchemy':
            if not class_name:
                # Return a mock SQLAlchemy module with our types
                mock_sqlalchemy = type('MockSQLAlchemy', (), {})()
                for name, value in sql_types.items():
                    setattr(mock_sqlalchemy, name, value)
                return mock_sqlalchemy

            if class_name in sql_types:
                return sql_types[class_name]

        elif module_path == 'sqlalchemy.orm':
            if not class_name:
                # Return a mock SQLAlchemy.orm module with our types
                mock_orm = type('MockORMModule', (), {})()
                for name, value in sql_types.items():
                    if name in ['DeclarativeBase', 'Mapped', 'mapped_column', 'relationship']:
                        setattr(mock_orm, name, value)
                return mock_orm

            if class_name in ['DeclarativeBase', 'Mapped', 'mapped_column', 'relationship']:
                return sql_types[class_name]

        # Import the module
        module = get_module(module_path)

        # If no class name is provided, return the module
        if not class_name:
            return module

        # Get the class from the module
        if hasattr(module, class_name):
            return getattr(module, class_name)

        # Special case handling
        if class_name == "SaleItem" and module_path == "database.models.sale":
            try:
                sale_item_module = get_module("database.models.sale_item")
                if hasattr(sale_item_module, "SaleItem"):
                    return getattr(sale_item_module, "SaleItem")
            except ImportError:
                pass

        if class_name == "ProjectComponent" and module_path == "database.models.project":
            try:
                comp_module = get_module("database.models.components")
                if hasattr(comp_module, "ProjectComponent"):
                    return getattr(comp_module, "ProjectComponent")
            except ImportError:
                pass

        # Class not found
        logger.error(f"Class {class_name} not found in module {module_path}")
        raise ImportError(f"Class {class_name} not found in module {module_path}")
    except Exception as e:
        logger.error(f"Error in lazy_import for {module_path}.{class_name}: {e}")
        raise ImportError(f"Failed in lazy_import: {e}") from e


def register_relationship(
        owner_class: Type,
        relationship_name: str,
        callback: RelationshipCallback
) -> None:
    """
    Register a relationship configuration to be resolved later.

    Args:
        owner_class: The SQLAlchemy model class that owns the relationship
        relationship_name: Name of the relationship attribute
        callback: A callback function that returns the relationship definition
    """
    global _relationship_registry

    key = f"{owner_class.__module__}.{owner_class.__name__}"
    if key not in _relationship_registry:
        _relationship_registry[key] = {}

    _relationship_registry[key][relationship_name] = callback
    logger.debug(f"Registered relationship: {key}.{relationship_name}")


def resolve_relationship(owner_class: Type, relationship_name: str) -> Any:
    """
    Resolve a previously registered relationship.

    Args:
        owner_class: The SQLAlchemy model class that owns the relationship
        relationship_name: Name of the relationship attribute

    Returns:
        The resolved relationship configuration
    """
    global _relationship_registry

    key = f"{owner_class.__module__}.{owner_class.__name__}"

    if key not in _relationship_registry or relationship_name not in _relationship_registry[key]:
        logger.error(f"No relationship registered for {key}.{relationship_name}")
        raise ValueError(f"No relationship registered for {key}.{relationship_name}")

    try:
        callback = _relationship_registry[key][relationship_name]
        result = callback()
        logger.debug(f"Resolved relationship: {key}.{relationship_name}")
        return result
    except Exception as e:
        logger.error(f"Error resolving relationship {key}.{relationship_name}: {e}")
        raise ValueError(f"Failed to resolve relationship {key}.{relationship_name}: {e}") from e


def resolve_lazy_relationships() -> None:
    """
    Resolve all registered lazy relationships and apply them to their models.

    This should be called after all models have been imported and initialized.
    """
    global _relationship_registry

    resolved_count = 0
    failed_count = 0

    for owner_key, relationships in _relationship_registry.items():
        # Extract module and class name from owner_key
        if '.' not in owner_key:
            logger.warning(f"Invalid owner_key format: {owner_key}")
            continue

        module_path, class_name = owner_key.rsplit('.', 1)

        try:
            # Get the owner class
            module = importlib.import_module(module_path)
            if not hasattr(module, class_name):
                logger.warning(f"Class {class_name} not found in module {module_path}")
                continue

            owner_class = getattr(module, class_name)

            # Process each relationship for this owner
            for rel_name, callback in relationships.items():
                try:
                    # Get the relationship definition from the callback
                    rel_def = callback()
                    # Set the relationship on the owner class
                    setattr(owner_class, rel_name, rel_def)
                    resolved_count += 1
                    logger.debug(f"Applied relationship: {owner_key}.{rel_name}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to resolve lazy relationship {owner_key}.{rel_name}: {e}")
        except Exception as e:
            logger.error(f"Error resolving lazy import {owner_key}: {e}")
            failed_count += len(relationships)

    logger.info(f"Resolved {resolved_count} lazy relationships, {failed_count} failed")


# Helper function to lazily create a relationship
def lazy_relationship(model_path: str, **kwargs) -> RelationshipCallback:
    """
    Create a callback that returns a SQLAlchemy relationship.

    Args:
        model_path: Path to the target model (e.g., 'Module.ClassName')
        **kwargs: Additional relationship arguments

    Returns:
        A callback that will create the relationship
    """

    def callback():
        target = lazy_import(model_path)
        # Use the relationship function imported at module level
        return relationship(target, **kwargs)

    return callback


class CircularImportResolver:
    """Class-based interface for resolving circular imports."""

    # SQLAlchemy types dict for convenient access
    sqlalchemy_types = sql_types

    @staticmethod
    def reset() -> None:
        """Reset the resolver state for testing."""
        global _lazy_imports, _resolved_imports, _relationship_registry
        global _module_aliases, _class_aliases, _registered_paths

        _lazy_imports = {}
        _resolved_imports = {}
        _relationship_registry = {}
        _module_aliases = {}
        _class_aliases = {}
        _registered_paths = set()

    @staticmethod
    def register_module_alias(alias_path: str, actual_path: str) -> None:
        """Register an alias for a module path."""
        register_module_alias(alias_path, actual_path)

    @staticmethod
    def register_class_alias(module_path: str, class_name: str,
                             actual_module_path: str, actual_class_name: Optional[str] = None) -> None:
        """Register an alias for a class within a module."""
        register_class_alias(module_path, class_name, actual_module_path, actual_class_name)

    @staticmethod
    def register_lazy_import(target_name: str, module_path: str, class_name: str) -> None:
        """
        Register a lazy import to be resolved later.

        Args:
            target_name: A unique name for this lazy import
            module_path: Full Python path to the module containing the target class
            class_name: Name of the class to import from the module
        """
        register_lazy_import(target_name, module_path, class_name)

    @staticmethod
    def resolve_lazy_import(target_name: str) -> Any:
        """
        Resolve a previously registered lazy import.

        Args:
            target_name: The unique name of the lazy import to resolve

        Returns:
            The imported class or object
        """
        return resolve_lazy_import(target_name)

    @staticmethod
    def register_relationship(owner_class: Type, relationship_name: str, callback: RelationshipCallback) -> None:
        """
        Register a relationship configuration to be resolved later.

        Args:
            owner_class: The SQLAlchemy model class that owns the relationship
            relationship_name: Name of the relationship attribute
            callback: A callback function that returns the relationship definition
        """
        register_relationship(owner_class, relationship_name, callback)

    @staticmethod
    def resolve_relationship(owner_class: Type, relationship_name: str) -> Any:
        """
        Resolve a previously registered relationship.

        Args:
            owner_class: The SQLAlchemy model class that owns the relationship
            relationship_name: Name of the relationship attribute

        Returns:
            The resolved relationship configuration
        """
        return resolve_relationship(owner_class, relationship_name)

    @staticmethod
    def get_module(module_path: str) -> ModuleType:
        """Get a module by path, handling aliases."""
        return get_module(module_path)

    @staticmethod
    def get_class(module_path: str, class_name: str) -> Type:
        """Get a class from a module, handling special cases."""
        return get_class(module_path, class_name)

    @staticmethod
    def get_sqlalchemy_type(type_name: str) -> Any:
        """Get a SQLAlchemy type by name."""
        if type_name in CircularImportResolver.sqlalchemy_types:
            return CircularImportResolver.sqlalchemy_types[type_name]
        raise ValueError(f"Unknown SQLAlchemy type: {type_name}")


# Register common aliases to handle model hierarchies
register_module_alias('database.models.sale.Sales', 'database.models.sales')
register_module_alias('database.models.sale.SalesItem', 'database.models.sales_item')
register_module_alias('database.models.sales_item.Sales', 'database.models.sales')
register_module_alias('database.models.sales_item.SalesItem', 'database.models.sales_item')

# Register special case for ProjectComponent being in the components module, not project module
register_class_alias('database.models.project', 'ProjectComponent', 'database.models.components', 'ProjectComponent')