# Relative path: store_management/database/sqlalchemy/manager_factory.py

"""
Manager factory for dynamically creating and managing database managers.
"""

import logging
from functools import lru_cache
from typing import Dict, Type, TypeVar, Any, Tuple, Optional

from database.sqlalchemy.base_manager import BaseManager, create_base_manager

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T')

class ManagerFactory:
    """
    A factory for creating and caching database managers.

    Provides a centralized mechanism for creating and managing
    database managers across different models with caching and 
    specialized manager support.

    Attributes:
        _managers (Dict[Type, Any]): Cache of created managers
        _specialized_managers (Dict[Type, Type]): Mapping of model classes to specialized manager classes
    """

    # Class-level caches for managers and specialized managers
    _managers: Dict[Type, Any] = {}
    _specialized_managers: Dict[Type, Type] = {}

    @classmethod
    def register_specialized_manager(cls, model_class: Type, manager_class: Type):
        """
        Register a specialized manager for a specific model class.

        Args:
            model_class (Type): The model class to register
            manager_class (Type): The specialized manager class
        """
        try:
            cls._specialized_managers[model_class] = manager_class
            logger.info(f"Registered specialized manager for {model_class.__name__}")
        except Exception as e:
            logger.error(f"Failed to register specialized manager: {e}")
            raise

    @classmethod
    @lru_cache(maxsize=None)
    def get_manager(
        cls, 
        model_class: Type[T], 
        session_factory: Any, 
        mixins: Tuple[Type, ...] = (), 
        force_new: bool = False
    ) -> Any:
        """
        Get or create a manager for a specific model class.

        Args:
            model_class (Type[T]): The model class to get a manager for
            session_factory (Any): Factory to create database sessions
            mixins (Tuple[Type, optional]): Additional mixins to apply to the manager
            force_new (bool, optional): Force creation of a new manager instance

        Returns:
            Any: A manager instance for the specified model
        """
        try:
            # Check if a cached manager exists and we're not forcing a new one
            if not force_new and model_class in cls._managers:
                return cls._managers[model_class]

            # Check for a specialized manager
            if model_class in cls._specialized_managers:
                manager_class = cls._specialized_managers[model_class]
                manager = manager_class(session_factory)
            else:
                # Create a base manager
                manager = create_base_manager(model_class, session_factory)

            # Apply mixins if provided
            if mixins:
                # Dynamically create a new class with mixins
                mixin_names = '+'.join(mixin.__name__ for mixin in mixins)
                manager.__class__ = type(
                    f'{mixin_names}{manager.__class__.__name__}', 
                    mixins + (manager.__class__,), 
                    {}
                )

            # Cache the manager unless forced to create a new one
            if not force_new:
                cls._managers[model_class] = manager

            return manager

        except Exception as e:
            logger.error(f"Failed to get manager for {model_class.__name__}: {e}")
            raise

    @classmethod
    def clear_manager_cache(cls):
        """
        Clear the cached managers.

        Removes all cached managers and specialized managers, 
        allowing for a fresh start or cache reset.
        """
        try:
            cls._managers.clear()
            cls._specialized_managers.clear()
            logger.info("Manager cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear manager cache: {e}")
            raise

def register_specialized_manager(model_class: Type, manager_class: Type):
    """
    Convenience function to register a specialized manager.

    Provides a more accessible way to register specialized managers.

    Args:
        model_class (Type): The model class to register
        manager_class (Type): The specialized manager class
    """
    ManagerFactory.register_specialized_manager(model_class, manager_class)