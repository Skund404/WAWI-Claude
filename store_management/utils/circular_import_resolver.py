# utils/circular_import_resolver.py
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
import inspect
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
    cast,
    Set,
    Tuple,
    get_type_hints
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

    This is implemented as a singleton to ensure consistent state across imports.
    """
    # Class instance for singleton pattern
    _instance = None

    # Class-level registries for managing imports and dependencies
    _model_registry: Dict[str, Type] = {}
    _lazy_imports: Dict[str, Dict[str, str]] = {}
    _relationship_registry: Dict[str, Dict[str, Callable]] = {}
    _type_aliases: Dict[str, Type] = {}
    _import_dependencies: Dict[str, Set[str]] = {}

    def __new__(cls):
        """
        Singleton pattern implementation.

        Returns:
            CircularImportResolver: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(CircularImportResolver, cls).__new__(cls)
            logger.debug("Created new CircularImportResolver instance")
        return cls._instance

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
                'class_name': class_name or target_name.split('.')[-1]
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
            raise ImportError(f"Circular import resolution failed for {target_name}: {e}")

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

    @classmethod
    def resolve_lazy_relationships(cls) -> None:
        """
        Resolve all registered relationships across all models.

        This is useful during application startup to ensure all
        relationships are properly initialized.
        """
        for model_name in cls._relationship_registry:
            try:
                cls.resolve_relationships(model_name)
                logger.debug(f"Resolved relationships for model {model_name}")
            except Exception as e:
                logger.error(f"Failed to resolve relationships for model {model_name}: {e}")


# Standalone convenience functions
def get_module(module_path: str) -> ModuleType:
    """
    Get a module by path, importing it if necessary.

    Args:
        module_path: Full Python path to the module

    Returns:
        The imported module

    Raises:
        ImportError: If the module cannot be imported
    """
    try:
        return importlib.import_module(module_path)
    except Exception as e:
        logger.error(f"Failed to import module {module_path}: {e}")
        raise ImportError(f"Could not import module {module_path}: {e}")


def get_class(module_path: str, class_name: str) -> Type:
    """
    Get a class from a module, importing the module if necessary.

    Args:
        module_path: Full Python path to the module
        class_name: Name of the class to retrieve

    Returns:
        The requested class

    Raises:
        ImportError: If the module or class cannot be found
    """
    try:
        module = get_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to get class {class_name} from {module_path}: {e}")
        raise ImportError(f"Could not get class {class_name} from {module_path}: {e}")


def lazy_import(module_path: str, class_name: Optional[str] = None) -> Any:
    """
    Convenience function for lazy importing a module or class.

    Args:
        module_path: Full Python path to the module
        class_name: Optional specific class name to import

    Returns:
        Imported module or class
    """
    try:
        module = get_module(module_path)

        if class_name:
            return getattr(module, class_name)

        return module
    except Exception as e:
        logger.error(f"Lazy import failed for {module_path}.{class_name}: {e}")
        raise ImportError(f"Lazy import failed for {module_path}.{class_name}: {e}")


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
    CircularImportResolver.register_lazy_import(
        target_name,
        module_path,
        class_name
    )


def resolve_lazy_import(target_name: str) -> Any:
    """
    Resolve a previously registered lazy import.

    Args:
        target_name: Unique identifier for the import

    Returns:
        The imported model or class
    """
    return CircularImportResolver.resolve_lazy_import(target_name)


def register_relationship(
        model_name: str,
        relationship_name: str,
        relationship_config: Callable
) -> None:
    """
    Register a relationship configuration for lazy resolution.

    Args:
        model_name: Name of the model owning the relationship
        relationship_name: Name of the relationship attribute
        relationship_config: Callable returning the relationship configuration
    """
    CircularImportResolver.register_relationship(
        model_name,
        relationship_name,
        relationship_config
    )


def resolve_relationship(model_name: str, relationship_name: str) -> Any:
    """
    Resolve a specific relationship for a model.

    Args:
        model_name: Name of the model owning the relationship
        relationship_name: Name of the relationship to resolve

    Returns:
        The resolved relationship configuration

    Raises:
        KeyError: If the relationship is not registered
    """
    relationships = CircularImportResolver.resolve_relationships(model_name)

    if relationship_name not in relationships:
        raise KeyError(f"No relationship named {relationship_name} registered for model {model_name}")

    return relationships[relationship_name]


def resolve_lazy_relationships() -> None:
    """
    Resolve all registered lazy relationships.
    """
    CircularImportResolver.resolve_lazy_relationships()


def lazy_relationship(model_path: str, relationship_attr: str) -> Callable:
    """
    Create a lazy relationship configuration.

    This function returns a decorator that can be used to define
    relationships that depend on models not yet imported.

    Args:
        model_path: Full path to the related model
        relationship_attr: Attribute name on the related model

    Returns:
        Callable decorator for lazy relationship definition
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get the model at runtime
            try:
                if '.' in model_path:
                    module_name, class_name = model_path.rsplit('.', 1)
                    model = get_class(module_name, class_name)
                else:
                    model = resolve_lazy_import(model_path)

                # Get relationship configuration
                return func(model, relationship_attr, *args, **kwargs)
            except Exception as e:
                logger.error(f"Failed to resolve lazy relationship to {model_path}.{relationship_attr}: {e}")
                raise

        return wrapper

    return decorator


# Create instance at module load time to initialize the singleton
_resolver_instance = CircularImportResolver()

# Expose key functionality
__all__ = [
    'CircularImportResolver',
    'lazy_import',
    'register_lazy_import',
    'resolve_lazy_import',
    'register_relationship',
    'resolve_relationship',
    'resolve_lazy_relationships',
    'get_module',
    'get_class',
    'lazy_relationship'
]