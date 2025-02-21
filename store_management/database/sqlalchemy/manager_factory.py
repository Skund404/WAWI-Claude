# store_management/database/sqlalchemy/manager_factory.py
"""Factory for creating database managers."""
from typing import Type, Dict, Any, TypeVar, Optional, Callable, Union, List
from sqlalchemy.orm import Session
from store_management.database.sqlalchemy.base_manager import BaseManager
from store_management.database.session import get_db_session

T = TypeVar('T')

# Cache of manager instances
_manager_cache = {}

# Registry of specialized managers
_specialized_managers = {}


def register_specialized_manager(model_class, manager_class):
    """Register a specialized manager for a specific model class.

    Args:
        model_class: The SQLAlchemy model class
        manager_class: The specialized manager class to use for this model
    """
    _specialized_managers[model_class] = manager_class


def get_manager(model_class, session_factory=None, mixins=None, force_new=False):
    """Get or create a manager for the specified model class.

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
    # Use default session factory if none provided
    if session_factory is None:
        session_factory = get_db_session

    # Always create new instance if requested
    if force_new:
        return _create_manager(model_class, session_factory, mixins)

    # Use cached instance if available
    cache_key = f"{model_class.__module__}.{model_class.__name__}"
    if cache_key in _manager_cache:
        return _manager_cache[cache_key]

    # Create and cache new instance
    manager = _create_manager(model_class, session_factory, mixins)
    _manager_cache[cache_key] = manager
    return manager


def _create_manager(model_class, session_factory, mixins=None):
    """Create a new manager instance.

    Args:
        model_class: The SQLAlchemy model class
        session_factory: Function to create database sessions
        mixins: Optional list of mixins to apply

    Returns:
        A BaseManager instance for the model class
    """
    # Check if there's a specialized manager for this model
    if model_class in _specialized_managers:
        manager_class = _specialized_managers[model_class]
        return manager_class(session_factory)

    # Create a basic manager with optional mixins
    if mixins:
        # Create a dynamic class with mixins
        class_name = f"{model_class.__name__}Manager"
        bases = tuple([BaseManager] + mixins)
        manager_class = type(class_name, bases, {})
        return manager_class(model_class, session_factory)
    else:
        # Create a basic manager
        return BaseManager(model_class, session_factory)


def clear_manager_cache():
    """Clear the manager instance cache.

    Useful for testing or resetting the application state.
    """
    _manager_cache.clear()