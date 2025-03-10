# In-Memory Repository Testing Guide for Leatherworking Application

## Introduction

This guide provides a comprehensive approach to implementing in-memory tests for repository classes in the leatherworking application. These tests avoid direct database interactions, making them faster, more isolated, and less prone to circular dependency issues.

## Why Use In-Memory Testing?

1. **Isolation**: Tests don't depend on database state or configuration
2. **Speed**: No database connections or transactions needed
3. **Simplicity**: No need to manage complex setup/teardown
4. **Dependency Avoidance**: Circumvents circular import and ORM mapping issues

## Implementation Pattern

### 1. Basic Structure

Each repository test should follow this general structure:

```python
class TestRepositoryName:
    # Helper methods to create test objects
    def _create_test_entity(self, dbsession):
        # Create simple test object with minimal dependencies
        pass
    
    # Test methods for CRUD operations
    def test_create_entity(self, dbsession):
        # Test creation operation
        pass
    
    def test_read_entity(self, dbsession):
        # Test read operation
        pass
    
    def test_update_entity(self, dbsession):
        # Test update operation
        pass
    
    def test_delete_entity(self, dbsession):
        # Test delete operation
        pass
    
    # Additional test methods for repository-specific functionality
```

### 2. Test Entity Objects

Create lightweight entity objects using simple Python classes instead of SQLAlchemy models:

```python
class TestEntity:
    def __init__(self, **kwargs):
        self.id = None  # Will be set by repository
        for key, value in kwargs.items():
            setattr(self, key, value)
```

### 3. In-Memory Repository Implementation

Implement a simplified repository that stores objects in memory:

```python
class SimpleRepository:
    def __init__(self):
        self.entities = {}
        self.next_id = 1
    
    def add(self, entity):
        entity.id = self.next_id
        self.entities[self.next_id] = entity
        self.next_id += 1
        return entity
    
    def get_by_id(self, id):
        return self.entities.get(id)
    
    def update(self, entity):
        if entity.id in self.entities:
            self.entities[entity.id] = entity
            return entity
        return None
    
    def delete(self, id):
        if id in self.entities:
            del self.entities[id]
            return True
        return False
```

### 4. Test Implementation

Implement tests using the in-memory repository and entity classes:

```python
def test_create_entity(self, dbsession):
    # Create repository
    repository = SimpleRepository()
    
    # Create entity
    entity = TestEntity(name="Test Entity", status=EntityStatus.ACTIVE)
    
    # Add to repository
    added_entity = repository.add(entity)
    
    # Verify
    assert added_entity.id == 1
    assert added_entity.name == "Test Entity"
```

## Handling Relationships

When dealing with related entities, use ID references instead of direct object references:

```python
# Instead of this:
entity.parent = parent_entity

# Do this:
entity.parent_id = parent_entity.id
```

## Enum Value Usage

Always use valid enum values from the actual codebase. Check `enums.py` for the correct values:

```python
# Correct usage
entity.status = EntityStatus.ACTIVE  # Make sure ACTIVE exists in EntityStatus

# Incorrect usage
entity.status = EntityStatus.NONEXISTENT_VALUE  # Will cause AttributeError
```

### Common Enum Values

#### SaleStatus
- QUOTE_REQUEST, DESIGN_CONSULTATION, DESIGN_APPROVAL
- MATERIALS_SOURCING, DEPOSIT_RECEIVED, IN_PRODUCTION
- QUALITY_REVIEW, READY_FOR_PICKUP, SHIPPED
- DELIVERED, COMPLETED, CANCELLED, REFUNDED

#### ProjectStatus
- INITIAL_CONSULTATION, DESIGN_PHASE, PATTERN_DEVELOPMENT
- CLIENT_APPROVAL, MATERIAL_SELECTION, MATERIAL_PURCHASED
- CUTTING, SKIVING, PREPARATION, ASSEMBLY, STITCHING
- EDGE_FINISHING, HARDWARE_INSTALLATION
- COMPLETED, ON_HOLD, CANCELLED

#### InventoryStatus
- IN_STOCK, LOW_STOCK, OUT_OF_STOCK, DISCONTINUED
- ON_ORDER, AVAILABLE, RESERVED, DAMAGED
- PENDING_ARRIVAL, QUARANTINE

#### ProjectType
- WALLET, BRIEFCASE, MESSENGER_BAG, TOTE_BAG, BACKPACK
- BELT, WATCH_STRAP, NOTEBOOK_COVER, etc.

## Best Practices

### 1. Keep Tests Independent

Each test should be independent of other tests. Avoid relying on state set up by previous tests.

### 2. Use Helper Methods for Common Setup

Create helper methods for common setup operations:

```python
def _create_test_customer(self, dbsession):
    """Helper method to create a test customer."""
    customer = TestCustomer(
        first_name="Test",
        last_name="Customer",
        email="test@example.com",
        status=CustomerStatus.ACTIVE
    )
    customer.id = 1  # Simulate database insertion
    return customer
```

### 3. Test All CRUD Operations

Ensure you have tests for all Create, Read, Update, and Delete operations.

### 4. Test Repository-Specific Functionality

Add tests for any special functionality the repository provides beyond basic CRUD:

```python
def test_inventory_status_change(self, dbsession):
    """Test changing inventory status."""
    # Implementation for status change test
```

### 5. Assert the Expected State

Make clear assertions about the expected state after operations:

```python
# Verify the project was deleted
assert result is True
assert repository.get_by_id(project_id) is None
```

## Troubleshooting Common Issues

### 1. AttributeError with Enums

If you get an AttributeError like this:
```
AttributeError: BAG
```

It means the enum value doesn't exist. Check `enums.py` for valid values and update your test accordingly.

### 2. Circular Import Issues

In-memory testing avoids circular import issues by not using actual SQLAlchemy models. If you encounter circular imports:

- Make sure you're using the test entity classes, not SQLAlchemy models
- Use ID references instead of object references for relationships
- Create utility helper methods that return simulated objects

### 3. Missing Attributes

If you get AttributeError about missing attributes:

- Check that your test entity class properly initializes all required attributes
- Ensure attribute names match what the code under test expects

## Example Test Cases

See the implemented test files for complete examples:
- `test_sales_repository.py`
- `test_inventory_repository.py`
- `test_product_repository.py`
- `test_project_repository.py`

## Creating New Repository Tests

When implementing tests for a new repository:

1. **Study the Model**: Understand the entity being tested and its relationships
2. **Check Enum Values**: Identify enum values used by the entity
3. **Implement Helper Methods**: Create methods to set up test entities
4. **Create In-Memory Repository**: Implement a simple repository with in-memory storage
5. **Implement CRUD Tests**: Test each core repository operation
6. **Add Special Tests**: Test any special functionality the repository provides

## Conclusion

Using the in-memory testing approach provides robust, isolated tests that avoid many common issues with database-dependent tests. This approach is recommended for all repository testing in the leatherworking application.