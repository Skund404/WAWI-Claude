# database/session.py
"""
Database session management for the store management system.
Provides functions to create and retrieve SQLAlchemy sessions.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Change this relative import to an absolute import
from config.settings import get_database_path

# Global variables
_engine = None
_SessionFactory = None
Base = declarative_base()


def init_database(db_url=None):
    """
    Initialize the database connection.

    Args:
        db_url (str): Database URL. If None, it will be determined from settings.

    Returns:
        Engine: SQLAlchemy engine
    """
    global _engine
    global _SessionFactory

    if not db_url:
        db_path = get_database_path()
        db_url = f"sqlite:///{db_path}"

    _engine = create_engine(db_url, echo=False)
    _SessionFactory = sessionmaker(bind=_engine)

    return _engine


def get_db_session():
    """
    Get a new database session.

    Returns:
        Session: A new SQLAlchemy session
    """
    global _SessionFactory

    if _SessionFactory is None:
        init_database()

    return _SessionFactory()


def close_db_session():
    """
    Close all sessions
    """
    if _SessionFactory:
        _SessionFactory.close_all()