# File: store_management/database/session.py

from contextlib import contextmanager
from .config import session_factory


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Ensures proper session management and cleanup.

    Usage:
        with get_db_session() as session:
            # Perform database operations
            session.add(some_object)
            session.commit()
    """
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()