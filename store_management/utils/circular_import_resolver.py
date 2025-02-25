# utils/circular_import_resolver.py
"""
Module for resolving circular import issues in the leatherworking store management application.

This module provides a mechanism to manage and prevent circular imports by
registering and lazily importing modules.
"""

import importlib
import logging
import sys
from types import ModuleType  # Updated import for ModuleType
from typing import Dict, Optional, Any, Callable, List, Tuple

class CircularImportResolver:
    """
    A singleton class to manage and resolve circular import dependencies.

    This class provides mechanisms to:
    - Register modules
    - Prevent circular imports
    - Lazily import modules as needed
    """

    _instance = None
    _registered_modules: Dict[str, str] = {}
    _imported_modules: Dict[str, ModuleType] = {}

    def __new__(cls):
        """
        Ensure a singleton instance of the CircularImportResolver.

        Returns:
            CircularImportResolver: The singleton instance
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls.register_common_modules()
        return cls._instance

    @classmethod
    def register_module(cls, module_name: str, module_path: Optional[str] = None) -> None:
        """
        Register a module with its import path.

        Args:
            module_name (str): Name used to reference the module
            module_path (str, optional): Full import path for the module.
                                         Defaults to module_name if not provided.
        """
        module_path = module_path or module_name
        cls._registered_modules[module_name] = module_path

    @classmethod
    def get_module(cls, module_name: str) -> Optional[ModuleType]:
        """
        Retrieve a module by its registered name.

        Args:
            module_name (str): Name of the module to retrieve

        Returns:
            Optional[ModuleType]: The imported module or None if not found
        """
        # Check if module is already imported
        if module_name in cls._imported_modules:
            return cls._imported_modules[module_name]

        # Check if module is registered
        if module_name not in cls._registered_modules:
            logging.warning(f"Module {module_name} not registered")
            return None

        try:
            # Dynamically import the module
            module_path = cls._registered_modules[module_name]
            imported_module = importlib.import_module(module_path)
            cls._imported_modules[module_name] = imported_module
            return imported_module
        except ImportError as e:
            logging.error(f"Failed to import module {module_name}: {e}")
            return None

    @classmethod
    def register_common_modules(cls) -> None:
        """
        Register commonly used modules to prevent circular imports.
        """
        common_modules = [
            'database.models',
            'services.interfaces',
            'database.repositories',
            'config',
            'di.core',
        ]

        for module in common_modules:
            cls.register_module(module.split('.')[-1], module)

def get_module(module_name: str) -> Optional[ModuleType]:
    """
    Convenience function to get a module from the CircularImportResolver.

    Args:
        module_name (str): Name of the module to retrieve

    Returns:
        Optional[ModuleType]: The imported module or None if not found
    """
    resolver = CircularImportResolver()
    return resolver.get_module(module_name)