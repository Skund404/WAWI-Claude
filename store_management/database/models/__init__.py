# database/models/__init__.py
"""
Database models package initialization.

This module initializes the models package and registers all model classes
to make them available throughout the application.
"""

import importlib
import logging
from typing import Dict, Optional, Type, Any

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Registry for all model classes.

    Provides methods to register and retrieve model classes by name.
    """
    _models: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, model_class: Type) -> None:
        """
        Register a model class.

        Args:
            name: Name to register the model under
            model_class: The model class to register
        """
        cls._models[name] = model_class
        logger.debug(f"Registered model: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        """
        Get a registered model class.

        Args:
            name: Name of the model to retrieve

        Returns:
            Type or None: The model class, or None if not found
        """
        return cls._models.get(name)

    @classmethod
    def get_all_models(cls) -> Dict[str, Type]:
        """
        Get all registered model classes.

        Returns:
            Dict[str, Type]: Dictionary of all registered model classes
        """
        return cls._models.copy()


def _safe_import(module_name: str, class_name: str) -> Optional[Type]:
    """
    Safely import a class from a module.

    Args:
        module_name: Name of the module to import from
        class_name: Name of the class to import

    Returns:
        Type or None: The imported class, or None if import failed
    """
    try:
        module = importlib.import_module(f'database.models.{module_name}')
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.warning(f"Failed to import {class_name} from {module_name}: {e}")
        return None


def _register_models() -> None:
    """
    Register all model classes.

    This function imports and registers all model classes that should be
    available throughout the application.
    """
    # Import base models first
    from database.models.base import Base, BaseModel
    from database.models.model_metaclass import ModelMetaclass

    # Register core models
    # These should be imported in dependency order
    model_imports = [
        ('enums', 'ProjectStatus'),
        ('enums', 'ProjectType'),
        ('enums', 'SkillLevel'),
        ('enums', 'MaterialType'),
        ('project', 'Project'),
        # Add other models here
    ]

    for module_name, class_name in model_imports:
        model_class = _safe_import(module_name, class_name)
        if model_class:
            ModelRegistry.register(class_name, model_class)


# Register all models when this module is imported
_register_models()

# Export the registry
__all__ = ['ModelRegistry']