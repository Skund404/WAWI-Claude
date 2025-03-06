# database/sqlalchemy/session_helper.py
"""
Session helper utilities for SQLAlchemy session management.

This module provides utility functions for managing SQLAlchemy sessions,
including session creation, safe execution with session management,
and transaction management.
"""

import logging
import functools
from contextlib import contextmanager
from typing import Callable, TypeVar, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.sqlalchemy.session import get_db_session

logger = logging.getLogger(__name__)

T = TypeVar('T')


def with_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to provide a session to a function and handle session management.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if a session is already provided
        if 'session' in kwargs and kwargs['session'] is not None:
            return func(*args, **kwargs)

        # Create a new session
        session = get_db_session()
        try:
            # Add session to kwargs
            kwargs['session'] = session
            return func(*args, **kwargs)
        finally:
            session.close()

    return wrapper


@contextmanager
def session_scope() -> Session:
    """
    Context manager for handling session lifecycle.

    Yields:
        Session: SQLAlchemy session

    Raises:
        Any exceptions that occur during session use
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Error during session scope: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def safe_execute(session: Optional[Session] = None, auto_commit: bool = True) -> Callable:
    """
    Decorator for safely executing database operations with proper error handling.

    Args:
        session: Optional existing session to use
        auto_commit: Whether to automatically commit after successful execution

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided session or create a new one
            use_session = session or get_db_session()
            own_session = session is None

            try:
                # Execute the function
                result = func(*args, **kwargs, session=use_session)

                # Commit if needed and we own the session
                if auto_commit and own_session:
                    use_session.commit()

                return result
            except SQLAlchemyError as e:
                logger.error(f"Database error in {func.__name__}: {e}")

                # Rollback if we own the session
                if own_session:
                    use_session.rollback()

                raise
            finally:
                # Close if we own the session
                if own_session:
                    use_session.close()

        return wrapper

    return decorator


def refresh_session(service_instance, operation_name: str = "unknown") -> bool:
    """
    Attempts to refresh a service's database session.

    Args:
        service_instance: Service instance with a _session attribute
        operation_name: Name of the operation requiring a fresh session (for logging)

    Returns:
        bool: True if session was successfully refreshed, False otherwise
    """
    try:
        logger.info(f"Refreshing session for {operation_name} operation")

        # Check if service has a session
        if not hasattr(service_instance, '_session'):
            logger.error("Service instance has no _session attribute")
            return False

        # Create a new session
        new_session = get_db_session()

        # Close old session if it exists
        if service_instance._session:
            try:
                service_instance._session.close()
            except Exception as e:
                logger.warning(f"Error closing old session: {e}")

        # Set new session
        service_instance._session = new_session

        # Reinitialize repositories if needed
        if hasattr(service_instance, '_repository') and hasattr(service_instance._repository, 'session'):
            service_instance._repository.session = new_session

        # Log success
        logger.info(f"Session refreshed successfully for {operation_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to refresh session: {e}")
        return False