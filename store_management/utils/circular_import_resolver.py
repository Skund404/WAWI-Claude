# utils/circular_import_resolver.py
import importlib
import logging
from typing import Any, Dict, Optional, Type


class CircularImportResolver:
    """
    A utility class for resolving circular imports in the application.

    This class provides mechanisms to handle circular dependencies by deferring
    imports and resolving them at runtime when needed.
    """

    # Dictionary to store pending imports that need to be resolved
    _pending_imports = {}

    # Cache for resolved classes to avoid repeated imports
    _class_cache = {}

    @classmethod
    def clear_cache(cls):
        """
        Clear the internal caches for pending imports and resolved classes.

        This is useful for testing or when resetting the application state.
        """
        cls._pending_imports.clear()
        cls._class_cache.clear()

    @classmethod
    def register_pending_import(cls, module_name: str, error: ImportError):
        """
        Register a pending import that failed due to circular dependencies.

        Args:
            module_name: The name of the module where the import failed
            error: The ImportError exception that was raised
        """
        if module_name not in cls._pending_imports:
            cls._pending_imports[module_name] = error
            logging.getLogger(__name__).debug(f"Registered pending import for {module_name}")

    @classmethod
    def resolve_class(cls, module_path: str, class_name: str) -> Type:
        """
        Resolve a class from a module path, handling circular dependencies.

        Args:
            module_path: The dotted path to the module
            class_name: The name of the class to import

        Returns:
            The requested class

        Raises:
            ImportError: If the class cannot be imported
        """
        cache_key = f"{module_path}.{class_name}"

        # Check if we already resolved this class
        if cache_key in cls._class_cache:
            return cls._class_cache[cache_key]

        try:
            # Try to import the module and get the class
            module = importlib.import_module(module_path)
            resolved_class = getattr(module, class_name)

            # Cache the resolved class
            cls._class_cache[cache_key] = resolved_class
            return resolved_class
        except ImportError as e:
            # Register the pending import and re-raise
            cls.register_pending_import(module_path, e)
            raise

    @classmethod
    def lazy_import(cls, module_path: str, class_name: Optional[str] = None) -> Any:
        """
        Lazily import a module or class to avoid circular dependencies.

        Args:
            module_path: The dotted path to the module
            class_name: Optional name of the class to import

        Returns:
            The imported module or class
        """
        if class_name:
            return cls.resolve_class(module_path, class_name)

        try:
            return importlib.import_module(module_path)
        except ImportError as e:
            cls.register_pending_import(module_path, e)
            raise