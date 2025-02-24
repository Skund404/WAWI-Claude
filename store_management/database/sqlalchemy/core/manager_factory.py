from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

T = TypeVar("T")
_manager_cache = {}
_specialized_managers = {}


def register_specialized_manager(model_class: Type, manager_class: Type[BaseManager]):
    """Register a specialized manager for a specific model class.

    Args:
        model_class: The SQLAlchemy model class
        manager_class: The specialized manager class to use for this model
    """
    _specialized_managers[model_class] = manager_class


def get_manager(
    model_class: Type[T],
    session_factory: Optional[Callable[[], Session]] = None,
    force_new: bool = False,
) -> BaseManager[T]:
    """Get or create a manager for the specified model class.

    This factory ensures only one manager is created per model class,
    with support for specialized managers.

    Args:
        model_class: The SQLAlchemy model class
        session_factory: Optional custom session factory (defaults to global session factory)
        force_new: If True, create a new manager instance

    Returns:
        A BaseManager instance for the model class
    """
    if force_new:
        return _create_manager(model_class, session_factory)
    if model_class in _manager_cache:
        return _manager_cache[model_class]
    manager = _create_manager(model_class, session_factory)
    _manager_cache[model_class] = manager
    return manager


def _create_manager(
    model_class: Type[T], session_factory: Optional[Callable[[], Session]] = None
) -> BaseManager[T]:
    """Create a new manager instance for the specified model class.

    Args:
        model_class: The SQLAlchemy model class
        session_factory: Optional custom session factory

    Returns:
        A BaseManager instance for the model class
    """
    if session_factory is None:
        from database.sqlalchemy.session import get_db_session

        session_factory = get_db_session
    if model_class in _specialized_managers:
        manager_class = _specialized_managers[model_class]
        return manager_class(model_class, session_factory)
    return BaseManager(model_class, session_factory)


def clear_manager_cache():
    """Clear the manager instance cache.

    Useful for testing or resetting the application state.
    """
    global _manager_cache
    _manager_cache = {}
