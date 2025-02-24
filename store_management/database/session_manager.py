from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/session_manager.py

SQLAlchemy session management with context managers.
"""
logger = logging.getLogger(__name__)
T = TypeVar('T')


class SessionManager:
    """
    Session manager for SQLAlchemy.

    This class provides context managers for session management.
    """

        @inject(MaterialService)
        def __init__(self, session_factory: Callable[[], Session]=None):
        """
        Initialize a new SessionManager.

        Args:
            session_factory: Function that returns a new SQLAlchemy session.
                             If not provided, the default session factory is used.
        """
        self.session_factory = session_factory or get_db_session

        @contextmanager
    @inject(MaterialService)
    def session_scope(self) ->Iterator[Session]:
        """
        Provide a transactional scope around a series of operations.

        Yields:
            SQLAlchemy session.

        Raises:
            TransactionError: If a database transaction error occurs.
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f'Database transaction error: {str(e)}')
            raise TransactionError(operation='session_scope', details=str(e)
                ) from e
        finally:
            session.close()

        @contextmanager
    @inject(MaterialService)
    def read_only_session_scope(self) ->Iterator[Session]:
        """
        Provide a read-only transactional scope.

        This is useful for operations that don't modify the database.

        Yields:
            SQLAlchemy session.

        Raises:
            TransactionError: If a database transaction error occurs.
        """
        session = self.session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f'Database read transaction error: {str(e)}')
            raise TransactionError(operation='read_only_session_scope',
                details=str(e)) from e
        finally:
            session.close()

        @inject(MaterialService)
        def execute_in_transaction(self, operation: Callable[[Session], T]) ->T:
        """
        Execute an operation in a transaction.

        Args:
            operation: Function that takes a session and returns a result.

        Returns:
            The result of the operation.

        Raises:
            TransactionError: If a database transaction error occurs.
        """
        with self.session_scope() as session:
            return operation(session)

        @inject(MaterialService)
        def execute_read_only(self, operation: Callable[[Session], T]) ->T:
        """
        Execute a read-only operation.

        Args:
            operation: Function that takes a session and returns a result.

        Returns:
            The result of the operation.

        Raises:
            TransactionError: If a database transaction error occurs.
        """
        with self.read_only_session_scope() as session:
            return operation(session)

        @inject(MaterialService)
        def execute_bulk_operation(self, operation: Callable[[Session], T]) ->T:
        """
        Execute a bulk operation in a transaction.

        This is useful for operations that modify many records.

        Args:
            operation: Function that takes a session and returns a result.

        Returns:
            The result of the operation.

        Raises:
            TransactionError: If a database transaction error occurs.
        """
        with self.session_scope() as session:
            session.bulk_insert_mappings = True
            session.bulk_save_objects = True
            return operation(session)


session_manager = SessionManager()
