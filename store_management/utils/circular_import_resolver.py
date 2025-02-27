"""
Utility for resolving circular imports.

This module provides utilities to help resolve circular imports
by deferring imports until they are actually needed.
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
    to avoid circular import issues.
    """

    _module_cache: Dict[str, Any] = {}
    _class_cache: Dict[str, Any] = {}
    _lazy_imports: Dict[str, Callable] = {}
    _registered_modules: Set[str] = set()

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
        if module_path in cls._module_cache:
            return cls._module_cache[module_path]

        try:
            module = importlib.import_module(module_path)
            cls._module_cache[module_path] = module
            return module
        except ImportError as e:
            logging.error(f"Failed to import module {module_path}: {e}")
            raise

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
    def lazy_import(cls, module_path: str, class_name: Optional[str] = None) -> Callable:
        """
        Lazily import a module or class.

        Use this as a decorator to defer imports until the function is called.

        Args:
            module_path: Dot-separated path to the module
            class_name: Optional name of the class to import

        Returns:
            A decorator function

        Example:
            @CircularImportResolver.lazy_import('services.implementations.material_service', 'MaterialService')
            def get_material_service():
                return MaterialService()
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            def wrapper(*args, **kwargs) -> T:
                try:
                    if class_name:
                        # Import the specific class
                        imported = cls.get_class(module_path, class_name)
                    else:
                        # Import the entire module
                        imported = cls.get_module(module_path)

                    # Add the imported module or class to the function's globals
                    func.__globals__[class_name or module_path.split('.')[-1]] = imported

                    # Call the original function
                    return func(*args, **kwargs)
                except (ImportError, AttributeError) as e:
                    logging.error(f"Lazy import failed: {e}")
                    raise

            return wrapper

        return decorator

    @classmethod
    def register_lazy_import(cls, import_path: str, loader_func: Optional[Callable] = None) -> None:
        """
        Register a lazy import to be resolved later.

        Args:
            import_path: Dot-separated path including module and class (e.g. 'module.path.ClassName')
            loader_func: Optional function that returns the imported object
        """
        if loader_func is None:
            # If no loader function is provided, create a default one
            module_path, class_name = import_path.rsplit('.', 1)

            def default_loader():
                try:
                    return cls.get_class(module_path, class_name)
                except (ImportError, AttributeError) as e:
                    logging.error(f"Failed to lazy load {import_path}: {e}")
                    return None

            loader_func = default_loader

        cls._lazy_imports[import_path] = loader_func

        # Mark the module as registered
        module_path = import_path.rsplit('.', 1)[0]
        cls._registered_modules.add(module_path)

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

        loader = cls._lazy_imports[import_path]
        return loader()

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


def lazy_import(module_path: str, class_name: Optional[str] = None) -> Callable:
    """
    Decorator for lazy importing modules or classes.

    Args:
        module_path: Dot-separated path to the module
        class_name: Optional name of the class to import

    Returns:
        A decorator function
    """
    return CircularImportResolver.lazy_import(module_path, class_name)


def register_lazy_import(import_path: str, loader_func: Optional[Callable] = None) -> None:
    """
    Register a lazy import to be resolved later.

    Args:
        import_path: Dot-separated path including module and class
        loader_func: Optional function that returns the imported object
    """
    CircularImportResolver.register_lazy_import(import_path, loader_func)


def resolve_lazy_import(import_path: str) -> Any:
    """
    Resolve a previously registered lazy import.

    Args:
        import_path: The full import path to resolve

    Returns:
        The imported object
    """
    return CircularImportResolver.resolve_lazy_import(import_path)


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