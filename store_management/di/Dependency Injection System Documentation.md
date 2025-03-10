# Dependency Injection System Documentation

## Overview

The Dependency Injection (DI) system provides a centralized mechanism for managing dependencies between components in the Leatherworking Application. It allows for loose coupling between services and their dependencies, making the application more maintainable, testable, and easier to extend.

## Key Components

The DI system consists of four main modules:

1. **Container** (`di/container.py`): Core DI container that manages service registrations and resolutions
2. **Inject** (`di/inject.py`): Provides decorators for injecting dependencies into classes and functions
3. **Config** (`di/config.py`): Centralized configuration for service mappings
4. **Setup** (`di/setup.py`): Initializes the DI container with all required services

Additionally, the system includes a structured mock implementation framework:

5. **Mock Implementations** (`di/tests/mock_implementations/`): Test implementations of service interfaces

## API Reference

### Container

The `Container` class manages service registrations and resolves dependencies:

```python
from di import Container, Lifetime

container = Container()

# Register a service
container.register("IService", "path.to.implementation.ServiceImpl")

# Register with specific lifetime
container.register("ITransientService", TransientService, Lifetime.TRANSIENT)

# Register an instance
container.register_instance("Logger", logger_instance)

# Register a factory
container.register_factory("DatabaseSession", lambda c: create_db_session())

# Resolve a service
service = container.resolve("IService")

# Check if registered
if container.is_registered("IService"):
    # Do something

# Create a scope
scoped_container = container.create_scope()

# Reset the container
container.reset()  # Only clears non-singleton instances
container.reset(include_singletons=True)  # Clears all instances
```

### Lifetime Options

Services can be registered with different lifetimes:

- **SINGLETON** (default): Single instance shared across all resolutions
- **TRANSIENT**: New instance created for each resolution
- **SCOPED**: Single instance per scope (useful for request-scoped services)

### Inject Decorator

The `@inject` decorator simplifies dependency injection in constructors:

```python
from di import inject

# Class injection
@inject
class CustomerService:
    def __init__(self, repository=None):
        self.repository = repository
```

### Resolution Functions

The `resolve()` function allows direct resolution without the decorator:

```python
from di import resolve

def calculate_inventory():
    inventory_service = resolve('IInventoryService')
    return inventory_service.calculate_totals()
```

### Initialization

The `initialize()` function sets up the DI container:

```python
from di import initialize

def main():
    container = initialize()
    # Application startup...
```

### Verification

The `verify_container()` function checks that critical services are resolvable:

```python
from di import verify_container

is_valid = verify_container()
if not is_valid:
    # Handle initialization issues
```

## Configuration

### Service Mappings

Services are configured in `di/config.py`:

```python
# Real implementations
'IPatternService': 'services.implementations.pattern_service.PatternService',

# Mock implementations (use None to indicate mock should be used)
'IInventoryService': None,  # Using mock implementation
```

### Repository Mappings

Repositories are also configured in `di/config.py`:

```python
REPOSITORY_MAPPINGS = [
    'database.repositories.customer_repository.CustomerRepository',
    'database.repositories.material_repository.MaterialRepository',
    # ...
]
```

### Database Session Configuration

Database session factory is configured in `di/config.py`:

```python
DATABASE_SESSION_CONFIG = {
    'module': 'database.sqlalchemy.session',
    'factory_function': 'get_db_session'  # Set to None to use a mock
}
```

## Usage Patterns

### Constructor Injection

The preferred pattern for using the DI system is constructor injection:

```python
@inject
class MaterialService:
    def __init__(self, material_repository=None, inventory_service=None):
        self.material_repository = material_repository
        self.inventory_service = inventory_service
```

### Direct Resolution

For cases where constructor injection is not possible:

```python
def process_order(order_id):
    order_service = resolve('IOrderService')
    return order_service.process(order_id)
```

### Service Factory

Creating services with additional parameters:

```python
@inject
class OrderProcessor:
    def __init__(self, order_service=None):
        self.order_service = order_service
        
    def create_processor_for_customer(self, customer_id):
        # Use the injected order_service 
        return OrderProcessorForCustomer(
            customer_id, 
            self.order_service
        )
```

## Mock Implementation Framework

The DI system includes a structured mock implementation framework for testing and development:

### Directory Structure

```
di/
  tests/
    mock_implementations/
      __init__.py            # Exports and MOCK_SERVICES mapping
      base_service.py        # Base implementation for all services
      pattern_service.py     # IPatternService implementation
      tool_list_service.py   # IToolListService implementation
      material_service.py    # IMaterialService implementation
      inventory_service.py   # IInventoryService implementation
```

### Using Mocks

Mocks are automatically registered when no real implementation is available:

1. To use a mock, set the implementation to `None` in `config.py`:
   ```python
   'IPatternService': None,  # Will use mock implementation
   ```

2. Mock implementations clearly identify themselves with `[MOCK]` prefixes in their data:
   ```python
   # Example mock pattern
   {"id": 1, "name": "[MOCK] Test Pattern 1", "skill_level": "BEGINNER"}
   ```

### Transitioning from Mocks to Real Implementations

When you create a real implementation:

1. Update `config.py` with the implementation path:
   ```python
   # Replace:
   'IPatternService': None,  # Using mock implementation
   
   # With:
   'IPatternService': 'services.implementations.pattern_service.PatternService',
   ```

2. The DI system will automatically use the real implementation instead of the mock

## Best Practices

1. **Use Interfaces**: Register services by their interface names to allow for easy substitution
2. **Favor Constructor Injection**: Pass dependencies through constructors rather than methods
3. **Use String Names**: When possible, use string identifiers (e.g., `'ICustomerService'`) for resolution
4. **Avoid Service Locator**: Don't use `resolve()` extensively within application code; prefer injection
5. **Keep Services Stateless**: Design services to be stateless when possible
6. **Use Appropriate Lifetimes**: Most services should be singletons, but use transient for stateful services

## Troubleshooting

### Resolution Failures

If a service fails to resolve:

1. Check that the service is registered in `di/config.py`
2. Verify the implementation class exists at the specified path
3. Examine the `di_setup.log` file for detailed error information
4. Check for circular dependencies that might not be properly handled

### Injection Issues

If dependencies aren't being injected:

1. Make sure you're using the `@inject` decorator
2. Check that parameter names match registration names
3. Ensure the dependencies are registered in the container
4. Try direct resolution to see if the dependency resolves manually

## Initialization Process

The DI system initialization process follows these steps:

1. Create the container
2. Register database session factory
3. Register repositories
4. Register real service implementations from configuration
5. Register mock implementations for any services without real implementations
6. Verify critical services can be resolved

## Example: Full Service with DI

```python
# services/implementations/material_service.py
from typing import List, Optional
from di import inject

@inject
class MaterialService:
    def __init__(
        self,
        material_repository=None,  # Will be injected
        inventory_service=None     # Will be injected
    ):
        self.material_repository = material_repository
        self.inventory_service = inventory_service
    
    def get_material(self, material_id: int):
        return self.material_repository.get_by_id(material_id)
    
    def update_inventory(self, material_id: int, quantity: float):
        material = self.material_repository.get_by_id(material_id)
        if not material:
            raise ValueError(f"Material with ID {material_id} not found")
        
        self.inventory_service.update_material_quantity(material_id, quantity)
        return True
```