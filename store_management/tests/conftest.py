# tests/conftest.py
"""
Pytest configuration for model tests.
Provides fixtures for database setup and teardown.
"""

import pytest
import logging
from typing import Generator, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models.base import Base, initialize_all_model_relationships

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for testing."""
    # Create an in-memory SQLite database
    test_engine = create_engine('sqlite:///:memory:', echo=False)

    # Create all tables
    Base.metadata.create_all(test_engine)

    # Initialize relationships
    initialize_all_model_relationships()

    # Log registered models
    logger.info(f"Registered models: {', '.join(Base.list_models())}")

    return test_engine


@pytest.fixture(scope="session")
def session_factory(engine):
    """Create a new session factory."""
    return sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db_session(session_factory) -> Generator[Session, None, None]:
    """
    Create a new database session for a test.

    This fixture ensures each test runs with a fresh session.
    The database transaction is rolled back at the end of each test.
    """
    # Create a new session for the test
    session = session_factory()

    try:
        # Begin a nested transaction (using savepoints)
        session.begin_nested()

        # Return the session for the test to use
        yield session

        # Roll back the transaction after the test is complete
        session.rollback()
    finally:
        # Close the session
        session.close()


@pytest.fixture(scope="function")
def sample_data(db_session) -> Dict[str, Dict[str, Any]]:
    """
    Create sample data for testing.

    Returns a dictionary of entities with their IDs for easy reference in tests.
    """
    # Import models to prevent circular imports
    from database.models import (
        Customer, Sales, Product, Supplier, Material, Leather, Hardware,
        Tool, Pattern, Component
    )
    from database.models.enums import (
        CustomerStatus, CustomerTier, SaleStatus, PaymentStatus,
        MaterialType, LeatherType, HardwareType, ComponentType,
        QualityGrade, ProjectType, SkillLevel
    )

    # Create a dictionary to store created entities
    entities = {}

    # Create a customer
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
        status=CustomerStatus.ACTIVE,
        tier=CustomerTier.STANDARD
    )
    db_session.add(customer)
    db_session.flush()
    entities['customer'] = {'id': customer.id, 'obj': customer}

    # Create a supplier
    supplier = Supplier(
        name="Test Supplier",
        contact_email="supplier@example.com",
        status="ACTIVE"
    )
    db_session.add(supplier)
    db_session.flush()
    entities['supplier'] = {'id': supplier.id, 'obj': supplier}

    # Create a product
    product = Product(
        name="Test Product",
        price=99.99
    )
    db_session.add(product)
    db_session.flush()
    entities['product'] = {'id': product.id, 'obj': product}

    # Create a sale
    sale = Sales(
        customer_id=customer.id,
        total_amount=99.99,
        status=SaleStatus.COMPLETED,
        payment_status=PaymentStatus.PAID
    )
    db_session.add(sale)
    db_session.flush()
    entities['sale'] = {'id': sale.id, 'obj': sale}

    # Create materials
    material = Material(
        name="Test Material",
        type=MaterialType.LEATHER,
        unit=MeasurementUnit.SQUARE_FOOT,
        quality=QualityGrade.PREMIUM,
        supplier_id=supplier.id
    )
    db_session.add(material)
    db_session.flush()
    entities['material'] = {'id': material.id, 'obj': material}

    leather = Leather(
        name="Test Leather",
        type=LeatherType.FULL_GRAIN,
        quality=QualityGrade.PREMIUM,
        supplier_id=supplier.id
    )
    db_session.add(leather)
    db_session.flush()
    entities['leather'] = {'id': leather.id, 'obj': leather}

    hardware = Hardware(
        name="Test Hardware",
        type=HardwareType.BUCKLE,
        supplier_id=supplier.id
    )
    db_session.add(hardware)
    db_session.flush()
    entities['hardware'] = {'id': hardware.id, 'obj': hardware}

    tool = Tool(
        name="Test Tool",
        description="A tool for testing",
        type="CUTTING",
        supplier_id=supplier.id
    )
    db_session.add(tool)
    db_session.flush()
    entities['tool'] = {'id': tool.id, 'obj': tool}

    # Create a pattern
    pattern = Pattern(
        name="Test Pattern",
        description="A test pattern",
        skill_level=SkillLevel.INTERMEDIATE
    )
    db_session.add(pattern)
    db_session.flush()
    entities['pattern'] = {'id': pattern.id, 'obj': pattern}

    # Create a component
    component = Component(
        name="Test Component",
        type=ComponentType.LEATHER
    )
    db_session.add(component)
    db_session.flush()
    entities['component'] = {'id': component.id, 'obj': component}

    # Commit all the sample data
    db_session.commit()

    return entities