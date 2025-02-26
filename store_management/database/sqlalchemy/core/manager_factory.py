# database/sqlalchemy/core/manager_factory.py
"""
Factory for creating and managing database model managers.

This module provides a centralized factory for creating and retrieving
database managers for different model types. It supports specialized
manager registration and caching for performance optimization.
"""

import logging
from typing import Callable, Dict, Optional, Type, TypeVar

from sqlalchemy.orm import Session

# Use relative imports or full path imports to avoid the 'core' module issue
from database.sqlalchemy.core.base_manager import BaseManager
# Alternatively, if base_manager is in a different location:
# from database.sqlalchemy.managers.base_manager import BaseManager

# Import the database session manager
from database.sqlalchemy.session import get_db_session

# Import service interfaces through dependency injection
from services.interfaces import (
    MaterialService,
    InventoryService,
    OrderService,
    ProjectService
)

# Create a type variable for generic type hinting
T = TypeVar('T')

# Logger for this module
logger = logging.getLogger(__name__)

# Cache for specialized managers
_MANAGER_REGISTRY: Dict[Type, Type[BaseManager]] = {}
# Cache for manager instances
_MANAGER_INSTANCES: Dict[str, BaseManager] = {}


def get_manager(model_class: Type[T], session_factory: Optional[Callable[[], Session]] = None) -> BaseManager[T]:
    """
    Get a manager instance for the specified model class.

    Args:
        model_class: The SQLAlchemy model class for which to get a manager
        session_factory: Optional custom session factory function

    Returns:
        A manager instance for the specified model class
    """
    # Generate a cache key based on model class name
    cache_key = f"{model_class.__name__}"

    # Check if a manager instance already exists in the cache
    if cache_key in _MANAGER_INSTANCES:
        logger.debug(f"Returning cached manager instance for {model_class.__name__}")
        return _MANAGER_INSTANCES[cache_key]

    # Use provided session factory or fallback to default
    if session_factory is None:
        session_factory = get_db_session

    # Try to get a specialized manager for this model class
    manager_class = _MANAGER_REGISTRY.get(model_class, BaseManager)

    # Create a new manager instance
    logger.debug(f"Creating new {manager_class.__name__} for {model_class.__name__}")
    manager = manager_class(model_class, session_factory)

    # Cache the manager instance
    _MANAGER_INSTANCES[cache_key] = manager

    return manager


def register_specialized_manager(model_class: Type, manager_class: Type[BaseManager]) -> None:
    """
    Register a specialized manager for a specific model class.

    Args:
        model_class: The SQLAlchemy model class
        manager_class: The specialized manager class to use for this model
    """
    logger.info(f"Registering specialized manager {manager_class.__name__} for {model_class.__name__}")
    _MANAGER_REGISTRY[model_class] = manager_class


def clear_manager_cache() -> None:
    """
    Clear the manager instance cache.

    Useful for testing or resetting the application state.
    """
    logger.debug("Clearing manager instance cache")
    _MANAGER_INSTANCES.clear()


def force_new_manager(model_class: Type[T], session_factory: Optional[Callable[[], Session]] = None) -> BaseManager[T]:
    """
    Force creation of a new manager instance without using the cache.

    Args:
        model_class: The SQLAlchemy model class
        session_factory: Optional custom session factory function

    Returns:
        A new manager instance for the specified model class
    """
    # Use provided session factory or fallback to default
    if session_factory is None:
        session_factory = get_db_session

    # Get the manager class for this model
    manager_class = _MANAGER_REGISTRY.get(model_class, BaseManager)

    # Create a new manager instance
    logger.debug(f"Forcing creation of new {manager_class.__name__} for {model_class.__name__}")
    return manager_class(model_class, session_factory)