# tests/betsy_validation/conftest.py
"""
Specific conftest for betsy_validation tests to handle circular dependencies and test setup.
"""
import pytest
import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure base and enums are loaded first
from database.models.base import Base, ModelValidationError
from database.models.enums import *

# Set up relationship tables
from database.models.relationship_tables import (
    component_material_table, component_leather_table,
    component_hardware_table, component_tool_table,
    product_pattern_table
)


# Define a shared db_session fixture for all tests in this directory
@pytest.fixture(scope="function")
def db_session():
    """Create a SQLite in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    Base.metadata.create_all(engine)

    # Create and yield session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()