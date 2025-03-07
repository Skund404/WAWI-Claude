# 1. Repositories Documentation

## 1.1 Repository Pattern Overview

The repositories in this leatherworking application follow the Repository pattern, providing a clean abstraction over data access operations and separating business logic from data access concerns.

### Core Repository Architecture

All repositories extend the `BaseRepository` class, which is a generic class that provides common CRUD operations for any model type. This ensures a consistent interface across all repositories.

### BaseRepository Implementation

The `BaseRepository` class:

1. Manages database sessions and model classes.
2. Provides standardized error handling through custom exceptions.
3. Implements common query patterns with SQLAlchemy.
4. Handles transaction management.

### Specialized Repositories

The application features specialized repositories for each model type, enhancing the base functionality with model-specific operations:

1. **ComponentRepository**: Manages components, including materials, hardware, and leather.
2. **CustomerRepository**: Handles customer data with search and filtering capabilities.
3. **HardwareRepository/Inventory**: Manages hardware items and their inventory levels.
4. **LeatherRepository/Inventory**: Manages leather materials and tracks inventory.
5. **MaterialRepository/Inventory**: Handles generic materials and their inventory.
6. **PatternRepository**: Manages pattern designs with filtering by skill level.
7. **PickingListRepository**: Manages picking lists for projects.
8. **ProductRepository/Inventory**: Handles finished products and inventory tracking.
9. **ProjectRepository**: Manages leatherworking projects with status tracking.
10. **PurchaseRepository**: Tracks purchases of materials and supplies.
11. **SalesRepository**: Manages sales transactions and related items.
12. **StorageRepository**: Handles storage locations for inventory items.
13. **SupplierRepository**: Manages vendor information.
14. **ToolRepository/Inventory**: Tracks tools and their availability.
15. **TransactionRepository**: Records inventory movements and adjustments.

### Factory Pattern for Repositories

The `RepositoryFactory` class:

1. Centralizes repository creation.
2. Manages database session sharing.
3. Ensures consistent repository configuration.

### Query Capabilities

The repositories implement sophisticated query capabilities through SQLAlchemy:

1. **Filtering**: Complex filter conditions using SQLAlchemy expressions.
2. **Sorting**: Multiple sort fields and directions.
3. **Pagination**: Efficient data paging for large result sets.
4. **Eager Loading**: Optimized relationship loading using joinedload.
5. **Aggregation**: Sum, average, count, and other aggregation functions.

### Transaction Management

The repositories handle transactions through:

1. Session management with proper commit/rollback.
2. Context managers for transaction scope.
3. Exception handling to ensure data integrity.

### Error Handling

Repositories use a consistent error handling approach with custom exceptions:

1. **ModelNotFoundError**: When requested entities don't exist.
2. **DatabaseError**: For general database access issues.
3. **RepositoryError**: For logical errors within repository operations.

## 1.2 Dependency Injection Integration

Many repositories are designed to work with the application's Dependency Injection system:

1. Some repositories accept service dependencies in their constructors.
2. The `@inject` decorator is used to mark dependencies.
3. Repositories are registered in the DI container for automatic resolution.

## 1.3 Metrics and Analytics Support

The `MetricsRepository` provides specialized functionality for:

1. Collecting performance metrics across the application.
2. Generating reports by timeframe (daily, weekly, monthly).
3. Tracking material usage and efficiency.

## 1.4 Circular Import Resolution

The repositories integrate with the application's circular import resolution system:

1. Using lazy imports for circular dependencies.
2. Leveraging the `CircularImportResolver` for dynamic imports.
3. Maintaining clean architecture despite complex dependency graphs.

This documentation provides a comprehensive overview of the models and repositories in the leatherworking application, highlighting their structure, capabilities, and integration points within the broader system architecture.