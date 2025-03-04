# Not release ready
# Leatherworking Store Management Application

This application provides a comprehensive solution for managing a leatherworking store, including inventory management, order processing, project tracking, and more.

## Features
- Manage leather, hardware, and other material inventory
- Track inventory quantities, storage locations, suppliers and more  
- Create and manage customer orders
- Generate and print picking lists for order fulfillment
- Manage leatherworking projects and track progress
- Analyze project costs and optimize pricing
- Powerful reporting and analytics capabilities
- Extensible architecture with dependency injection
- SQLite database for data persistence 
- Integrated backup and restore functionality

## Getting Started

### Prerequisites
- Python 3.7+
- SQLite 3

### Installation
1. Clone the repo:
   ```sh
   git clone https://github.com/yourusername/leatherworking-store-app.git
   ```
2. Install dependencies:
   ```sh
   cd leatherworking-store-app
   pip install -r requirements.txt
   ```
3. Run database migrations:
   ```sh
   python -m database.migrations.migration_manager
   ```
4. Start the application:
   ```sh 
   python main.py
   ```

## Architecture Overview
The application follows a layered architecture with clear separation of concerns:
- `gui` - Tkinter based graphical user interface 
- `services` - Business logic layer with service interfaces and implementations
- `database` - Data access layer using SQLAlchemy ORM
- `di` - Dependency injection setup for decoupling components
- `utils` - Various utility modules for cross-cutting concerns

## Database Schema
The application uses a SQLite database with the following key entities:
- `Material` - Represents inventory items like leather, hardware etc.
- `Storage` - Represents physical storage locations 
- `Supplier` - Represents material suppliers
- `Order` - Represents customer orders
- `OrderItem` - Line items within an order 
- `Project` - Represents leatherworking projects
- `ProjectComponent` - Components/materials used in a project
- `PickingList` - Represents a picking list for order fulfillment

Refer to the `database/models` directory for the complete schema definition.

## Dependency Injection
The application uses a custom dependency injection system to decouple components and facilitate testing. The DI setup is defined in the `di` directory.

To access a service from within the application, use the `@inject` decorator:

```python
from di.core import inject
from services.interfaces import IMaterialService

@inject(IMaterialService)
def some_function(material_service: IMaterialService):
    # use the injected service
```

## Testing
The application includes a comprehensive test suite covering various layers:
- `tests/test_integration.py` - End-to-end integration tests
- `tests/test_database` - Database and repository tests  
- `tests/test_services` - Service layer unit tests

To run all tests:
```sh
pytest
```

## License
Distributed under the MIT License. See `LICENSE` for more information.

## Contact
Pascal - 
https://github.com/Skund404/WAWI-Claude

Let me know if you would like me to modify or expand the README in any way! I'm happy to refine it further.