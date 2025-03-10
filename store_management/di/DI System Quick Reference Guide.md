# Dependency Injection System Quick Reference

## Core Components

- **Container** (`di/container.py`): Manages service registrations and resolution
- **Inject** (`di/inject.py`): Decorators for injecting dependencies
- **Config** (`di/config.py`): Centralized service configuration
- **Setup** (`di/setup.py`): Initializes the DI system
- **Mock Implementations** (`di/tests/mock_implementations/`): Test service implementations

## Basic Usage

### Application Startup

```python
from di import initialize

def main():
    # Initialize the DI container
    container = initialize()
    
    # Start application...
```

### Constructor Injection

```python
from di import inject

@inject
class MaterialService:
    def __init__(self, material_repository=None, inventory_service=None):
        self.material_repository = material_repository
        self.inventory_service = inventory_service
```

### Direct Resolution

```python
from di import resolve

def process_data():
    # Get a service directly
    material_service = resolve('IMaterialService')
    
    # Use the service
    return material_service.get_material(123)
```

## Configuration

### Adding a New Service

1. Create the interface in `services/interfaces/`
2. Create the implementation in `services/implementations/`
3. Add to `di/config.py`:

```python
# In di/config.py
SERVICE_MAPPINGS = {
    # Existing services...
    
    # Add your new service:
    'INewService': 'services.implementations.new_service.NewService',
}
```

### Using Mock Service

```python
# In di/config.py
SERVICE_MAPPINGS = {
    # Set to None to use mock implementation
    'INewService': None,
}
```

## Testing

### Using Built-in Mocks

```python
from di import initialize, resolve

def test_with_built_in_mocks():
    # Initialize (uses mocks for any None implementations)
    initialize()
    
    # Get mock service
    service = resolve('IPatternService')
    
    # Test with mock
    patterns = service.get_all_patterns()
    assert "[MOCK]" in patterns[0]['name']
```

### Custom Test Container

```python
from di import Container, set_container

def test_with_custom_mocks():
    # Create container
    container = Container()
    
    # Register custom mock
    mock_service = MagicMock()
    mock_service.get_data.return_value = ["test data"]
    container.register_instance('IMyService', mock_service)
    
    # Set as global
    set_container(container)
    
    # Run test...
```

## Container API

```python
# Create container
container = Container()

# Register service
container.register('IService', 'path.to.ServiceImpl')
container.register('IService', ServiceImpl)
container.register('ServiceImpl')  # Self-registration

# Different lifetimes
container.register('IService', ServiceImpl, Lifetime.SINGLETON)
container.register('IService', ServiceImpl, Lifetime.TRANSIENT)
container.register('IService', ServiceImpl, Lifetime.SCOPED)

# Register instance
container.register_instance('IService', service_instance)

# Register factory
container.register_factory('IService', lambda c: create_service())

# Check registration
container.is_registered('IService')

# Resolve service
service = container.resolve('IService')

# Create scope
scoped = container.create_scope()

# Reset container
container.reset()  # Keeps singletons
container.reset(include_singletons=True)  # Clears all
```

## Inject Decorator

```python
# Basic usage
@inject
class Service:
    def __init__(self, dependency=None):
        self.dependency = dependency

# With multiple dependencies
@inject
class ComplexService:
    def __init__(
        self, 
        first_dependency=None,
        second_dependency=None
    ):
        self.first = first_dependency
        self.second = second_dependency
```

## Mock Implementations

```python
# Import built-in mocks
from di.tests.mock_implementations import (
    MockPatternService,
    MockToolListService,
    MockMaterialService,
    MockInventoryService,
    MockBaseService
)

# Create custom mock
class CustomMock(MockBaseService):
    def get_special_data(self):
        return ["Custom mock data"]

# Register custom mock
container.register_instance('ISpecialService', CustomMock())
```

## Common Patterns

### Service Factory

```python
@inject
class ServiceFactory:
    def __init__(self, dependency=None):
        self.dependency = dependency
        
    def create_service(self, config):
        return SpecialService(self.dependency, config)
```

### Scoped Service

```python
# Register with scoped lifetime
container.register('IScopedService', ScopedService, Lifetime.SCOPED)

# Create a scope
request_scope = container.create_scope()

# Resolve from scope
service1 = request_scope.resolve('IScopedService')
service2 = request_scope.resolve('IScopedService')  # Same instance
```

### Verification

```python
from di import verify_container

def startup():
    container = initialize()
    
    # Verify critical services
    if not verify_container():
        logger.error("Container verification failed")
        # Handle failure...
```