# tests/conftest.py
"""
Centralized test configuration for pytest.
This module handles database initialization for tests.
"""
import pytest
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force initialization of all models and relationships
from database.models.base import Base
from database.models.relationship_tables import *

# Import the circular import resolver
from utils.circular_import_resolver import register_lazy_import, resolve_lazy_import

# Now import all models needed for tests
from database.models import (
    Component, Customer, Leather, Hardware, Material,
    Pattern, PickingList, PickingListItem, Product,
    Project, ProjectComponent, Sales, SalesItem, Storage,
    Supplier, Tool, ToolList, ToolListItem
)


@pytest.fixture(scope="function")
def db_engine():
    """Create a SQLite in-memory database engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for a test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()