# tests/betsy_validation/conftest.py
"""
Pytest configuration for Betsy validation tests.
"""
import os
import sys
import pytest
import logging
import datetime

# Ensure project root is in Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lazy import of database dependencies
from utils.circular_import_resolver import get_class, register_lazy_import


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest file after command line options have been parsed.
    """
    # Add a marker to mark tests in this directory
    config.addinivalue_line(
        "markers",
        "betsy_validation: mark test as part of the Betsy validation test suite"
    )


@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for testing."""
    from sqlalchemy import create_engine

    # Use an in-memory SQLite database
    test_engine = create_engine('sqlite:///:memory:', echo=False)

    # Import Base and create tables
    Base = get_class('database.models.base', 'Base')

    # Create all tables
    Base.metadata.create_all(test_engine)

    return test_engine


@pytest.fixture(scope="session")
def session_factory(engine):
    """Create a new session factory."""
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db_session(session_factory):
    """
    Create a new database session for a test.
    Rolls back after each test.
    """
    session = session_factory()

    try:
        # Begin a nested transaction
        session.begin_nested()

        # Yield the session to the test
        yield session

        # Roll back the transaction
        session.rollback()
    finally:
        # Close the session
        session.close()


@pytest.fixture(scope="function")
def sample_data(db_session):
    """
    Create sample data for testing.
    This fixture creates a base set of data that can be used across different tests.
    """
    # Import all necessary models
    Customer = get_class('database.models.customer', 'Customer')
    Sales = get_class('database.models.sales', 'Sales')
    Product = get_class('database.models.product', 'Product')
    Pattern = get_class('database.models.pattern', 'Pattern')
    Component = get_class('database.models.components', 'Component')
    Material = get_class('database.models.material', 'Material')
    Leather = get_class('database.models.leather', 'Leather')
    Hardware = get_class('database.models.hardware', 'Hardware')
    Tool = get_class('database.models.tool', 'Tool')
    Supplier = get_class('database.models.supplier', 'Supplier')
    Storage = get_class('database.models.storage', 'Storage')

    # Also import enums
    CustomerStatus = get_class('database.models.enums', 'CustomerStatus')
    SaleStatus = get_class('database.models.enums', 'SaleStatus')
    PaymentStatus = get_class('database.models.enums', 'PaymentStatus')
    MaterialType = get_class('database.models.enums', 'MaterialType')
    LeatherType = get_class('database.models.enums', 'LeatherType')
    HardwareType = get_class('database.models.enums', 'HardwareType')
    ComponentType = get_class('database.models.enums', 'ComponentType')
    SkillLevel = get_class('database.models.enums', 'SkillLevel')

    # Create a supplier
    supplier = Supplier(
        name="Test Supplier",
        contact_email="supplier@example.com",
        status="ACTIVE"
    )
    db_session.add(supplier)
    db_session.flush()

    # Create a storage location
    storage = Storage(
        name="Test Storage",
        location_type="SHELF",
        description="A test storage location"
    )
    db_session.add(storage)
    db_session.flush()

    # Create a customer
    customer = Customer(
        name="Test Customer",
        email="customer@example.com",
        status=CustomerStatus.ACTIVE
    )
    db_session.add(customer)
    db_session.flush()

    # Create a product
    product = Product(
        name="Test Product",
        price=99.99
    )
    db_session.add(product)
    db_session.flush()

    # Create a sale
    sale = Sales(
        customer_id=customer.id,
        total_amount=99.99,
        status=SaleStatus.COMPLETED,
        payment_status=PaymentStatus.PAID
    )
    db_session.add(sale)
    db_session.flush()

    # Create a pattern
    pattern = Pattern(
        name="Test Pattern",
        description="A test pattern",
        skill_level=SkillLevel.INTERMEDIATE
    )
    db_session.add(pattern)
    db_session.flush()

    # Create a component
    component = Component(
        name="Test Component",
        type=ComponentType.LEATHER
    )
    db_session.add(component)
    db_session.flush()

    # Create materials
    material = Material(
        name="Test Material",
        type=MaterialType.THREAD,
        supplier_id=supplier.id
    )
    db_session.add(material)
    db_session.flush()

    # Create leather
    leather = Leather(
        name="Test Leather",
        type=LeatherType.FULL_GRAIN,
        supplier_id=supplier.id
    )
    db_session.add(leather)
    db_session.flush()

    # Create hardware
    hardware = Hardware(
        name="Test Hardware",
        type=HardwareType.BUCKLE,
        supplier_id=supplier.id
    )
    db_session.add(hardware)
    db_session.flush()

    # Create tool
    tool = Tool(
        name="Test Tool",
        description="A test tool",
        supplier_id=supplier.id
    )
    db_session.add(tool)
    db_session.flush()

    # Commit the changes
    db_session.commit()

    # Return a dictionary with all the created entities
    return {
        'customer': customer,
        'sale': sale,
        'product': product,
        'pattern': pattern,
        'component': component,
        'material': material,
        'leather': leather,
        'hardware': hardware,
        'tool': tool,
        'supplier': supplier,
        'storage': storage
    }


# Minimal test to ensure pytest can discover and run tests
def test_placeholder():
    """
    A minimal placeholder test to ensure test discovery works.

    This test should always pass and serves as a sanity check
    that the test infrastructure is functioning correctly.
    """
    assert True, "Placeholder test to ensure test discovery works"