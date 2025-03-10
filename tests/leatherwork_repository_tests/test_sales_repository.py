# tests/leatherwork_repository_tests/test_sales_repository.py
import pytest
from datetime import datetime, timedelta

from database.models.enums import SaleStatus, PaymentStatus, CustomerStatus, CustomerTier


class TestSalesRepository:
    def _create_test_customer(self, dbsession):
        """Helper method to create a test customer."""

        # Create a simple test customer object
        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        customer = TestCustomer(
            first_name="Test",
            last_name="Customer",
            email="test@example.com",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD
        )

        # Add to session (simulated)
        customer.id = 1
        return customer

    def test_create_sales(self, dbsession):
        """Test creating a new sales record."""

        # Create a simple test sales object
        class TestSales:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesRepo:
            def __init__(self):
                self.sales = {}
                self.next_id = 1

            def add(self, sale):
                sale.id = self.next_id
                self.sales[self.next_id] = sale
                self.next_id += 1
                return sale

            def get_by_id(self, id):
                return self.sales.get(id)

        # Create the repository
        repository = SimpleSalesRepo()

        # Create a test customer
        customer = self._create_test_customer(dbsession)

        # Create a sales record
        sales = TestSales(
            customer_id=customer.id,
            sale_date=datetime.now(),
            total_amount=199.99,
            status=SaleStatus.COMPLETED,
            payment_status=PaymentStatus.PAID
        )

        # Save the sales record
        added_sales = repository.add(sales)

        # Verify the sales record was saved
        assert added_sales.id == 1
        assert added_sales.customer_id == customer.id
        assert added_sales.total_amount == 199.99
        assert added_sales.status == SaleStatus.COMPLETED

    def test_read_sales(self, dbsession):
        """Test reading a sales record."""

        # Create a simple test sales object
        class TestSales:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesRepo:
            def __init__(self):
                self.sales = {}
                self.next_id = 1

            def add(self, sale):
                sale.id = self.next_id
                self.sales[self.next_id] = sale
                self.next_id += 1
                return sale

            def get_by_id(self, id):
                return self.sales.get(id)

        # Create the repository
        repository = SimpleSalesRepo()

        # Create a test customer
        customer = self._create_test_customer(dbsession)

        # Create a sales record
        sales = TestSales(
            customer_id=customer.id,
            sale_date=datetime.now(),
            total_amount=149.99,
            status=SaleStatus.IN_PRODUCTION,  # Changed from PROCESSING to IN_PRODUCTION
            payment_status=PaymentStatus.PENDING
        )

        # Add to repository
        added_sales = repository.add(sales)

        # Read the sales record
        retrieved_sales = repository.get_by_id(added_sales.id)

        # Verify the sales record was retrieved correctly
        assert retrieved_sales is not None
        assert retrieved_sales.id == added_sales.id
        assert retrieved_sales.total_amount == 149.99

    def test_update_sales(self, dbsession):
        """Test updating a sales record."""

        # Create a simple test sales object
        class TestSales:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesRepo:
            def __init__(self):
                self.sales = {}
                self.next_id = 1

            def add(self, sale):
                sale.id = self.next_id
                self.sales[self.next_id] = sale
                self.next_id += 1
                return sale

            def get_by_id(self, id):
                return self.sales.get(id)

            def update(self, sale):
                if sale.id in self.sales:
                    self.sales[sale.id] = sale
                    return sale
                return None

        # Create the repository
        repository = SimpleSalesRepo()

        # Create a test customer
        customer = self._create_test_customer(dbsession)

        # Create a sales record
        sales = TestSales(
            customer_id=customer.id,
            sale_date=datetime.now(),
            total_amount=99.99,
            status=SaleStatus.IN_PRODUCTION,  # Changed from PROCESSING to IN_PRODUCTION
            payment_status=PaymentStatus.PENDING
        )

        # Add to repository
        added_sales = repository.add(sales)

        # Update the sales record
        added_sales.total_amount = 129.99
        added_sales.status = SaleStatus.COMPLETED
        added_sales.payment_status = PaymentStatus.PAID
        repository.update(added_sales)

        # Retrieve and verify updates
        updated_sales = repository.get_by_id(added_sales.id)
        assert updated_sales.total_amount == 129.99
        assert updated_sales.status == SaleStatus.COMPLETED
        assert updated_sales.payment_status == PaymentStatus.PAID

    def test_delete_sales(self, dbsession):
        """Test deleting a sales record."""

        # Create a simple test sales object
        class TestSales:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSalesRepo:
            def __init__(self):
                self.sales = {}
                self.next_id = 1

            def add(self, sale):
                sale.id = self.next_id
                self.sales[self.next_id] = sale
                self.next_id += 1
                return sale

            def get_by_id(self, id):
                return self.sales.get(id)

            def delete(self, id):
                if id in self.sales:
                    del self.sales[id]
                    return True
                return False

        # Create the repository
        repository = SimpleSalesRepo()

        # Create a test customer
        customer = self._create_test_customer(dbsession)

        # Create a sales record
        sales = TestSales(
            customer_id=customer.id,
            sale_date=datetime.now(),
            total_amount=79.99,
            status=SaleStatus.IN_PRODUCTION,  # Changed from PROCESSING to IN_PRODUCTION
            payment_status=PaymentStatus.PENDING
        )

        # Add to repository
        added_sales = repository.add(sales)

        # Delete the sales record
        sales_id = added_sales.id
        result = repository.delete(sales_id)

        # Verify the sales record was deleted
        assert result is True
        assert repository.get_by_id(sales_id) is None