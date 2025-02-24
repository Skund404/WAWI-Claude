from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/session.py

Database session management functions.
"""
logger = logging.getLogger(__name__)
_engine = None
_SessionFactory = None
_scoped_session = None


def init_database(database_url: str) -> None:
    """
    Initialize the database connection.

    Args:
        database_url: The database connection URL.
    """
    global _engine, _SessionFactory, _scoped_session
    try:
        _engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )
        _SessionFactory = sessionmaker(bind=_engine)
        _scoped_session = scoped_session(_SessionFactory)
        logger.info(f"Database engine initialized with {database_url}")
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {str(e)}")
        raise


def get_db_session() -> Session:
    """
    Get a database session from the scoped session registry.

    Returns:
        A database session.

    Raises:
        RuntimeError: If the database has not been initialized.
    """
    if _scoped_session is None:
        raise RuntimeError(
            "Database session has not been initialized. Call init_database first."
        )
    return _scoped_session()


def close_db_session() -> None:
    """
    Close the current database session.
    """
    if _scoped_session is not None:
        _scoped_session.remove()


def get_engine():
    """
    Get the SQLAlchemy engine.

    Returns:
        The SQLAlchemy engine.

    Raises:
        RuntimeError: If the database has not been initialized.
    """
    if _engine is None:
        raise RuntimeError(
            "Database engine has not been initialized. Call init_database first."
        )
    return _engine
