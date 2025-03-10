# Repository Layer Design Document for Leatherworking ERP System

## 1. Introduction

This document outlines the architecture, design patterns, and implementation details of the repository layer in the Leatherworking ERP System. The repository layer serves as the data access abstraction layer between the domain model and the underlying database, providing a collection-like interface for accessing and manipulating domain entities.

### 1.1 Purpose

The repository layer is designed to:
- Encapsulate data access logic and SQL queries
- Provide a type-safe, domain-focused API for accessing and manipulating entities
- Support the service layer with rich domain operations
- Enable testability and separation of concerns
- Support GUI requirements through specialized query methods

### 1.2 Scope

This document covers:
- Repository architecture and design patterns
- Base repository implementation and common operations
- Entity-specific repository implementations
- Integration with the dependency injection (DI) system
- Transaction management
- Error handling strategies
- GUI integration patterns

## 2. Architecture Overview

### 2.1 Layered Architecture

The Leatherworking ERP System follows a layered architecture with clear separation of concerns:

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│     GUI       │────▶│   Services    │────▶│ Repositories  │────▶│   Database    │
└───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
```

The repository layer sits between the service layer and the database, providing the service layer with a domain-focused API for data access and manipulation.

### 2.2 Repository Pattern

Each repository is responsible for a specific entity type or aggregate and encapsulates all database operations related to that entity. Repositories provide methods for:
- CRUD operations (Create, Read, Update, Delete)
- Querying by various criteria
- Business-specific operations
- GUI-specific operations

### 2.3 Generic Base Repository

The system uses a generic base repository that implements common CRUD operations, with entity-specific repositories extending this base to add specialized functionality:

```
BaseRepository<T>
    ├── MaterialRepository
    │   └── LeatherRepository
    │   └── HardwareRepository
    │   └── SuppliesRepository
    ├── InventoryRepository
    ├── PatternRepository
    ├── ProductRepository
    ├── CustomerRepository
    └── ...
```

## 3. Core Design Principles

### 3.1 Session Injection

Sessions are injected into repositories rather than created internally, allowing for:
- Shared transactions across multiple repositories
- Centralized session lifecycle management in the service layer
- Better testability and control over database connections

### 3.2 Singleton Pattern

Repositories are registered as singletons in the DI container:
- Stateless except for configuration and injected dependencies
- Reduced memory footprint and instantiation overhead
- Consistent access throughout the application

### 3.3 Repository Independence

Repositories should not depend on other repositories to prevent circular dependencies:
- Each repository focuses on its specific entity type
- Complex operations spanning multiple entities are orchestrated at the service layer
- Repository interfaces maintain clear boundaries

### 3.4 Generic Type Safety

The generic base repository ensures type safety:
- Entity types are specified through generic type parameters
- Operations return strongly-typed results
- Entity-specific repositories can add domain-specific methods

### 3.5 Explicit Error Handling

Repositories use specific exception types for different error conditions:
- `EntityNotFoundError` for queries that don't find the expected entity
- `ValidationError` for data validation failures
- `RepositoryError` for generic data access errors

## 4. Base Repository Implementation

### 4.1 Generic Base Repository

The `BaseRepository` class provides common CRUD operations for all entity types:

```python
class BaseRepository(Generic[T]):
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.model_class: Type[T] = self._get_model_class()
    
    def _get_model_class(self) -> Type[T]:
        raise NotImplementedError("Subclasses must implement _get_model_class")
    
    def get_by_id(self, id: int) -> Optional[T]:
        return self.session.query(self.model_class).filter_by(id=id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.session.query(self.model_class).offset(skip).limit(limit).all()
    
    def create(self, entity: T) -> T:
        try:
            self.session.add(entity)
            self.session.flush()
            return entity
        except Exception as e:
            self.session.rollback()
            raise ValidationError(f"Failed to create {self.model_class.__name__}: {str(e)}")
    
    def update(self, entity: T) -> T:
        try:
            self.session.merge(entity)
            self.session.flush()
            return entity
        except Exception as e:
            self.session.rollback()
            raise ValidationError(f"Failed to update {self.model_class.__name__}: {str(e)}")
    
    def delete(self, entity: T) -> None:
        try:
            self.session.delete(entity)
            self.session.flush()
        except Exception as e:
            self.session.rollback()
            raise RepositoryError(f"Failed to delete {self.model_class.__name__}: {str(e)}")
    
    def filter_by(self, **kwargs) -> List[T]:
        return self.session.query(self.model_class).filter_by(**kwargs).all()
    
    def search(self, search_term: str, fields: List[str]) -> List[T]:
        # Implementation...
        
    def count(self, **filter_criteria) -> int:
        # Implementation...
        
    def exists(self, **filter_criteria) -> bool:
        # Implementation...
```

### 4.2 Exception Hierarchy

The repository layer defines specific exception types for different error conditions:

```python
class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass

class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass

class ValidationError(RepositoryError):
    """Raised when entity validation fails."""
    pass
```

## 5. Entity-Specific Repositories

### 5.1 Material Repository

The `MaterialRepository` handles basic material management operations and common material queries:

```python
class MaterialRepository(BaseRepository[Material]):
    def _get_model_class(self) -> Type[Material]:
        return Material
    
    # Query methods
    def get_by_name(self, name: str) -> Optional[Material]:
        # Implementation...
    
    def get_by_supplier(self, supplier_id: int) -> List[Material]:
        # Implementation...
    
    # Inventory-related methods
    def get_with_inventory_status(self) -> List[Dict[str, Any]]:
        # Implementation...
        
    def get_low_stock(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        # Implementation...
        
    # Business logic methods
    def create_material_with_inventory(self, material_data: Dict[str, Any], inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation...
        
    def get_materials_with_supplier_info(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        # Implementation...
```

### 5.2 Leather Repository

The `LeatherRepository` extends the `MaterialRepository` to add leather-specific operations:

```python
class LeatherRepository(MaterialRepository):
    def _get_model_class(self) -> Type[Leather]:
        return Leather
    
    # Leather-specific query methods
    def get_by_leather_type(self, leather_type: LeatherType) -> List[Leather]:
        # Implementation...
    
    def get_by_thickness(self, min_thickness: float, max_thickness: float) -> List[Leather]:
        # Implementation...
    
    # Business logic methods
    def calculate_cutting_yield(self, leather_id: int, pattern_id: int) -> Dict[str, Any]:
        # Implementation...
    
    def track_hide_usage(self, leather_id: int, area_used: float) -> Dict[str, Any]:
        # Implementation...
```

### 5.3 Inventory Repository

The `InventoryRepository` handles inventory tracking for all item types:

```python
class InventoryRepository(BaseRepository[Inventory]):
    def _get_model_class(self) -> Type[Inventory]:
        return Inventory
    
    # Basic query methods
    def get_by_item_type(self, item_type: str) -> List[Inventory]:
        # Implementation...
    
    def get_by_item(self, item_id: int, item_type: str) -> Optional[Inventory]:
        # Implementation...
    
    # Inventory management methods
    def adjust_inventory(self, inventory_id: int, quantity_change: float, 
                        adjustment_type: InventoryAdjustmentType, 
                        reason: Optional[str] = None) -> Dict[str, Any]:
        # Implementation...
    
    def track_inventory_movement(self, inventory_id: int, 
                               from_location: str, to_location: str) -> Dict[str, Any]:
        # Implementation...
    
    # Analysis methods
    def calculate_inventory_value(self, item_type: Optional[str] = None) -> Dict[str, Any]:
        # Implementation...
```

### 5.4 Pattern Repository

The `PatternRepository` manages pattern data including components and material requirements:

```python
class PatternRepository(BaseRepository[Pattern]):
    def _get_model_class(self) -> Type[Pattern]:
        return Pattern
    
    # Basic query methods
    def get_by_skill_level(self, skill_level: SkillLevel) -> List[Pattern]:
        # Implementation...
    
    # Component methods
    def get_pattern_with_components(self, pattern_id: int) -> Dict[str, Any]:
        # Implementation...
    
    def add_component_to_pattern(self, pattern_id: int, component_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation...
    
    # Material methods
    def get_pattern_material_requirements(self, pattern_id: int) -> Dict[str, Any]:
        # Implementation...
```

## 6. Dependency Injection Integration

### 6.1 Repository Registration

Repositories are registered as singletons in the DI container:

```python
# di/config.py
REPOSITORY_MAPPINGS = {
    'MaterialRepository': 'database.repositories.material_repository.MaterialRepository',
    'LeatherRepository': 'database.repositories.leather_repository.LeatherRepository',
    'InventoryRepository': 'database.repositories.inventory_repository.InventoryRepository',
    'PatternRepository': 'database.repositories.pattern_repository.PatternRepository',
    # ...
}

# di/setup.py
def register_repositories(container):
    for repo_name, repo_path in REPOSITORY_MAPPINGS.items():
        container.register(repo_name, repo_path, Lifetime.SINGLETON)
```

### 6.2 Repository Factory

For specialized repositories, the DI container may register factory functions:

```python
# di/setup_tools.py
def setup_tool_di(container: Container) -> None:
    # Register repositories
    container.register('ToolRepository', ToolRepository, Lifetime.SINGLETON)
    
    # Register dependencies if not already registered
    if not container.is_registered('InventoryRepository'):
        container.register('InventoryRepository', InventoryRepository, Lifetime.SINGLETON)
```

## 7. Transaction Management

### 7.1 Service-Controlled Transactions

Transactions are managed at the service layer, with repositories participating in the active transaction:

```python
# Example service method
def process_sale(self, sale_data: Dict[str, Any]) -> Sale:
    try:
        # Create sale record
        sale = Sale(**sale_data)
        created_sale = self.sales_repository.create(sale)
        
        # Update inventory for each item
        for item in sale.items:
            product = self.product_repository.get_by_id(item.product_id)
            if not product:
                raise ValidationError(f"Product with ID {item.product_id} not found")
            
            # Create sales item
            self.sales_item_repository.create(item)
            
            # Update inventory
            self.inventory_repository.reduce_stock(
                item_id=product.id,
                item_type="product",
                quantity=item.quantity
            )
        
        # Commit the transaction
        self.session.commit()
        return created_sale
    except Exception as e:
        self.session.rollback()
        raise ServiceError(f"Failed to process sale: {str(e)}")
```

### 7.2 Repository Transaction Boundaries

Repositories handle their own transaction boundaries for isolated operations:

```python
def create_material_with_inventory(self, material_data: Dict[str, Any], inventory_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Create material
        material = Material(**material_data)
        created_material = self.create(material)
        
        # Create inventory record
        inventory = Inventory(
            item_id=created_material.id,
            item_type='material',
            **inventory_data
        )
        self.session.add(inventory)
        self.session.flush()
        
        # Prepare result
        result = created_material.to_dict()
        result['inventory'] = inventory.to_dict()
        
        return result
    except Exception as e:
        self.session.rollback()
        raise ValidationError(f"Failed to create material with inventory: {str(e)}")
```

## 8. GUI Integration Patterns

### 8.1 Dashboard Data Methods

Repositories provide methods to collect and format data for dashboard displays:

```python
def get_inventory_dashboard_data(self) -> Dict[str, Any]:
    # Get current inventory counts by status
    status_counts = self.session.query(
        Inventory.status, 
        func.count().label('count')
    ).group_by(Inventory.status).all()
    
    status_data = {status.value: count for status, count in status_counts}
    
    # Get inventory value
    inventory_value = self.calculate_inventory_value()
    
    # Get low stock items
    low_stock = self.get_low_stock_items()
    
    # Get recent movements
    recent_movements = # ...
    
    # Combine all data
    return {
        'status_counts': status_data,
        'valuation': inventory_value,
        'low_stock_count': len(low_stock),
        'low_stock_items': low_stock[:10],  # Top 10 for preview
        'recent_movements': recent_movements[:10],  # Top 10 recent movements
        'total_items': sum(status_data.values())
    }
```

### 8.2 Filtering and Pagination Methods

Each repository includes methods for flexible filtering and pagination to support GUI displays:

```python
def filter_materials_for_gui(self, 
                           search_term: Optional[str] = None,
                           material_types: Optional[List[MaterialType]] = None,
                           supplier_id: Optional[int] = None,
                           in_stock_only: bool = False,
                           sort_by: str = 'name',
                           sort_dir: str = 'asc',
                           page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
    # Implementation...
    
    # Return paginated results with metadata
    return {
        'items': items,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'pages': (total_count + page_size - 1) // page_size,
        'has_next': page < ((total_count + page_size - 1) // page_size),
        'has_prev': page > 1
    }
```

### 8.3 Export Methods

Repositories include methods to export data in various formats:

```python
def export_material_data(self, format: str = "csv") -> Dict[str, Any]:
    materials = self.get_all(limit=10000)  # Reasonable limit
    
    # Transform to dictionaries
    data = [m.to_dict() for m in materials]
    
    # Create metadata
    metadata = {
        'count': len(data),
        'timestamp': datetime.now().isoformat(),
        'format': format
    }
    
    return {
        'data': data,
        'metadata': metadata
    }
```

## 9. Advanced Repository Patterns

### 9.1 Composite Repositories

Composite repositories combine functionality from multiple repositories while maintaining separation of concerns:

```python
class InventoryAnalyticsRepository:
    def __init__(self, session):
        self.session = session
        self.inventory_repo = InventoryRepository(session)
        self.material_repo = MaterialRepository(session)
        self.product_repo = ProductRepository(session)
        
    def get_inventory_turnover_rates(self):
        # Implementation that uses multiple repositories
        # but presents a unified interface
```

### 9.2 Query Builder Pattern

The Query Builder pattern provides a fluent interface for building complex queries:

```python
class QueryBuilder:
    def __init__(self, session, model_class):
        self.session = session
        self.model_class = model_class
        self.query = session.query(model_class)
        self.joins = set()
    
    def filter_by(self, **kwargs):
        self.query = self.query.filter_by(**kwargs)
        return self
    
    def filter(self, *criteria):
        self.query = self.query.filter(*criteria)
        return self
    
    # Other query building methods...
```

### 9.3 Repository Decorators

Repository decorators enhance repository functionality without modifying the core implementation:

```python
def log_repository_access(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        logger = logging.getLogger(f"{self.__class__.__name__}")
        logger.debug(f"Accessing {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = func(self, *args, **kwargs)
        return result
    return wrapper

def measure_performance(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = func(self, *args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.debug(f"Method {func.__name__} took {elapsed_time:.4f} seconds")
        return result
    return wrapper
```

## 10. Implementation Roadmap

The repository layer implementation follows this phased approach:

### Phase 1: Core Infrastructure
1. Implement `BaseRepository` with common operations
2. Set up dependency injection configuration
3. Implement basic transaction management

### Phase 2: Essential Entity Repositories
1. Implement `MaterialRepository` and material type repositories
2. Implement `CustomerRepository` and `SupplierRepository`
3. Implement `InventoryRepository`

### Phase 3: Production-Related Repositories
1. Implement `PatternRepository` and `ComponentRepository`
2. Implement `ProductRepository` and `ProjectRepository`
3. Implement `ToolRepository`

### Phase 4: Transaction Repositories
1. Implement `SalesRepository` and `SalesItemRepository`
2. Implement `PurchaseRepository` and `PurchaseItemRepository`
3. Implement `PickingListRepository` and `ToolListRepository`

### Phase 5: GUI Integration and Testing
1. Implement GUI-specific repository extensions
2. Create integration tests for all repositories
3. Implement advanced filtering and search capabilities

### Phase 6: Performance Optimization
1. Add caching for frequently accessed data
2. Optimize query patterns for large datasets
3. Implement batch processing for bulk operations

## 11. Testing Strategies

### 11.1 Unit Testing with Mocks

```python
def test_get_by_id(self):
    # Arrange
    material_id = 1
    expected_material = Material(id=material_id, name="Test Material")
    session_mock = MagicMock()
    query_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter_by.return_value = query_mock
    query_mock.first.return_value = expected_material
    
    repository = MaterialRepository(session_mock)
    
    # Act
    result = repository.get_by_id(material_id)
    
    # Assert
    session_mock.query.assert_called_once_with(Material)
    query_mock.filter_by.assert_called_once_with(id=material_id)
    self.assertEqual(result, expected_material)
```

### 11.2 Integration Testing with Test Database

```python
def test_create_material(self):
    # Arrange
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    repository = MaterialRepository(session)
    
    new_material = Material(
        name="New Material",
        material_type=MaterialType.SUPPLIES,
        unit=MeasurementUnit.PIECE,
        supplier_id=1
    )
    
    # Act
    created = repository.create(new_material)
    session.commit()
    
    # Assert
    self.assertIsNotNone(created.id)
    retrieved = repository.get_by_id(created.id)
    self.assertEqual(retrieved.name, "New Material")
```

## 12. Conclusion

The repository layer is a critical component of the Leatherworking ERP System, providing a robust, domain-focused interface for data access and manipulation. By following the design patterns and principles outlined in this document, the repository layer enables:

- Clear separation of concerns
- Type-safe, domain-focused data access
- Consistent error handling
- Efficient transaction management
- Flexible GUI integration
- Testability and maintainability

The implementation strategy outlined in this document ensures a systematic approach to building the repository layer, prioritizing core functionality and essential entities before expanding to more specialized areas of the system.