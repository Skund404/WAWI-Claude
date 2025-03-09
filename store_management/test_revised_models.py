#!/usr/bin/env python
"""
Completely isolated test script for a Storage-like model.
This avoids importing any existing models with relationship issues.
"""

import unittest
import logging
from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from enum import Enum as PyEnum

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('isolated_test')

# Create a separate base class for this test only
TestBase = declarative_base()


# Define enums just for this test
class TestStorageLocationType(PyEnum):
    """Storage location type for test only."""
    SHELF = "shelf"
    BIN = "bin"
    DRAWER = "drawer"
    CABINET = "cabinet"
    RACK = "rack"
    BOX = "box"
    OTHER = "other"


# Simple exception for validation
class TestModelValidationError(Exception):
    """Exception for model validation errors."""
    pass


# Define a minimal Storage-like model for testing
class TestStorage(TestBase):
    """Test Storage model with minimal dependencies."""
    __tablename__ = 'test_storage'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location_type = Column(Enum(TestStorageLocationType), nullable=False)
    capacity = Column(Integer)
    description = Column(String(500))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate storage data."""
        if not self.name:
            raise TestModelValidationError("Storage name cannot be empty")

        if self.capacity is not None and self.capacity < 0:
            raise TestModelValidationError("Storage capacity cannot be negative")


class IsolatedStorageTest(unittest.TestCase):
    """Test case for completely isolated Storage model testing."""

    @classmethod
    def setUpClass(cls):
        """Set up test database and session."""
        # Create an in-memory SQLite database for testing
        cls.engine = create_engine(
            'sqlite:///:memory:',
            echo=False,
            poolclass=StaticPool,
            connect_args={'check_same_thread': False}
        )

        # Create tables
        TestBase.metadata.create_all(cls.engine)

        # Create a session factory
        cls.Session = sessionmaker(bind=cls.engine)

        logger.info("Test database initialized")

    def setUp(self):
        """Create a new session for each test."""
        self.session = self.Session()
        logger.info("New test session created")

    def tearDown(self):
        """Close session after each test."""
        self.session.close()
        logger.info("Test session closed")

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Drop tables
        TestBase.metadata.drop_all(cls.engine)
        logger.info("Test database cleaned up")

    def test_storage_crud(self):
        """Test CRUD operations for Storage model."""
        logger.info("Testing Storage CRUD operations")

        # Create
        storage = TestStorage(
            name="Main Shelf",
            location_type=TestStorageLocationType.SHELF,
            capacity=100,
            description="Main storage shelf for leather materials"
        )
        self.session.add(storage)
        self.session.commit()

        # Read
        retrieved_storage = self.session.query(TestStorage).filter_by(name="Main Shelf").first()
        self.assertIsNotNone(retrieved_storage)
        self.assertEqual(retrieved_storage.name, "Main Shelf")
        self.assertEqual(retrieved_storage.location_type, TestStorageLocationType.SHELF)
        self.assertEqual(retrieved_storage.capacity, 100)

        # Update
        retrieved_storage.capacity = 150
        retrieved_storage.description = "Updated description"
        self.session.commit()

        updated_storage = self.session.query(TestStorage).filter_by(id=retrieved_storage.id).first()
        self.assertEqual(updated_storage.capacity, 150)
        self.assertEqual(updated_storage.description, "Updated description")

        # Delete
        self.session.delete(updated_storage)
        self.session.commit()

        deleted_check = self.session.query(TestStorage).filter_by(id=retrieved_storage.id).first()
        self.assertIsNone(deleted_check)

        logger.info("Storage CRUD tests passed")

    def test_storage_validation(self):
        """Test validation rules for Storage model."""
        logger.info("Testing Storage validation")

        # Test empty name validation
        with self.assertRaises(TestModelValidationError):
            invalid_storage = TestStorage(
                name="",
                location_type=TestStorageLocationType.SHELF,
                capacity=100
            )

        # Test negative capacity validation
        with self.assertRaises(TestModelValidationError):
            invalid_storage = TestStorage(
                name="Test Storage",
                location_type=TestStorageLocationType.SHELF,
                capacity=-10
            )

        logger.info("Storage validation tests passed")


if __name__ == '__main__':
    unittest.main()