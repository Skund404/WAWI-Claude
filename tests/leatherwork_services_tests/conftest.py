# tests/leatherwork_services_tests/conftest.py
"""
Pytest configuration and fixtures for customer service testing.
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from services.implementations.customer_service import CustomerService
from database.models.enums import CustomerStatus, CustomerTier, CustomerSource


@pytest.fixture
def customer_repository_mock():
    """
    Create a mock for the CustomerRepository.

    Returns:
        MagicMock: A mock repository with configurable behavior
    """
    mock_repo = MagicMock()

    # Set up some default mock behavior for create method
    def create_mock(data):
        # Create a mock customer with the input data
        mock_customer = MagicMock()
        for key, value in data.items():
            setattr(mock_customer, key, value)
        mock_customer.id = 1  # Default ID
        return mock_customer

    mock_repo.create.side_effect = create_mock

    # Default get_by_id behavior
    def get_by_id_mock(customer_id):
        mock_customer = MagicMock()
        mock_customer.id = customer_id
        mock_customer.name = 'Test Customer'
        mock_customer.email = 'test@example.com'
        mock_customer.status = CustomerStatus.ACTIVE.value
        mock_customer.tier = CustomerTier.STANDARD.value
        return mock_customer

    mock_repo.get_by_id.side_effect = get_by_id_mock

    # Default update behavior
    def update_mock(customer_id, data):
        mock_customer = get_by_id_mock(customer_id)
        for key, value in data.items():
            setattr(mock_customer, key, value)
        return mock_customer

    mock_repo.update.side_effect = update_mock

    # Default search behavior
    mock_repo.search.return_value = []

    # Default get_by_status behavior
    mock_repo.get_by_status.return_value = []

    # Default get_by_tier behavior
    mock_repo.get_by_tier.return_value = []

    return mock_repo


@pytest.fixture
def sales_repository_mock():
    """
    Create a mock for the SalesRepository.

    Returns:
        MagicMock: A mock sales repository
    """
    mock_repo = MagicMock()

    # Default get_by_customer behavior (empty list)
    mock_repo.get_by_customer.return_value = []

    return mock_repo


@pytest.fixture
def project_repository_mock():
    """
    Create a mock for the ProjectRepository.

    Returns:
        MagicMock: A mock project repository
    """
    mock_repo = MagicMock()

    # Default get_by_customer behavior (empty list)
    mock_repo.get_by_customer.return_value = []

    return mock_repo


@pytest.fixture
def customer_service_with_mock_repo(
        customer_repository_mock,
        sales_repository_mock,
        project_repository_mock
):
    """
    Creates a CustomerService with mocked repositories.

    Args:
        customer_repository_mock (MagicMock): Mock customer repository
        sales_repository_mock (MagicMock): Mock sales repository
        project_repository_mock (MagicMock): Mock project repository

    Returns:
        CustomerService: A service instance with mocked dependencies
    """
    # Create a mock session
    mock_session = MagicMock(spec=Session)

    # Create the service with mock repositories
    service = CustomerService(
        session=mock_session,
        customer_repository=customer_repository_mock,
        sales_repository=sales_repository_mock,
        project_repository=project_repository_mock
    )

    return service