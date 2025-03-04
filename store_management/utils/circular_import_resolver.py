# utils/circular_import_resolver.py
"""
Enhanced utility for resolving circular imports.

This module provides utilities to help resolve circular imports
by deferring imports until they are actually needed, with improved
support for SQLAlchemy models and relationships.
"""

import importlib
import logging
import sys
from typing import Any, Callable, Dict, Optional, Set, Type, TypeVar, Union

# Type variable for generic function
T = TypeVar('T')

class CircularImportResolver:
    """
    Utility class for resolving circular imports.

    This class provides methods to lazily import modules and classes
    to avoid circular import issues, with specialized handling for
    SQLAlchemy models and relationships.
    """

    _module_cache: Dict[str, Any] = {}
    _class_cache: Dict[str, Any] = {}
    _lazy_imports: Dict[str, Callable] = {}
    _registered_modules: Set[str] = set()
    _import_stack: Set[str] = set()  # Track imports in process to detect circular dependencies
    _relationship_map: Dict[str, Dict[str, str]] = {}  # Track relationship definitions for models

    @classmethod
    def get_module(cls, module_path: str) -> Any:
        """
        Get a module by its path, with caching.

        Args:
            module_path: Dot-separated path to the module

        Returns:
            The imported module

        Raises:
            ImportError: If the module cannot be imported
        """
        # Check for circular import
        if module_path in cls._import_stack:
            logging.debug(f"Potential circular import detected for {module_path}")
            # Return from cache if available to break the cycle
            if module_path in cls._module_cache:
                return cls._module_cache[module_path]
            raise ImportError(f"Circular import detected for {module_path}")

        # Return cached module if available
        if module_path in cls._module_cache:
            return cls._module_cache[module_path]

        try:
            # Add to import stack to detect circular imports
            cls._import_stack.add(module_path)

            module = importlib.import_module(module_path)
            cls._module_cache[module_path] = module
            return module
        except ImportError as e:
            logging.error(f"Failed to import module {module_path}: {e}")
            raise
        finally:
            # Remove from import stack
            cls._import_stack.discard(module_path)

    @classmethod
    def get_class(cls, module_path: str, class_name: str) -> Type:
        """
        Get a class from a module, with caching.

        Args:
            module_path: Dot-separated path to the module
            class_name: Name of the class to import

        Returns:
            The imported class

        Raises:
            ImportError: If the module or class cannot be imported
            AttributeError: If the class doesn't exist in the module
        """
        cache_key = f"{module_path}.{class_name}"
        if cache_key in cls._class_cache:
            return cls._class_cache[cache_key]

        try:
            module = cls.get_module(module_path)
            class_obj = getattr(module, class_name)
            cls._class_cache[cache_key] = class_obj
            return class_obj
        except (ImportError, AttributeError) as e:
            logging.error(f"Failed to import class {class_name} from {module_path}: {e}")
            raise

    @classmethod
    def lazy_import(cls, module_path: str, class_name: Optional[str] = None) -> Any:
        """
        Lazily import a module or class.

        This version returns a proxy object that resolves the import when
        accessed, providing better compatibility with SQLAlchemy relationships.

        Args:
            module_path: Dot-separated path to the module
            class_name: Optional name of the class to import

        Returns:
            LazyImportProxy or the module itself

        Example:
            Material = lazy_import('database.models.material', 'Material')
            material = Material(name='test')  # Import only happens here
        """
        if class_name:
            # For class imports, return a proxy
            return LazyImportProxy(lambda: cls.get_class(module_path, class_name))
        else:
            # For module imports, we can directly return the module
            return cls.get_module(module_path)

    @classmethod
    def register_lazy_import(cls, import_path: str, module_path: str = None) -> None:
        """
        Register a lazy import to be resolved later.

        Args:
            import_path: Dot-separated path including module and class (e.g. 'module.path.ClassName')
            module_path: Optional module path if different from import_path

        Example:
            register_lazy_import('database.models.material.Material', 'database.models.material')
        """
        if not module_path:
            # Default to the module part of the import path
            # Make sure the import_path has at least one dot before trying to split
            if '.' in import_path:
                module_path = import_path.rsplit('.', 1)[0]
            else:
                # If there's no dot, then use the import_path as both module and class name
                module_path = import_path
                class_name = import_path
                logger.warning(
                    f"Import path '{import_path}' does not contain a module separator. Using as both module and class.")

        # Only try to extract class_name if we didn't already set it above
        if not locals().get('class_name'):
            if '.' in import_path:
                class_name = import_path.rsplit('.', 1)[1]
            else:
                class_name = import_path

        def loader_func():
            try:
                return cls.get_class(module_path, class_name)
            except (ImportError, AttributeError) as e:
                logging.error(f"Failed to lazy load {import_path}: {e}")
                return None

        cls._lazy_imports[import_path] = loader_func

        # Mark the module as registered
        cls._registered_modules.add(module_path)

    @classmethod
    def register_relationship(cls, source_model: str, relationship_name: str, target_model: str) -> None:
        """
        Register a relationship between SQLAlchemy models.

        This helps with generating proper join conditions even with circular dependencies.

        Args:
            source_model: Full path to the source model (e.g. 'database.models.project.Project')
            relationship_name: Name of the relationship attribute
            target_model: Full path to the target model (e.g. 'database.models.component.Component')
        """
        if source_model not in cls._relationship_map:
            cls._relationship_map[source_model] = {}

        cls._relationship_map[source_model][relationship_name] = target_model

        # Also register both models for lazy import
        src_module = source_model.rsplit('.', 1)[0]
        tgt_module = target_model.rsplit('.', 1)[0]

        cls.register_lazy_import(source_model, src_module)
        cls.register_lazy_import(target_model, tgt_module)

    @classmethod
    def resolve_lazy_import(cls, import_path: str) -> Any:
        """
        Resolve a previously registered lazy import.

        Args:
            import_path: The full import path to resolve

        Returns:
            The imported object or None if not found

        Raises:
            KeyError: If the import path hasn't been registered
        """
        if import_path not in cls._lazy_imports:
            raise KeyError(f"No lazy import registered for {import_path}")

        # Check if we're in a circular import situation
        if import_path in cls._import_stack:
            logging.debug(f"Circular resolution detected for {import_path}, returning partial result")
            return None

        try:
            cls._import_stack.add(import_path)
            loader = cls._lazy_imports[import_path]
            result = loader()
            return result
        finally:
            cls._import_stack.discard(import_path)

    @classmethod
    def get_relationship_info(cls, source_model: str, relationship_name: str) -> Optional[str]:
        """
        Get information about a registered relationship.

        Args:
            source_model: Full path to the source model
            relationship_name: Name of the relationship attribute

        Returns:
            Target model path or None if not found
        """
        if source_model in cls._relationship_map and relationship_name in cls._relationship_map[source_model]:
            return cls._relationship_map[source_model][relationship_name]
        return None

    @classmethod
    def is_module_registered(cls, module_path: str) -> bool:
        """
        Check if a module has been registered for lazy imports.

        Args:
            module_path: The module path to check

        Returns:
            True if the module is registered, False otherwise
        """
        return module_path in cls._registered_modules

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all caches and registrations."""
        cls._module_cache.clear()
        cls._class_cache.clear()
        cls._lazy_imports.clear()
        cls._registered_modules.clear()
        cls._import_stack.clear()
        cls._relationship_map.clear()


class LazyImportProxy:
    """
    Proxy class for lazy imports that resolves the actual class on first use.
    Compatible with SQLAlchemy relationship targets.
    """
    def __init__(self, import_func: Callable[[], Type[T]]):
        self._import_func = import_func
        self._actual_class = None

    def __call__(self, *args, **kwargs):
        if self._actual_class is None:
            self._actual_class = self._import_func()

        return self._actual_class(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        if self._actual_class is None:
            self._actual_class = self._import_func()

        return getattr(self._actual_class, name)


# Function aliases for convenience
def get_module(module_path: str) -> Any:
    """
    Get a module by its path.

    Args:
        module_path: Dot-separated path to the module

    Returns:
        The imported module
    """
    return CircularImportResolver.get_module(module_path)


def get_class(module_path: str, class_name: str) -> Type:
    """
    Get a class from a module.

    Args:
        module_path: Dot-separated path to the module
        class_name: Name of the class to import

    Returns:
        The imported class
    """
    return CircularImportResolver.get_class(module_path, class_name)


def lazy_import(module_path: str, class_name: Optional[str] = None) -> Any:
    """
    Lazily import a module or class.

    Args:
        module_path: Dot-separated path to the module
        class_name: Optional name of the class to import

    Returns:
        LazyImportProxy or the module itself
    """
    return CircularImportResolver.lazy_import(module_path, class_name)


def register_lazy_import(import_path: str, module_path: str = None) -> None:
    """
    Register a lazy import to be resolved later.

    Args:
        import_path: Dot-separated path including module and class
        module_path: Optional module path if different from import_path
    """
    CircularImportResolver.register_lazy_import(import_path, module_path)


def register_relationship(source_model: str, relationship_name: str, target_model: str) -> None:
    """
    Register a relationship between SQLAlchemy models.

    Args:
        source_model: Full path to the source model
        relationship_name: Name of the relationship attribute
        target_model: Full path to the target model
    """
    CircularImportResolver.register_relationship(source_model, relationship_name, target_model)


def resolve_lazy_import(import_path: str) -> Any:
    """
    Resolve a previously registered lazy import.

    Args:
        import_path: The full import path to resolve

    Returns:
        The imported object
    """
    return CircularImportResolver.resolve_lazy_import(import_path)


def get_relationship_info(source_model: str, relationship_name: str) -> Optional[str]:
    """
    Get information about a registered relationship.

    Args:
        source_model: Full path to the source model
        relationship_name: Name of the relationship attribute

    Returns:
        Target model path or None if not found
    """
    return CircularImportResolver.get_relationship_info(source_model, relationship_name)


def is_module_registered(module_path: str) -> bool:
    """
    Check if a module has been registered for lazy imports.

    Args:
        module_path: The module path to check

    Returns:
        True if the module is registered, False otherwise
    """
    return CircularImportResolver.is_module_registered(module_path)


def clear_cache() -> None:
    """Clear all circular import resolver caches."""
    CircularImportResolver.clear_cache()