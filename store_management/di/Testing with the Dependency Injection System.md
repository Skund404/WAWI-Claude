# Dependency Injection Testing Guide

This guide demonstrates how to effectively use the new DI system in your tests to isolate components and verify behavior with mocked dependencies.

## Overview

The DI system makes testing significantly easier by allowing you to:

1. Replace real dependencies with test doubles (mocks, stubs, fakes)
2. Isolate the component under test
3. Verify interactions between components
4. Control the test environment

## Mock Implementation Framework

The DI system includes a built-in mock implementation framework for testing:

### Directory Structure

```
di/
  tests/
    mock_implementations/
      __init__.py            # Exports all mocks and provides MOCK_SERVICES map
      base_service.py        # Generic mock implementation
      pattern_service.py     # IPatternService mock
      tool_list_service.py   # IToolListService mock
      material_service.py    # IMaterialService mock
      inventory_service.py   # IInventoryService mock
```

### Features of the Mock Framework

1. **Consistent Interface**: Mocks implement the same interfaces as real services
2. **Clearly Identified**: All mock data includes `[MOCK]` prefixes
3. **Testing Indicators**: Mock operations set flags like `mock_generated: true`
4. **Base Implementation**: Common methods come from the base service
5. **Easy Registration**: Mocks are automatically registered when needed

## Basic Test Approaches

### 1. Using Direct Resolution with Built-in Mocks

The simplest approach is to use the built-in mocks via direct resolution:

```python
from di import initialize, resolve

def test_with_built_in_mocks():
    # Initialize the container (will use mocks if no real implementations exist)
    initialize()
    
    # Get a mock service
    pattern_service = resolve('IPatternService')
    
    # Use the mock
    patterns = pattern_service.get_all_patterns()
    assert len(patterns) > 0
    assert "[MOCK]" in patterns[0]['name']
```

### 2. Using Constructor Injection

Test a class that uses constructor injection:

```python
from di import initialize, inject

@inject
class PatternProcessor:
    def __init__(self, pattern_service=None):
        self.pattern_service = pattern_service
        
    def get_beginner_patterns(self):
        all_patterns = self.pattern_service.get_all_patterns()
        return [p for p in all_patterns if p['skill_level'] == 'BEGINNER']

def test_pattern_processor():
    # Initialize the container
    initialize()
    
    # Create instance (will receive injected mock)
    processor = PatternProcessor()
    
    # Test the functionality
    beginner_patterns = processor.get_beginner_patterns()
    assert len(beginner_patterns) > 0
    assert beginner_patterns[0]['skill_level'] == 'BEGINNER'
```

### 3. Using a Custom Test Container

For more control, create a custom test container:

```python
from di import Container, set_container

def test_with_custom_test_container():
    # Create a test container
    container = Container()
    
    # Create custom mocks
    pattern_service_mock = MockPatternService()
    pattern_service_mock.get_all_patterns = lambda: [
        {"id": 1, "name": "Custom Test Pattern", "skill_level": "ADVANCED"}
    ]
    
    # Register the custom mock
    container.register_instance('IPatternService', pattern_service_mock)
    
    # Set as global container
    set_container(container)
    
    # Test with the custom mock
    from my_module import process_patterns
    result = process_patterns()
    assert "Custom Test Pattern" in result
```

## Advanced Testing Techniques

### Testing With Scope Containers

If your components use scoped lifetimes:

```python
def test_scoped_services():
    # Initialize main container
    container = initialize()
    
    # Create scope 1
    scope1 = container.create_scope()
    service1a = scope1.resolve('IToolListService')
    service1b = scope1.resolve('IToolListService')
    
    # Create scope 2
    scope2 = container.create_scope()
    service2 = scope2.resolve('IToolListService')
    
    # Same instance within scope
    assert service1a is service1b
    
    # Different instance between scopes
    assert service1a is not service2
```

### Testing Components with Circular Dependencies

When testing components with circular dependencies:

```python
def test_circular_dependencies():
    # Create a test container
    container = Container()
    
    # Create mock services
    order_service_mock = MagicMock()
    customer_service_mock = MagicMock()
    
    # Register mocks
    container.register_instance('IOrderService', order_service_mock)
    container.register_instance('ICustomerService', customer_service_mock)
    
    # Set as global container
    set_container(container)
    
    # Test functionality that uses these services
    # ...
```

### Testing with Partial Mocking

Sometimes you want to use some real dependencies and some mocks:

```python
def test_with_partial_mocking():
    # Create a test container
    container = Container()
    
    # Import real repository
    from database.repositories.material_repository import MaterialRepository
    
    # Create a mock session
    mock_session = MagicMock()
    
    # Create a real repository with mock session
    real_repo = MaterialRepository(mock_session)
    
    # Register the real repository
    container.register_instance('MaterialRepository', real_repo)
    
    # Register mock services
    container.register_instance('IInventoryService', MockInventoryService())
    
    # Set as global container
    set_container(container)
    
    # Test with real repository but mock service
    # ...
```

## Common Testing Patterns

### 1. Mocking Repository Results

```python
def test_service_with_mocked_repository():
    # Create test container
    container = Container()
    
    # Create mock repository
    repo_mock = MagicMock()
    repo_mock.get_by_id.return_value = {"id": 1, "name": "Test Item"}
    repo_mock.get_all.return_value = [{"id": 1, "name": "Test Item"}]
    
    # Register mock repository
    container.register_instance('MaterialRepository', repo_mock)
    
    # Register real service implementation to test
    from services.implementations.material_service import MaterialService
    container.register_instance('IMaterialService', MaterialService())
    
    # Set as global container
    set_container(container)
    
    # Test the service with mocked repository
    service = resolve('IMaterialService')
    result = service.get_material(1)
    assert result['name'] == "Test Item"
    repo_mock.get_by_id.assert_called_once_with(1)
```

### 2. Verifying Service Interactions

```python
def test_service_interactions():
    # Create test container
    container = Container()
    
    # Create mocks with transaction tracking
    material_service_mock = MagicMock()
    inventory_service_mock = MagicMock()
    
    # Register mocks
    container.register_instance('IMaterialService', material_service_mock)
    container.register_instance('IInventoryService', inventory_service_mock)
    
    # Set as global container
    set_container(container)
    
    # Import the service to test
    from services.implementations.project_service import ProjectService
    project_service = ProjectService()
    
    # Perform the test action
    project_service.allocate_materials_to_project(1, [{"material_id": 5, "quantity": 10}])
    
    # Verify interactions
    material_service_mock.get_material.assert_called_once_with(5)
    inventory_service_mock.update_inventory_quantity.assert_called_once_with(5, -10)
```

### 3. Testing Error Handling

```python
def test_error_handling():
    # Create test container
    container = Container()
    
    # Create mock that raises an exception
    repo_mock = MagicMock()
    repo_mock.get_by_id.side_effect = ValueError("Test error")
    
    # Register the mock
    container.register_instance('MaterialRepository', repo_mock)
    
    # Register service to test
    from services.implementations.material_service import MaterialService
    container.register_instance('IMaterialService', MaterialService())
    
    # Set as global container
    set_container(container)
    
    # Test error handling
    service = resolve('IMaterialService')
    
    # Should properly handle the repository error
    with pytest.raises(ValueError):
        service.get_material(1)
```

## Creating Mock Services

### 1. Using the Built-in Mock Services

```python
from di.tests.mock_implementations import MockPatternService, MockInventoryService

def test_with_built_in_mocks():
    # Create instances of the built-in mocks
    pattern_service = MockPatternService()
    inventory_service = MockInventoryService()
    
    # Use them in your test
    patterns = pattern_service.get_all_patterns()
    assert len(patterns) > 0
```

### 2. Extending Built-in Mocks

```python
from di.tests.mock_implementations import MockMaterialService

class CustomMockMaterialService(MockMaterialService):
    """Custom mock with specialized behavior."""
    
    def get_material(self, material_id):
        if material_id == 999:
            return {"id": 999, "name": "Special Test Material", "test_specific": True}
        return super().get_material(material_id)

def test_with_extended_mock():
    # Create a test container
    container = Container()
    
    # Register custom mock
    container.register_instance('IMaterialService', CustomMockMaterialService())
    
    # Set as global container
    set_container(container)
    
    # Test with the custom mock
    service = resolve('IMaterialService')
    result = service.get_material(999)
    assert result['test_specific'] is True
```

### 3. Creating Mock Factories

```python
def create_tool_list_service_mock(tools_to_include=None):
    """Factory function to create a specialized tool list service mock."""
    mock = MockToolListService()
    
    # Override get_tool_list_items
    def get_custom_items(tool_list_id):
        return [{"id": i, "tool_id": tid, "quantity": 1, "mock": True} 
                for i, tid in enumerate(tools_to_include or [1, 2])]
    
    mock.get_tool_list_items = get_custom_items
    return mock

def test_with_mock_factory():
    # Create a test container
    container = Container()
    
    # Register custom mock from factory
    container.register_instance('IToolListService', 
                               create_tool_list_service_mock([5, 6, 7]))
    
    # Set as global container
    set_container(container)
    
    # Test with specialized mock
    service = resolve('IToolListService')
    items = service.get_tool_list_items(1)
    assert len(items) == 3
    assert items[0]['tool_id'] == 5
```

## Best Practices

1. **Reset Between Tests**: Always clear the container between tests to avoid state leakage
2. **Register Mocks Explicitly**: Register each mock explicitly for clarity
3. **Test in Isolation**: Test each component in isolation with all dependencies mocked
4. **Verify Interactions**: Verify that the component interacts correctly with its dependencies
5. **Use Real Dependencies When Needed**: For integration tests, use some real dependencies
6. **Test Both Success and Failure Paths**: Test how your components handle failures in dependencies
7. **Set Up Common Test Fixtures**: Create reusable fixtures for common test scenarios

## Example: Complete Test Module

```python
import pytest
from unittest.mock import MagicMock
from di import Container, set_container, clear_container, resolve

# Fixtures
@pytest.fixture
def mock_dependencies():
    """Fixture that provides mock dependencies."""
    return {
        'MaterialRepository': MagicMock(),
        'InventoryService': MagicMock(),
        'SupplierRepository': MagicMock()
    }

@pytest.fixture
def test_container(mock_dependencies):
    """Fixture that sets up a test container with mock dependencies."""
    # Create container
    container = Container()
    
    # Register mocks
    for name, mock in mock_dependencies.items():
        container.register_instance(name, mock)
    
    # Set as global container
    set_container(container)
    
    # Return for test use
    yield container
    
    # Clean up after test
    clear_container()

# Tests
def test_material_service(test_container, mock_dependencies):
    """Test MaterialService with mocked dependencies."""
    # Setup test data
    repo_mock = mock_dependencies['MaterialRepository']
    repo_mock.get_by_id.return_value = {"id": 1, "name": "Test Leather"}
    
    # Create service to test
    from services.implementations.material_service import MaterialService
    service = MaterialService()
    
    # Test the service
    result = service.get_material(1)
    
    # Verify results
    assert result['name'] == "Test Leather"
    repo_mock.get_by_id.assert_called_once_with(1)
```

## Conclusion

The DI system makes testing much easier by allowing you to isolate components and mock dependencies. Use the built-in mock framework for quick tests, and create custom mocks for more specific scenarios.

For further testing support:
- Use the built-in mocks as a starting point
- Extend the mock framework with additional mock implementations
- Create reusable test fixtures for DI container setup