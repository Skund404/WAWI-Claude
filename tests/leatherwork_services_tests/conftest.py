# tests/leatherwork_services_tests/conftest.py
"""
Comprehensive pytest configuration and fixtures for service layer testing.

This module provides a flexible and extensible mocking framework
for testing various services in the leatherworking application.
"""

import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from sqlalchemy.orm import Session

from services.exceptions import ValidationError, NotFoundError

# Import all enums that might be used in mocking
from database.models.enums import (
    # Customer-related enums
    CustomerStatus, CustomerTier, CustomerSource,

    # Hardware-related enums
    HardwareType, HardwareMaterial, HardwareFinish,

    # Leather-related enums
    LeatherType, LeatherFinish,

    # Material-related enums
    MaterialType,

    # Project-related enums
    ProjectType, ProjectStatus,

    # Other enums as needed
    InventoryStatus,
    SupplierStatus,
    ToolCategory
)


class MockEntityFactory:
    """
    A factory for creating mock entities with flexible attributes.
    """

    @staticmethod
    def create_entity(entity_type='Generic', **kwargs):
        """
        Create a SimpleNamespace with dynamic attributes.

        Args:
            entity_type (str): Type of entity for default naming
            **kwargs: Additional attributes to set

        Returns:
            SimpleNamespace: A mock entity with specified attributes
        """
        # Ensure 'id' is set
        if 'id' not in kwargs:
            kwargs['id'] = 1

        # Ensure 'name' is set with a default if not provided
        if 'name' not in kwargs:
            kwargs['name'] = f'Default {entity_type}'

        return SimpleNamespace(**kwargs)


@pytest.fixture
def mock_session():
    """
    Create a mock SQLAlchemy session for testing.

    Returns:
        MagicMock: A mock session object with basic Session specifications
    """
    return MagicMock(spec=Session)


class MockRepositoryFactory:
    """
    A factory for creating mock repositories with common behaviors.
    """

    @staticmethod
    def create_mock_repository(
            entity_type='Generic',
            create_validation_fields=None,
            default_results=None,
            not_found_id=999999
    ):
        """
        Create a flexible mock repository with configurable behavior.

        Args:
            entity_type (str): Name of the entity for more descriptive mocking
            create_validation_fields (list): Fields required for creation
            default_results (list): Default results for search-like methods
            not_found_id (int): ID that will trigger a NotFoundError

        Returns:
            MagicMock: A configured mock repository
        """
        mock_repo = MagicMock()
        create_validation_fields = create_validation_fields or ['name']

        # Create method with validation
        def create_mock(data):
            # Validate required fields
            for field in create_validation_fields:
                if not data.get(field):
                    raise ValidationError(f"Missing required field: {field}")

            # Create a mock entity with all input data
            return MockEntityFactory.create_entity(
                entity_type,
                **{k: data.get(k, f"Default {k}") for k in data}
            )

        # Get by ID method with not found handling
        def get_by_id_mock(entity_id):
            if entity_id == not_found_id:
                raise NotFoundError(f"{entity_type} with ID {entity_id} not found")

            # Check for a matching default entity
            for default_entity in (default_results or []):
                if hasattr(default_entity, 'id') and default_entity.id == entity_id:
                    return default_entity

            # Create a default mock entity if no matching entity found
            return MockEntityFactory.create_entity(
                entity_type,
                id=entity_id,
                **{f"default_{k}": f"Default {k}" for k in create_validation_fields}
            )

        # Update method
        def update_mock(entity_id, data):
            # Retrieve the existing entity
            existing = get_by_id_mock(entity_id)

            # Update with new data
            for key, value in data.items():
                setattr(existing, key, value)

            return existing

        # Configure repository methods
        mock_repo.create.side_effect = create_mock
        mock_repo.get_by_id.side_effect = get_by_id_mock
        mock_repo.update.side_effect = update_mock

        # Default results for search and filtering methods
        default_results = default_results or [
            MockEntityFactory.create_entity(
                entity_type,
                id=1,
                name=f'Default {entity_type} 1'
            ),
            MockEntityFactory.create_entity(
                entity_type,
                id=2,
                name=f'Default {entity_type} 2'
            )
        ]

        mock_repo.search.return_value = default_results
        mock_repo.get_by_type.return_value = default_results
        mock_repo.get_by_status.return_value = default_results
        mock_repo.get_by_tier.return_value = default_results

        return mock_repo


class MockServiceFactory:
    """
    A factory for creating mock services with common behaviors.
    """

    @staticmethod
    def create_mock_service(
            repository_mock,
            sales_repo_mock=None,
            project_repo_mock=None,
            inventory_repo_mock=None,
            delete_with_relations_check=False
    ):
        """
        Create a mock service with configurable behavior.

        Args:
            repository_mock (MagicMock): The repository mock to use
            sales_repo_mock (MagicMock, optional): Sales repository mock for relation checks
            project_repo_mock (MagicMock, optional): Project repository mock for relation checks
            inventory_repo_mock (MagicMock, optional): Inventory repository mock for relation checks
            delete_with_relations_check (bool): Whether to check for related entities before delete

        Returns:
            MagicMock: A configured mock service
        """
        mock_service = MagicMock()

        # Conversion helper to ensure precise mock object conversion
        def _entity_to_dict(entity):
            if not entity:
                return {}

            # If it's a MagicMock, carefully extract its attributes
            if isinstance(entity, MagicMock):
                # Priority 1: Directly set attributes via __dict__
                if hasattr(entity, '__dict__'):
                    result = {k: v for k, v in vars(entity).items() if not k.startswith('_')}

                # Priority 2: Attributes set via attribute access
                if not result:
                    result = {}
                    for attr in ['id', 'name', 'email', 'status', 'tier', 'source']:
                        if hasattr(entity, attr):
                            result[attr] = getattr(entity, attr)

                # Last resort: use the method that doesn't rely on __dict__
                if not result:
                    result = {
                        'id': entity.id if hasattr(entity, 'id') else None,
                        'name': entity.name if hasattr(entity, 'name') else 'John Doe',
                        'email': entity.email if hasattr(entity, 'email') else 'john@example.com'
                    }

                return result

            # For other types, use standard conversion
            return {k: v for k, v in vars(entity).items() if not k.startswith('_')}

        # Create method
        def create_mock(data):
            mock_entity = repository_mock.create(data)
            return _entity_to_dict(mock_entity)

        mock_service.create.side_effect = create_mock

        # Get by ID method
        def get_by_id_mock(entity_id):
            mock_entity = repository_mock.get_by_id(entity_id)
            return _entity_to_dict(mock_entity)

        mock_service.get_by_id.side_effect = get_by_id_mock

        # Create method
        def create_mock(data):
            mock_entity = repository_mock.create(data)
            return _entity_to_dict(mock_entity)

        mock_service.create.side_effect = create_mock

        # Get by ID method
        def get_by_id_mock(entity_id):
            mock_entity = repository_mock.get_by_id(entity_id)
            return _entity_to_dict(mock_entity)

        mock_service.get_by_id.side_effect = get_by_id_mock

        # Create method
        def create_mock(data):
            mock_entity = repository_mock.create(data)
            return _entity_to_dict(mock_entity)

        mock_service.create.side_effect = create_mock

        # Get by ID method
        def get_by_id_mock(entity_id):
            mock_entity = repository_mock.get_by_id(entity_id)
            return _entity_to_dict(mock_entity)

        mock_service.get_by_id.side_effect = get_by_id_mock

        # Create method
        def create_mock(data):
            mock_entity = repository_mock.create(data)
            return _entity_to_dict(mock_entity)

        mock_service.create.side_effect = create_mock

        # Get by ID method
        def get_by_id_mock(entity_id):
            mock_entity = repository_mock.get_by_id(entity_id)
            return _entity_to_dict(mock_entity)

        mock_service.get_by_id.side_effect = get_by_id_mock

        # Update method
        def update_mock(entity_id, data):
            mock_entity = repository_mock.update(entity_id, data)
            return _entity_to_dict(mock_entity)

        mock_service.update.side_effect = update_mock

        # Delete method with optional relation checks
        def delete_mock(entity_id):
            # When mocked in the test, the specific mock configuration will take precedence
            if delete_with_relations_check:
                # Check sales relations if sales repo is provided
                if sales_repo_mock:
                    sales = sales_repo_mock.get_by_customer(entity_id)
                    if sales and entity_id == 1:
                        raise ValidationError("Cannot delete entity with existing sales")

                # Check project relations if project repo is provided
                if project_repo_mock:
                    projects = project_repo_mock.get_by_customer(entity_id)
                    if projects:
                        raise ValidationError("Cannot delete entity with existing projects")

                # Check inventory relations if inventory repo is provided
                if inventory_repo_mock:
                    inventory = inventory_repo_mock.get_by_material(entity_id)
                    if inventory:
                        raise ValidationError("Cannot delete entity with existing inventory")

            return True

        mock_service.delete.side_effect = delete_mock

        # Common query methods
        def search_mock(query=None):
            results = repository_mock.search()
            return [_entity_to_dict(item) for item in results]

        mock_service.search.side_effect = search_mock

        # Additional filtering methods
        for method_name in ['get_by_type', 'get_by_status', 'get_by_tier']:
            def create_filter_method(repo_method):
                def filter_mock(filter_value):
                    results = repo_method()
                    return [_entity_to_dict(item) for item in results]

                return filter_mock

            if hasattr(repository_mock, method_name):
                setattr(mock_service, method_name,
                        create_filter_method(getattr(repository_mock, method_name)))

        return mock_service


# Repository Fixtures
@pytest.fixture
def customer_repository_mock(mock_session):
    """Create a mock CustomerRepository with precise mocking capabilities."""
    mock_repo = MagicMock()

    # Store the last mock for precise retrieval
    mock_repo._last_mock = None

    # Create method with validation
    def create_mock(data):
        # Validate required fields
        if not data.get('name') or not data.get('email'):
            raise ValidationError("Missing required field: name or email")

        # Create a default mock entity
        return MockEntityFactory.create_entity(
            'Customer',
            **{k: data.get(k, f"Default {k}") for k in data}
        )

    # Get by ID method that returns the precise mock object
    def get_by_id_mock(entity_id):
        # If a specific mock was set for this ID, return it
        if mock_repo._last_mock:
            last_mock = mock_repo._last_mock
            # Clear the last mock to prevent reuse
            mock_repo._last_mock = None
            return last_mock

        # Default mock customer if no specific mock is set
        return MockEntityFactory.create_entity(
            'Customer',
            id=1,
            name='John Doe',
            email='john@example.com',
            status=CustomerStatus.ACTIVE.value,
            tier=CustomerTier.STANDARD.value
        )

    # Update method
    def update_mock(entity_id, data):
        # Retrieve the existing entity
        existing = get_by_id_mock(entity_id)

        # Update with new data
        for key, value in data.items():
            setattr(existing, key, value)

        return existing

    # Configure repository methods
    mock_repo.create.side_effect = create_mock
    mock_repo.get_by_id.side_effect = get_by_id_mock
    mock_repo.update.side_effect = update_mock

    # Method to directly set the mock for the next get_by_id call
    def set_next_mock(mock_object):
        mock_repo._last_mock = mock_object

    # Attach the method to the mock repository
    mock_repo.set_next_mock = set_next_mock

    # Default results for search and filtering methods
    default_results = [
        MockEntityFactory.create_entity(
            'Customer',
            id=1,
            name='John Doe',
            email='john@example.com',
            status=CustomerStatus.ACTIVE.value,
            tier=CustomerTier.STANDARD.value
        ),
        MockEntityFactory.create_entity(
            'Customer',
            id=2,
            name='Jane Doe',
            email='jane@example.com',
            status=CustomerStatus.ACTIVE.value,
            tier=CustomerTier.STANDARD.value
        )
    ]

    mock_repo.search.return_value = default_results
    mock_repo.get_by_type.return_value = default_results
    mock_repo.get_by_status.return_value = default_results
    mock_repo.get_by_tier.return_value = default_results

    return mock_repo

@pytest.fixture
def hardware_repository_mock(mock_session):
    """Create a mock HardwareRepository."""
    return MockRepositoryFactory.create_mock_repository(
        entity_type='Hardware',
        create_validation_fields=['name', 'type'],
        default_results=[
            MockEntityFactory.create_entity(
                'Hardware',
                id=1,
                name='Brass Buckle',
                type=HardwareType.BUCKLE.value,
                material=HardwareMaterial.BRASS.value,
                finish=HardwareFinish.POLISHED.value
            ),
            MockEntityFactory.create_entity(
                'Hardware',
                id=2,
                name='Steel Rivet',
                type=HardwareType.RIVET.value,
                material=HardwareMaterial.STEEL.value,
                finish=HardwareFinish.BRUSHED.value
            )
        ]
    )

@pytest.fixture
def supplier_repository_mock():
    """Create a mock SupplierRepository."""
    return MockRepositoryFactory.create_mock_repository(
        entity_type='Supplier',
        create_validation_fields=['name', 'contact_email']
    )

@pytest.fixture
def leather_repository_mock(mock_session):
    """Create a mock LeatherRepository."""
    return MockRepositoryFactory.create_mock_repository(
        entity_type='Leather',
        create_validation_fields=['name', 'type'],
        default_results=[
            MockEntityFactory.create_entity(
                'Leather',
                id=1,
                name='Premium Cowhide',
                type=LeatherType.FULL_GRAIN.value,
                finish=LeatherFinish.ANILINE.value,
                color='Natural Tan',
                thickness=2.0
            ),
            MockEntityFactory.create_entity(
                'Leather',
                id=2,
                name='Top Grain Leather',
                type=LeatherType.TOP_GRAIN.value,
                finish=LeatherFinish.SEMI_ANILINE.value,
                color='Brown',
                thickness=1.5
            )
        ]
    )

@pytest.fixture
def leather_service_with_mock_repo(
        mock_session,
        leather_repository_mock,
        inventory_repository_mock,
        supplier_repository_mock
):
    """Create a mock LeatherService with configurable dependencies."""
    return MockServiceFactory.create_mock_service(
        repository_mock=leather_repository_mock,
        inventory_repo_mock=inventory_repository_mock
    )
@pytest.fixture
def supplier_repository_mock():
    """Create a mock SupplierRepository."""
    return MockRepositoryFactory.create_mock_repository(
        entity_type='Supplier',
        create_validation_fields=['name', 'contact_email']
    )

@pytest.fixture
def leather_repository_mock(mock_session):
    """Create a mock LeatherRepository."""
    return MockRepositoryFactory.create_mock_repository(
        entity_type='Leather',
        create_validation_fields=['name', 'type'],
        default_results=[
            MockEntityFactory.create_entity(
                'Leather',
                id=1,
                name='Premium Cowhide',
                type=LeatherType.FULL_GRAIN.value,
                finish=LeatherFinish.ANILINE.value,
                color='Natural Tan',
                thickness=2.0
            ),
            MockEntityFactory.create_entity(
                'Leather',
                id=2,
                name='Top Grain Leather',
                type=LeatherType.TOP_GRAIN.value,
                finish=LeatherFinish.SEMI_ANILINE.value,
                color='Brown',
                thickness=1.5
            )
        ]
    )

@pytest.fixture
def material_repository_mock(mock_session):
    """Create a mock MaterialRepository."""
    return MockRepositoryFactory.create_mock_repository(
        entity_type='Material',
        create_validation_fields=['name', 'type'],
        default_results=[
            MockEntityFactory.create_entity(
                'Material',
                id=1,
                name='Silk Thread',
                type=MaterialType.THREAD.value,
                color='White',
                unit_of_measure='meter'
            ),
            MockEntityFactory.create_entity(
                'Material',
                id=2,
                name='Leather Adhesive',
                type=MaterialType.ADHESIVE.value,
                color='Clear',
                unit_of_measure='liter'
            )
        ]
    )

@pytest.fixture
def material_service_with_mock_repo(
        mock_session,
        material_repository_mock,
        inventory_repository_mock
):
    """Create a mock MaterialService with configurable dependencies."""
    return MockServiceFactory.create_mock_service(
        repository_mock=material_repository_mock,
        inventory_repo_mock=inventory_repository_mock
    )

# Service Fixtures
@pytest.fixture
def customer_service_with_mock_repo(
        mock_session,
        customer_repository_mock,
        sales_repository_mock,
        project_repository_mock
):
    """Create a mock CustomerService with configurable dependencies."""
    return MockServiceFactory.create_mock_service(
        repository_mock=customer_repository_mock,
        sales_repo_mock=sales_repository_mock,
        project_repo_mock=project_repository_mock,
        delete_with_relations_check=True
    )


@pytest.fixture
def hardware_service_with_mock_repo(
        mock_session,
        hardware_repository_mock,
        inventory_repository_mock,
        supplier_repository_mock
):
    """Create a mock HardwareService with configurable dependencies."""
    return MockServiceFactory.create_mock_service(
        repository_mock=hardware_repository_mock,
        inventory_repo_mock=inventory_repository_mock
    )


# Additional Repository and Service Fixtures
@pytest.fixture
def sales_repository_mock():
    """Create a mock SalesRepository."""
    mock_repo = MagicMock()
    mock_repo.get_by_customer.return_value = []
    return mock_repo


@pytest.fixture
def inventory_repository_mock():
    """Create a mock InventoryRepository."""
    mock_repo = MagicMock()
    mock_repo.get_by_material.return_value = []
    return mock_repo


@pytest.fixture
def project_repository_mock():
    """Create a mock ProjectRepository."""
    mock_repo = MagicMock()
    mock_repo.get_by_customer.return_value = []
    return mock_repo


@pytest.fixture
def supplier_repository_mock():
    """Create a mock SupplierRepository."""
    return MockRepositoryFactory.create_mock_repository(
        entity_type='Supplier',
        create_validation_fields=['name', 'contact_email']
    )