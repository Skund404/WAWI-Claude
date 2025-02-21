# File: store_management/database/sqlalchemy/base_manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from store_management.database.sqlalchemy.base import Base


class BaseManager:
    """
    Base class for database operations providing common functionality.
    """

    def __init__(self, connection_string="sqlite:///store_management.db"):
        """
        Initialize the manager with a database connection.

        Args:
            connection_string: Database connection string
        """
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables defined in model classes"""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session object to interact with the database
        """
        return self.Session()