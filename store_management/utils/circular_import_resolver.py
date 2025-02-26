# utils/circular_import_resolver.py
"""
Utility module for resolving circular import issues in the project.

This module provides mechanisms to handle complex import scenarios
and break circular dependency chains.
"""

import importlib
import logging
import sys
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple


class CircularImportResolver:
    """
    A utility class to resolve circular import dependencies with various strategies.

    This resolver provides methods to safely import modules, handle
    circular dependencies, and manage complex import scenarios.
    """

    _import_cache: Dict[str, Any] = {}
    _module_aliases: Dict[str, str] = {
        'models.order': 'database.models.order',
        'models.material': 'database.models.material',
        # Add more mappings as needed
    }

    @classmethod
    def get_module(cls, module_name: str) -> ModuleType:
        """
        Safely retrieve a module, handling potential circular import issues.

        Args:
            module_name (str): Fully qualified module name to import

        Returns:
            ModuleType: The imported module

        Raises:
            ImportError: If the module cannot be imported
        """
        # Check cache first
        if module_name in cls._import_cache:
            return cls._import_cache[module_name]

        # Check for module alias
        actual_module_name = cls._module_aliases.get(module_name, module_name)

        try:
            # Attempt to import the module
            module = importlib.import_module(actual_module_name)

            # Cache the module
            cls._import_cache[module_name] = module

            return module
        except ImportError as e:
            logging.error(f"Failed to import module {module_name}: {e}")

            # Fallback strategies
            try:
                # Try using sys.path manipulation
                if actual_module_name not in sys.path:
                    sys.path.append(actual_module_name.replace('.', '/'))
                module = importlib.import_module(actual_module_name)
                cls._import_cache[module_name] = module
                return module
            except ImportError:
                logging.critical(f"Absolute import failed for {module_name}")
                raise ImportError(f"Could not import module {module_name}")

    @classmethod
    def add_module_alias(cls, original_name: str, actual_name: str) -> None:
        """
        Add a module alias to help resolve import paths.

        Args:
            original_name (str): The original module name
            actual_name (str): The actual fully qualified module name
        """
        cls._module_aliases[original_name] = actual_name

    @classmethod
    def clear_import_cache(cls) -> None:
        """
        Clear the import cache to force fresh imports.
        """
        cls._import_cache.clear()


def get_module(module_name: str) -> ModuleType:
    """
    Convenience function to get a module using CircularImportResolver.

    Args:
        module_name (str): Fully qualified module name to import

    Returns:
        ModuleType: The imported module
    """
    return CircularImportResolver.get_module(module_name)