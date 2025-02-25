# store_management/database/repositories/unit_of_work.py
"""
Unit of Work implementation for managing database transactions 
and repository interactions.

Provides a robust mechanism for coordinating database operations 
across multiple repositories within a single transaction.
"""

from typing import Optional, Any
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces import MaterialService
from database.connection import engine

# Import repositories
from .part_repository import PartRepository
from .product_repository import ProductRepository
from .project_repository import ProjectRepository
from .order_repository import OrderRepository
from .supplier_repository import SupplierRepository
from .storage_repository import StorageRepository
from .shopping_list_repository import ShoppingListRepository

# Configure logging
logger = logging.getLogger(__name__)


class SQLAlchemyUnitOfWork:
    """
    SQLAlchemy implementation of the Unit of Work pattern.

    Manages database transactions and provides access to repositories
    within a transactional context.
    """

    def __init__(self, session_factory=None):
        """
        Initialize the Unit of Work.

        Args:
            session_factory (Optional[sessionmaker]): SQLAlchemy session factory
        """
        # Use provided session factory or create default
        self.session_factory = session_factory or sessionmaker(bind=engine)
        self.session: Optional[Session] = None

        # Repositories managed by this Unit of Work
        self.parts: Optional[PartRepository] = None
        self.products: Optional[ProductRepository] = None
        self.projects: Optional[ProjectRepository] = None
        self.orders: Optional[OrderRepository] = None
        self.suppliers: Optional[SupplierRepository] = None
        self.storage: Optional[StorageRepository] = None
        self.shopping_lists: Optional[ShoppingListRepository] = None

    def __enter__(self):
        """
        Enter the runtime context for the Unit of Work.

        Creates a new database session and initializes repositories.

        Returns:
            SQLAlchemyUnitOfWork: The current Unit of Work instance
        """
        try:
            # Create new session
            self.session = self.session_factory()

            # Initialize repositories with the current session
            self.parts = PartRepository(self.session)
            self.products = ProductRepository(self.session)
            self.projects = ProjectRepository(self.session)
            self.orders = OrderRepository(self.session)
            self.suppliers = SupplierRepository(self.session)
            self.storage = StorageRepository(self.session)
            self.shopping_lists = ShoppingListRepository(self.session)

            return self
        except Exception as e:
            logger.error(f"Error initializing Unit of Work: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context for the Unit of Work.

        Handles transaction commit or rollback based on execution results.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Traceback
        """
        try:
            # If no exception occurred, commit the transaction
            if exc_type is None:
                self.commit()
            else:
                # Log the exception and roll back
                logger.error(f"Exception in Unit of Work: {exc_val}")
                self.rollback()
        except Exception as e:
            logger.error(f"Error during Unit of Work exit: {e}")
        finally:
            # Always close the session
            if self.session:
                self.session.close()

    def commit(self):
        """
        Commit the current database transaction.
        """
        try:
            if self.session:
                self.session.commit()
                logger.info("Transaction committed successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error committing transaction: {e}")
            raise

    def rollback(self):
        """
        Roll back the current database transaction.
        """
        try:
            if self.session:
                self.session.rollback()
                logger.warning("Transaction rolled back")
        except SQLAlchemyError as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise

    def close(self):
        """
        Close the current database session.
        """
        try:
            if self.session:
                self.session.close()
                logger.info("Database session closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    @classmethod
    def create_session_factory(cls, connection_string: str) -> sessionmaker:
        """
        Create a new session factory with a specific connection string.

        Args:
            connection_string (str): Database connection string

        Returns:
            sessionmaker: Configured SQLAlchemy session factory
        """
        try:
            new_engine = create_engine(connection_string)
            return sessionmaker(bind=new_engine)
        except Exception as e:
            logger.error(f"Error creating session factory: {e}")
            raise

    def execute_transaction(self, transaction_func, *args, **kwargs):
        """
        Execute a database transaction with automatic commit/rollback.

        Args:
            transaction_func (Callable): Function to execute within a transaction
            *args: Positional arguments for the transaction function
            **kwargs: Keyword arguments for the transaction function

        Returns:
            Any: Result of the transaction function
        """
        try:
            # Begin transaction
            result = transaction_func(*args, **kwargs)

            # Commit if no exceptions
            self.commit()

            return result
        except Exception as e:
            # Roll back on any exception
            self.rollback()
            logger.error(f"Transaction failed: {e}")
            raise