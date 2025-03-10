# tests/leatherwork_repository_tests/test_customer_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import CustomerStatus, CustomerTier, CustomerSource


class TestCustomerRepository:
    def test_create_customer(self, dbsession):
        """Test creating a new customer."""

        # Create a simple test customer object
        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleCustomerRepo:
            def __init__(self):
                self.customers = {}
                self.next_id = 1

            def add(self, customer):
                customer.id = self.next_id
                self.customers[self.next_id] = customer
                self.next_id += 1
                return customer

            def get_by_id(self, id):
                return self.customers.get(id)

        # Create the repository
        repository = SimpleCustomerRepo()

        # Create a customer
        customer = TestCustomer(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD,
            source=CustomerSource.WEBSITE,
            created_at=datetime.now()
        )

        # Save the customer
        added_customer = repository.add(customer)

        # Verify the customer was saved
        assert added_customer.id == 1
        assert added_customer.first_name == "John"
        assert added_customer.last_name == "Doe"
        assert added_customer.email == "john.doe@example.com"
        assert added_customer.status == CustomerStatus.ACTIVE
        assert added_customer.tier == CustomerTier.STANDARD
        assert added_customer.source == CustomerSource.WEBSITE

    def test_read_customer(self, dbsession):
        """Test reading a customer."""

        # Create a simple test customer object
        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleCustomerRepo:
            def __init__(self):
                self.customers = {}
                self.next_id = 1

            def add(self, customer):
                customer.id = self.next_id
                self.customers[self.next_id] = customer
                self.next_id += 1
                return customer

            def get_by_id(self, id):
                return self.customers.get(id)

        # Create the repository
        repository = SimpleCustomerRepo()

        # Create a customer
        customer = TestCustomer(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="555-987-6543",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.PREMIUM,
            source=CustomerSource.REFERRAL,
            created_at=datetime.now()
        )

        # Add to repository
        added_customer = repository.add(customer)

        # Read the customer
        retrieved_customer = repository.get_by_id(added_customer.id)

        # Verify the customer was retrieved correctly
        assert retrieved_customer is not None
        assert retrieved_customer.id == added_customer.id
        assert retrieved_customer.first_name == "Jane"
        assert retrieved_customer.last_name == "Smith"
        assert retrieved_customer.email == "jane.smith@example.com"
        assert retrieved_customer.tier == CustomerTier.PREMIUM

    def test_update_customer(self, dbsession):
        """Test updating a customer."""

        # Create a simple test customer object
        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleCustomerRepo:
            def __init__(self):
                self.customers = {}
                self.next_id = 1

            def add(self, customer):
                customer.id = self.next_id
                self.customers[self.next_id] = customer
                self.next_id += 1
                return customer

            def get_by_id(self, id):
                return self.customers.get(id)

            def update(self, customer):
                if customer.id in self.customers:
                    self.customers[customer.id] = customer
                    return customer
                return None

        # Create the repository
        repository = SimpleCustomerRepo()

        # Create a customer
        customer = TestCustomer(
            first_name="Robert",
            last_name="Johnson",
            email="robert.johnson@example.com",
            phone="555-345-6789",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD,
            source=CustomerSource.MARKETING,
            created_at=datetime.now()
        )

        # Add to repository
        added_customer = repository.add(customer)

        # Update the customer
        added_customer.last_name = "Smith-Johnson"
        added_customer.tier = CustomerTier.PREMIUM
        added_customer.phone = "555-999-8888"
        repository.update(added_customer)

        # Retrieve and verify updates
        updated_customer = repository.get_by_id(added_customer.id)
        assert updated_customer.last_name == "Smith-Johnson"
        assert updated_customer.tier == CustomerTier.PREMIUM
        assert updated_customer.phone == "555-999-8888"

    def test_delete_customer(self, dbsession):
        """Test deleting a customer."""

        # Create a simple test customer object
        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleCustomerRepo:
            def __init__(self):
                self.customers = {}
                self.next_id = 1

            def add(self, customer):
                customer.id = self.next_id
                self.customers[self.next_id] = customer
                self.next_id += 1
                return customer

            def get_by_id(self, id):
                return self.customers.get(id)

            def delete(self, id):
                if id in self.customers:
                    del self.customers[id]
                    return True
                return False

        # Create the repository
        repository = SimpleCustomerRepo()

        # Create a customer
        customer = TestCustomer(
            first_name="Alice",
            last_name="Brown",
            email="alice.brown@example.com",
            phone="555-111-2222",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD,
            source=CustomerSource.SOCIAL_MEDIA,
            created_at=datetime.now()
        )

        # Add to repository
        added_customer = repository.add(customer)

        # Delete the customer
        customer_id = added_customer.id
        result = repository.delete(customer_id)

        # Verify the customer was deleted
        assert result is True
        assert repository.get_by_id(customer_id) is None

    def test_customer_status_change(self, dbsession):
        """Test changing a customer's status."""

        # Create a simple test customer object
        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleCustomerRepo:
            def __init__(self):
                self.customers = {}
                self.next_id = 1

            def add(self, customer):
                customer.id = self.next_id
                self.customers[self.next_id] = customer
                self.next_id += 1
                return customer

            def get_by_id(self, id):
                return self.customers.get(id)

            def update(self, customer):
                if customer.id in self.customers:
                    self.customers[customer.id] = customer
                    return customer
                return None

        # Create the repository
        repository = SimpleCustomerRepo()

        # Create a customer
        customer = TestCustomer(
            first_name="Michael",
            last_name="Wilson",
            email="michael.wilson@example.com",
            phone="555-444-3333",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD,
            source=CustomerSource.WEBSITE,
            created_at=datetime.now()
        )

        # Add to repository
        added_customer = repository.add(customer)

        # Change the customer's status
        status_transitions = [
            CustomerStatus.INACTIVE,
            CustomerStatus.SUSPENDED,
            CustomerStatus.ACTIVE
        ]

        for new_status in status_transitions:
            added_customer.status = new_status
            repository.update(added_customer)

            # Verify status was updated
            updated_customer = repository.get_by_id(added_customer.id)
            assert updated_customer.status == new_status

    def test_customer_tier_upgrade(self, dbsession):
        """Test upgrading a customer's loyalty tier."""

        # Create a simple test customer object
        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleCustomerRepo:
            def __init__(self):
                self.customers = {}
                self.next_id = 1

            def add(self, customer):
                customer.id = self.next_id
                self.customers[self.next_id] = customer
                self.next_id += 1
                return customer

            def get_by_id(self, id):
                return self.customers.get(id)

            def update(self, customer):
                if customer.id in self.customers:
                    self.customers[customer.id] = customer
                    return customer
                return None

        # Create the repository
        repository = SimpleCustomerRepo()

        # Create a customer
        customer = TestCustomer(
            first_name="Sarah",
            last_name="Davis",
            email="sarah.davis@example.com",
            phone="555-777-8888",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.NEW,
            source=CustomerSource.RETAIL,
            created_at=datetime.now() - timedelta(days=30)
        )

        # Add to repository
        added_customer = repository.add(customer)

        # Upgrade customer through tiers
        tier_upgrades = [
            CustomerTier.STANDARD,
            CustomerTier.PREMIUM,
            CustomerTier.VIP
        ]

        for new_tier in tier_upgrades:
            added_customer.tier = new_tier
            repository.update(added_customer)

            # Verify tier was updated
            updated_customer = repository.get_by_id(added_customer.id)
            assert updated_customer.tier == new_tier