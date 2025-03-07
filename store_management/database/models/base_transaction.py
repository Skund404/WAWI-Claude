# database/models/base_transaction.py
"""
Base Transaction Model for Leatherworking Management System

This module defines the CircularImportResolver class to resolve circular
imports in database models. It enables proper relationship management
without circular dependencies.
"""

import logging
from typing import Dict, Type, Any, Optional, List, Callable

from sqlalchemy.orm import DeclarativeBase

# Setup logger
logger = logging.getLogger(__name__)


class CircularImportResolver:
    """
    A utility class to manage and resolve circular import dependencies.

    This class provides a centralized way to register and retrieve model classes
    that might cause circular import issues in the leatherworking system.
    """
    _registered_models: Dict[str, Type[DeclarativeBase]] = {}
    _registered_callbacks: Dict[str, List[Callable]] = {}

    @classmethod
    def register_model(cls, model_name: str, model_class: Type[DeclarativeBase]) -> None:
        """
        Register a model class with a given name.

        Args:
            model_name: Unique identifier for the model
            model_class: The model class to register
        """
        cls._registered_models[model_name] = model_class
        logger.debug(f"Registered model: {model_name}")

        # Execute any pending callbacks for this model
        if model_name in cls._registered_callbacks:
            for callback in cls._registered_callbacks[model_name]:
                try:
                    callback(model_class)
                    logger.debug(f"Executed callback for {model_name}")
                except Exception as e:
                    logger.error(f"Error executing callback for {model_name}: {e}")

            # Clear processed callbacks
            cls._registered_callbacks[model_name] = []

    @classmethod
    def get_model(cls, model_name: str) -> Type[DeclarativeBase]:
        """
        Retrieve a registered model class.

        Args:
            model_name: Unique identifier for the model

        Returns:
            The requested model class

        Raises:
            KeyError: If the model is not registered
        """
        if model_name not in cls._registered_models:
            raise KeyError(f"Model '{model_name}' is not registered")
        return cls._registered_models[model_name]

    @classmethod
    def register_callback(cls, model_name: str, callback: Callable) -> None:
        """
        Register a callback to be executed when a model is registered.

        Args:
            model_name: Model name to watch for
            callback: Function to call when the model is registered
        """
        if model_name in cls._registered_models:
            # Model already registered, execute callback immediately
            try:
                callback(cls._registered_models[model_name])
                logger.debug(f"Executed immediate callback for {model_name}")
            except Exception as e:
                logger.error(f"Error executing immediate callback for {model_name}: {e}")
        else:
            # Store callback for later execution
            if model_name not in cls._registered_callbacks:
                cls._registered_callbacks[model_name] = []
            cls._registered_callbacks[model_name].append(callback)
            logger.debug(f"Registered callback for model: {model_name}")

    @classmethod
    def clear_models(cls) -> None:
        """
        Clear all registered models.
        Useful for testing or resetting the resolver.
        """
        cls._registered_models.clear()
        cls._registered_callbacks.clear()
        logger.debug("Cleared all registered models and callbacks")

    @classmethod
    def is_model_registered(cls, model_name: str) -> bool:
        """
        Check if a model is registered.

        Args:
            model_name: Unique identifier for the model

        Returns:
            True if the model is registered, False otherwise
        """
        return model_name in cls._registered_models

    @classmethod
    def get_registered_models(cls) -> List[str]:
        """
        Get a list of all registered model names.

        Returns:
            List of registered model names
        """
        return list(cls._registered_models.keys())

    @classmethod
    def get_pending_callbacks(cls) -> List[str]:
        """
        Get a list of model names with pending callbacks.

        Returns:
            List of model names with pending callbacks
        """
        return [name for name, callbacks in cls._registered_callbacks.items() if callbacks]