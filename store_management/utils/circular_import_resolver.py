# utils/circular_import_resolver.py
"""
Advanced Circular Import Resolution Utility

Provides comprehensive mechanisms for resolving circular import dependencies
in a complex database model ecosystem.
"""

import importlib
import logging
import sys
import traceback
from typing import (
    Any, Callable, Dict, List, Optional,
    Type, TypeVar, Union, Set
)

# Setup logging
logger = logging.getLogger(__name__)

# Type variables for generic typing
T = TypeVar('T')
ModelType = TypeVar('ModelType')


class CircularImportResolver:
    """
    Advanced circular import management system.

    Provides robust mechanisms for:
    - Lazy module and class loading
    - Dependency tracking
    - Runtime import resolution
    """

    # Singleton instance
    _instance = None

    # Class-level registries
    _lazy_imports: Dict[str, Dict[str, str]] = {}
    _import_dependencies: Dict[str, Set[str]] = {}
    _type_registry: Dict[str, Type] = {}

    def __new__(cls):
        """
        Singleton pattern implementation.

        Returns:
            CircularImportResolver: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            logger.debug("Created new CircularImportResolver instance")
        return cls._instance

    @classmethod
    def register_lazy_import(
            cls,
            target_name: str,
            module_path: str,
            class_name: Optional[str] = None
    ) -> None:
        """
        Register a lazy import for deferred loading.

        Args:
            target_name: Unique identifier for the import
            module_path: Full Python path to the module
            class_name: Optional specific class name to import
        """
        try:
            cls._lazy_imports[target_name] = {
                'module_path': module_path,
                'class_name': class_name or target_name.split('.')[-1]
            }
            logger.debug(f"Registered lazy import: {target_name} -> {module_path}")
        except Exception as e:
            logger.error(f"Lazy import registration failed for {target_name}: {e}")

    @classmethod
    def resolve_lazy_import(cls, target_name: str) -> Any:
        """
        Resolve a previously registered lazy import.

        Args:
            target_name: Unique identifier for the import

        Returns:
            The imported module or class

        Raises:
            ImportError: If resolution fails
        """
        if target_name not in cls._lazy_imports:
            raise ImportError(f"No lazy import registered for {target_name}")

        try:
            # Retrieve import configuration
            import_info = cls._lazy_imports[target_name]

            # Import the module
            module = importlib.import_module(import_info['module_path'])

            # Get the specific class or entire module
            if import_info['class_name']:
                return getattr(module, import_info['class_name'])

            return module
        except Exception as e:
            logger.error(f"Lazy import resolution failed for {target_name}: {e}")
            raise ImportError(f"Could not resolve lazy import {target_name}: {e}")

    @classmethod
    def track_import_dependency(
            cls,
            source_module: str,
            dependent_module: str
    ) -> None:
        """
        Track import dependencies between modules.

        Args:
            source_module: Module providing the import
            dependent_module: Module dependent on the source
        """
        if source_module not in cls._import_dependencies:
            cls._import_dependencies[source_module] = set()

        cls._import_dependencies[source_module].add(dependent_module)
        logger.debug(f"Tracked import dependency: {source_module} -> {dependent_module}")

    @classmethod
    def get_import_dependencies(cls, module_name: str) -> Set[str]:
        """
        Retrieve import dependencies for a given module.

        Args:
            module_name: Module to check dependencies for

        Returns:
            Set of dependent modules
        """
        return cls._import_dependencies.get(module_name, set())

    @classmethod
    def register_type(
            cls,
            type_name: str,
            type_obj: Type
    ) -> None:
        """
        Register a type for runtime resolution.

        Args:
            type_name: Unique identifier for the type
            type_obj: The type to register
        """
        cls._type_registry[type_name] = type_obj
        logger.debug(f"Registered type: {type_name}")

    @classmethod
    def resolve_type(cls, type_name: str) -> Optional[Type]:
        """
        Resolve a registered type.

        Args:
            type_name: Unique identifier for the type

        Returns:
            The resolved type or None
        """
        return cls._type_registry.get(type_name)

    @classmethod
    def reset(cls) -> None:
        """
        Reset all registries. Useful for testing.
        """
        cls._lazy_imports.clear()
        cls._import_dependencies.clear()
        cls._type_registry.clear()
        logger.info("Circular import resolver registries reset")


# Convenience functions for direct usage
def lazy_import(
        module_path: str,
        class_name: Optional[str] = None
) -> Any:
    """
    Convenience function for lazy importing a module or class.

    Args:
        module_path: Full Python path to the module
        class_name: Optional specific class name to import

    Returns:
        Imported module or class
    """
    resolver = CircularImportResolver()

    try:
        # Import the module
        module = importlib.import_module(module_path)

        # Return specific class if provided
        if class_name:
            return getattr(module, class_name)

        return module
    except Exception as e:
        logger.error(f"Lazy import failed for {module_path}.{class_name}: {e}")
        raise ImportError(f"Could not lazy import {module_path}.{class_name}: {e}")


def register_lazy_import(
        target_name: str,
        module_path: str,
        class_name: Optional[str] = None
) -> None:
    """
    Register a lazy import for deferred loading.

    Args:
        target_name: Unique identifier for the import
        module_path: Full Python path to the module
        class_name: Optional specific class name to import
    """
    resolver = CircularImportResolver()
    resolver.register_lazy_import(target_name, module_path, class_name)


def resolve_lazy_import(target_name: str) -> Any:
    """
    Resolve a previously registered lazy import.

    Args:
        target_name: Unique identifier for the import

    Returns:
        The imported module or class
    """
    resolver = CircularImportResolver()
    return resolver.resolve_lazy_import(target_name)


# Create singleton instance
_resolver_instance = CircularImportResolver()

# Export key components
__all__ = [
    'CircularImportResolver',
    'lazy_import',
    'register_lazy_import',
    'resolve_lazy_import'
]