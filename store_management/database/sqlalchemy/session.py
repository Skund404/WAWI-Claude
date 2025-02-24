from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Database session management.
"""
logger = logging.getLogger(__name__)
_session_factory = None
_engine = None


def init_database() ->Engine:
    """
    Initialize database engine and session factory.

    Returns:
        SQLAlchemy engine instance
    """
    global _session_factory, _engine
    try:
        db_url = get_database_url()
        logger.debug(f'Initializing database with URL: {db_url}')
        _engine = create_engine(db_url, echo=False, pool_pre_ping=True,
            pool_recycle=3600)
        session_factory = sessionmaker(bind=_engine, autocommit=False,
            autoflush=False)
        _session_factory = scoped_session(session_factory)
        return _engine
    except Exception as e:
        logger.error(f'Failed to initialize database: {str(e)}')
        raise


def get_db_session():
    """
    Get a database session.

    Returns:
        Scoped session instance

    Raises:
        RuntimeError: If database is not initialized
    """
    if _session_factory is None:
        raise RuntimeError(
            'Database not initialized. Call init_database() first.')
    return _session_factory()


def close_db_session() ->None:
    """Close all sessions and clean up."""
    if _session_factory is not None:
        _session_factory.remove()
