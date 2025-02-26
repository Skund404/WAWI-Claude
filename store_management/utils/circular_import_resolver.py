# store_management/utils/circular_import_resolver.py
"""
Circular Import Resolver Utility.

Provides mechanisms to handle and resolve circular import dependencies.
"""

import importlib
import logging
import sys
from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar('T')

class CircularImportResolver:
    """
    Utility class to resolve circular import dependencies.
    """
    _module_cache: Dict[str, Any] = {}
    _lazy_imports: Dict[str, Callable[[], Any]] = {}

    @classmethod
    def lazy_import(
        cls,
        module_path: str,
        class_name: Optional[str] = None
    ) -> Any:
        """
        Lazily import a module or class to break circular dependencies.

        Args:
            module_path (str): Full module path to import
            class_name (Optional[str], optional): Specific class to import

        Returns:
            Any: Imported module or class
        """
        try:
            # Check cache first
            if module_path in cls._module_cache:
                module = cls._module_cache[module_path]
            else:
                # Dynamically import the module
                module = importlib.import_module(module_path)
                cls._module_cache[module_path] = module

            # If a specific class is requested
            if class_name:
                return getattr(module, class_name)

            return module

        except ImportError as e:
            logging.error(f"Circular import resolution failed for {module_path}: {e}")
            raise

    @classmethod
    def register_lazy_import(
        cls,
        key: str,
        import_func: Callable[[], Any]
    ):
        """
        Register a lazy import function.

        Args:
            key (str): Unique key for the import
            import_func (Callable[[], Any]): Function to lazily import
        """
        cls._lazy_imports[key] = import_func

    @classmethod
    def get_lazy_import(
        cls,
        key: str
    ) -> Any:
        """
        Retrieve a lazily imported module or class.

        Args:
            key (str): Unique key for the import

        Returns:
            Any: Imported module or class
        """
        import_func = cls._lazy_imports.get(key)
        if import_func:
            return import_func()
        raise KeyError(f"No lazy import registered for key: {key}")

def get_module(module_path: str) -> Any:
    """
    Convenience function to get a module, breaking potential circular imports.

    Args:
        module_path (str): Full module path to import

    Returns:
        Any: Imported module
    """
    return CircularImportResolver.lazy_import(module_path)