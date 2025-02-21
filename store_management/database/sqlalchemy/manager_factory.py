# File: database/sqlalchemy/manager_factory.py
# Purpose: Provide a flexible factory for creating database managers

from typing import (
    Type, Dict, Any, TypeVar, Optional,
    Callable, Union, List
)
from sqlalchemy.orm import Session

from .base_manager import BaseManager
from .session import get_db_session

# Cache for storing manager instances to ensure singleton-like behavior
_manager_cache: Dict[Type, BaseManager] = {}

# Mapping for specialized managers
_specialized_managers: Dict[Type, Type[BaseManager]] = {}

T = TypeVar('T')


def register_specialized_manager(
        model_class: Type[T],
        manager_class: Type[BaseManager[T]]
):
    """
    Register a specialized manager for a specific model class.

    Args:
        model_class: The SQLAlchemy model class
        manager_class: The specialized manager class to use for this model
    """
    _specialized_managers[model_class] = manager_class


def get_manager(
        model_class: Type[T],
        session_factory: Optional[Callable[[], Session]] = None,
        mixins: Optional[List[Type]] = None,
        force_new: bool = False
) -> BaseManager[T]:
    """
    Get or create a manager for the specified model class.

    This factory ensures only one manager is created per model class,
    with support for specialized managers and optional mixins.

    Args:
        model_class: The SQLAlchemy model class
        session_factory: Optional custom session factory (defaults to get_db_session)
        mixins: Optional list of additional mixins to apply
        force_new: If True, create a new manager instance

    Returns:
        A BaseManager instance for the model class
    """
    # Use default session factory if not provided
    if session_factory is None:
        session_factory = get_db_session

    # Check for existing manager if not forcing new
    if not force_new and model_class in _manager_cache:
        return _manager_cache[model_class]

    # Check for specialized manager
    manager_class = _specialized_managers.get(model_class, BaseManager)

    # Create manager instance
    manager = manager_class(
        model_class=model_class,
        session_factory=session_factory,
        mixins=mixins
    )

    # Cache the manager unless forced new
    if not force_new:
        _manager_cache[model_class] = manager

    return manager


def clear_manager_cache():
    """
    Clear the manager instance cache.

    Useful for testing or resetting the application state.
    """
    global _manager_cache
    _manager_cache.clear()