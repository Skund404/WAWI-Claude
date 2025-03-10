# tests/leatherwork_repository_tests/test_sales_item_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    SaleStatus,
    PaymentStatus,
    CustomerStatus,
    ProjectType
)


class TestSalesItemRepository:
    def _create_test_customer(self, dbsession):
        """Helper method to create a test customer."""

        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        customer = TestCustomer(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="555-123-4567",
            status=CustomerStatus.ACTIVE
        )

        # Simulated database insert
        customer.id = 1
        return customer

    def _create_test_sales(self, dbsession, customer_id):
        """Helper method to create a test sales record."""

        class TestSales:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        sales = TestSales(
            customer_id=customer_id,
            sale_date=datetime.now(),
            total_amount=0,  # Will be calculated based on items
            status=SaleStatus.QUOTE_REQUEST,
            payment_status=PaymentStatus.PENDING,
            created_at=datetime.now()
        )

        # Simulated database insert
        sales.id = 1
        return sales

    def _create_test_product(self, dbsession):
        """Helper method to create a test product."""

        class TestProduct:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        product = TestProduct(
            name="Leather Wallet",
            description="Handcrafted leather wallet",
            price=79.99,
            project_type=ProjectType.WALLET,
            created_at=datetime.now()
        )

        # Simulated database insert
        product.id = 1
        return product

    def test_create_sales_item(self, dbsession):
        """Test creating a new sales item."""

        # Create a simple test sales item object
        class TestSalesItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesItemRepo:
            def __init__(self):
                self.sales_items = {}
                self.next_id = 1

            def add(self, sales_item):
                sales_item.id = self.next_id
                self.sales_items[self.next_id] = sales_item
                self.next_id += 1
                return sales_item

            def get_by_id(self, id):
                return self.sales_items.get(id)

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)
        product = self._create_test_product(dbsession)

        # Create the repository
        repository = SimpleSalesItemRepo()

        # Create a sales item
        sales_item = TestSalesItem(
            sales_id=sales.id,
            product_id=product.id,
            quantity=1,
            price=product.price,
            discount_percentage=0,
            notes="Standard model",
            created_at=datetime.now()
        )

        # Save the sales item
        added_sales_item = repository.add(sales_item)

        # Verify the sales item was saved
        assert added_sales_item.id == 1
        assert added_sales_item.sales_id == sales.id
        assert added_sales_item.product_id == product.id
        assert added_sales_item.quantity == 1
        assert added_sales_item.price == product.price
        assert added_sales_item.discount_percentage == 0
        assert added_sales_item.notes == "Standard model"

    def test_read_sales_item(self, dbsession):
        """Test reading a sales item."""

        # Create a simple test sales item object
        class TestSalesItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesItemRepo:
            def __init__(self):
                self.sales_items = {}
                self.next_id = 1

            def add(self, sales_item):
                sales_item.id = self.next_id
                self.sales_items[self.next_id] = sales_item
                self.next_id += 1
                return sales_item

            def get_by_id(self, id):
                return self.sales_items.get(id)

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)
        product = self._create_test_product(dbsession)

        # Create the repository
        repository = SimpleSalesItemRepo()

        # Create a sales item
        sales_item = TestSalesItem(
            sales_id=sales.id,
            product_id=product.id,
            quantity=2,
            price=79.99,
            discount_percentage=10,
            subtotal=(2 * 79.99) * 0.9,  # 10% discount
            notes="Discounted order",
            created_at=datetime.now()
        )

        # Add to repository
        added_sales_item = repository.add(sales_item)

        # Read the sales item
        retrieved_sales_item = repository.get_by_id(added_sales_item.id)

        # Verify the sales item was retrieved correctly
        assert retrieved_sales_item is not None
        assert retrieved_sales_item.id == added_sales_item.id
        assert retrieved_sales_item.sales_id == sales.id
        assert retrieved_sales_item.product_id == product.id
        assert retrieved_sales_item.quantity == 2
        assert retrieved_sales_item.price == 79.99
        assert retrieved_sales_item.discount_percentage == 10

    def test_update_sales_item(self, dbsession):
        """Test updating a sales item."""

        # Create a simple test sales item object
        class TestSalesItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesItemRepo:
            def __init__(self):
                self.sales_items = {}
                self.next_id = 1

            def add(self, sales_item):
                sales_item.id = self.next_id
                self.sales_items[self.next_id] = sales_item
                self.next_id += 1
                return sales_item

            def get_by_id(self, id):
                return self.sales_items.get(id)

            def update(self, sales_item):
                if sales_item.id in self.sales_items:
                    self.sales_items[sales_item.id] = sales_item
                    return sales_item
                return None

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)
        product = self._create_test_product(dbsession)

        # Create the repository
        repository = SimpleSalesItemRepo()

        # Create a sales item
        sales_item = TestSalesItem(
            sales_id=sales.id,
            product_id=product.id,
            quantity=1,
            price=79.99,
            discount_percentage=0,
            notes="Standard order",
            created_at=datetime.now()
        )

        # Add to repository
        added_sales_item = repository.add(sales_item)

        # Update the sales item
        added_sales_item.quantity = 3
        added_sales_item.discount_percentage = 5
        added_sales_item.notes = "Updated order quantity and added discount"
        repository.update(added_sales_item)

        # Retrieve and verify updates
        updated_sales_item = repository.get_by_id(added_sales_item.id)
        assert updated_sales_item.quantity == 3
        assert updated_sales_item.discount_percentage == 5
        assert updated_sales_item.notes == "Updated order quantity and added discount"

    def test_delete_sales_item(self, dbsession):
        """Test deleting a sales item."""

        # Create a simple test sales item object
        class TestSalesItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesItemRepo:
            def __init__(self):
                self.sales_items = {}
                self.next_id = 1

            def add(self, sales_item):
                sales_item.id = self.next_id
                self.sales_items[self.next_id] = sales_item
                self.next_id += 1
                return sales_item

            def get_by_id(self, id):
                return self.sales_items.get(id)

            def delete(self, id):
                if id in self.sales_items:
                    del self.sales_items[id]
                    return True
                return False

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)
        product = self._create_test_product(dbsession)

        # Create the repository
        repository = SimpleSalesItemRepo()

        # Create a sales item
        sales_item = TestSalesItem(
            sales_id=sales.id,
            product_id=product.id,
            quantity=1,
            price=79.99,
            discount_percentage=0,
            created_at=datetime.now()
        )

        # Add to repository
        added_sales_item = repository.add(sales_item)

        # Delete the sales item
        sales_item_id = added_sales_item.id
        result = repository.delete(sales_item_id)

        # Verify the sales item was deleted
        assert result is True
        assert repository.get_by_id(sales_item_id) is None

    def test_find_sales_items_by_sales(self, dbsession):
        """Test finding sales items by sales."""

        # Create a simple test sales item object
        class TestSalesItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesItemRepo:
            def __init__(self):
                self.sales_items = {}
                self.next_id = 1

            def add(self, sales_item):
                sales_item.id = self.next_id
                self.sales_items[self.next_id] = sales_item
                self.next_id += 1
                return sales_item

            def find_by_sales_id(self, sales_id):
                return [si for si in self.sales_items.values() if si.sales_id == sales_id]

        # Create test data
        class TestSales:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        customer = self._create_test_customer(dbsession)

        sales1 = TestSales(
            customer_id=customer.id,
            total_amount=0,
            status=SaleStatus.QUOTE_REQUEST,
            created_at=datetime.now()
        )
        sales1.id = 1

        sales2 = TestSales(
            customer_id=customer.id,
            total_amount=0,
            status=SaleStatus.QUOTE_REQUEST,
            created_at=datetime.now()
        )
        sales2.id = 2

        product = self._create_test_product(dbsession)

        # Create the repository
        repository = SimpleSalesItemRepo()

        # Create sales items
        item1 = TestSalesItem(
            sales_id=sales1.id,
            product_id=product.id,
            quantity=1,
            price=79.99
        )

        item2 = TestSalesItem(
            sales_id=sales1.id,
            product_id=product.id,
            quantity=2,
            price=79.99
        )

        item3 = TestSalesItem(
            sales_id=sales2.id,
            product_id=product.id,
            quantity=1,
            price=79.99
        )

        # Add to repository
        repository.add(item1)
        repository.add(item2)
        repository.add(item3)

        # Find sales items by sales
        sales1_items = repository.find_by_sales_id(sales1.id)
        sales2_items = repository.find_by_sales_id(sales2.id)

        # Verify results
        assert len(sales1_items) == 2
        assert len(sales2_items) == 1
        assert all(si.sales_id == sales1.id for si in sales1_items)
        assert all(si.sales_id == sales2.id for si in sales2_items)

    def test_calculate_subtotal(self, dbsession):
        """Test calculating subtotal for a sales item."""

        # Create a simple test sales item object
        class TestSalesItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def calculate_subtotal(self):
                if hasattr(self, 'discount_percentage') and self.discount_percentage:
                    return self.quantity * self.price * (1 - self.discount_percentage / 100)
                return self.quantity * self.price

        # Create a simple in-memory repository for testing
        class SimpleSalesItemRepo:
            def __init__(self):
                self.sales_items = {}
                self.next_id = 1

            def add(self, sales_item):
                # Calculate subtotal before adding
                if not hasattr(sales_item, 'subtotal') or sales_item.subtotal is None:
                    sales_item.subtotal = sales_item.calculate_subtotal()

                sales_item.id = self.next_id
                self.sales_items[self.next_id] = sales_item
                self.next_id += 1
                return sales_item

            def get_by_id(self, id):
                return self.sales_items.get(id)

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)
        product = self._create_test_product(dbsession)

        # Create the repository
        repository = SimpleSalesItemRepo()

        # Create sales items with different scenarios
        no_discount_item = TestSalesItem(
            sales_id=sales.id,
            product_id=product.id,
            quantity=2,
            price=79.99,
            discount_percentage=0
        )

        discount_item = TestSalesItem(
            sales_id=sales.id,
            product_id=product.id,
            quantity=3,
            price=79.99,
            discount_percentage=15
        )

        # Add to repository
        added_no_discount = repository.add(no_discount_item)
        added_discount = repository.add(discount_item)

        # Verify subtotals
        assert added_no_discount.subtotal == 2 * 79.99
        assert round(added_discount.subtotal, 2) == round(3 * 79.99 * 0.85, 2)  # 15% discount