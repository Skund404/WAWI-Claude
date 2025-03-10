# tests/leatherwork_repository_tests/conftest.py
import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

# Determine the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Explicit import of models to avoid potential circular import issues
from store_management.database.models.base import Base

# Import specific models to ensure they are registered
import store_management.database.models.component
import store_management.database.models.component_material
import store_management.database.models.customer
import store_management.database.models.enums
import store_management.database.models.inventory
import store_management.database.models.material
import store_management.database.models.pattern
import store_management.database.models.picking_list
import store_management.database.models.picking_list_item
import store_management.database.models.product
import store_management.database.models.project
import store_management.database.models.project_component
import store_management.database.models.purchase
import store_management.database.models.purchase_item
import store_management.database.models.relationship_tables
import store_management.database.models.sales
import store_management.database.models.sales_item
import store_management.database.models.supplier
import store_management.database.models.tool
import store_management.database.models.tool_list
import store_management.database.models.tool_list_item

@pytest.fixture(scope='session')
def engine():
    """
    Create an in-memory SQLite engine for testing.
    Using StaticPool to ensure the same connection is used across threads.
    """
    return create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool
    )

@pytest.fixture(scope='session')
def tables(engine):
    """Create tables in the test database."""
    # Ensure all models are imported before creating tables
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope='function')
def dbsession(engine, tables):
    """
    Create a new database session for a test.
    Uses function scope to reset for each test.
    """
    # Create a scoped session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    session = Session()

    try:
        yield session
    finally:
        session.close()
        Session.remove()