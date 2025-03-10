# tests/leatherwork_services_tests/test_customer_service.py
"""
Unit tests for the CustomerService implementation.

This module tests the functionality of the CustomerService,
covering CRUD operations, business logic, and error handling.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from database.models.enums import CustomerStatus, CustomerSource, CustomerTier
from services.exceptions import ValidationError, NotFoundError
from services.dto.customer_dto import CustomerDTO


class TestCustomerService:
    def test_create_customer_success(self, customer_service_with_mock_repo):
        """
        Test successful customer creation with valid data.
        """
        # Prepare customer data
        customer_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'status': CustomerStatus.ACTIVE.value,
            'source': CustomerSource.REFERRAL.value,
            'tier': CustomerTier.STANDARD.value
        }

        # Create customer
        created_customer = customer_service_with_mock_repo.create(customer_data)

        # Assertions
        assert created_customer is not None
        assert created_customer['name'] == 'John Doe'
        assert created_customer['email'] == 'john.doe@example.com'
        assert created_customer['status'] == CustomerStatus.ACTIVE.value

    def test_create_customer_validation_error(self, customer_service_with_mock_repo):
        """
        Test customer creation with invalid data raises ValidationError.
        """
        # Prepare invalid customer data (missing required fields)
        invalid_customer_data = {
            'email': 'invalid-email'  # Missing name and invalid email
        }

        # Expect ValidationError
        with pytest.raises(ValidationError) as excinfo:
            customer_service_with_mock_repo.create(invalid_customer_data)

        # Optional: Check error message
        assert 'Missing required field' in str(excinfo.value)

    def test_get_customer_by_id_success(self, customer_service_with_mock_repo, customer_repository_mock):
        """
        Test retrieving an existing customer by ID.
        """
        # Create a mock customer with all required attributes as an object
        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.name = 'Test Customer'
        mock_customer.email = 'test@example.com'
        mock_customer.status = CustomerStatus.ACTIVE.value
        mock_customer.tier = CustomerTier.STANDARD.value
        mock_customer.source = CustomerSource.REFERRAL.value

        # Configure the repository mock
        customer_repository_mock.get_by_id.return_value = mock_customer

        # Retrieve the customer
        retrieved_customer = customer_service_with_mock_repo.get_by_id(1)

        # Assertions
        assert retrieved_customer is not None
        assert retrieved_customer['id'] == 1
        assert retrieved_customer['name'] == 'Test Customer'

    def test_get_customer_by_id_not_found(self, customer_service_with_mock_repo, customer_repository_mock):
        """
        Test retrieving a non-existent customer raises NotFoundError.
        """

        # Configure mock to simulate not finding the customer and prepare side effect
        def raise_not_found_error(*args, **kwargs):
            raise NotFoundError(f"Customer with ID 999999 not found")

        customer_repository_mock.get_by_id.side_effect = raise_not_found_error

        # Attempt to retrieve non-existent customer
        with pytest.raises(NotFoundError, match="Customer with ID 999999 not found"):
            customer_service_with_mock_repo.get_by_id(999999)

    def test_update_customer_success(self, customer_service_with_mock_repo, customer_repository_mock):
        """
        Test successful customer update.
        """
        # Create a mock customer with all required attributes
        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.name = 'John Doe'
        mock_customer.email = 'john@example.com'
        mock_customer.status = CustomerStatus.ACTIVE.value
        mock_customer.tier = CustomerTier.STANDARD.value
        mock_customer.source = CustomerSource.REFERRAL.value

        # Configure the repository mock
        customer_repository_mock.get_by_id.return_value = mock_customer
        customer_repository_mock.update.return_value = mock_customer

        # Prepare update data
        update_data = {
            'name': 'John Smith',
            'tier': CustomerTier.PREMIUM.value
        }

        # Perform update
        updated_customer = customer_service_with_mock_repo.update(1, update_data)

        # Assertions
        assert updated_customer['name'] == 'John Smith'
        assert updated_customer['tier'] == CustomerTier.PREMIUM.value

    def test_delete_customer_success(self, customer_service_with_mock_repo,
                                     customer_repository_mock,
                                     sales_repository_mock):
        """
        Test successful customer deletion.
        """
        # Create a mock customer
        mock_customer = MagicMock()
        mock_customer.id = 1

        # Configure mock repositories
        customer_repository_mock.get_by_id.return_value = mock_customer
        sales_repository_mock.get_by_customer.return_value = []

        # Perform deletion
        result = customer_service_with_mock_repo.delete(1)

        # Assertions
        assert result is True

    def test_delete_customer_with_sales(self, customer_service_with_mock_repo,
                                        customer_repository_mock,
                                        sales_repository_mock):
        """
        Test deleting a customer with sales records raises ValidationError.
        """
        # Create a mock customer
        mock_customer = MagicMock()
        mock_customer.id = 1

        # Configure mock repositories
        customer_repository_mock.get_by_id.return_value = mock_customer
        sales_repository_mock.get_by_customer.return_value = [MagicMock()]  # Non-empty sales list

        # Attempt to delete customer with sales
        with pytest.raises(ValidationError):
            customer_service_with_mock_repo.delete(1)

    def test_search_customers(self, customer_service_with_mock_repo, customer_repository_mock):
        """
        Test searching for customers.
        """
        # Set up mock search results where each item will be converted to an object
        mock_results = [
            SimpleNamespace(
                id=1,
                name='John Doe',
                email='john@example.com',
                status=CustomerStatus.ACTIVE.value,
                tier=CustomerTier.STANDARD.value,
                source=CustomerSource.REFERRAL.value
            ),
            SimpleNamespace(
                id=2,
                name='Jane Doe',
                email='jane@example.com',
                status=CustomerStatus.ACTIVE.value,
                tier=CustomerTier.STANDARD.value,
                source=CustomerSource.REFERRAL.value
            )
        ]

        # Configure the repository mock to return these customers
        customer_repository_mock.search.return_value = mock_results

        # Perform search
        results = customer_service_with_mock_repo.search('Doe')

        # Assertions
        assert len(results) == 2
        assert any(result['name'] == 'John Doe' for result in results)

    def test_get_by_status(self, customer_service_with_mock_repo, customer_repository_mock):
        """
        Test retrieving customers by status.
        """
        # Set up mock customers as SimpleNamespace objects
        mock_customers = [
            SimpleNamespace(
                id=1,
                status=CustomerStatus.ACTIVE.value,
                name='Active Customer 1',
                email='active1@example.com',
                tier=CustomerTier.STANDARD.value,
                source=CustomerSource.REFERRAL.value
            ),
            SimpleNamespace(
                id=2,
                status=CustomerStatus.ACTIVE.value,
                name='Active Customer 2',
                email='active2@example.com',
                tier=CustomerTier.STANDARD.value,
                source=CustomerSource.REFERRAL.value
            )
        ]
        customer_repository_mock.get_by_status.return_value = mock_customers

        # Retrieve customers by status
        results = customer_service_with_mock_repo.get_by_status(CustomerStatus.ACTIVE.value)

        # Assertions
        assert len(results) == 2
        assert all(result['status'] == CustomerStatus.ACTIVE.value for result in results)

    def test_get_by_tier(self, customer_service_with_mock_repo, customer_repository_mock):
        """
        Test retrieving customers by tier.
        """
        # Set up mock customers as SimpleNamespace objects
        mock_customers = [
            SimpleNamespace(
                id=1,
                tier=CustomerTier.PREMIUM.value,
                name='Premium Customer 1',
                email='premium1@example.com',
                status=CustomerStatus.ACTIVE.value,
                source=CustomerSource.REFERRAL.value
            ),
            SimpleNamespace(
                id=2,
                tier=CustomerTier.PREMIUM.value,
                name='Premium Customer 2',
                email='premium2@example.com',
                status=CustomerStatus.ACTIVE.value,
                source=CustomerSource.REFERRAL.value
            )
        ]
        customer_repository_mock.get_by_tier.return_value = mock_customers

        # Retrieve customers by tier
        results = customer_service_with_mock_repo.get_by_tier(CustomerTier.PREMIUM.value)

        # Assertions
        assert len(results) == 2
        assert all(result['tier'] == CustomerTier.PREMIUM.value for result in results)