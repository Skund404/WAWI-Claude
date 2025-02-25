# database/models/__init__.py
"""
Model initialization and registration module.

This module handles dynamic model discovery and registration for the application.
"""

import importlib
import logging
from typing import Any, Dict, Optional, Type

from database.models.model_metaclass import Base, BaseModel, ModelMetaclass


class ModelRegistry:
    """
    A registry to manage and track model classes dynamically.
    """
    _registered_models: Dict[str, Type] = {}

    @classmethod
    def register_model(cls, model_name: str, model_class: Type) -> None:
        """
        Register a model class with the registry.

        Args:
            model_name (str): The name of the model
            model_class (Type): The model class to register
        """
        cls._registered_models[model_name] = model_class

    @classmethod
    def load_models(cls) -> None:
        """
        Load all models from the models package.

        This method dynamically imports model modules and registers
        all model classes that inherit from Base.
        """
        # List of model modules to import
        model_modules = [
            'base', 'components', 'config', 'enums', 'factories',
            'hardware', 'interfaces', 'leather', 'material', 'metrics',
            'mixins', 'order', 'order_item', 'pattern', 'product',
            'project', 'shopping_list', 'storage', 'supplier', 'transaction'
        ]

        for module_name in model_modules:
            try:
                # Dynamically import the module
                module = importlib.import_module(f'.{module_name}', package='database.models')

                # Find and register classes that inherit from Base
                for name, obj in module.__dict__.items():
                    if (isinstance(obj, type) and
                            issubclass(obj, Base) and
                            obj is not Base and
                            obj is not BaseModel):
                        cls.register_model(name, obj)
            except ImportError as e:
                logging.warning(f"Could not import model module {module_name}: {e}")
            except Exception as e:
                logging.error(f"Error processing model module {module_name}: {e}")


# Automatically load models when the module is imported
ModelRegistry.load_models()

# Export Base and BaseModel for convenience
__all__ = ['Base', 'BaseModel', 'ModelRegistry']