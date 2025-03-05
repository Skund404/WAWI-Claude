# utils/circular_import_resolver.py
"""
Utility for resolving circular import dependencies in the application.

This module provides a mechanism to handle circular dependencies between modules
by using lazy imports and resolving them at runtime. It's particularly useful
for SQLAlchemy models with complex relationships.
"""

import logging
import functools
import importlib
import inspect
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast, get_type_hints

# Type definition for relationship configuration
T = TypeVar('T')
RelationshipCallback = Callable[[], Any]

# Setup logger
logger = logging.getLogger(__name__)

# Global registries
_lazy_imports: Dict[str, Dict[str, str]] = {}
_relationship_registry: Dict[str, Dict[str, RelationshipCallback]] = {}
_resolved_imports: Dict[str, Any] = {}
_module_aliases: Dict[str, str] = {}
_class_aliases: Dict[str, Dict[str, tuple]] = {}
_registered_paths: set = set()


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
    global _class_aliases

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

        # Special case handling for OrderItem
        if class_name == "OrderItem" and module_path == "database.models.order":
            try:
                # First try to import from dedicated order_item module
                order_item_module = get_module("database.models.order_item")
                if hasattr(order_item_module, "OrderItem"):
                    return getattr(order_item_module, "OrderItem")
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
    global _lazy_imports, _resolved_imports

    if target_name in _resolved_imports:
        return _resolved_imports[target_name]

    if target_name not in _lazy_imports:
        logger.error(f"No lazy import registered for {target_name}")
        raise ImportError(f"No lazy import registered for {target_name}")

    try:
        import_info = _lazy_imports[target_name]
        module_path = import_info['module_path']
        class_name = import_info['class_name']

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
        # Import the module
        module = get_module(module_path)

        # If no class name is provided, return the module
        if not class_name:
            return module

        # Get the class from the module
        if hasattr(module, class_name):
            return getattr(module, class_name)

        # Special case handling
        if class_name == "OrderItem" and module_path == "database.models.order":
            try:
                order_item_module = get_module("database.models.order_item")
                if hasattr(order_item_module, "OrderItem"):
                    return getattr(order_item_module, "OrderItem")
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

    from sqlalchemy.orm import relationship

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
            logger.error(f"Error resolving lazy import {owner_key}.None: {e}")
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
        from sqlalchemy.orm import relationship
        target = lazy_import(model_path)
        return relationship(target, **kwargs)

    return callback


class CircularImportResolver:
    """Class-based interface for resolving circular imports."""

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


# Register common aliases to handle model hierarchies
register_module_alias('database.models.order.Order', 'database.models.order')
register_module_alias('database.models.order.OrderItem', 'database.models.order_item')
register_module_alias('database.models.order_item.Order', 'database.models.order')
register_module_alias('database.models.order_item.OrderItem', 'database.models.order_item')

# Register special case for ProjectComponent being in the components module, not project module
register_class_alias('database.models.project', 'ProjectComponent', 'database.models.components', 'ProjectComponent')