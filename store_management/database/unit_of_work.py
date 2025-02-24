from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/unit_of_work.py

Unit of Work pattern implementation for database transactions.
"""
logger = logging.getLogger(__name__)


class IUnitOfWork(ABC):
    """
    Interface for the Unit of Work pattern.

    This interface defines the methods that all unit of work implementations must provide.
    """

    @abstractmethod
    @inject(MaterialService)
        def __enter__(self):
        """Enter the context manager."""
        pass

        @abstractmethod
    @inject(MaterialService)
        def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass

        @abstractmethod
    @inject(MaterialService)
        def commit(self):
        """Commit the transaction."""
        pass

        @abstractmethod
    @inject(MaterialService)
        def rollback(self):
        """Rollback the transaction."""
        pass


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.

    This class provides methods for transaction management using SQLAlchemy sessions.
    """

    @inject(MaterialService)
        def __init__(self, session_factory: Callable[[], Session] = None):
        """
        Initialize a new SQLAlchemyUnitOfWork instance.

        Args:
            session_factory: Function that returns a new SQLAlchemy session.
                             If not provided, the default session factory is used.
        """
        self.session_factory = session_factory or get_db_session
        self.session = None

        @inject(MaterialService)
            def __enter__(self) -> 'SQLAlchemyUnitOfWork':
        """
        Enter the context manager.

        Returns:
            The unit of work instance.
        """
        self.session = self.session_factory()
        return self

        @inject(MaterialService)
            def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager.

        Args:
            exc_type: Exception type, if an exception was raised.
            exc_val: Exception value, if an exception was raised.
            exc_tb: Exception traceback, if an exception was raised.
        """
        if self.session:
            if exc_type:
                self.rollback()
            self.session.close()

        @inject(MaterialService)
            def commit(self) -> None:
        """
        Commit the transaction.

        Raises:
            RuntimeError: If the session is not initialized.
        """
        if not self.session:
            raise RuntimeError('Cannot commit - no active session')
        try:
            self.session.commit()
            logger.debug('Transaction committed successfully')
        except Exception as e:
            logger.error(f'Failed to commit transaction: {str(e)}')
            self.rollback()
            raise

        @inject(MaterialService)
            def rollback(self) -> None:
        """
        Rollback the transaction.

        Raises:
            RuntimeError: If the session is not initialized.
        """
        if not self.session:
            raise RuntimeError('Cannot rollback - no active session')
        try:
            self.session.rollback()
            logger.debug('Transaction rolled back')
        except Exception as e:
            logger.error(f'Failed to rollback transaction: {str(e)}')
            raise


def run_in_transaction(func, *args, **kwargs) -> Any:
    """
    Run a function within a transaction.

    Args:
        func: The function to run.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function.
    """
    with SQLAlchemyUnitOfWork() as uow:
        result = func(*args, **kwargs, session=uow.session)
        uow.commit()
        return result
