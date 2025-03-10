# Leatherworking Application Service Layer Testing Guide

## Overview

This guide provides comprehensive instructions for writing and maintaining service layer tests in the Leatherworking Application. Service layer tests are crucial for ensuring the reliability, functionality, and business logic of our application's core services.

## Testing Philosophy

Our service layer tests follow these key principles:
- **Isolation**: Tests should isolate the service from external dependencies
- **Comprehensive Coverage**: Test all possible scenarios, including success and failure cases
- **Realistic Mocking**: Use realistic mock objects that closely simulate real-world data
- **Business Logic Validation**: Ensure that each service method implements correct business rules

## Prerequisites

Before writing service tests, ensure you have:
- Pytest installed
- Understanding of the service interface
- Access to the service implementation
- Knowledge of the specific business rules for the service

## Test Structure

### Basic Test Class Structure

```python
class TestServiceName:
    def test_method_success(self, service_with_mock_repo):
        """Test successful scenario for a specific method."""
        # Arrange
        # Act
        # Assert

    def test_method_validation_error(self, service_with_mock_repo):
        """Test validation error scenarios."""
        # Arrange
        # Act
        # Assert

    def test_method_not_found_error(self, service_with_mock_repo):
        """Test scenarios where an entity is not found."""
        # Arrange
        # Act
        # Assert
```

## Mocking Strategies

### Repository Mocking

Use `SimpleNamespace` or `MagicMock` to create mock repository responses:

```python
from types import SimpleNamespace
from unittest.mock import MagicMock

# Using SimpleNamespace (Recommended)
mock_customer = SimpleNamespace(
    id=1,
    name='John Doe',
    email='john@example.com',
    status=CustomerStatus.ACTIVE.value
)

# Using MagicMock
mock_customer = MagicMock()
mock_customer.id = 1
mock_customer.name = 'John Doe'
```

### Dependency Injection Fixtures

Create fixtures that provide mocked services:

```python
@pytest.fixture
def customer_service_with_mock_repo(
    customer_repository_mock, 
    sales_repository_mock, 
    project_repository_mock
):
    """
    Creates a CustomerService with mocked repositories.
    
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
```

## Test Coverage Recommendations

### CRUD Operations
1. **Create Method**
   - Successful creation
   - Validation errors
   - Duplicate entry handling

2. **Read Methods**
   - Retrieve by ID (successful)
   - Retrieve non-existent ID
   - List/search methods
   - Filtering and pagination

3. **Update Method**
   - Successful update
   - Partial update
   - Validation errors
   - Update non-existent entity

4. **Delete Method**
   - Successful deletion
   - Delete with dependent entities
   - Delete non-existent entity

### Business Logic Testing

1. **Validation Tests**
   - Required fields
   - Field format (e.g., email validation)
   - Enum value validation

2. **Business Rule Tests**
   - Complex logic scenarios
   - Interdependent entity checks
   - State transitions

## Common Test Patterns

### Validation Error Testing

```python
def test_create_with_invalid_data(self, service_with_mock_repo):
    """Test creation with invalid data raises ValidationError."""
    invalid_data = {
        # Incomplete or invalid data
    }
    
    with pytest.raises(ValidationError) as excinfo:
        service_with_mock_repo.create(invalid_data)
    
    # Optionally, check specific error message
    assert 'Specific validation error message' in str(excinfo.value)
```

### Not Found Error Testing

```python
def test_get_non_existent_entity(self, service_with_mock_repo, repository_mock):
    """Test retrieving a non-existent entity raises NotFoundError."""
    # Configure repository to return None
    repository_mock.get_by_id.return_value = None
    
    with pytest.raises(NotFoundError):
        service_with_mock_repo.get_by_id(999999)
```

## Best Practices

1. **Use Meaningful Test Names**
   - Describe the scenario being tested
   - Include the expected behavior

2. **Keep Tests Focused**
   - One assertion per test when possible
   - Test a single scenario per test method

3. **Use Realistic Mock Data**
   - Populate all necessary fields
   - Simulate real-world scenarios

4. **Handle Edge Cases**
   - Test boundary conditions
   - Consider unusual input scenarios

5. **Avoid Hardcoded Test Data**
   - Use fixtures or factories for test data
   - Make tests reproducible and maintainable

## Common Pitfalls to Avoid

1. **Over-mocking**: Don't mock too much; keep tests realistic
2. **Incomplete Coverage**: Test all possible paths
3. **Fragile Tests**: Avoid tests that are too tightly coupled to implementation
4. **Ignoring Business Rules**: Ensure tests validate core business logic

## Example Complete Test File

```python
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from services.exceptions import ValidationError, NotFoundError
from database.models.enums import CustomerStatus, CustomerTier

class TestCustomerService:
    def test_create_customer_success(self, customer_service_with_mock_repo):
        """Test successful customer creation with valid data."""
        customer_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'status': CustomerStatus.ACTIVE.value,
            'tier': CustomerTier.STANDARD.value
        }
        
        created_customer = customer_service_with_mock_repo.create(customer_data)
        
        assert created_customer['name'] == 'John Doe'
        assert created_customer['status'] == CustomerStatus.ACTIVE.value

    def test_create_customer_validation_error(self, customer_service_with_mock_repo):
        """Test customer creation with invalid data raises ValidationError."""
        invalid_customer_data = {
            'email': 'invalid-email'  # Missing required fields
        }
        
        with pytest.raises(ValidationError):
            customer_service_with_mock_repo.create(invalid_customer_data)
```

## Continuous Improvement

- Regularly review and update tests
- Add tests for new features and bug fixes
- Maintain high test coverage
- Use code coverage tools to identify untested code paths

## Conclusion

Effective service layer testing is crucial for maintaining the reliability and correctness of the Leatherworking Application. By following these guidelines, developers can create robust, comprehensive tests that validate the application's core business logic.