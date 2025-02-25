# database/sqlalchemy/core/manager_factory.py
"""
Manager factory for creating and managing database managers.

Provides a centralized mechanism for creating and caching database managers
for different model classes.
"""

from typing import Type, TypeVar, Optional, Callable, Dict
from sqlalchemy.orm import Session

from core.managers.base_manager import BaseManager
from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

T = TypeVar("T")

# Caches for managers and specialized managers
_manager_cache: Dict[Type, BaseManager] = {}
_specialized_managers: Dict[Type, Type[BaseManager]] = {}


def register_specialized_manager(model_class: Type, manager_class: Type[BaseManager]):
    """
    Register a specialized manager for a specific model class.

    Args:
        model_class (Type): The SQLAlchemy model class
        manager_class (Type[BaseManager]): The specialized manager class to use for this model
    """
    _specialized_managers[model_class] = manager_class


def get_manager(
        model_class: Type[T],
        session_factory: Optional[Callable[[], Session]] = None,
        force_new: bool = False,
) -> BaseManager[T]:
    """
    Get or create a manager for the specified model class.

    This factory ensures only one manager is created per model class,
    with support for specialized managers.

    Args:
        model_class (Type[T]): The SQLAlchemy model class
        session_factory (Optional[Callable[[], Session]], optional): 
            Optional custom session factory (defaults to global session factory)
        force_new (bool, optional): If True, create a new manager instance

    Returns:
        BaseManager[T]: A BaseManager instance for the model class
    """
    # If force_new is True, always create a new manager
    if force_new:
        return _create_manager(model_class, session_factory)

    # Return cached manager if it exists
    if model_class in _manager_cache:
        return _manager_cache[model_class]

    # Create and cache a new manager
    manager = _create_manager(model_class, session_factory)
    _manager_cache[model_class] = manager
    return manager


def _create_manager(
        model_class: Type[T],
        session_factory: Optional[Callable[[], Session]] = None
) -> BaseManager[T]:
    """
    Create a new manager instance for the specified model class.

    Args:
        model_class (Type[T]): The SQLAlchemy model class
        session_factory (Optional[Callable[[], Session]], optional): 
            Optional custom session factory

    Returns:
        BaseManager[T]: A BaseManager instance for the model class
    """
    # Use default session factory if not provided
    if session_factory is None:
        from database.sqlalchemy.session import get_db_session
        session_factory = get_db_session

    # Use specialized manager if registered, otherwise use base manager
    if model_class in _specialized_managers:
        manager_class = _specialized_managers[model_class]
        return manager_class(model_class, session_factory)

    # Fallback to base manager
    from core.managers.base_manager import BaseManager
    return BaseManager(model_class, session_factory)


def clear_manager_cache():
    """
    Clear the manager instance cache.

    Useful for testing or resetting the application state.
    """
    global _manager_cache
    _manager_cache = {}