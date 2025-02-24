# Path: database/models/circular_import_resolver.py
"""
Utility to resolve circular import dependencies in SQLAlchemy models.
"""

from typing import Any, Dict, Type
from sqlalchemy.orm import DeclarativeBase


class CircularImportResolver:
    """
    A utility class to manage and resolve circular import dependencies.

    This class provides a centralized way to register and retrieve model classes
    that might cause circular import issues.
    """

    _registered_models: Dict[str, Type[DeclarativeBase]] = {}

    @classmethod
    def register_model(cls, model_name: str, model_class: Type[DeclarativeBase]) -> None:
        """
        Register a model class with a given name.

        Args:
            model_name (str): Unique identifier for the model.
            model_class (Type[DeclarativeBase]): The model class to register.
        """
        cls._registered_models[model_name] = model_class

    @classmethod
    def get_model(cls, model_name: str) -> Type[DeclarativeBase]:
        """
        Retrieve a registered model class.

        Args:
            model_name (str): Unique identifier for the model.

        Returns:
            Type[DeclarativeBase]: The requested model class.

        Raises:
            KeyError: If the model is not registered.
        """
        if model_name not in cls._registered_models:
            raise KeyError(f"Model '{model_name}' is not registered")
        return cls._registered_models[model_name]

    @classmethod
    def clear_models(cls) -> None:
        """
        Clear all registered models.
        Useful for testing or resetting the resolver.
        """
        cls._registered_models.clear()

    @classmethod
    def is_model_registered(cls, model_name: str) -> bool:
        """
        Check if a model is registered.

        Args:
            model_name (str): Unique identifier for the model.

        Returns:
            bool: True if the model is registered, False otherwise.
        """
        return model_name in cls._registered_models