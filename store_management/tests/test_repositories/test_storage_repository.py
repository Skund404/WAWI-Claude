# tests/test_repositories/test_storage_repository.py

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models.base import Base
from database.models.storage import Storage
from database.repositories.storage_repository import StorageRepository


class TestStorageRepository(unittest.TestCase):
    """Test cases for StorageRepository"""

    def setUp(self):
        """Set up test database and repository"""
        # Create in-memory SQLite database
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)

        # Create session and repository
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.repo = StorageRepository(self.session)

        # Add test data
        self.test_storage = Storage(
            location="Test Location",
            capacity=100,
            status="available"
        )
        self.session.add(self.test_storage)
        self.session.commit()

    def tearDown(self):
        """Clean up resources"""
        self.session.close()

    def test_get_all(self):
        """Test getting all storage locations"""
        storage_list = self.repo.get_all()
        self.assertEqual(len(storage_list), 1)
        self.assertEqual(storage_list[0].location, "Test Location")

    def test_get_by_id(self):
        """Test getting storage by ID"""
        storage = self.repo.get(self.test_storage.id)
        self.assertIsNotNone(storage)
        self.assertEqual(storage.location, "Test Location")

    def test_get_by_location(self):
        """Test getting storage by location"""
        storage = self.repo.get_by_location("Test Location")
        self.assertIsNotNone(storage)
        self.assertEqual(storage.capacity, 100)

    def test_create(self):
        """Test creating a new storage location"""
        new_storage = self.repo.create(
            location="New Location",
            capacity=200,
            status="maintenance"
        )
        self.session.commit()

        # Verify storage was created
        self.assertIsNotNone(new_storage.id)
        self.assertEqual(new_storage.location, "New Location")

        # Verify it can be retrieved
        retrieved = self.repo.get(new_storage.id)
        self.assertEqual(retrieved.capacity, 200)

    def test_update(self):
        """Test updating a storage location"""
        # Update the test storage
        self.repo.update(self.test_storage.id,
                         location="Updated Location",
                         capacity=150
                         )
        self.session.commit()

        # Verify changes
        updated_storage = self.repo.get(self.test_storage.id)
        self.assertEqual(updated_storage.location, "Updated Location")
        self.assertEqual(updated_storage.capacity, 150)

    def test_delete(self):
        """Test deleting a storage location"""
        # Delete the test storage
        result = self.repo.delete(self.test_storage.id)
        self.session.commit()

        # Verify deletion
        self.assertTrue(result)
        self.assertIsNone(self.repo.get(self.test_storage.id))


if __name__ == "__main__":
    unittest.main()