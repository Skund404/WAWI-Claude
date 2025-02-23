# Path: store_management\database\sqlalchemy\manager_factory.py
"""
Manager factory for creating and managing database managers dynamically.
"""

from typing import Any, Dict, Type, TypeVar, Generic
from functools import lru_cache

T = TypeVar('T')


class ManagerFactory:
    """
    A factory for creating and caching database managers.

    Provides a centralized mechanism for creating and managing
    database managers across different models.
    """

    _managers: Dict[Type, Any] = {}
    _specialized_managers: Dict[Type, Type] = {}

    @classmethod
    def register_specialized_manager(
            cls,
            model_class: Type,
            manager_class: Type
    ):
        """
        Register a specialized manager for a specific model class.

        Args:
            model_class (Type): The model class to register
            manager_class (Type): The specialized manager class
        """
        cls._specialized_managers[model_class] = manager_class

    @classmethod
    @lru_cache(maxsize=None)
    def get_manager(
            cls,
            model_class: Type[T],
            session_factory: Any,
            mixins: tuple = (),
            force_new: bool = False
    ) -> Any:
        """
        Get or create a manager for a specific model class.

        Args:
            model_class (Type[T]): The model class to get a manager for
            session_factory (Any): Factory to create database sessions
            mixins (tuple, optional): Additional mixins to apply to the manager
            force_new (bool, optional): Force creation of a new manager instance

        Returns:
            Any: A manager instance for the specified model
        """
        # Check for a previously cached manager
        if not force_new and model_class in cls._managers:
            return cls._managers[model_class]

        # Check for a specialized manager
        if model_class in cls._specialized_managers:
            manager_class = cls._specialized_managers[model_class]
            manager = manager_class(session_factory)
        else:
            # Import here to avoid circular imports
            from database.sqlalchemy.base_manager import BaseManager, create_base_manager
            manager = create_base_manager(model_class, session_factory)

        # Apply mixins if provided
        for mixin in mixins:
            manager.__class__ = type(
                f'{mixin.__name__}{manager.__class__.__name__}',
                (mixin, manager.__class__),
                {}
            )

        # Cache the manager unless forced to create a new one
        if not force_new:
            cls._managers[model_class] = manager

        return manager

    @classmethod
    def clear_manager_cache(cls):
        """
        Clear the cached managers.
        """
        cls._managers.clear()
        cls._specialized_managers.clear()


# Top-level function for convenience
def register_specialized_manager(
        model_class: Type,
        manager_class: Type
):
    """
    Convenience function to register a specialized manager.

    Args:
        model_class (Type): The model class to register
        manager_class (Type): The specialized manager class
    """
    ManagerFactory.register_specialized_manager(model_class, manager_class)