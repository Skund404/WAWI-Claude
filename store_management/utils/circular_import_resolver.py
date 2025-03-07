# database/models/circular_import_resolver.py
"""
Advanced Circular Import Resolution Utility

Provides comprehensive mechanisms for resolving circular import dependencies
in a complex database model ecosystem, with support for:
- Lazy imports
- Dynamic model registration
- Relationship management
- Type resolution
- Dependency tracking
"""

import importlib
import logging
import sys
from types import ModuleType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast, Set
)

# Setup logging
logger = logging.getLogger(__name__)

# Type variables for generic typing
T = TypeVar('T')
ModelType = TypeVar('ModelType')


class CircularImportResolver:
    """
    Comprehensive utility for managing circular import complexities.

    Provides advanced mechanisms for:
    - Lazy model loading
    - Relationship resolution
    - Dependency tracking
    - Type management
    """

    # Class-level registries for managing imports and dependencies
    _model_registry: Dict[str, Type] = {}
    _lazy_imports: Dict[str, Dict[str, str]] = {}
    _relationship_registry: Dict[str, Dict[str, Callable]] = {}
    _type_aliases: Dict[str, Type] = {}
    _import_dependencies: Dict[str, Set[str]] = {}

    @classmethod
    def register_model(
            cls,
            model_name: str,
            model_class: Type,
            module_path: Optional[str] = None
    ) -> None:
        """
        Register a model class with optional module path tracking.

        Args:
            model_name: Unique identifier for the model
            model_class: The model class to register
            module_path: Optional path to the module containing the model
        """
        try:
            # Store the model in the registry
            cls._model_registry[model_name] = model_class

            # Track module path if provided
            if module_path:
                logger.debug(f"Registered model {model_name} from {module_path}")
        except Exception as e:
            logger.error(f"Error registering model {model_name}: {e}")
            raise

    @classmethod
    def get_model(cls, model_name: str) -> Type:
        """
        Retrieve a registered model class.

        Args:
            model_name: Unique identifier for the model

        Returns:
            The requested model class

        Raises:
            KeyError: If the model is not registered
        """
        if model_name not in cls._model_registry:
            # Attempt lazy loading if not directly registered
            try:
                return cls.resolve_lazy_import(model_name)
            except Exception:
                raise KeyError(f"Model '{model_name}' is not registered")

        return cls._model_registry[model_name]

    @classmethod
    def register_lazy_import(
            cls,
            target_name: str,
            module_path: str,
            class_name: Optional[str] = None
    ) -> None:
        """
        Register a lazy import for deferred model loading.

        Args:
            target_name: Unique identifier for the import
            module_path: Full Python path to the module
            class_name: Optional specific class name to import
        """
        try:
            # Store lazy import configuration
            cls._lazy_imports[target_name] = {
                'module_path': module_path,
                'class_name': class_name or target_name
            }
            logger.debug(f"Registered lazy import: {target_name} -> {module_path}.{class_name}")
        except Exception as e:
            logger.error(f"Error registering lazy import {target_name}: {e}")
            raise

    @classmethod
    def resolve_lazy_import(cls, target_name: str) -> Any:
        """
        Resolve a previously registered lazy import.

        Args:
            target_name: Unique identifier for the import

        Returns:
            The imported model or class

        Raises:
            ImportError: If resolution fails
        """
        if target_name not in cls._lazy_imports:
            raise ImportError(f"No lazy import registered for {target_name}")

        try:
            import_info = cls._lazy_imports[target_name]
            module = importlib.import_module(import_info['module_path'])

            # Import specific class or entire module
            if import_info['class_name']:
                model = getattr(module, import_info['class_name'])
            else:
                model = module

            # Register the resolved model
            cls.register_model(target_name, model)

            return model
        except Exception as e:
            logger.error(f"Failed to resolve lazy import {target_name}: {e}")
            raise ImportError(f"Circular import resolution failed for {target_name}")

    @classmethod
    def register_relationship(
            cls,
            model_name: str,
            relationship_name: str,
            relationship_config: Callable
    ) -> None:
        """
        Register a relationship configuration for lazy loading.

        Args:
            model_name: Name of the model owning the relationship
            relationship_name: Name of the relationship attribute
            relationship_config: Callable returning the relationship configuration
        """
        if model_name not in cls._relationship_registry:
            cls._relationship_registry[model_name] = {}

        cls._relationship_registry[model_name][relationship_name] = relationship_config
        logger.debug(f"Registered relationship: {model_name}.{relationship_name}")

    @classmethod
    def resolve_relationships(cls, model_name: str) -> Dict[str, Any]:
        """
        Resolve all registered relationships for a given model.

        Args:
            model_name: Name of the model to resolve relationships for

        Returns:
            Dictionary of resolved relationships
        """
        if model_name not in cls._relationship_registry:
            return {}

        resolved_relationships = {}
        for rel_name, rel_config in cls._relationship_registry[model_name].items():
            try:
                resolved_relationships[rel_name] = rel_config()
            except Exception as e:
                logger.error(f"Failed to resolve relationship {model_name}.{rel_name}: {e}")

        return resolved_relationships

    @classmethod
    def register_type_alias(cls, alias_name: str, actual_type: Type) -> None:
        """
        Register a type alias for resolution.

        Args:
            alias_name: Alias identifier
            actual_type: The actual type being aliased
        """
        cls._type_aliases[alias_name] = actual_type
        logger.debug(f"Registered type alias: {alias_name}")

    @classmethod
    def resolve_type_alias(cls, alias_name: str) -> Type:
        """
        Resolve a type alias.

        Args:
            alias_name: Alias to resolve

        Returns:
            The resolved type

        Raises:
            KeyError: If no alias is found
        """
        if alias_name not in cls._type_aliases:
            raise KeyError(f"No type alias registered for {alias_name}")

        return cls._type_aliases[alias_name]

    @classmethod
    def track_import_dependency(cls, source_module: str, dependent_module: str) -> None:
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
    def reset(cls) -> None:
        """
        Reset all registries. Useful for testing and resetting state.
        """
        cls._model_registry.clear()
        cls._lazy_imports.clear()
        cls._relationship_registry.clear()
        cls._type_aliases.clear()
        cls._import_dependencies.clear()
        logger.info("Circular import resolver registries reset")


# Convenience imports and exports
def lazy_import(module_path: str, class_name: Optional[str] = None) -> Any:
    """
    Convenience wrapper for lazy import resolution.

    Args:
        module_path: Full Python path to the module
        class_name: Optional specific class name to import

    Returns:
        Imported module or class
    """
    try:
        module = importlib.import_module(module_path)

        if class_name:
            return getattr(module, class_name)

        return module
    except Exception as e:
        logger.error(f"Lazy import failed for {module_path}.{class_name}: {e}")
        raise


def register_lazy_import(
        target_name: str,
        module_path: str,
        class_name: Optional[str] = None
) -> None:
    """
    Convenience wrapper for registering lazy imports.

    Args:
        target_name: Unique identifier for the import
        module_path: Full Python path to the module
        class_name: Optional specific class name to import
    """
    CircularImportResolver.register_lazy_import(
        target_name,
        module_path,
        class_name or target_name
    )


# Expose key functionality
__all__ = [
    'CircularImportResolver',
    'lazy_import',
    'register_lazy_import'
]