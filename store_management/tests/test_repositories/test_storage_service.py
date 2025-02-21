# tests/test_services/test_storage_service.py

import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from store_management.services.storage_service import StorageService
from store_management.database.repositories.storage_repository import StorageRepository
from store_management.database.repositories.product_repository import ProductRepository
from store_management.database.models.storage import Storage
from store_management.database.models.product import Product


class TestStorageService(unittest.TestCase):
    """Test cases for StorageService"""

    def setUp(self):
        """Set up test service with mock repositories"""
        # Create mock session
        self.session = MagicMock(spec=Session)

        # Create mock repositories
        self.storage_repo = MagicMock(spec=StorageRepository)
        self.product_repo = MagicMock(spec=ProductRepository)

        # Create patchers for repository constructors
        self.storage_repo_patcher = patch(
            'store_management.services.storage_service.StorageRepository',
            return_value=self.storage_repo
        )
        self.product_repo_patcher = patch(
            'store_management.services.storage_service.ProductRepository',
            return_value=self.product_repo
        )

        # Start patchers
        self.mock_storage_repo = self.storage_repo_patcher.start()
        self.mock_product_repo = self.product_repo_patcher.start()

        # Create service
        self.service = StorageService(self.session)

    def tearDown(self):
        """Clean up resources"""
        # Stop patchers
        self.storage_repo_patcher.stop()
        self.product_repo_patcher.stop()

    def test_assign_product_to_storage(self):
        """Test assigning a product to storage"""
        # Set up mock objects
        mock_storage = MagicMock(spec=Storage)
        mock_storage.id = 1

        mock_product = MagicMock(spec=Product)
        mock_product.id = 1

        # Set up repository mock returns
        self.storage_repo.get.return_value = mock_storage
        self.product_repo.get.return_value = mock_product

        # Call the service method
        result = self.service.assign_product_to_storage(1, 1)

        # Verify results
        self.assertTrue(result)
        self.assertEqual(mock_product.storage_id, 1)
        self.session.commit.assert_called_once()

        # tests/test_services/test_storage_service.py (continued)

        def test_assign_product_to_nonexistent_storage(self):
            """Test assigning a product to nonexistent storage"""
            # Set up repository mock returns
            self.storage_repo.get.return_value = None

            # Call the service method
            result = self.service.assign_product_to_storage(1, 1)

            # Verify results
            self.assertFalse(result)
            self.session.commit.assert_not_called()

        def test_get_storage_utilization(self):
            """Test getting storage utilization metrics"""
            # Set up mock storage locations
            mock_storage1 = MagicMock(spec=Storage)
            mock_storage1.id = 1
            mock_storage1.location = "Location A"
            mock_storage1.capacity = 100

            mock_storage2 = MagicMock(spec=Storage)
            mock_storage2.id = 2
            mock_storage2.location = "Location B"
            mock_storage2.capacity = 50

            # Set up repository mock returns
            self.storage_repo.get_all.return_value = [mock_storage1, mock_storage2]

            # Mock product repository to return different counts for each storage
            def get_by_storage_side_effect(storage_id):
                if storage_id == 1:
                    return [MagicMock(spec=Product) for _ in range(20)]  # 20 products
                elif storage_id == 2:
                    return [MagicMock(spec=Product) for _ in range(40)]  # 40 products
                return []

            self.product_repo.get_by_storage.side_effect = get_by_storage_side_effect

            # Call the service method
            result = self.service.get_storage_utilization()

            # Verify results
            self.assertEqual(len(result), 2)

            # Check first storage
            self.assertEqual(result[0]['id'], 1)
            self.assertEqual(result[0]['location'], "Location A")
            self.assertEqual(result[0]['capacity'], 100)
            self.assertEqual(result[0]['product_count'], 20)
            self.assertEqual(result[0]['utilization_percent'], 20.0)

            # Check second storage
            self.assertEqual(result[1]['id'], 2)
            self.assertEqual(result[1]['location'], "Location B")
            self.assertEqual(result[1]['capacity'], 50)
            self.assertEqual(result[1]['product_count'], 40)
            self.assertEqual(result[1]['utilization_percent'], 80.0)

        def test_create_storage_location(self):
            """Test creating a storage location"""
            # Set up repository mock returns
            self.storage_repo.get_by_location.return_value = None

            # Mock the create method to return a new Storage object
            def create_side_effect(**kwargs):
                storage = MagicMock(spec=Storage)
                storage.id = 1
                storage.location = kwargs.get('location')
                storage.capacity = kwargs.get('capacity')
                storage.status = kwargs.get('status')
                return storage

            self.storage_repo.create.side_effect = create_side_effect

            # Call the service method
            data = {
                "location": "New Location",
                "capacity": 200,
                "status": "available"
            }
            result = self.service.create_storage_location(data)

            # Verify results
            self.assertIsNotNone(result)
            self.assertEqual(result.location, "New Location")
            self.session.commit.assert_called_once()

        def test_create_duplicate_storage_location(self):
            """Test creating a duplicate storage location"""
            # Mock the repository to simulate an existing location
            mock_storage = MagicMock(spec=Storage)
            self.storage_repo.get_by_location.return_value = mock_storage

            # Call the service method
            data = {
                "location": "Existing Location",
                "capacity": 200,
                "status": "available"
            }
            result = self.service.create_storage_location(data)

            # Verify results
            self.assertIsNone(result)
            self.storage_repo.create.assert_not_called()

    if __name__ == "__main__":
        unittest.main()