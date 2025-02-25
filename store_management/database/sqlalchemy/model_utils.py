# Relative path: store_management/database/sqlalchemy/model_utils.py

"""
Utility module for lazy loading of model classes to avoid circular imports.

This module provides a centralized, dynamic way to import and access model classes
without creating circular import dependencies.
"""

import importlib
import logging
from typing import Dict, Type, Any

# Configure logging
logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    A centralized registry for managing and accessing model classes.

    Provides lazy loading of model classes to prevent circular import issues
    and improve module dependency management.
    """

    _model_cache: Dict[str, Type[Any]] = {}
    _registry_initialized = False

    @classmethod
    def _initialize_registry(cls):
        """
        Lazy initialization of the model registry.
        Prevents unnecessary imports and resolves potential circular dependencies.
        """
        if not cls._registry_initialized:
            try:
                # Dynamically import models module
                models_module = importlib.import_module('database.models')

                # List of model names to cache
                model_names = [
                    "Supplier", "Order", "OrderItem", "Part", "Leather",
                    "Project", "ProjectComponent", "ShoppingList",
                    "ShoppingListItem", "Shelf", "InventoryTransaction",
                    "LeatherTransaction", "ProductionOrder", "ProducedItem"
                ]

                # Populate model cache
                for name in model_names:
                    if hasattr(models_module, name):
                        cls._model_cache[name] = getattr(models_module, name)
                    else:
                        logger.warning(f"Model {name} not found in models module")

                cls._registry_initialized = True
            except ImportError as e:
                logger.error(f"Failed to import models module: {e}")
                raise

    @classmethod
    def get_model_class(cls, model_name: str) -> Type[Any]:
        """
        Retrieve a model class by its name.

        Args:
            model_name (str): Name of the model class to retrieve

        Returns:
            Type[Any]: The requested model class

        Raises:
            ValueError: If the model class is not found
        """
        # Ensure registry is initialized
        if not cls._registry_initialized:
            cls._initialize_registry()

        # Retrieve model class
        if model_name not in cls._model_cache:
            raise ValueError(f"Model class '{model_name}' not found in registry")

        return cls._model_cache[model_name]

    @classmethod
    def get_all_model_classes(cls) -> Dict[str, Type[Any]]:
        """
        Retrieve all registered model classes.

        Returns:
            Dict[str, Type[Any]]: Dictionary of model names to their classes
        """
        # Ensure registry is initialized
        if not cls._registry_initialized:
            cls._initialize_registry()

        return cls._model_cache.copy()


def get_model_classes() -> Dict[str, Type[Any]]:
    """
    Convenience function to get all model classes.

    Returns:
        Dict[str, Type[Any]]: Dictionary of model names to their classes
    """
    return ModelRegistry.get_all_model_classes()


def get_model_class(model_name: str) -> Type[Any]:
    """
    Convenience function to get a specific model class by name.

    Args:
        model_name (str): Name of the model class to retrieve

    Returns:
        Type[Any]: The requested model class
    """
    return ModelRegistry.get_model_class(model_name)