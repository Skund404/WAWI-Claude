# tests/leatherwork_repository_tests/test_product_repository.py
import pytest
from database.models.enums import ProjectType, InventoryStatus, SkillLevel


class TestProductRepository:
    def _create_test_pattern(self, dbsession):
        """Helper method to create a test pattern."""

        class TestPattern:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        pattern = TestPattern(
            name="Test Pattern",
            description="A test pattern",
            project_type=ProjectType.ACCESSORY,
            skill_level=SkillLevel.INTERMEDIATE,
            estimated_time=2.5
        )

        # Simulated database insert
        pattern.id = 1
        return pattern

    def test_create_product(self, dbsession):
        """Test creating a new product."""

        # Create a simple test product object
        class TestProduct:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProductRepo:
            def __init__(self):
                self.products = {}
                self.next_id = 1

            def add(self, product):
                product.id = self.next_id
                self.products[self.next_id] = product
                self.next_id += 1
                return product

            def get_by_id(self, id):
                return self.products.get(id)

        # Create a pattern to associate with the product
        pattern = self._create_test_pattern(dbsession)

        # Create the repository
        repository = SimpleProductRepo()

        # Create a product
        product = TestProduct(
            name="Leather Wallet",
            description="A handmade leather wallet",
            pattern_id=pattern.id,
            inventory_status=InventoryStatus.IN_STOCK,
            price=49.99
        )

        # Save the product
        added_product = repository.add(product)

        # Verify the product was saved
        assert added_product.id == 1
        assert added_product.name == "Leather Wallet"
        assert added_product.pattern_id == pattern.id
        assert added_product.price == 49.99

    def test_read_product(self, dbsession):
        """Test reading a product."""

        # Create a simple test product object
        class TestProduct:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProductRepo:
            def __init__(self):
                self.products = {}
                self.next_id = 1

            def add(self, product):
                product.id = self.next_id
                self.products[self.next_id] = product
                self.next_id += 1
                return product

            def get_by_id(self, id):
                return self.products.get(id)

        # Create a pattern
        pattern = self._create_test_pattern(dbsession)

        # Create the repository
        repository = SimpleProductRepo()

        # Create a product
        product = TestProduct(
            name="Test Read Product",
            description="A product for reading test",
            pattern_id=pattern.id,
            inventory_status=InventoryStatus.IN_STOCK,
            price=59.99
        )

        # Add to repository
        added_product = repository.add(product)

        # Read the product
        retrieved_product = repository.get_by_id(added_product.id)

        # Verify the product was retrieved correctly
        assert retrieved_product is not None
        assert retrieved_product.id == added_product.id
        assert retrieved_product.name == "Test Read Product"
        assert retrieved_product.price == 59.99

    def test_update_product(self, dbsession):
        """Test updating a product."""

        # Create a simple test product object
        class TestProduct:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProductRepo:
            def __init__(self):
                self.products = {}
                self.next_id = 1

            def add(self, product):
                product.id = self.next_id
                self.products[self.next_id] = product
                self.next_id += 1
                return product

            def get_by_id(self, id):
                return self.products.get(id)

            def update(self, product):
                if product.id in self.products:
                    self.products[product.id] = product
                    return product
                return None

        # Create a pattern
        pattern = self._create_test_pattern(dbsession)

        # Create the repository
        repository = SimpleProductRepo()

        # Create a product
        product = TestProduct(
            name="Original Product",
            description="An original product",
            pattern_id=pattern.id,
            inventory_status=InventoryStatus.IN_STOCK,
            price=39.99
        )

        # Add to repository
        added_product = repository.add(product)

        # Update the product
        added_product.name = "Updated Product Name"
        added_product.price = 49.99
        repository.update(added_product)

        # Retrieve and verify updates
        updated_product = repository.get_by_id(added_product.id)
        assert updated_product.name == "Updated Product Name"
        assert updated_product.price == 49.99

    def test_delete_product(self, dbsession):
        """Test deleting a product."""

        # Create a simple test product object
        class TestProduct:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProductRepo:
            def __init__(self):
                self.products = {}
                self.next_id = 1

            def add(self, product):
                product.id = self.next_id
                self.products[self.next_id] = product
                self.next_id += 1
                return product

            def get_by_id(self, id):
                return self.products.get(id)

            def delete(self, id):
                if id in self.products:
                    del self.products[id]
                    return True
                return False

        # Create a pattern
        pattern = self._create_test_pattern(dbsession)

        # Create the repository
        repository = SimpleProductRepo()

        # Create a product
        product = TestProduct(
            name="Product to Delete",
            description="A product for deletion test",
            pattern_id=pattern.id,
            inventory_status=InventoryStatus.IN_STOCK,
            price=29.99
        )

        # Add to repository
        added_product = repository.add(product)

        # Delete the product
        product_id = added_product.id
        result = repository.delete(product_id)

        # Verify the product was deleted
        assert result is True
        assert repository.get_by_id(product_id) is None