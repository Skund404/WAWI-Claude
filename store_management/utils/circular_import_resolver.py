# utils/circular_import_resolver.py
"""
Circular import resolver utility.

This module provides utilities for resolving circular import dependencies
in the application, allowing modules to reference each other without
causing import errors.
"""

import importlib
import logging
import sys
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

# Configure logger - use basic logging to avoid circular imports
logger = logging.getLogger(__name__)


class CircularImportResolver:
    """
    Utility class for resolving circular import dependencies.

    This class maintains a cache of imported modules and provides
    methods for safely importing modules that may have circular
    dependencies.
    """

    # Cache of imported modules
    _module_cache: Dict[str, Optional[ModuleType]] = {}

    # Modules currently being imported (to detect circular imports)
    _importing_modules: List[str] = []

    # Resolves circular imports by lazily importing modules.
    _pending_imports: Dict[str, Optional[Exception]] = {}

    @classmethod
    def register_pending_import(cls, module_name: str, exception: Optional[Exception] = None) -> None:
        """Registers a pending import to be resolved later.

        Args:
            module_name (str): The name of the module to be imported.
            exception (Optional[Exception]): The exception that occurred during the import attempt.
        """
        cls._pending_imports[module_name] = exception

    @classmethod
    def resolve_pending_imports(cls) -> None:
        """Resolves all pending imports."""
        for module_name, exception in cls._pending_imports.items():
            if exception is None:
                logger.warning(f"Resolving pending import: {module_name}")
                try:
                    __import__(module_name)
                except Exception as e:
                    logger.error(f"Error resolving pending import: {module_name}")
                    raise e
            else:
                logger.error(f"Error resolving pending import: {module_name}")
                raise exception

    @classmethod
    def get_module(cls, module_name: str) -> Any:
        """Lazily imports a module and returns it.

        Args:
            module_name (str): The name of the module to import.

        Returns:
            Any: The imported module.
        """
        if module_name not in sys.modules:
            __import__(module_name)
        return sys.modules[module_name]

    @classmethod
    def get_class(cls, module_path: str, class_name: str) -> Optional[type]:
        """
        Get a class from a module, handling circular dependencies.

        Args:
            module_path: Dot-separated import path to the module
            class_name: Name of the class to import

        Returns:
            The imported class, or None if import fails
        """
        module = cls.get_module(module_path)
        if module and hasattr(module, class_name):
            return getattr(module, class_name)
        return None

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the module cache.

        This can be useful for testing or when modules are
        dynamically reloaded.
        """
        cls._module_cache.clear()
        logger.debug("Cleared module cache")


# Convenience function to get a module
def get_module(module_path: str) -> Optional[ModuleType]:
    """
    Get a module by its import path, handling circular dependencies.

    Args:
        module_path: Dot-separated import path to the module

    Returns:
        The imported module, or None if import fails
    """
    module = None
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        CircularImportResolver.register_pending_import(module_path, e)
    return module
