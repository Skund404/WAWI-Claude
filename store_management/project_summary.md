# Project Analysis: store_management
Total Python files: 133

## application.py

### Imports:
- store_management.services.storage_service.StorageService
- store_management.services.inventory_service.InventoryService
- store_management.services.order_service.OrderService
- store_management.services.recipe_service.RecipeService
- store_management.database.sqlalchemy.session.init_database
- logging

### Classes:

#### Application
```
Main application class responsible for initialization and service creation
```

Methods:
- __init__(self, db_url)
  ```
  Initialize application with optional database URL
  ```
- initialize(self)
  ```
  Initialize the application, database connection and create services
  ```
- get_service(self, service_name)
  ```
  Get a service by name
  ```
- cleanup(self)
  ```
  Clean up resources
  ```

---

## config.py

### Imports:
- pathlib.Path
- os

### Functions:

#### get_database_path()
```
Returns the absolute path to the database file.

Returns:
    Path: The absolute path to the database file.
```

### Global Variables:
- APP_NAME
- WINDOW_SIZE
- APP_VERSION
- CONFIG_DIR
- DATABASE_FILENAME
- _DATABASE_PATH
- TABLES
- COLORS
- DEFAULT_PADDING
- MINIMUM_COLUMN_WIDTH
- DEFAULT_FONT
- HEADER_FONT
- BACKUP_DIR
- LOG_DIR

---

## main.py

### Imports:
- os
- sys
- logging
- tkinter
- pathlib.Path
- store_management.application.Application
- store_management.gui.main_window.MainWindow

### Functions:

#### setup_logging()
```
Configure logging for the application
```

#### main()
```
Main entry point for the application
```

---

## project_analyzer.py

### Imports:
- os
- ast
- json
- typing.Dict
- typing.List
- dataclasses.dataclass
- dataclasses.asdict
- pathlib.Path

### Classes:

#### FunctionInfo

#### ClassInfo

#### FileInfo

#### ProjectAnalyzer

Methods:
- __init__(self, project_path)
- analyze_project(self)
- analyze_file(self, file_path)
- _extract_function_info(self, node)
- _extract_class_info(self, node)
- generate_summary(self)

### Functions:

#### format_for_chat(summary)

#### analyze_project(project_path)

---

## setup.py

### Imports:
- setuptools.setup
- setuptools.find_packages

---

## __init__.py

### Imports:
- application.Application

### Global Variables:
- __version__
- __author__

---

## alembic\env.py

### Imports:
- sys
- os
- pathlib.Path
- logging
- logging.config.fileConfig
- sqlalchemy.create_engine
- sqlalchemy.pool
- alembic.context
- database.sqlalchemy.models.Base

### Functions:

#### run_migrations_offline()
```
Run migrations in 'offline' mode.
```

#### run_migrations_online()
```
Run migrations in 'online' mode.
```

### Global Variables:
- project_root
- config
- target_metadata

---

## config\application_config.py

### Imports:
- os
- pathlib.Path
- typing.Dict
- typing.Any
- typing.Optional
- json

### Classes:

#### ApplicationConfig
```
Centralized application configuration
```

Methods:
- __new__(cls)
  ```
  Singleton pattern to ensure only one configuration instance
  ```
- __init__(self)
- _load_config(self)
  ```
  Load configuration from file and environment variables
  ```
- _get_config_dir(self)
  ```
  Get the configuration directory
  ```
- _get_config_path(self)
  ```
  Get the path to the configuration file
  ```
- _merge_config(self, config)
  ```
  Recursively merge configuration dictionaries
  ```
- _load_from_env(self)
  ```
  Load configuration from environment variables
  ```
- get(self)
  ```
  Get a configuration value by key path
  ```
- set(self, value)
  ```
  Set a configuration value by key path
  ```
- save(self)
  ```
  Save configuration to file
  ```

---

## config\environment.py

### Imports:
- os
- pathlib.Path
- dotenv.load_dotenv

### Classes:

#### EnvironmentManager
```
Centralized environment configuration management
```

Methods:
- __new__(cls)
- _initialize(self)
- get(key, default)
  ```
  Retrieve environment variable with optional default
  ```
- is_debug()
  ```
  Check if application is in debug mode
  ```
- get_log_level()
  ```
  Get configured log level
  ```

### Global Variables:
- env

---

## config\settings.py

### Imports:
- os
- pathlib.Path

### Functions:

#### get_database_path()
```
Returns the absolute path to the database file.

Returns:
    Path: The absolute path to the database file.
```

### Global Variables:
- APP_NAME
- APP_VERSION
- WINDOW_SIZE
- PROJECT_ROOT
- CONFIG_DIR
- DATABASE_FILENAME
- _DATABASE_PATH
- BACKUP_DIR
- LOG_DIR
- TABLES
- COLORS
- DEFAULT_PADDING
- MINIMUM_COLUMN_WIDTH
- DEFAULT_FONT
- HEADER_FONT

---

## config\__init__.py

### Imports:
- settings.APP_NAME
- settings.APP_VERSION
- settings.WINDOW_SIZE
- settings.CONFIG_DIR
- settings.DATABASE_FILENAME
- settings.TABLES
- settings.COLORS
- settings.DEFAULT_PADDING
- settings.MINIMUM_COLUMN_WIDTH
- settings.DEFAULT_FONT
- settings.HEADER_FONT
- settings.BACKUP_DIR
- settings.LOG_DIR
- settings.get_database_path

### Global Variables:
- __all__

---

## database\base.py

### Imports:
- sqlalchemy.ext.declarative.declarative_base
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.DateTime
- datetime.datetime

### Classes:

#### BaseModel
Inherits from: Base
```
Abstract base model providing common fields and behaviors.

Automatically adds:
- Primary key (id)
- Creation timestamp
- Last update timestamp
```

Methods:
- __repr__(self)
  ```
  Default string representation of the model.

Returns:
    String representation with class name and ID
  ```
- to_dict(self)
  ```
  Convert model instance to dictionary.

Returns:
    Dictionary representation of the model
  ```

### Global Variables:
- Base

---

## database\config.py

### Imports:
- os
- typing.Dict
- typing.Any
- typing.Optional
- pathlib.Path

### Functions:

#### get_database_url(config)
```
Generate database connection URL with multiple configuration sources.

Priority:
1. Explicitly passed configuration
2. Environment variables
3. Default configuration

Args:
    config: Optional configuration dictionary

Returns:
    Database connection URL
```

#### _find_project_root()
```
Dynamically find the project root directory.

Returns:
    Path to the project root
```

#### get_database_config()
```
Retrieve comprehensive database configuration.

Combines configuration from multiple sources.

Returns:
    Dictionary with database configuration
```

---

## database\initialize.py

### Imports:
- logging
- sqlalchemy_utils.drop_database
- config.database_manager
- sqlalchemy.models.Base

### Functions:

#### initialize_database(drop_existing)
```
Comprehensive database initialization process

Args:
    drop_existing (bool): Whether to drop existing database before creation
```

#### add_initial_data()
```
Optional method to add initial data to the database
```

### Global Variables:
- logger

---

## database\session.py

### Imports:
- os
- contextlib.contextmanager
- typing.Optional
- sqlalchemy.create_engine
- sqlalchemy.orm.sessionmaker
- sqlalchemy.orm.scoped_session
- sqlalchemy.pool.NullPool
- sqlalchemy_utils.database_exists
- sqlalchemy_utils.create_database
- config.get_database_url
- utils.error_handling.DatabaseError

### Functions:

#### init_database(db_url)
```
Initialize the database, creating it if it doesn't exist.

Args:
    db_url: Optional database URL (uses default if not provided)
```

#### get_db_session()
```
Context manager for database sessions.

Provides a transactional scope for database operations.
Automatically handles session creation, commit, and rollback.

Yields:
    SQLAlchemy session object

Raises:
    DatabaseError: If session management fails
```

#### get_session_factory()
```
Get a thread-local scoped session factory.

Returns:
    Scoped session factory
```

#### close_all_sessions()
```
Close all active database sessions.
Useful for cleanup and testing.
```

---

## database\__init__.py

### Imports:
- store_management.database.base.BaseManager
- store_management.database.sqlalchemy.models.Base
- store_management.database.sqlalchemy.models.Supplier
- store_management.database.sqlalchemy.models.Part
- store_management.database.sqlalchemy.models.Leather
- store_management.database.sqlalchemy.models.Recipe
- store_management.database.sqlalchemy.models.RecipeItem
- store_management.database.sqlalchemy.models.ShoppingList
- store_management.database.sqlalchemy.models.ShoppingListItem
- store_management.database.sqlalchemy.models.Order
- store_management.database.sqlalchemy.models.OrderItem
- base_mixins.BaseMixin
- base_mixins.SearchMixin
- base_mixins.FilterMixin
- base_mixins.PaginationMixin
- base_mixins.TransactionMixin
- store_management.database.sqlalchemy.manager.DatabaseManagerSQLAlchemy

### Global Variables:
- __all__
- __all__

---

## gui\base_view.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- application.Application

### Classes:

#### BaseView
Inherits from: ttk.Frame
```
Base class for all view components
```

Methods:
- __init__(self, parent, app)
- load_data(self)
  ```
  Load data into the view
  ```
- save(self)
  ```
  Save current data
  ```
- undo(self)
  ```
  Undo the last action
  ```
- redo(self)
  ```
  Redo the last undone action
  ```
- show_error(self, title, message)
  ```
  Show error message
  ```
- show_info(self, title, message)
  ```
  Show information message
  ```
- show_warning(self, title, message)
  ```
  Show warning message
  ```
- confirm(self, title, message)
  ```
  Show confirmation dialog
  ```
- set_status(self, message)
  ```
  Set status message in main window
  ```

---

## gui\main_window.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- sys
- os
- pathlib.Path
- application.Application
- storage.storage_view.StorageView
- product.product_view.ProductView
- order.order_view.OrderView
- shopping_list.shopping_list_view.ShoppingListView

### Classes:

#### MainWindow
```
Main application window
```

Methods:
- __init__(self, root, app)
- setup_ui(self)
  ```
  Set up the main UI components
  ```
- bind_shortcuts(self)
  ```
  Bind global keyboard shortcuts
  ```
- save(self, event)
  ```
  Global save function
  ```
- load(self, event)
  ```
  Global load function
  ```
- search(self, event)
  ```
  Global search function
  ```
- undo(self, event)
  ```
  Global undo function
  ```
- redo(self, event)
  ```
  Global redo function
  ```
- get_current_view(self)
  ```
  Get the currently active view
  ```
- set_status(self, message)
  ```
  Set status bar message
  ```
- run(self)
  ```
  Start the application main loop
  ```

---

## gui\__init__.py

---

## modules\__init__.py

---

## services\inventory_service.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Tuple
- datetime.datetime
- store_management.database.sqlalchemy.models.part.Part
- store_management.database.sqlalchemy.models.leather.Leather
- store_management.database.sqlalchemy.models.supplier.Supplier
- store_management.database.sqlalchemy.models.enums.InventoryStatus
- store_management.database.sqlalchemy.models.enums.TransactionType
- store_management.database.sqlalchemy.models.transaction.InventoryTransaction
- store_management.database.sqlalchemy.manager_factory.get_manager

### Classes:

#### InventoryService
```
Service for inventory management operations
```

Methods:
- __init__(self)
  ```
  Initialize service with appropriate managers
  ```
- update_part_stock(self, part_id, quantity_change, transaction_type, notes)
  ```
  Update part stock with transaction tracking.

Args:
    part_id: Part ID
    quantity_change: Change in quantity (positive or negative)
    transaction_type: Type of transaction
    notes: Optional notes

Returns:
    Tuple of (success, message)
  ```

---

## services\order_service.py

### Imports:
- typing.List
- typing.Dict
- typing.Any
- typing.Optional
- typing.Tuple
- datetime.datetime
- store_management.database.sqlalchemy.models.order.Order
- store_management.database.sqlalchemy.models.order.OrderItem
- store_management.database.sqlalchemy.models.supplier.Supplier
- store_management.database.sqlalchemy.models.part.Part
- store_management.database.sqlalchemy.models.leather.Leather
- store_management.database.sqlalchemy.models.enums.OrderStatus
- store_management.database.sqlalchemy.models.enums.PaymentStatus
- store_management.database.sqlalchemy.manager_factory.get_manager

### Classes:

#### OrderService
```
Service for order management operations
```

Methods:
- __init__(self)
  ```
  Initialize with appropriate managers
  ```
- create_order(self, order_data, items)
  ```
  Create a new order with items.

Args:
    order_data: Dictionary with order data
    items: List of dictionaries with item data

Returns:
    Tuple of (created order or None, result message)
  ```
- update_order_status(self, order_id, status)
  ```
  Update order status with validation of status transitions.

Args:
    order_id: Order ID
    status: New status

Returns:
    Tuple of (success, message)
  ```
- _is_valid_status_transition(self, current_status, new_status)
  ```
  Validate if a status transition is allowed.

Args:
    current_status: Current order status
    new_status: New order status

Returns:
    True if transition is valid, False otherwise
  ```

---

## services\recipe_service.py

### Imports:
- typing.List
- typing.Dict
- typing.Any
- typing.Optional
- typing.Tuple
- store_management.database.sqlalchemy.models.recipe.Recipe
- store_management.database.sqlalchemy.models.recipe.RecipeItem
- store_management.database.sqlalchemy.models.part.Part
- store_management.database.sqlalchemy.models.leather.Leather
- store_management.database.sqlalchemy.manager_factory.get_manager

### Classes:

#### RecipeService
```
Service for recipe management operations
```

Methods:
- __init__(self)
  ```
  Initialize with appropriate managers
  ```
- create_recipe(self, recipe_data, items)
  ```
  Create a new recipe with items.

Args:
    recipe_data: Dictionary with recipe data
    items: List of dictionaries with item data

Returns:
    Tuple of (created recipe or None, result message)
  ```
- check_materials_availability(self, recipe_id, quantity)
  ```
  Check if materials for a recipe are available in sufficient quantity.

Args:
    recipe_id: Recipe ID
    quantity: Number of items to produce

Returns:
    Tuple of (all materials available, list of missing items)
  ```

---

## services\shopping_list_service.py

### Imports:
- typing.List
- typing.Dict
- typing.Any
- typing.Optional
- typing.Tuple
- datetime.datetime
- store_management.database.sqlalchemy.models.shopping_list.ShoppingList
- store_management.database.sqlalchemy.models.shopping_list.ShoppingListItem
- store_management.database.sqlalchemy.models.part.Part
- store_management.database.sqlalchemy.models.leather.Leather
- store_management.database.sqlalchemy.manager_factory.get_manager

### Classes:

#### ShoppingListService
```
Service for shopping list management operations
```

Methods:
- __init__(self)
  ```
  Initialize with appropriate managers
  ```
- create_shopping_list(self, list_data, items)
  ```
  Create a new shopping list with optional items.

Args:
    list_data: Shopping list data
    items: Optional list of item data

Returns:
    Tuple of (created shopping list or None, result message)
  ```
- add_item_to_list(self, list_id, item_data)
  ```
  Add an item to a shopping list.

Args:
    list_id: Shopping list ID
    item_data: Item data

Returns:
    Tuple of (created item or None, result message)
  ```
- mark_item_purchased(self, item_id, purchase_data)
  ```
  Mark a shopping list item as purchased with purchase details.

Args:
    item_id: Shopping list item ID
    purchase_data: Purchase details (date, price)

Returns:
    Tuple of (success, message)
  ```
- get_pending_items_by_supplier(self)
  ```
  Get pending items grouped by supplier.

Returns:
    Dictionary mapping supplier IDs to lists of pending items
  ```

---

## services\storage_service.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- store_management.database.sqlalchemy.models.storage.Storage
- store_management.database.sqlalchemy.models.product.Product
- store_management.database.sqlalchemy.manager_factory.get_manager

### Classes:

#### StorageService
```
Service for storage and product placement operations
```

Methods:
- __init__(self)
  ```
  Initialize with appropriate managers
  ```
- assign_product_to_storage(self, product_id, storage_id)
  ```
  Assign a product to a storage location.

Args:
    product_id: Product ID
    storage_id: Storage location ID

Returns:
    True if assignment succeeded, False otherwise
  ```
- get_storage_utilization(self)
  ```
  Get utilization metrics for all storage locations.

Returns:
    List of dictionaries with utilization metrics
  ```
- create_storage_location(self, data)
  ```
  Create a new storage location.

Args:
    data: Storage location data

Returns:
    Created storage location or None if failed
  ```

---

## services\__init__.py

---

## src\database_init.py

### Imports:
- sqlite3
- pathlib.Path

### Functions:

#### init_database()

---

## src\__init__.py

---

## tests\test_storage.py

### Imports:
- store_management.database.sqlalchemy.managers.storage_manager.StorageManager

### Functions:

#### test_storage_operations()

---

## tests\__init__.py

---

## tools\run_migration.py

### Imports:
- argparse
- logging
- sys
- pathlib.Path
- sqlalchemy.create_engine
- sqlalchemy.orm.sessionmaker
- store_management.database.models.base.Base
- store_management.config.application_config.ApplicationConfig

### Functions:

#### setup_logging()
```
Configure logging for migrations
```

#### run_migrations(db_url, drop_existing)
```
Run database migrations
```

#### main()
```
Main entry point
```

---

## tools\__init__.py

---

## utils\backup.py

### Imports:
- sqlite3
- os
- shutil
- json
- datetime.datetime
- typing.List
- typing.Dict
- typing.Any
- pathlib.Path
- datetime.datetime
- typing.Optional

### Classes:

#### DatabaseBackup
```
Handler for database backups
```

Methods:
- __init__(self, db_path)
- create_backup(self, operation)
  ```
  Create a backup before performing an operation
  ```
- restore_backup(self, backup_path)
  ```
  Restore database from backup
  ```
- list_backups(self)
  ```
  List available backups with metadata
  ```
- cleanup_old_backups(self, keep_days)
  ```
  Clean up backups older than specified days
  ```

---

## utils\database_utilities.py

### Imports:
- sqlite3
- json
- csv
- datetime
- pathlib.Path
- typing.Dict
- typing.List
- typing.Any
- zipfile
- io

### Classes:

#### DatabaseUtilities

Methods:
- __init__(self, db_path)
- export_database(self, export_path)
  ```
  Export database to a zip file containing JSON and CSV formats
  ```
- import_database(self, import_path)
  ```
  Import database from a zip file
  ```
- export_schema(self)
  ```
  Export database schema
  ```
- optimize_database(self)
  ```
  Optimize database (vacuum, analyze, etc.)
  ```
- verify_database(self)
  ```
  Verify database integrity and return status report
  ```
- generate_report(self, report_type)
  ```
  Generate various types of reports
  ```
- _generate_inventory_report(self, cursor)
  ```
  Generate inventory report
  ```
- _generate_orders_report(self, cursor)
  ```
  Generate orders report
  ```
- _generate_suppliers_report(self, cursor)
  ```
  Generate suppliers report
  ```

---

## utils\error_handler.py

### Imports:
- tkinter
- tkinter.messagebox
- functools
- functools.wraps
- store_management.utils.logger.log_error
- store_management.utils.logger.logger
- traceback

### Classes:

#### ErrorHandler
```
    
```

Methods:
- log_database_action(action, details)
  ```
  Log database-related actions
  ```
- validate_positive_integer(value, field_name)
  ```
  Validate that a value is a positive integer
  ```
- show_error(self, title, message, error)
  ```
  Show error message to user and log it
  ```
- show_warning(self, title, message)
  ```
  Show warning message to user and log it
  ```
- handle_error(self, func)
  ```
  Decorator for handling errors in functions
  ```

#### ApplicationError
Inherits from: Exception
```
Base class for application-specific errors
```

Methods:
- __init__(self, message, details)

#### DatabaseError
Inherits from: ApplicationError
```
Error raised for database-related issues
```

#### ValidationError
Inherits from: ApplicationError
```
Error raised for data validation issues
```

### Functions:

#### check_database_connection(func)
```
Decorator to check database connection before executing database operations
```

#### get_error_context()
```
Get current error context including stack trace
```

---

## utils\error_handling.py

### Imports:
- typing.Optional
- typing.Dict
- typing.Any
- traceback
- logging

### Classes:

#### DatabaseError
Inherits from: Exception
```
Custom exception for database-related errors.

Provides detailed context about database operation failures.
```

Methods:
- __init__(self, message, details, error_code)
  ```
  Initialize a database error with detailed information.

Args:
    message: Primary error message
    details: Additional error details or stack trace
    error_code: Optional error code for identification
  ```
- __str__(self)
  ```
  Provide a comprehensive string representation of the error.

Returns:
    Formatted error message with details
  ```

### Functions:

#### handle_database_error(operation, error, context)
```
Standardized handler for database-related errors.

Args:
    operation: Description of the operation that failed
    error: The original exception
    context: Optional context dictionary with additional information

Returns:
    A standardized DatabaseError instance
```

#### log_database_action(action, details, level)
```
Log database-related actions with optional details.

Args:
    action: Description of the database action
    details: Optional dictionary of additional details
    level: Logging level (info, warning, error)
```

---

## utils\exporters.py

### Imports:
- csv
- json
- xlsxwriter
- typing.Dict
- typing.List
- typing.Any
- typing.Optional
- pathlib.Path
- datetime.datetime
- pandas

### Classes:

#### OrderExporter
```
Handler for exporting order data
```

Methods:
- export_to_csv(data, filepath)
  ```
  Export order data to CSV
  ```
- export_to_excel(data, filepath)
  ```
  Export order data to Excel
  ```
- export_to_json(data, filepath)
  ```
  Export order data to JSON (backup)
  ```

#### OrderImporter
```
Handler for importing order data
```

Methods:
- import_from_csv(order_file, details_file)
  ```
  Import order data from CSV files
  ```
- import_from_excel(filepath)
  ```
  Import order data from Excel file
  ```
- import_from_json(filepath)
  ```
  Import order data from JSON backup
  ```

---

## utils\logger.py

### Imports:
- logging
- logging.handlers
- os
- pathlib.Path
- typing.Optional
- store_management.config.LOG_DIR

### Classes:

#### AppLogger

Methods:
- __new__(cls)
- _initialize_logger(self)
  ```
  Initialize the application logger with file and console handlers.
  ```
- get_logger(self)
  ```
  Get the configured logger instance.
  ```

### Functions:

#### get_logger(name)
```
Get a logger instance, optionally with a specific name.

Args:
    name: Optional name for the logger. If provided, returns a child logger
         of the main application logger.

Returns:
    logging.Logger: Configured logger instance
```

#### log_error(error, context)
```
Log an error with optional context information.

Args:
    error: The exception to log
    context: Optional dictionary with additional context
```

#### log_info(message)
```
Log an info message.

Args:
    message: The message to log
```

#### log_debug(message)
```
Log a debug message.

Args:
    message: The message to log
```

### Global Variables:
- logger_instance
- logger

---

## utils\logging_config.py

### Imports:
- os
- sys
- logging
- logging.handlers.RotatingFileHandler
- traceback
- typing.Optional
- typing.Any
- typing.Dict

### Classes:

#### LoggerConfig
```
Comprehensive logging configuration with multiple handlers
and advanced formatting
```

Methods:
- create_logger(name, log_level, log_dir)
  ```
  Create a configured logger with file and console handlers

Args:
    name (str): Logger name
    log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_dir (Optional[str]): Directory for log files

Returns:
    Configured logging.Logger instance
  ```

#### ErrorTracker
```
Advanced error tracking and logging utility
```

Methods:
- __init__(self, logger)
  ```
  Initialize ErrorTracker

Args:
    logger (Optional[logging.Logger]): Logger instance
  ```
- log_error(self, error, context, additional_info)
  ```
  Comprehensive error logging with context and stack trace

Args:
    error (Exception): The exception to log
    context (Optional[Dict]): Additional context information
    additional_info (Optional[str]): Extra descriptive information
  ```
- trace_method(self, method_name)
  ```
  Method decorator for tracing method calls and errors

Args:
    method_name (str): Name of the method being traced
  ```

### Global Variables:
- logger
- error_tracker

---

## utils\notifications.py

### Imports:
- tkinter
- tkinter.ttk
- typing.Optional
- typing.Callable
- time
- enum.Enum
- queue.Queue
- threading

### Classes:

#### NotificationType
Inherits from: Enum

#### StatusNotification
```
Status notification manager
```

Methods:
- __init__(self, parent)
- setup_styles(self)
  ```
  Setup notification styles
  ```
- start_processor(self)
  ```
  Start notification processing thread
  ```
- _process_notifications(self)
  ```
  Process notifications from queue
  ```
- _show_notification(self, notification)
  ```
  Show notification
  ```
- _clear_notification(self, callback)
  ```
  Clear current notification
  ```
- show_info(self, message, duration)
  ```
  Show info notification
  ```
- show_success(self, message, duration)
  ```
  Show success notification
  ```
- show_warning(self, message, duration)
  ```
  Show warning notification
  ```
- show_error(self, message, duration)
  ```
  Show error notification
  ```
- show_progress(self, message, callback)
  ```
  Show progress notification
  ```
- clear(self)
  ```
  Clear current notification
  ```
- cleanup(self)
  ```
  Cleanup resources
  ```

---

## utils\utils.py

---

## utils\validators.py

### Imports:
- typing.Dict
- typing.Any
- typing.Tuple
- typing.Optional
- datetime.datetime
- re

### Classes:

#### OrderValidator
```
Validator for order-related data
```

Methods:
- validate_order(data)
  ```
  Validate order data
  ```
- validate_order_details(data)
  ```
  Validate order details data
  ```

#### DataSanitizer
```
Sanitizer for input data
```

Methods:
- sanitize_string(value)
  ```
  Sanitize string input
  ```
- sanitize_numeric(value)
  ```
  Sanitize numeric input
  ```
- sanitize_identifier(value)
  ```
  Sanitize database identifiers
  ```
- sanitize_order_data(data)
  ```
  Sanitize order data
  ```

---

## utils\__init__.py

---

## views\__init__.py

---

## utils\order_exporter\order_exporter.py

### Imports:
- pandas
- typing.Dict
- typing.Any
- pathlib.Path
- json

### Classes:

#### OrderExporter

Methods:
- export_to_excel(data, filepath)
  ```
  Export order data to Excel
  ```
- export_to_csv(data, filepath)
  ```
  Export order data to CSV
  ```
- export_to_json(data, filepath)
  ```
  Export order data to JSON
  ```

---

## utils\order_exporter\__init__.py

---

## utils\validators\order_validator.py

### Imports:
- typing.Tuple
- typing.Dict
- typing.Any
- datetime.datetime

### Classes:

#### OrderValidator

Methods:
- validate_order(data)
  ```
  Validate order data
  ```
- validate_order_detail(data)
  ```
  Validate order detail data
  ```

---

## utils\validators\__init__.py

---

## tests\test_database\test_base_manager.py

### Imports:
- pytest
- typing.List
- typing.Dict
- typing.Any
- sqlalchemy.create_engine
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.orm.sessionmaker
- sqlalchemy.orm.declarative_base
- sqlalchemy.exc.SQLAlchemyError
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.manager_factory.get_manager
- store_management.database.sqlalchemy.manager_factory.register_specialized_manager
- store_management.database.sqlalchemy.manager_factory.clear_manager_cache
- store_management.utils.error_handling.DatabaseError

### Classes:

#### TestModel
Inherits from: TestBase
```
Test model for BaseManager unit tests.
```

#### TestSpecializedManager
```
Specialized test manager with additional method.
```

Methods:
- get_by_name(self, name)
  ```
  Retrieve models by name.

Args:
    name: Name to search for

Returns:
    List of matching models
  ```

#### TestBaseManager
```
Comprehensive test suite for BaseManager.
```

Methods:
- test_create_single_record(self, test_manager)
  ```
  Test creating a single record.
  ```
- test_get_record(self, test_manager)
  ```
  Test retrieving a single record by ID.
  ```
- test_update_record(self, test_manager)
  ```
  Test updating an existing record.
  ```
- test_delete_record(self, test_manager)
  ```
  Test deleting a record.
  ```
- test_bulk_create(self, test_manager)
  ```
  Test bulk creation of records.
  ```
- test_bulk_update(self, test_manager)
  ```
  Test bulk updating of records.
  ```
- test_get_all(self, test_manager)
  ```
  Test retrieving all records.
  ```
- test_search(self, test_manager)
  ```
  Test search functionality.
  ```
- test_filter(self, test_manager)
  ```
  Test complex filtering.
  ```
- test_exists(self, test_manager)
  ```
  Test existence check.
  ```
- test_count(self, test_manager)
  ```
  Test record counting.
  ```
- test_specialized_manager(self, session_factory)
  ```
  Test specialized manager functionality.
  ```

#### TestErrorHandling
```
Test error handling scenarios.
```

Methods:
- test_create_invalid_data(self, test_manager)
  ```
  Test creating record with invalid data.
  ```
- test_update_non_existent_record(self, test_manager)
  ```
  Test updating a non-existent record.
  ```
- test_delete_non_existent_record(self, test_manager)
  ```
  Test deleting a non-existent record.
  ```

### Functions:

#### test_engine()
```
Create an in-memory SQLite database for testing.
```

#### session_factory(test_engine)
```
Create a session factory for testing.
```

#### test_manager(session_factory)
```
Create a BaseManager instance for testing.
```

### Global Variables:
- TestBase

---

## tests\test_database\test_manager_factory.py

### Imports:
- pytest
- sqlalchemy.create_engine
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.orm.declarative_base
- sqlalchemy.orm.sessionmaker
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.manager_factory.get_manager
- store_management.database.sqlalchemy.manager_factory.register_specialized_manager
- store_management.database.sqlalchemy.manager_factory.clear_manager_cache

### Classes:

#### FactoryTestModel
Inherits from: FactoryTestBase
```
Test model for manager factory tests.
```

#### CustomTestManager
```
Specialized test manager with additional method.
```

Methods:
- custom_method(self)
  ```
  Custom method to test specialized manager functionality.

Returns:
    A test string
  ```

#### TestManagerFactory
```
Comprehensive test suite for manager factory.
```

Methods:
- test_engine(self)
  ```
  Create an in-memory SQLite database for testing.
  ```
- session_factory(self, test_engine)
  ```
  Create a session factory for testing.
  ```
- test_manager_cache(self, session_factory)
  ```
  Test manager caching mechanism.
  ```
- test_specialized_manager_registration(self, session_factory)
  ```
  Test registering and using a specialized manager.
  ```
- test_force_new_manager(self, session_factory)
  ```
  Test creating a new manager instance bypassing cache.
  ```
- test_manager_with_mixins(self, session_factory)
  ```
  Test creating a manager with additional mixins.
  ```
- test_invalid_mixin(self, session_factory)
  ```
  Test handling of invalid mixins.
  ```

#### TestManagerPerformance
```
Performance-oriented tests for manager operations.
```

Methods:
- large_dataset_manager(self, session_factory)
  ```
  Create a manager with a large dataset.
  ```
- test_large_dataset_retrieval(self, large_dataset_manager)
  ```
  Test performance of retrieving large datasets.
  ```
- test_large_dataset_filtering(self, large_dataset_manager)
  ```
  Test filtering performance on large datasets.
  ```

### Global Variables:
- FactoryTestBase

---

## tests\test_database\__init__.py

---

## tests\test_repositories\test_storage_repository.py

### Imports:
- unittest
- sqlalchemy.create_engine
- sqlalchemy.orm.sessionmaker
- store_management.database.models.base.Base
- store_management.database.models.storage.Storage
- store_management.database.repositories.storage_repository.StorageRepository

### Classes:

#### TestStorageRepository
Inherits from: unittest.TestCase
```
Test cases for StorageRepository
```

Methods:
- setUp(self)
  ```
  Set up test database and repository
  ```
- tearDown(self)
  ```
  Clean up resources
  ```
- test_get_all(self)
  ```
  Test getting all storage locations
  ```
- test_get_by_id(self)
  ```
  Test getting storage by ID
  ```
- test_get_by_location(self)
  ```
  Test getting storage by location
  ```
- test_create(self)
  ```
  Test creating a new storage location
  ```
- test_update(self)
  ```
  Test updating a storage location
  ```
- test_delete(self)
  ```
  Test deleting a storage location
  ```

---

## tests\test_repositories\test_storage_service.py

### Imports:
- unittest
- unittest.mock.MagicMock
- unittest.mock.patch
- sqlalchemy.orm.Session
- store_management.services.storage_service.StorageService
- store_management.database.repositories.storage_repository.StorageRepository
- store_management.database.repositories.product_repository.ProductRepository
- store_management.database.models.storage.Storage
- store_management.database.models.product.Product

### Classes:

#### TestStorageService
Inherits from: unittest.TestCase
```
Test cases for StorageService
```

Methods:
- setUp(self)
  ```
  Set up test service with mock repositories
  ```
- tearDown(self)
  ```
  Clean up resources
  ```
- test_assign_product_to_storage(self)
  ```
  Test assigning a product to storage
  ```

---

## tests\test_repositories\__init__.py

---

## src\models\__init__.py

---

## gui\dialogs\add_dialog.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- typing.Dict
- typing.Callable
- typing.Optional
- uuid

### Classes:

#### AddDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, save_callback, fields)
  ```
  Initialize add dialog

Args:
    parent: Parent window
    save_callback: Function to call with form data on save
    fields: List of tuples (field_name, display_name, required, field_type)
           field_type can be 'string', 'float', or 'text'
  ```
- show_storage_dialog(self)
- setup_ui(self)
  ```
  Setup the dialog UI components
  ```
- get_field_values(self)
  ```
  Get all field values from entries
  ```
- validate_required_fields(self)
  ```
  Validate that all required fields have values
  ```
- save(self)
  ```
  Validate and save the form data
  ```

---

## gui\dialogs\base_dialog.py

### Imports:
- tkinter
- tkinter.ttk
- typing.Optional
- typing.Tuple

### Classes:

#### BaseDialog
Inherits from: tk.Toplevel
```
Base class for all dialogs in the application
```

Methods:
- __init__(self, parent, title, size, modal)
  ```
  Initialize base dialog

Args:
    parent: Parent window
    title: Dialog title
    size: Dialog size as (width, height)
    modal: Whether dialog should be modal
  ```
- center_on_parent(self)
  ```
  Center the dialog on its parent window
  ```
- add_button(self, text, command, side, width, default)
  ```
  Add a button to the standard button frame

Args:
    text: Button text
    command: Button command
    side: Pack side (tk.RIGHT or tk.LEFT)
    width: Button width
    default: Whether this is the default button

Returns:
    The created button
  ```
- add_ok_cancel_buttons(self, ok_text, cancel_text, ok_command)
  ```
  Add standard OK and Cancel buttons
  ```
- ok(self, event)
  ```
  OK button handler
  ```
- cancel(self, event)
  ```
  Cancel button handler
  ```
- validate(self)
  ```
  Validate dialog contents
Override in subclasses to implement validation
  ```

---

## gui\dialogs\filter_dialog.py

### Imports:
- tkinter
- tkinter.ttk
- typing.List
- typing.Callable
- typing.Dict

### Classes:

#### FilterDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, columns, filter_callback)
  ```
  Initialize filter dialog

Args:
    parent: Parent window
    columns: List of column names to filter on
    filter_callback: Function to call with filter conditions
  ```
- setup_ui(self)
  ```
  Setup the dialog UI components
  ```
- add_filter(self)
  ```
  Add a new filter row
  ```
- remove_filter(self, filter_frame)
  ```
  Remove a filter row
  ```
- get_filter_conditions(self)
  ```
  Get all filter conditions
  ```
- apply_filters(self)
  ```
  Apply all filter conditions
  ```
- validate_numeric_filter(self, value, column)
  ```
  Validate numeric filters
  ```
- clear_filters(self)
  ```
  Clear all filter conditions
  ```

---

## gui\dialogs\report_dialog.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- tkinter.filedialog
- typing.Dict
- typing.List
- typing.Optional
- datetime.datetime
- csv
- store_management.database.sqlalchemy.manager.ReportManager
- store_management.database.sqlalchemy.session.get_session
- store_management.gui.dialogs.base_dialog.BaseDialog
- store_management.utils.logger.get_logger

### Classes:

#### ReportDialog
Inherits from: BaseDialog

Methods:
- __init__(self, parent)
- create_ui(self)
  ```
  Create the report dialog UI
  ```
- create_report_display(self, parent)
  ```
  Create the report display area
  ```
- update_options(self)
  ```
  Update visible options based on report type
  ```
- on_report_type_change(self)
  ```
  Handle report type change
  ```
- generate_report(self)
  ```
  Generate the selected report
  ```
- display_inventory_report(self)
  ```
  Display inventory report
  ```
- display_orders_report(self)
  ```
  Display orders report
  ```
- display_suppliers_report(self)
  ```
  Display suppliers report
  ```
- create_treeview(self, parent, columns, data)
  ```
  Create a treeview with given columns and data
  ```

### Global Variables:
- logger

---

## gui\dialogs\search_dialog.py

### Imports:
- tkinter
- tkinter.ttk
- typing.List
- typing.Callable
- typing.Dict

### Classes:

#### SearchDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, columns, search_callback)
  ```
  Initialize search dialog

Args:
    parent: Parent window
    columns: List of column names to search in
    search_callback: Function to call with search parameters
  ```
- setup_ui(self)
  ```
  Setup the dialog UI components
  ```
- search(self)
  ```
  Execute the search
  ```

---

## gui\dialogs\__init__.py

### Imports:
- base_dialog.BaseDialog
- add_dialog.AddDialog
- search_dialog.SearchDialog
- filter_dialog.FilterDialog

### Global Variables:
- __all__

---

## gui\order\incoming_goods_view.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- tkinter.filedialog
- typing.List
- typing.Optional
- typing.Dict
- sqlalchemy.orm.Session
- store_management.database.sqlalchemy.models.Order
- store_management.database.sqlalchemy.models.OrderStatus
- store_management.database.sqlalchemy.models.PaymentStatus
- store_management.database.sqlalchemy.managers.order_manager.OrderManager
- store_management.utils.exporters.order_exporter.OrderExporter
- store_management.utils.validators.order_validator.OrderValidator
- store_management.gui.base_view.BaseView

### Classes:

#### IncomingGoodsView
Inherits from: BaseView
```
View for managing incoming goods and orders
```

Methods:
- __init__(self, parent, session)
  ```
  Initialize Incoming Goods View

Args:
    parent: Parent widget
    session: SQLAlchemy database session
  ```
- _setup_ui(self)
  ```
  Setup the entire user interface
  ```
- _create_toolbar(self)
  ```
  Create the main toolbar with action buttons
  ```
- _create_content_area(self)
  ```
  Create main content area with orders and details tables
  ```
- _create_treeview(parent, columns, select_callback)
  ```
  Create a standardized treeview

Args:
    parent: Parent widget
    columns: List of column names
    select_callback: Optional selection callback

Returns:
    Configured Treeview widget
  ```
- _load_initial_data(self)
  ```
  Load initial orders data
  ```
- _populate_orders_tree(self, orders)
  ```
  Populate orders treeview

Args:
    orders: List of Order objects
  ```
- _on_order_select(self, event)
  ```
  Handle order selection in treeview
  ```
- _load_order_details(self, order_id)
  ```
  Load details for a specific order

Args:
    order_id: ID of the order to load details for
  ```
- cleanup(self)
  ```
  Cleanup resources and handle unsaved changes
  ```

---

## gui\order\shopping_list_view.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- sqlalchemy.exc.SQLAlchemyError
- typing.Optional
- typing.List
- datetime.datetime
- store_management.database.sqlalchemy.models.ShoppingList
- store_management.database.sqlalchemy.models.ShoppingListItem
- store_management.database.sqlalchemy.models.Supplier
- store_management.database.sqlalchemy.models.Part
- store_management.database.sqlalchemy.models.Leather
- store_management.database.sqlalchemy.manager.DatabaseManagerSQLAlchemy

### Classes:

#### ShoppingListView
Inherits from: ttk.Frame

Methods:
- __init__(self, parent)
- setup_table_selection(self)
  ```
  Create shopping list selection table view
  ```
- load_shopping_lists(self)
  ```
  Load available shopping lists
  ```
- show_add_list_dialog(self)
  ```
  Show dialog for creating new shopping list
  ```
- on_list_select(self, event)
  ```
  Handle shopping list selection
  ```
- load_list_items(self, list_id)
  ```
  Load items for selected shopping list
  ```
- show_add_item_dialog(self)
  ```
  Show dialog for adding item to shopping list
  ```

---

## gui\order\supplier_view.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- tkinter.filedialog
- typing.Dict
- typing.List
- typing.Optional
- datetime.datetime
- pathlib.Path
- csv
- pandas
- utils.logger.logger
- utils.logger.log_error
- utils.error_handler.ErrorHandler
- utils.error_handler.check_database_connection
- utils.error_handler.DatabaseError
- config.TABLES
- config.COLORS
- store_management.config.get_database_path
- store_management.database.base.DatabaseManager

### Classes:

#### SupplierView
Inherits from: ttk.Frame

Methods:
- handle_return(self, event)
  ```
  Handle Return key press
  ```
- handle_escape(self, event)
  ```
  Handle Escape key press
  ```
- show_search_dialog(self)
  ```
  Open dialog to search suppliers
  ```
- show_filter_dialog(self)
  ```
  Open dialog to filter suppliers
  ```
- save_table(self)
  ```
  Save the current table data to a file
  ```
- __init__(self, parent)
- setup_toolbar(self)
  ```
  Create the toolbar with all buttons
  ```
- setup_table(self)
  ```
  Create the main table view
  ```
- load_data(self)
  ```
  Load supplier data from the database and populate the treeview
  ```
- load_table(self)
  ```
  Alias for load_data method
  ```
- reset_view(self)
  ```
  Reset the view to show all suppliers
  ```
- show_add_dialog(self)
  ```
  Open dialog to add a new supplier
  ```
- delete_selected(self, event)
  ```
  Delete selected supplier(s)
  ```
- on_double_click(self, event)
  ```
  Handle double-click event for editing
  ```
- start_cell_edit(self, item, column)
  ```
  Start editing a cell
  ```
- undo(self)
  ```
  Undo last action
  ```
- redo(self)
  ```
  Redo last undone action
  ```
- sort_column(self, column)
  ```
  Sort tree contents when a column header is clicked
  ```

---

## gui\order\__init__.py

---

## gui\product\recipe_view.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- sqlalchemy.exc.SQLAlchemyError
- sqlalchemy.or_
- typing.Optional
- datetime.datetime
- store_management.database.sqlalchemy.models.Recipe
- store_management.database.sqlalchemy.models.RecipeItem
- store_management.database.sqlalchemy.models.Part
- store_management.database.sqlalchemy.models.Leather
- store_management.database.sqlalchemy.manager.DatabaseManagerSQLAlchemy

### Classes:

#### RecipeView
Inherits from: ttk.Frame

Methods:
- __init__(self, parent)
- create_ui(self)
  ```
  Create the user interface
  ```
- create_toolbar(self)
  ```
  Create the toolbar with action buttons
  ```
- create_main_content(self)
  ```
  Create both table views
  ```
- create_treeview(self, parent, columns, select_callback)
  ```
  Create a treeview with scrollbars
  ```
- create_status_bar(self)
  ```
  Create the status bar
  ```
- load_data(self)
  ```
  Load recipe data from database
  ```
- on_index_select(self, event)
  ```
  Handle selection in recipe index
  ```
- load_recipe_details(self, recipe_id)
  ```
  Load details for selected recipe
  ```
- show_add_recipe_dialog(self)
  ```
  Show dialog for adding new recipe
  ```
- show_add_item_dialog(self)
  ```
  Show dialog for adding item to recipe
  ```
- show_search_dialog(self)
  ```
  Show search dialog
  ```
- show_filter_dialog(self)
  ```
  Show filter dialog
  ```
- delete_selected(self, tree)
  ```
  Delete selected items
  ```
- undo(self, event)
  ```
  Undo last action
  ```
- redo(self, event)
  ```
  Redo last undone action
  ```
- sort_column(self, tree, col)
  ```
  Sort treeview column
  ```

---

## gui\product\storage_view.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- sqlalchemy.exc.SQLAlchemyError
- sqlalchemy.or_
- typing.Optional
- typing.Dict
- typing.Any
- uuid
- store_management.database.sqlalchemy.models.Storage
- store_management.database.sqlalchemy.models.Product
- store_management.database.sqlalchemy.models.Recipe
- store_management.database.sqlalchemy.manager.DatabaseManagerSQLAlchemy

### Classes:

#### StorageView
Inherits from: ttk.Frame

Methods:
- __init__(self, parent)
- setup_toolbar(self)
  ```
  Create the toolbar with all buttons
  ```
- setup_table(self)
  ```
  Create the main table view
  ```
- load_data(self)
  ```
  Load storage data using SQLAlchemy
  ```
- show_add_dialog(self)
  ```
  Show dialog for adding new storage item
  ```
- show_search_dialog(self)
  ```
  Show search dialog
  ```
- show_filter_dialog(self)
  ```
  Show filter dialog
  ```
- delete_selected(self, event)
  ```
  Delete selected storage items
  ```
- on_double_click(self, event)
  ```
  Handle double-click for cell editing
  ```
- start_cell_edit(self, item, column)
  ```
  Start editing a cell
  ```
- undo(self, event)
  ```
  Undo last action
  ```
- redo(self, event)
  ```
  Redo last undone action
  ```
- reset_view(self)
  ```
  Reset view to default state
  ```

---

## gui\product\__init__.py

---

## gui\reports\report_manager.py

---

## gui\reports\__init__.py

---

## gui\storage\sorting_system_view.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- typing.Dict
- typing.List
- typing.Optional
- pandas
- sqlalchemy.select
- sqlalchemy.orm.joinedload
- store_management.database.sqlalchemy.session.SessionLocal
- store_management.database.sqlalchemy.models.Storage
- store_management.database.sqlalchemy.models.Product
- store_management.gui.dialogs.add_dialog.AddDialog
- store_management.gui.dialogs.search_dialog.SearchDialog
- store_management.gui.dialogs.filter_dialog.FilterDialog
- store_management.utils.error_handler.handle_error
- store_management.utils.logger.log_action

### Classes:

#### SortingSystemView
Inherits from: ttk.Frame

Methods:
- __init__(self, parent, session_factory)
  ```
  Initialize the Sorting System View with SQLAlchemy integration

Args:
    parent (tk.Widget): Parent widget
    session_factory (callable): SQLAlchemy session factory
  ```
- setup_toolbar(self)
  ```
  Create the toolbar with all buttons
  ```
- setup_table(self)
  ```
  Create the main table view
  ```
- load_data(self)
  ```
  Load data from database into table
  ```
- get_warning_tag(self, amount, warning_threshold)
  ```
  Determine the warning level tag based on stock level

Args:
    amount (int): Current stock level
    warning_threshold (int): Warning threshold level

Returns:
    str: Warning tag level or empty string if no warning
  ```
- show_add_dialog(self)
  ```
  Show dialog for adding a new storage item
  ```
- save_new_item(self, data)
  ```
  Save a new storage item to the database

Args:
    data (Dict): Dictionary of item data
  ```
- generate_unique_id(self, name)
  ```
  Generate a unique product ID based on the name

Args:
    name (str): Product name

Returns:
    str: Generated unique ID
  ```
- on_double_click(self, event)
  ```
  Handle double-click event for cell editing

Args:
    event (tk.Event): Tkinter event object
  ```
- start_cell_edit(self, item, column)
  ```
  Start inline cell editing

Args:
    item (str): Treeview item identifier
    column (str): Column identifier
  ```
- delete_selected(self, event)
  ```
  Delete selected storage items
  ```
- undo(self)
  ```
  Undo the last action
  ```
- redo(self)
  ```
  Redo the last undone action
  ```

---

## gui\storage\storage_view.py

### Imports:
- tkinter
- tkinter.ttk
- tkinter.messagebox
- application.Application

### Classes:

#### StorageView
Inherits from: ttk.Frame
```
Storage view for managing storage locations
```

Methods:
- __init__(self, parent, app)
- setup_ui(self)
  ```
  Set up the UI components
  ```
- load_data(self)
  ```
  Load storage data from service
  ```
- show_add_dialog(self)
  ```
  Show dialog for adding a new storage location
  ```
- on_double_click(self, event)
  ```
  Handle double-click event
  ```
- start_cell_edit(self, item, column)
  ```
  Start editing a cell
  ```
- delete_selected(self, event)
  ```
  Delete selected storage locations
  ```
- show_search_dialog(self)
  ```
  Show search dialog
  ```

---

## gui\storage\__init__.py

---

## database\interfaces\base_repository.py

### Imports:
- typing.TypeVar
- typing.Generic
- typing.Optional
- typing.List
- typing.Dict
- typing.Any
- sqlalchemy.orm.Session
- models.base.Base

### Classes:

#### BaseRepository
```
Generic base repository implementing common database operations.

Type parameter T must be a SQLAlchemy model class.
```

Methods:
- __init__(self, session, model_class)
  ```
  Initialize the repository with a session and model class.

Args:
    session: SQLAlchemy session
    model_class: Model class this repository handles
  ```
- get(self, id)
  ```
  Get a single record by ID.

Args:
    id: Primary key value

Returns:
    Model instance if found, None otherwise
  ```
- get_all(self)
  ```
  Get all records.

Returns:
    List of all model instances
  ```
- create(self)
  ```
  Create a new record.

Args:
    **kwargs: Model attributes

Returns:
    Created model instance
  ```
- update(self, id)
  ```
  Update a record by ID.

Args:
    id: Primary key value
    **kwargs: Attributes to update

Returns:
    Updated model instance or None if not found
  ```
- delete(self, id)
  ```
  Delete a record by ID.

Args:
    id: Primary key value

Returns:
    True if deleted, False if not found
  ```
- filter_by(self)
  ```
  Get records matching the given criteria.

Args:
    **kwargs: Filter criteria

Returns:
    List of matching model instances
  ```
- exists(self)
  ```
  Check if a record exists with the given criteria.

Args:
    **kwargs: Filter criteria

Returns:
    True if exists, False otherwise
  ```

### Global Variables:
- T

---

## database\interfaces\__init__.py

---

## database\models\base.py

### Imports:
- sqlalchemy.ext.declarative.declarative_base

### Global Variables:
- Base

---

## database\models\enums.py

### Imports:
- enum.Enum

### Classes:

#### InventoryStatus
Inherits from: Enum

#### ProductionStatus
Inherits from: Enum

#### TransactionType
Inherits from: Enum

#### OrderStatus
Inherits from: Enum

#### PaymentStatus
Inherits from: Enum

---

## database\models\leather.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.ForeignKey
- sqlalchemy.Enum
- sqlalchemy.orm.relationship
- base.Base
- enums.InventoryStatus

### Classes:

#### Leather
Inherits from: Base
```
Leather model
```

Methods:
- __repr__(self)

---

## database\models\order.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.ForeignKey
- sqlalchemy.Enum
- sqlalchemy.orm.relationship
- base.Base
- enums.OrderStatus
- enums.PaymentStatus

### Classes:

#### Order
Inherits from: Base
```
Purchase order model
```

Methods:
- __repr__(self)

#### OrderItem
Inherits from: Base
```
Items in a purchase order
```

Methods:
- __repr__(self)

---

## database\models\part.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.ForeignKey
- sqlalchemy.Enum
- sqlalchemy.orm.relationship
- base.Base
- enums.InventoryStatus

### Classes:

#### Part
Inherits from: Base
```
Part model
```

Methods:
- __repr__(self)

---

## database\models\prdouct.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.ForeignKey
- sqlalchemy.orm.relationship
- base.Base

### Classes:

#### Product
Inherits from: Base
```
Product model
```

Methods:
- __repr__(self)

---

## database\models\recipe.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.ForeignKey
- sqlalchemy.orm.relationship
- base.Base

### Classes:

#### Recipe
Inherits from: Base
```
Recipe model for manufacturing products
```

Methods:
- __repr__(self)

#### RecipeItem
Inherits from: Base
```
Items required for a recipe
```

Methods:
- __repr__(self)

---

## database\models\shopping_list.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.ForeignKey
- sqlalchemy.Boolean
- sqlalchemy.orm.relationship
- base.Base

### Classes:

#### ShoppingList
Inherits from: Base
```
Shopping list model
```

Methods:
- __repr__(self)

#### ShoppingListItem
Inherits from: Base
```
Shopping list item model
```

Methods:
- __repr__(self)

---

## database\models\storage.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.orm.relationship
- base.Base

### Classes:

#### Storage
Inherits from: Base
```
Storage location model
```

Methods:
- __repr__(self)

---

## database\models\supplier.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.orm.relationship
- base.Base

### Classes:

#### Supplier
Inherits from: Base
```
Supplier model
```

Methods:
- __repr__(self)

---

## database\models\transaction.py

### Imports:
- datetime.datetime
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.Float
- sqlalchemy.DateTime
- sqlalchemy.ForeignKey
- sqlalchemy.Enum
- sqlalchemy.orm.relationship
- base.Base
- enums.TransactionType

### Classes:

#### InventoryTransaction
Inherits from: Base
```
Transaction for part inventory changes
```

Methods:
- __repr__(self)

#### LeatherTransaction
Inherits from: Base
```
Transaction for leather inventory changes
```

Methods:
- __repr__(self)

---

## database\models\__init__.py

### Imports:
- base.Base
- enums.InventoryStatus
- enums.ProductionStatus
- enums.TransactionType
- enums.OrderStatus
- enums.PaymentStatus
- storage.Storage
- product.Product
- supplier.Supplier
- part.Part
- leather.Leather
- recipe.Recipe
- recipe.RecipeItem
- order.Order
- order.OrderItem
- shopping_list.ShoppingList
- shopping_list.ShoppingListItem
- transaction.InventoryTransaction
- transaction.LeatherTransaction

---

## database\repositories\leather_repository.py

### Imports:
- typing.List
- typing.Optional
- sqlalchemy.orm.Session
- sqlalchemy.orm.joinedload
- interfaces.base_repository.BaseRepository
- models.leather.Leather
- models.enums.InventoryStatus

### Classes:

#### LeatherRepository
```
Repository for Leather model operations
```

Methods:
- __init__(self, session)
- get_low_stock(self)
  ```
  Get leathers with low stock levels.

Returns:
    List of leathers with low stock
  ```
- get_by_supplier(self, supplier_id)
  ```
  Get leathers by supplier.

Args:
    supplier_id: Supplier ID

Returns:
    List of leathers from the specified supplier
  ```
- get_with_transactions(self, leather_id)
  ```
  Get leather with transaction history.

Args:
    leather_id: Leather ID

Returns:
    Leather with loaded transactions or None
  ```

---

## database\repositories\order_repository.py

### Imports:
- typing.List
- typing.Optional
- datetime.datetime
- sqlalchemy.orm.Session
- sqlalchemy.orm.joinedload
- interfaces.base_repository.BaseRepository
- models.order.Order
- models.order.OrderItem
- models.enums.OrderStatus

### Classes:

#### OrderRepository
```
Repository for Order model operations
```

Methods:
- __init__(self, session)
- get_with_items(self, order_id)
  ```
  Get order with all items.

Args:
    order_id: Order ID

Returns:
    Order with loaded items or None
  ```
- get_by_status(self, status)
  ```
  Get orders by status.

Args:
    status: Order status

Returns:
    List of orders with the specified status
  ```
- get_by_date_range(self, start_date, end_date)
  ```
  Get orders within a date range.

Args:
    start_date: Start date
    end_date: End date

Returns:
    List of orders within the date range
  ```
- get_by_supplier(self, supplier_id)
  ```
  Get orders for a supplier.

Args:
    supplier_id: Supplier ID

Returns:
    List of orders for the supplier
  ```

---

## database\repositories\part_repository.py

### Imports:
- typing.List
- typing.Optional
- sqlalchemy.orm.Session
- sqlalchemy.orm.joinedload
- interfaces.base_repository.BaseRepository
- models.part.Part
- models.enums.InventoryStatus

### Classes:

#### PartRepository
```
Repository for Part model operations
```

Methods:
- __init__(self, session)
- get_low_stock(self)
  ```
  Get parts with low stock levels.

Returns:
    List of parts with low stock
  ```
- get_by_supplier(self, supplier_id)
  ```
  Get parts by supplier.

Args:
    supplier_id: Supplier ID

Returns:
    List of parts from the specified supplier
  ```
- get_with_transactions(self, part_id)
  ```
  Get part with transaction history.

Args:
    part_id: Part ID

Returns:
    Part with loaded transactions or None
  ```

---

## database\repositories\product_repository.py

### Imports:
- typing.List
- typing.Optional
- sqlalchemy.orm.Session
- interfaces.base_repository.BaseRepository
- models.product.Product

### Classes:

#### ProductRepository
```
Repository for Product model operations
```

Methods:
- __init__(self, session)
- get_by_storage(self, storage_id)
  ```
  Get products by storage location.

Args:
    storage_id: Storage location ID

Returns:
    List of products in the specified storage
  ```
- search_by_name(self, name)
  ```
  Search products by name.

Args:
    name: Product name to search for

Returns:
    List of matching products
  ```

---

## database\repositories\recipe_repository.py

### Imports:
- typing.List
- typing.Optional
- typing.Tuple
- sqlalchemy.orm.Session
- sqlalchemy.orm.joinedload
- interfaces.base_repository.BaseRepository
- models.recipe.Recipe
- models.recipe.RecipeItem

### Classes:

#### RecipeRepository
```
Repository for Recipe model operations
```

Methods:
- __init__(self, session)
- get_with_items(self, recipe_id)
  ```
  Get recipe with all items.

Args:
    recipe_id: Recipe ID

Returns:
    Recipe with loaded items or None
  ```
- get_by_product(self, product_id)
  ```
  Get recipes for a product.

Args:
    product_id: Product ID

Returns:
    List of recipes for the product
  ```
- get_recipe_item(self, item_id)
  ```
  Get a specific recipe item.

Args:
    item_id: Recipe item ID

Returns:
    Recipe item or None
  ```
- add_recipe_item(self, recipe_id, item_data)
  ```
  Add an item to a recipe.

Args:
    recipe_id: Recipe ID
    item_data: Item data

Returns:
    Created recipe item
  ```

---

## database\repositories\shopping_list_repository.py

### Imports:
- typing.List
- typing.Optional
- sqlalchemy.orm.Session
- sqlalchemy.orm.joinedload
- interfaces.base_repository.BaseRepository
- models.shopping_list.ShoppingList
- models.shopping_list.ShoppingListItem

### Classes:

#### ShoppingListRepository
```
Repository for ShoppingList model operations
```

Methods:
- __init__(self, session)
- get_with_items(self, list_id)
  ```
  Get shopping list with all items.

Args:
    list_id: Shopping list ID

Returns:
    Shopping list with loaded items or None
  ```
- get_pending_items(self)
  ```
  Get all unpurchased shopping list items.

Returns:
    List of unpurchased shopping list items
  ```
- get_items_by_supplier(self, supplier_id)
  ```
  Get shopping list items for a supplier.

This is more complex as it needs to join through the part or leather
to find items for a supplier.

Args:
    supplier_id: Supplier ID

Returns:
    List of shopping list items for the supplier
  ```

---

## database\repositories\storage_repository.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- sqlalchemy.orm.Session
- sqlalchemy.select
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.storage.Storage
- store_management.database.sqlalchemy.manager_factory.register_specialized_manager

### Classes:

#### StorageRepository
```
Specialized repository for Storage model with additional methods.

Provides storage-specific operations beyond standard CRUD methods.
```

Methods:
- get_by_location(self, location)
  ```
  Retrieve a storage location by its specific location.

Args:
    location: The location identifier

Returns:
    Storage instance if found, None otherwise
  ```
- get_available_storage(self)
  ```
  Retrieve all available storage locations.

Returns:
    List of available storage locations
  ```
- get_storage_with_details(self, storage_id)
  ```
  Get detailed information about a storage location.

Args:
    storage_id: ID of the storage location

Returns:
    Dictionary with storage details, or None if not found
  ```
- search_storage(self, search_term)
  ```
  Search storage locations by location or description.

Args:
    search_term: Term to search for

Returns:
    List of matching storage locations
  ```

### Functions:

#### get_storage_repository(session)
```
Backward-compatible method to get a storage repository.

Args:
    session: Optional SQLAlchemy session (for backward compatibility)

Returns:
    StorageRepository instance
```

---

## database\repositories\supplier_repository.py

### Imports:
- typing.List
- typing.Optional
- sqlalchemy.orm.Session
- sqlalchemy.orm.joinedload
- interfaces.base_repository.BaseRepository
- models.supplier.Supplier

### Classes:

#### SupplierRepository
```
Repository for Supplier model operations
```

Methods:
- __init__(self, session)
- get_with_products(self, supplier_id)
  ```
  Get supplier with eagerly loaded products.

Args:
    supplier_id: Supplier ID

Returns:
    Supplier with products if found, None otherwise
  ```
- search(self, term)
  ```
  Search suppliers by name or contact name.

Args:
    term: Search term

Returns:
    List of matching suppliers
  ```

---

## database\repositories\__init__.py

---

## database\scripts\run_migration.py

### Imports:
- sqlalchemy.create_engine
- store_management.database.sqlalchemy.models.Base
- store_management.database.sqlalchemy.session.DATABASE_URL

### Functions:

#### initialize_database()
```
Initialize the database with all tables.
```

---

## database\scripts\__init__.py

---

## database\sqlalchemy\base.py

### Imports:
- sqlalchemy.ext.declarative.declarative_base

### Global Variables:
- Base

---

## database\sqlalchemy\base_manager.py

### Imports:
- typing.TypeVar
- typing.Generic
- typing.Type
- typing.List
- typing.Dict
- typing.Any
- typing.Optional
- typing.Callable
- typing.Union
- typing.Type
- sqlalchemy.orm.Session
- sqlalchemy.select
- sqlalchemy.inspect
- sqlalchemy.exc.SQLAlchemyError
- mixins.base_mixins.SearchMixin
- mixins.base_mixins.FilterMixin
- mixins.base_mixins.PaginationMixin
- mixins.base_mixins.TransactionMixin
- utils.error_handling.DatabaseError

### Classes:

#### BaseManager
Inherits from: SearchMixin, FilterMixin, PaginationMixin, TransactionMixin
```
Comprehensive base manager for database operations.

Provides a generic, type-safe implementation of common database 
operations with support for mixins and extensive error handling.
```

Methods:
- __init__(self, model_class, session_factory, mixins)
  ```
  Initialize the base manager with a model class and session factory.

Args:
    model_class: The SQLAlchemy model class this manager operates on
    session_factory: A callable that returns a database session
    mixins: Optional list of additional mixin classes to apply
  ```
- _apply_mixins(self, mixins)
  ```
  Dynamically apply additional mixins to the manager.

Args:
    mixins: List of mixin classes to apply
  ```
- create(self, data)
  ```
  Create a new record in the database.

Args:
    data: Dictionary of attributes for the new record

Returns:
    The created record

Raises:
    DatabaseError: If creation fails
  ```
- get(self, id)
  ```
  Retrieve a record by its primary key.

Args:
    id: Primary key value

Returns:
    The record if found, None otherwise

Raises:
    DatabaseError: If retrieval fails
  ```
- get_all(self, order_by, limit)
  ```
  Retrieve all records, with optional ordering and limit.

Args:
    order_by: Optional column to order by
    limit: Optional maximum number of records to return

Returns:
    List of records

Raises:
    DatabaseError: If retrieval fails
  ```
- update(self, id, data)
  ```
  Update an existing record.

Args:
    id: Primary key of the record to update
    data: Dictionary of attributes to update

Returns:
    The updated record, or None if not found

Raises:
    DatabaseError: If update fails
  ```
- delete(self, id)
  ```
  Delete a record by its primary key.

Args:
    id: Primary key of the record to delete

Returns:
    True if deletion was successful, False if record not found

Raises:
    DatabaseError: If deletion fails
  ```
- bulk_create(self, items)
  ```
  Bulk create multiple records in a single transaction.

Args:
    items: List of dictionaries with record data

Returns:
    List of created records

Raises:
    DatabaseError: If bulk creation fails
  ```

### Global Variables:
- T

---

## database\sqlalchemy\config.py

### Imports:
- os
- typing.Dict
- typing.Any
- sqlalchemy.create_engine
- sqlalchemy.text
- sqlalchemy.orm.sessionmaker
- sqlalchemy.orm.scoped_session
- sqlalchemy.orm.Session
- sqlalchemy_utils.database_exists
- sqlalchemy_utils.create_database
- pathlib.Path

### Classes:

#### DatabaseConfig
```
Centralized database configuration management with singleton pattern
```

Methods:
- __new__(cls)
- _initialize(self)
  ```
  Initialize database configuration with comprehensive setup
  ```
- _find_project_root(self)
  ```
  Dynamically find the project root directory

Returns:
    Path: Project root directory
  ```
- _load_config(self)
  ```
  Load database configuration with environment variable precedence

Returns:
    Dict[str, Any]: Configured database settings
  ```
- _get_database_url(self)
  ```
  Generate database URL based on configuration

Returns:
    str: Fully qualified database connection URL
  ```
- _create_engine(self)
  ```
  Create SQLAlchemy engine with comprehensive configuration

Returns:
    Engine: Configured SQLAlchemy engine
  ```
- _create_session_factory(self)
  ```
  Create thread-local scoped session factory

Returns:
    scoped_session: Configured session factory
  ```
- get_session(self)
  ```
  Get a database session

Returns:
    Session: Active database session
  ```
- close_session(self)
  ```
  Close all sessions and remove session factory
  ```
- test_connection(self)
  ```
  Test database connection

Returns:
    bool: True if connection successful, False otherwise
  ```
- get_database_url(self)
  ```
  Public method to retrieve database URL

Returns:
    str: Database connection URL
  ```

### Functions:

#### get_database_url()
```
Function to get the database URL for direct import

Returns:
    str: Database connection URL
```

#### get_database_path()
```
Get the absolute path to the database file

Returns:
    Path: Absolute path to the database file
```

### Global Variables:
- database_config
- __all__

---

## database\sqlalchemy\manager.py

### Imports:
- models.Base
- contextlib.contextmanager
- typing.Optional
- typing.List
- typing.Dict
- typing.Any
- typing.Type
- typing.Union
- sqlalchemy.orm.Session
- sqlalchemy.orm.sessionmaker
- sqlalchemy.exc.SQLAlchemyError
- sqlalchemy.create_engine
- sqlalchemy.inspect
- sqlalchemy.or_
- sqlalchemy.select
- sqlalchemy.delete
- datetime.datetime
- .models

### Classes:

#### DatabaseError
Inherits from: Exception
```
Custom database error for SQLAlchemy operations
```

#### BaseManager
```
Base manager class with common session and logging methods
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize base manager with session factory

Args:
    session_factory: SQLAlchemy session factory
  ```
- session_scope(self)
  ```
  Provide a transactional scope around a series of operations

Yields:
    SQLAlchemy Session
  ```

#### DatabaseManagerSQLAlchemy
```
Comprehensive database manager using SQLAlchemy ORM
```

Methods:
- __init__(self, database_url)
  ```
  Initialize database manager with database URL

Args:
    database_url (str): SQLAlchemy database connection URL
  ```
- session(self)
  ```
  Get current session or create a new one

Returns:
    SQLAlchemy Session
  ```
- session_scope(self)
  ```
  Provide a transactional scope around a series of operations

Yields:
    SQLAlchemy Session
  ```
- get_model_columns(self, model)
  ```
  Get column names for a specific model

Args:
    model (Type[models.Base]): SQLAlchemy model class

Returns:
    List of column names
  ```
- add_record(self, model, data)
  ```
  Add a new record to the database

Args:
    model (Type[models.Base]): Model class
    data (Dict[str, Any]): Record data

Returns:
    Newly created record or None
  ```
- update_record(self, model, record_id, data)
  ```
  Update an existing record

Args:
    model (Type[Base]): Model class
    record_id (int): Record ID
    data (Dict[str, Any]): Updated data

Returns:
    Updated record or None
  ```
- delete_record(self, model, record_id)
  ```
  Delete a record from the database

Args:
    model (Type[Base]): Model class
    record_id (int): Record ID

Returns:
    Boolean indicating success
  ```
- get_record(self, model, record_id)
  ```
  Get a single record by ID

Args:
    model (Type[Base]): Model class
    record_id (int): Record ID

Returns:
    Record or None
  ```
- get_all_records(self, model)
  ```
  Get all records of a model, optionally filtered

Args:
    model (Type[Base]): Model class
    **filters: Optional filter conditions

Returns:
    List of records
  ```
- search_records(self, model, search_term)
  ```
  Search for records across specified fields

Args:
    model (Type[Base]): Model class
    search_term (str): Term to search for
    *fields: Fields to search in

Returns:
    List of matching records
  ```
- bulk_update(self, model, updates)
  ```
  Perform bulk updates on records

Args:
    model (Type[Base]): Model class
    updates (List[Dict]): List of update dictionaries

Returns:
    Boolean indicating success
  ```
- execute_query(self, query, params)
  ```
  Execute a raw SQL query

Args:
    query (str): SQL query string
    params (Optional[tuple]): Query parameters

Returns:
    List of query results
  ```

---

## database\sqlalchemy\manager_factory.py

### Imports:
- typing.Type
- typing.Dict
- typing.Any
- typing.TypeVar
- typing.Optional
- typing.Callable
- typing.Union
- typing.List
- sqlalchemy.orm.Session
- base_manager.BaseManager
- session.get_db_session

### Functions:

#### register_specialized_manager(model_class, manager_class)
```
Register a specialized manager for a specific model class.

Args:
    model_class: The SQLAlchemy model class
    manager_class: The specialized manager class to use for this model
```

#### get_manager(model_class, session_factory, mixins, force_new)
```
Get or create a manager for the specified model class.

This factory ensures only one manager is created per model class,
with support for specialized managers and optional mixins.

Args:
    model_class: The SQLAlchemy model class
    session_factory: Optional custom session factory (defaults to get_db_session)
    mixins: Optional list of additional mixins to apply
    force_new: If True, create a new manager instance

Returns:
    A BaseManager instance for the model class
```

#### clear_manager_cache()
```
Clear the manager instance cache.

Useful for testing or resetting the application state.
```

### Global Variables:
- T

---

## database\sqlalchemy\migration.py

### Imports:
- os
- sys
- logging
- datetime.datetime
- typing.Optional
- sqlalchemy.create_engine
- sqlalchemy.inspect
- sqlalchemy.orm.sessionmaker
- store_management.database.sqlalchemy.models.Base

### Classes:

#### DatabaseInitializer
```
Comprehensive database initialization and migration utility
```

Methods:
- __init__(self, db_url, backup_dir)
  ```
  Initialize database initialization process

Args:
    db_url (str): SQLAlchemy database URL
    backup_dir (str, optional): Directory for database backups
  ```
- create_backup(self)
  ```
  Create a backup of the existing database if it exists

Returns:
    Optional[str]: Path to the backup file, or None if no backup created
  ```
- drop_all_tables(self)
  ```
  Drop all existing tables in the database
  ```
- initialize_database(self)
  ```
  Complete database initialization process

1. Create backup of existing database
2. Drop all existing tables
3. Create new tables based on current model definitions
  ```

### Functions:

#### run_database_initialization(db_url, backup_dir, force)
```
Execute database initialization

Args:
    db_url (str, optional): SQLAlchemy database URL
    backup_dir (str, optional): Directory for database backups
    force (bool, optional): Force initialization even if database exists

Returns:
    bool: Initialization success status
```

### Global Variables:
- project_root
- logger

---

## database\sqlalchemy\models.py

### Imports:
- enum.Enum
- enum.auto

### Classes:

#### InventoryStatus
Inherits from: Enum
```
Inventory status for parts and materials.
```

#### OrderStatus
Inherits from: Enum
```
Order processing status.
```

#### PaymentStatus
Inherits from: Enum
```
Payment processing status.
```

#### TransactionType
Inherits from: Enum
```
Types of inventory transactions.
```

#### ProductionStatus
Inherits from: Enum
```
Status of production processes.
```

---

## database\sqlalchemy\model_utils.py

### Functions:

#### get_model_classes()
```
Dynamically import and return a dictionary of model classes.

Returns:
    Dict of model names to their corresponding classes
```

---

## database\sqlalchemy\session.py

### Imports:
- contextlib.contextmanager
- sqlalchemy.create_engine
- sqlalchemy.orm.sessionmaker
- sqlalchemy.orm.scoped_session
- sqlalchemy_utils.database_exists
- sqlalchemy_utils.create_database
- store_management.database.sqlalchemy.models.base.Base
- store_management.utils.logger.logger
- os
- typing.Optional

### Functions:

#### init_database()
```
Initialize database if it doesn't exist
```

#### get_db_session()
```
Provide a transactional scope around database operations.

Usage:
    with get_db_session() as session:
        # Perform database operations
        session.add(some_object)

Yields:
    SQLAlchemy Session object
```

#### get_session()
```
Create and return a new database session for compatibility with existing code.

Note: This function is provided for backward compatibility.
New code should use get_db_session() context manager instead.

Returns:
    SQLAlchemy Session object
```

### Global Variables:
- DATABASE_URL
- engine
- session_factory
- SessionLocal

---

## database\sqlalchemy\__init__.py

### Imports:
- base.Base
- models.Storage
- models.Product
- models.Recipe
- models.RecipeItem
- models.Supplier
- models.Part
- models.Leather
- models.ShoppingList
- models.ShoppingListItem
- models.Order
- models.OrderItem
- models.InventoryStatus
- models.ProductionStatus
- models.TransactionType
- models.OrderStatus
- models.PaymentStatus

### Global Variables:
- __all__

---

## database\sqlalchemy\managers\incoming_goods_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- datetime.datetime
- store_management.database.sqlalchemy.models.Order
- store_management.database.sqlalchemy.models.OrderDetail
- store_management.database.sqlalchemy.models.Supplier
- store_management.database.sqlalchemy.models.Storage
- store_management.database.sqlalchemy.models.Product
- store_management.database.sqlalchemy.models.order.OrderStatus
- store_management.database.sqlalchemy.models.order.PaymentStatus
- store_management.database.sqlalchemy.session.get_session

### Classes:

#### IncomingGoodsManager

Methods:
- __init__(self)
- create_order(self, data)
  ```
  Create a new order
  ```
- get_all_orders(self)
  ```
  Get all orders
  ```
- get_order_by_id(self, order_id)
  ```
  Get an order by its ID
  ```
- get_order_by_number(self, order_number)
  ```
  Get an order by its order number
  ```
- update_order(self, order_id, data)
  ```
  Update an order
  ```
- delete_order(self, order_id)
  ```
  Delete an order
  ```
- add_order_detail(self, order_id, data)
  ```
  Add a detail to an order
  ```
- get_order_details(self, order_id)
  ```
  Get all details for an order
  ```
- update_order_detail(self, detail_id, data)
  ```
  Update an order detail
  ```
- delete_order_detail(self, detail_id)
  ```
  Delete an order detail
  ```
- get_suppliers(self)
  ```
  Get a list of supplier names
  ```
- update_inventory(self, unique_id, amount, is_shelf)
  ```
  Update inventory for a product
  ```

---

## database\sqlalchemy\managers\inventory_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Union
- typing.Tuple
- datetime.datetime
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.func
- sqlalchemy.orm.joinedload
- sqlalchemy.exc.SQLAlchemyError
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.Part
- store_management.database.sqlalchemy.models.Leather
- store_management.database.sqlalchemy.models.InventoryTransaction
- store_management.database.sqlalchemy.models.LeatherTransaction
- store_management.database.sqlalchemy.models.InventoryStatus
- store_management.database.sqlalchemy.models.TransactionType
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### InventoryManager
```
Comprehensive inventory manager handling both Part and Leather inventory.
Uses separate BaseManager instances for each model type.
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize inventory managers with session factory.
  ```
- add_part(self, data)
  ```
  Add a new part to inventory.

Args:
    data: Part data including initial stock levels

Returns:
    Created Part instance
  ```
- add_leather(self, data)
  ```
  Add a new leather to inventory.

Args:
    data: Leather data including initial area

Returns:
    Created Leather instance
  ```
- update_part_stock(self, part_id, quantity_change, transaction_type, notes)
  ```
  Update part stock levels with transaction tracking.

Args:
    part_id: Part ID
    quantity_change: Change in quantity (positive or negative)
    transaction_type: Type of transaction
    notes: Optional transaction notes

Returns:
    Updated Part instance
  ```
- update_leather_stock(self, leather_id, area_change, transaction_type, notes)
  ```
  Update leather stock levels with transaction tracking.

Args:
    leather_id: Leather ID
    area_change: Change in area (positive or negative)
    transaction_type: Type of transaction
    notes: Optional transaction notes

Returns:
    Updated Leather instance
  ```
- get_part_with_transactions(self, part_id)
  ```
  Get part with its transaction history.

Args:
    part_id: Part ID

Returns:
    Part instance with transactions loaded or None if not found
  ```
- get_leather_with_transactions(self, leather_id)
  ```
  Get leather with its transaction history.

Args:
    leather_id: Leather ID

Returns:
    Leather instance with transactions loaded or None if not found
  ```
- get_low_stock_parts(self, include_out_of_stock)
  ```
  Get all parts with low stock levels.

Args:
    include_out_of_stock: Whether to include out of stock items

Returns:
    List of Part instances with low stock
  ```
- get_low_stock_leather(self, include_out_of_stock)
  ```
  Get all leather with low stock levels.

Args:
    include_out_of_stock: Whether to include out of stock items

Returns:
    List of Leather instances with low stock
  ```
- get_inventory_transactions(self, part_id, leather_id, start_date, end_date)
  ```
  Get inventory transactions with optional filtering.

Args:
    part_id: Optional Part ID to filter by
    leather_id: Optional Leather ID to filter by
    start_date: Optional start date for date range
    end_date: Optional end date for date range

Returns:
    List of transaction instances
  ```
- get_inventory_value(self)
  ```
  Calculate total value of inventory.

Returns:
    Dictionary with total values for parts and leather
  ```
- search_inventory(self, search_term)
  ```
  Search both parts and leather inventory.

Args:
    search_term: Term to search for

Returns:
    Dictionary with matching parts and leather items
  ```
- adjust_min_stock_levels(self, part_id, new_min_level)
  ```
  Adjust minimum stock level for a part.

Args:
    part_id: Part ID
    new_min_level: New minimum stock level

Returns:
    Updated Part instance
  ```
- adjust_min_leather_area(self, leather_id, new_min_area)
  ```
  Adjust minimum area for a leather type.

Args:
    leather_id: Leather ID
    new_min_area: New minimum area in square feet

Returns:
    Updated Leather instance
  ```
- get_inventory_summary(self)
  ```
  Get comprehensive inventory summary including counts and values.

Returns:
    Dictionary containing inventory summary statistics
  ```
- bulk_update_parts(self, updates)
  ```
  Update multiple parts in a single transaction.

Args:
    updates: List of dictionaries containing part updates

Returns:
    Number of parts updated
  ```
- bulk_update_leather(self, updates)
  ```
  Update multiple leather items in a single transaction.

Args:
    updates: List of dictionaries containing leather updates

Returns:
    Number of leather items updated
  ```
- get_transaction_history(self, start_date, end_date, transaction_type)
  ```
  Get transaction history with optional filtering.

Args:
    start_date: Optional start date for filtering
    end_date: Optional end date for filtering
    transaction_type: Optional transaction type filter

Returns:
    Dictionary containing part and leather transactions
  ```
- get_part_stock_history(self, part_id, days)
  ```
  Get stock level history for a part.

Args:
    part_id: Part ID
    days: Optional number of days to look back

Returns:
    List of stock level changes with timestamps
  ```
- get_leather_stock_history(self, leather_id, days)
  ```
  Get stock level history for a leather item.

Args:
    leather_id: Leather ID
    days: Optional number of days to look back

Returns:
    List of stock level changes with timestamps
  ```
- get_reorder_suggestions(self)
  ```
  Get suggestions for items that need reordering.

Returns:
    Dictionary containing parts and leather that need reordering
  ```

---

## database\sqlalchemy\managers\leather_inventory_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Tuple
- datetime.datetime
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.func
- sqlalchemy.case
- sqlalchemy.orm.joinedload
- sqlalchemy.exc.SQLAlchemyError
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.Leather
- store_management.database.sqlalchemy.models.LeatherTransaction
- store_management.database.sqlalchemy.models.Supplier
- store_management.database.sqlalchemy.models.TransactionType
- store_management.database.sqlalchemy.models.InventoryStatus
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### LeatherInventoryManager
```
Specialized manager for leather inventory operations with area tracking.
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize LeatherInventoryManager with session factory.
  ```
- add_leather(self, data)
  ```
  Add new leather to inventory with initial area tracking.

Args:
    data: Leather data including initial area and supplier

Returns:
    Created Leather instance

Raises:
    DatabaseError: If validation fails or database operation fails
  ```
- update_leather_area(self, leather_id, area_change, transaction_type, notes, wastage)
  ```
  Update leather area with transaction tracking and wastage calculation.

Args:
    leather_id: Leather ID
    area_change: Change in area (negative for consumption)
    transaction_type: Type of transaction
    notes: Optional transaction notes
    wastage: Optional wastage area to track

Returns:
    Tuple of (updated Leather instance, created Transaction)

Raises:
    DatabaseError: If update fails or would result in negative area
  ```
- get_leather_with_transactions(self, leather_id, include_wastage)
  ```
  Get leather details with transaction history and optional wastage analysis.

Args:
    leather_id: Leather ID
    include_wastage: Whether to include wastage calculations

Returns:
    Dictionary with leather details and transaction history
  ```
- get_low_stock_leather(self, include_out_of_stock, supplier_id)
  ```
  Get leather items with low stock levels.

Args:
    include_out_of_stock: Whether to include out of stock items
    supplier_id: Optional supplier ID to filter by

Returns:
    List of Leather instances with low stock
  ```
- calculate_leather_efficiency(self, leather_id, date_range)
  ```
  Calculate leather usage efficiency metrics.

Args:
    leather_id: Leather ID
    date_range: Optional tuple of (start_date, end_date)

Returns:
    Dictionary containing efficiency metrics
  ```
- adjust_minimum_area(self, leather_id, new_minimum)
  ```
  Adjust minimum area threshold for a leather type.

Args:
    leather_id: Leather ID
    new_minimum: New minimum area threshold

Returns:
    Updated Leather instance
  ```

---

## database\sqlalchemy\managers\order_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Union
- datetime.datetime
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.orm.joinedload
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.Order
- store_management.database.sqlalchemy.models.OrderItem
- store_management.database.sqlalchemy.models.Part
- store_management.database.sqlalchemy.models.Leather
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### OrderManager
```
Enhanced order manager implementing specialized order operations
while leveraging base manager functionality.
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize OrderManager with session factory.
  ```
- create_order(self, order_data, items)
  ```
  Create a new order with items.

Args:
    order_data: Dictionary containing order data
    items: List of dictionaries containing order item data

Returns:
    Created Order instance

Raises:
    DatabaseError: If validation fails or database operation fails
  ```
- get_order_with_items(self, order_id)
  ```
  Get order with all its items.

Args:
    order_id: Order ID

Returns:
    Order instance with items loaded or None if not found
  ```
- update_order_status(self, order_id, status)
  ```
  Update order status with proper validation.

Args:
    order_id: Order ID
    status: New status

Returns:
    Updated Order instance or None if not found
  ```
- add_order_items(self, order_id, items)
  ```
  Add items to an existing order.

Args:
    order_id: Order ID
    items: List of dictionaries containing item data

Returns:
    Updated Order instance

Raises:
    DatabaseError: If order not found or validation fails
  ```
- remove_order_item(self, order_id, item_id)
  ```
  Remove an item from an order.

Args:
    order_id: Order ID
    item_id: Order Item ID

Returns:
    True if item was removed, False otherwise
  ```
- search_orders(self, search_term)
  ```
  Search orders by various fields.

Args:
    search_term: Term to search for

Returns:
    List of matching Order instances
  ```
- get_orders_by_date_range(self, start_date, end_date)
  ```
  Get orders within a date range.

Args:
    start_date: Start date
    end_date: End date

Returns:
    List of Order instances within the date range
  ```
- get_supplier_orders(self, supplier_id)
  ```
  Get all orders for a specific supplier.

Args:
    supplier_id: Supplier ID

Returns:
    List of Order instances for the supplier
  ```
- calculate_order_total(self, order_id)
  ```
  Calculate total value of an order.

Args:
    order_id: Order ID

Returns:
    Total order value

Raises:
    DatabaseError: If order not found
  ```

---

## database\sqlalchemy\managers\production_order_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Tuple
- datetime.datetime
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.func
- sqlalchemy.orm.joinedload
- sqlalchemy.exc.SQLAlchemyError
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.ProductionOrder
- store_management.database.sqlalchemy.models.Recipe
- store_management.database.sqlalchemy.models.ProducedItem
- store_management.database.sqlalchemy.models.InventoryTransaction
- store_management.database.sqlalchemy.models.LeatherTransaction
- store_management.database.sqlalchemy.models.ProductionStatus
- store_management.database.sqlalchemy.models.TransactionType
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### ProductionOrderManager
```
Enhanced manager for production orders with recipe relationships.
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize ProductionOrderManager with session factory.
  ```
- create_production_order(self, recipe_id, quantity, start_date, notes)
  ```
  Create a new production order with recipe validation.

Args:
    recipe_id: Recipe ID to produce
    quantity: Number of items to produce
    start_date: Optional planned start date
    notes: Optional production notes

Returns:
    Created ProductionOrder instance

Raises:
    DatabaseError: If recipe not found or validation fails
  ```
- start_production(self, order_id, operator_notes)
  ```
  Start a production order and reserve materials.

Args:
    order_id: Production order ID
    operator_notes: Optional notes from operator

Returns:
    Updated ProductionOrder instance
  ```
- _reserve_materials(self, session, order)
  ```
  Reserve materials for production through transactions.

Args:
    session: Database session
    order: ProductionOrder instance with loaded recipe
  ```
- complete_item(self, order_id, serial_number, quality_check_passed, notes)
  ```
  Record completion of a single produced item.

Args:
    order_id: Production order ID
    serial_number: Unique serial number for item
    quality_check_passed: Whether item passed quality check
    notes: Optional production notes

Returns:
    Created ProducedItem instance
  ```
- get_production_status(self, order_id)
  ```
  Get detailed production status including material usage.

Args:
    order_id: Production order ID

Returns:
    Dictionary containing status details and metrics
  ```
- get_active_orders(self)
  ```
  Get all active production orders with their recipes.

Returns:
    List of ProductionOrder instances with loaded relationships
  ```
- get_production_metrics(self, start_date, end_date)
  ```
  Get production metrics for a date range.

Args:
    start_date: Optional start date for filtering
    end_date: Optional end date for filtering

Returns:
    Dictionary containing production metrics
  ```

---

## database\sqlalchemy\managers\recipe_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Tuple
- datetime.datetime
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.orm.joinedload
- sqlalchemy.exc.SQLAlchemyError
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.Recipe
- store_management.database.sqlalchemy.models.RecipeItem
- store_management.database.sqlalchemy.models.Part
- store_management.database.sqlalchemy.models.Leather
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### RecipeManager
```
Recipe manager implementing specialized recipe operations
while leveraging base manager functionality.
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize RecipeManager with session factory.
  ```
- create_recipe(self, recipe_data, items)
  ```
  Create a new recipe with items.

Args:
    recipe_data: Dictionary containing recipe data
    items: List of dictionaries containing recipe item data

Returns:
    Created Recipe instance

Raises:
    DatabaseError: If validation fails or database operation fails
  ```
- get_recipe_with_items(self, recipe_id)
  ```
  Get recipe with all its items.

Args:
    recipe_id: Recipe ID

Returns:
    Recipe instance with items loaded or None if not found
  ```
- update_recipe_items(self, recipe_id, items)
  ```
  Update recipe items (replace existing items).

Args:
    recipe_id: Recipe ID
    items: New list of recipe items

Returns:
    Updated Recipe instance

Raises:
    DatabaseError: If recipe not found or validation fails
  ```
- add_recipe_item(self, recipe_id, item_data)
  ```
  Add a single item to a recipe.

Args:
    recipe_id: Recipe ID
    item_data: Dictionary containing item data

Returns:
    Created RecipeItem instance
  ```
- remove_recipe_item(self, recipe_id, item_id)
  ```
  Remove an item from a recipe.

Args:
    recipe_id: Recipe ID
    item_id: Recipe Item ID

Returns:
    True if item was removed, False otherwise
  ```
- update_recipe_item_quantity(self, recipe_id, item_id, quantity)
  ```
  Update the quantity of a recipe item.

Args:
    recipe_id: Recipe ID
    item_id: Recipe Item ID
    quantity: New quantity

Returns:
    Updated RecipeItem instance
  ```
- check_materials_availability(self, recipe_id, quantity)
  ```
  Check if all materials for a recipe are available in sufficient quantity.

Args:
    recipe_id: Recipe ID
    quantity: Number of items to produce

Returns:
    Tuple of (bool, list of missing items)
  ```
- get_recipes_by_type(self, recipe_type)
  ```
  Get all recipes of a specific type.

Args:
    recipe_type: Type of recipe to filter by

Returns:
    List of matching Recipe instances
  ```
- get_recipes_by_collection(self, collection)
  ```
  Get all recipes in a specific collection.

Args:
    collection: Collection name

Returns:
    List of matching Recipe instances
  ```
- search_recipes(self, search_term)
  ```
  Search recipes by various fields.

Args:
    search_term: Term to search for

Returns:
    List of matching Recipe instances
  ```
- duplicate_recipe(self, recipe_id, new_name)
  ```
  Create a duplicate of an existing recipe.

Args:
    recipe_id: Source recipe ID
    new_name: Name for the new recipe

Returns:
    New Recipe instance
  ```
- calculate_recipe_cost(self, recipe_id)
  ```
  Calculate the total cost of materials for a recipe.

Args:
    recipe_id: Recipe ID

Returns:
    Total cost of all materials
  ```

---

## database\sqlalchemy\managers\report_manager.py

### Imports:
- sqlalchemy.func
- sqlalchemy.and_
- sqlalchemy.orm.Session
- pandas
- datetime.datetime
- pdfkit
- typing.List
- typing.Dict
- typing.Any
- typing.Optional
- tkinter
- tkinter.ttk
- tkinter.messagebox
- datetime.datetime
- typing.Dict
- typing.Any

### Classes:

#### ReportManager
Inherits from: BaseManager

Methods:
- __init__(self, session)
- generate_report(self, report_type, filters)
  ```
  Generate a report based on type and optional filters.
  ```
- generate_inventory_report(self, filters)
  ```
  Generate inventory report with current stock levels.
  ```
- generate_products_report(self, filters)
  ```
  Generate products report with recipe relationships.
  ```
- generate_low_stock_report(self, filters)
  ```
  Generate report for items with stock below warning threshold.
  ```
- generate_recipe_usage_report(self, filters)
  ```
  Generate report showing recipe usage in products.
  ```
- export_to_csv(self, df, filename)
  ```
  Export report to CSV format.
  ```
- export_to_excel(self, df, filename)
  ```
  Export report to Excel format with formatting.
  ```
- export_to_pdf(self, df, filename)
  ```
  Export report to PDF format via HTML conversion.
  ```

#### ReportDialog
Inherits from: BaseDialog

Methods:
- __init__(self, parent, title)
- setup_ui(self)
  ```
  Setup the report dialog UI components.
  ```
- on_report_type_change(self, event)
  ```
  Update filters based on selected report type.
  ```
- _add_filter(self, name, label, widget_type)
  ```
  Add a filter widget to the filters frame.
  ```
- get_filters(self)
  ```
  Get current filter values.
  ```
- generate_report(self)
  ```
  Generate and export the selected report.
  ```

---

## database\sqlalchemy\managers\shopping_list_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Union
- typing.Tuple
- datetime.datetime
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.func
- sqlalchemy.orm.joinedload
- sqlalchemy.exc.SQLAlchemyError
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.ShoppingList
- store_management.database.sqlalchemy.models.ShoppingListItem
- store_management.database.sqlalchemy.models.Part
- store_management.database.sqlalchemy.models.Leather
- store_management.database.sqlalchemy.models.Supplier
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### ShoppingListManager
```
Manager for handling shopping list operations and related functionality.
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize ShoppingListManager with session factory.
  ```
- create_shopping_list(self, data, items)
  ```
  Create a new shopping list with optional items.

Args:
    data: Shopping list data (name, description, etc.)
    items: Optional list of shopping list items

Returns:
    Created ShoppingList instance

Raises:
    DatabaseError: If validation fails or database operation fails
  ```
- get_shopping_list_with_items(self, list_id)
  ```
  Get shopping list with all its items.

Args:
    list_id: Shopping list ID

Returns:
    ShoppingList instance with items loaded or None if not found
  ```
- add_shopping_list_item(self, list_id, item_data)
  ```
  Add an item to a shopping list.

Args:
    list_id: Shopping list ID
    item_data: Item data including quantity and supplier

Returns:
    Created ShoppingListItem instance
  ```
- update_shopping_list_status(self, list_id, status)
  ```
  Update shopping list status.

Args:
    list_id: Shopping list ID
    status: New status

Returns:
    Updated ShoppingList instance or None if not found
  ```
- mark_item_purchased(self, list_id, item_id, purchase_data)
  ```
  Mark a shopping list item as purchased.

Args:
    list_id: Shopping list ID
    item_id: Shopping list item ID
    purchase_data: Purchase details including date and price

Returns:
    Updated ShoppingListItem instance or None if not found
  ```
- get_pending_items(self)
  ```
  Get all pending (unpurchased) items across all shopping lists.

Returns:
    List of unpurchased ShoppingListItem instances
  ```
- get_items_by_supplier(self, supplier_id)
  ```
  Get all shopping list items for a specific supplier.

Args:
    supplier_id: Supplier ID

Returns:
    List of ShoppingListItem instances for the supplier
  ```
- get_shopping_list_summary(self, list_id)
  ```
  Get summary statistics for a shopping list.

Args:
    list_id: Shopping list ID

Returns:
    Dictionary containing summary statistics
  ```
- search_shopping_lists(self, search_term)
  ```
  Search shopping lists across name and description.

Args:
    search_term: Term to search for

Returns:
    List of matching ShoppingList instances
  ```
- filter_shopping_lists(self, status, priority, date_range)
  ```
  Filter shopping lists based on various criteria.

Args:
    status: Optional status filter
    priority: Optional priority filter
    date_range: Optional tuple of (start_date, end_date)

Returns:
    List of filtered ShoppingList instances
  ```
- bulk_update_items(self, updates, list_id)
  ```
  Bulk update shopping list items.

Args:
    updates: List of dictionaries containing item updates
    list_id: Optional shopping list ID to restrict updates to

Returns:
    Number of items updated
  ```
- merge_shopping_lists(self, source_ids, target_id)
  ```
  Merge multiple shopping lists into a target list.

Args:
    source_ids: List of source shopping list IDs
    target_id: Target shopping list ID

Returns:
    Updated target ShoppingList instance

Raises:
    DatabaseError: If any list is not found or merge fails
  ```
- get_overdue_items(self)
  ```
  Get all overdue items from active shopping lists.

Returns:
    List of overdue ShoppingListItem instances
  ```

---

## database\sqlalchemy\managers\storage_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Union
- datetime.datetime
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.func
- sqlalchemy.orm.joinedload
- sqlalchemy.exc.SQLAlchemyError
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.Storage
- store_management.database.sqlalchemy.models.Product
- store_management.database.sqlalchemy.models.Leather
- store_management.database.sqlalchemy.models.Part
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### StorageManager
Inherits from: BaseManager
```
Enhanced storage manager implementing specialized storage operations.
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize storage manager with session factory.

Args:
    session_factory: Function to create database sessions
  ```
- get_all_storage_locations(self)
  ```
  Retrieve all storage locations.

Returns:
    List[Storage]: List of all storage locations
  ```
- add_storage_location(self, data)
  ```
  Add a new storage location.

Args:
    data: Dictionary containing storage location data
        Required keys:
        - location: str
        - capacity: float
        Optional keys:
        - description: str
        - status: str

Returns:
    Optional[Storage]: Added storage location or None if failed

Raises:
    DatabaseError: If validation fails or database operation fails
  ```
- update_storage_location(self, location_id, data)
  ```
  Update a storage location.

Args:
    location_id: ID of storage location to update
    data: Dictionary containing update data

Returns:
    Optional[Storage]: Updated storage location or None if not found

Raises:
    DatabaseError: If validation fails or database operation fails
  ```
- delete_storage_location(self, location_id)
  ```
  Delete a storage location.

Args:
    location_id: ID of storage location to delete

Returns:
    bool: True if deleted, False if not found

Raises:
    DatabaseError: If deletion fails or has dependent records
  ```
- get_storage_with_items(self, storage_id)
  ```
  Get storage location with all associated items.

Args:
    storage_id: ID of storage location

Returns:
    Optional[Storage]: Storage with items loaded or None if not found
  ```
- get_available_storage(self)
  ```
  Get storage locations with available capacity.

Returns:
    List[Storage]: List of storage locations with space available
  ```
- search_storage(self, term)
  ```
  Search storage locations by location or description.

Args:
    term: Search term

Returns:
    List[Storage]: List of matching storage locations
  ```
- get_storage_status(self, storage_id)
  ```
  Get detailed status of a storage location.

Args:
    storage_id: ID of storage location

Returns:
    Dict containing:
    - total_capacity: float
    - used_capacity: float
    - available_capacity: float
    - item_count: int
    - last_modified: datetime
  ```
- get_storage_utilization(self)
  ```
  Get utilization metrics for all storage locations.

Returns:
    List of dictionaries containing utilization metrics for each location
  ```
- bulk_update_storage(self, updates)
  ```
  Update multiple storage locations in bulk.

Args:
    updates: List of dictionaries containing:
        - id: Storage location ID
        - updates: Dictionary of fields to update

Returns:
    int: Number of storage locations updated
  ```

---

## database\sqlalchemy\managers\supplier_manager.py

### Imports:
- typing.List
- typing.Optional
- typing.Dict
- typing.Any
- typing.Tuple
- datetime.datetime
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.func
- sqlalchemy.orm.joinedload
- sqlalchemy.exc.SQLAlchemyError
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.database.sqlalchemy.models.Supplier
- store_management.database.sqlalchemy.models.Order
- store_management.database.sqlalchemy.models.Part
- store_management.database.sqlalchemy.models.Leather
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### SupplierManager
```
Manager for handling supplier operations and relationships.
Includes supplier performance tracking and order history management.
```

Methods:
- __init__(self, session_factory)
  ```
  Initialize SupplierManager with session factory.
  ```
- create_supplier(self, data)
  ```
  Create a new supplier with validation.

Args:
    data: Supplier data including contact information

Returns:
    Created Supplier instance

Raises:
    DatabaseError: If validation fails
  ```
- update_supplier(self, supplier_id, data)
  ```
  Update supplier information.

Args:
    supplier_id: Supplier ID
    data: Updated supplier data

Returns:
    Updated Supplier instance or None if not found
  ```
- get_supplier_with_orders(self, supplier_id)
  ```
  Get supplier with their order history.

Args:
    supplier_id: Supplier ID

Returns:
    Supplier instance with orders loaded or None if not found
  ```
- get_supplier_products(self, supplier_id)
  ```
  Get all products supplied by a supplier.

Args:
    supplier_id: Supplier ID

Returns:
    Dictionary containing parts and leather supplied
  ```
- get_supplier_performance(self, supplier_id)
  ```
  Calculate supplier performance metrics.

Args:
    supplier_id: Supplier ID

Returns:
    Dictionary containing performance metrics
  ```
- update_supplier_rating(self, supplier_id, rating, notes)
  ```
  Update supplier quality rating.

Args:
    supplier_id: Supplier ID
    rating: New rating (0-5)
    notes: Optional notes about the rating

Returns:
    Updated Supplier instance
  ```
- get_supplier_order_history(self, supplier_id, start_date, end_date)
  ```
  Get supplier's order history with optional date range.

Args:
    supplier_id: Supplier ID
    start_date: Optional start date
    end_date: Optional end date

Returns:
    List of Order instances
  ```
- get_top_suppliers(self, limit)
  ```
  Get top suppliers based on order volume and performance.

Args:
    limit: Number of suppliers to return

Returns:
    List of supplier data with performance metrics
  ```
- get_supplier_categories(self, supplier_id)
  ```
  Get categories of products supplied by a supplier.

Args:
    supplier_id: Supplier ID

Returns:
    List of unique product categories
  ```
- search_suppliers(self, search_term)
  ```
  Search suppliers across multiple fields.

Args:
    search_term: Term to search for

Returns:
    List of matching Supplier instances
  ```
- get_supplier_statistics(self)
  ```
  Get overall supplier statistics.

Returns:
    Dictionary containing supplier statistics
  ```

---

## database\sqlalchemy\managers\__init__.py

---

## database\sqlalchemy\migrations\manager.py

### Imports:
- typing.List
- typing.Optional
- logging
- pathlib.Path
- datetime.datetime
- alembic.config
- alembic.command
- alembic.script.ScriptDirectory
- alembic.runtime.migration.MigrationContext
- sqlalchemy.create_engine
- sqlalchemy.inspect
- store_management.database.sqlalchemy.base_manager.BaseManager
- store_management.utils.error_handler.DatabaseError
- store_management.utils.logger.logger

### Classes:

#### MigrationManager
```
Handles database migrations and schema updates.
```

Methods:
- __init__(self, database_url, migrations_path)
  ```
  Initialize migration manager.

Args:
    database_url: Database connection URL
    migrations_path: Optional custom path to migrations directory
  ```
- _create_alembic_config(self)
  ```
  Create Alembic configuration.
  ```
- check_current_version(self)
  ```
  Get current database version.

Returns:
    Current revision identifier
  ```
- get_pending_migrations(self)
  ```
  Get list of pending migrations.

Returns:
    List of pending migration identifiers
  ```
- create_backup(self)
  ```
  Create database backup before migration.

Returns:
    Path to backup file
  ```
- run_migrations(self, target)
  ```
  Run pending migrations.

Args:
    target: Target revision (defaults to latest)
  ```
- revert_migration(self, revision)
  ```
  Revert to a specific migration.

Args:
    revision: Target revision to revert to
  ```
- verify_migration(self)
  ```
  Verify database schema matches models.

Returns:
    True if verification passes
  ```

---

## database\sqlalchemy\migrations\migration_manager.py

### Imports:
- os
- sys
- logging.config.fileConfig
- typing.Optional
- typing.Union
- sqlalchemy.engine_from_config
- sqlalchemy.pool
- sqlalchemy.engine.Connection
- sqlalchemy.ext.declarative.DeclarativeMeta
- alembic.context

### Classes:

#### MigrationCLI

Methods:
- create_migration(message)
  ```
  Create a new database migration

Args:
    message (str): Description of migration changes
  ```
- upgrade(revision)
  ```
  Upgrade database to specific or latest revision

Args:
    revision (str, optional): Target migration revision. Defaults to 'head'.
  ```
- downgrade(revision)
  ```
  Downgrade database to previous migration

Args:
    revision (str, optional): Target migration revision. Defaults to previous migration.
  ```

#### MigrationTracker

Methods:
- get_current_version()
  ```
  Get current database migration version

Returns:
    str: Current migration revision
  ```

### Functions:

#### get_base_metadata()

#### run_migrations_offline(config, target_metadata)
```
Run migrations in 'offline' mode.
```

#### run_migrations_online(config, target_metadata)
```
Run migrations in 'online' mode.
```

#### main(config_file)
```
Run database migrations with advanced configuration options.

Args:
    config_file (Optional[str]): Path to Alembic configuration file.
```

### Global Variables:
- project_root

---

## database\sqlalchemy\migrations\__init__.py

---

## database\sqlalchemy\mixins\base_mixins.py

### Imports:
- typing.TypeVar
- typing.Generic
- typing.Type
- typing.List
- typing.Dict
- typing.Any
- typing.Optional
- typing.Callable
- typing.Union
- sqlalchemy.orm.Session
- sqlalchemy.select
- sqlalchemy.or_
- sqlalchemy.and_
- sqlalchemy.func
- sqlalchemy.sql.expression.ColumnElement

### Classes:

#### BaseMixin
```
Base mixin providing core functionality for database managers.

This mixin serves as a foundational class for other database-related mixins,
providing common initialization and type safety.
```

Methods:
- __init__(self, model_class, session_factory)
  ```
  Initialize the base mixin with a model class and session factory.

Args:
    model_class: The SQLAlchemy model class this mixin operates on
    session_factory: A callable that returns a database session
  ```

#### SearchMixin
```
Advanced search functionality for database managers.

Provides comprehensive search capabilities across multiple fields
with flexible configuration.
```

Methods:
- search(self, search_term, fields)
  ```
  Perform a comprehensive search across multiple fields.

Args:
    search_term: The term to search for
    fields: Optional list of fields to search.
            If None, uses all string columns.

Returns:
    List of matching records
  ```
- advanced_search(self, criteria)
  ```
  Perform an advanced search with multiple criteria.

Args:
    criteria: Dictionary of field-operator-value criteria
    Example: {
        'name': {'op': 'like', 'value': '%Widget%'},
        'stock_level': {'op': 'gt', 'value': 10}
    }

Returns:
    List of matching records
  ```

#### FilterMixin
```
Advanced filtering capabilities for database managers.

Provides methods for complex, flexible filtering of database records.
```

Methods:
- filter_by_multiple(self, filters)
  ```
  Filter records by multiple exact match criteria.

Args:
    filters: Dictionary of field-value pairs

Returns:
    List of matching records
  ```
- filter_with_or(self, filters)
  ```
  Filter records with OR conditions for each field.

Args:
    filters: Dictionary of field-values pairs where values is a list
    Example: {'status': ['NEW', 'PENDING']}

Returns:
    List of matching records
  ```
- filter_complex(self, conditions, join_type)
  ```
  Execute a complex filter with custom conditions.

Args:
    conditions: List of condition dictionaries
    join_type: How to join conditions ('and' or 'or')

Returns:
    List of matching records
  ```

#### PaginationMixin
```
Pagination support for database managers.

Provides methods for retrieving paginated results with
optional filtering and ordering.
```

Methods:
- get_paginated(self, page, page_size, order_by, filters)
  ```
  Get paginated results with optional ordering and filtering.

Args:
    page: Page number (1-based)
    page_size: Number of records per page
    order_by: Optional column to order by
    filters: Optional filtering criteria

Returns:
    Pagination result dictionary
  ```

#### TransactionMixin
```
Transaction handling mixin for database managers.

Provides methods for running operations within database transactions
with robust error handling.
```

Methods:
- run_in_transaction(self, operation)
  ```
  Execute an operation within a database transaction.

Args:
    operation: Function to execute within the transaction
    *args: Positional arguments for the operation
    **kwargs: Keyword arguments for the operation

Returns:
    Result of the operation

Raises:
    Exception: If the transaction fails
  ```
- execute_with_result(self, operation)
  ```
  Execute an operation in a transaction and return a standard result.

Args:
    operation: Function to execute
    *args: Arguments for the operation
    **kwargs: Keyword arguments for the operation

Returns:
    Dictionary with operation result
  ```

### Global Variables:
- T

---

## database\sqlalchemy\mixins\filter_mixin.py

### Imports:
- typing.List
- typing.Optional
- typing.Type
- typing.Any
- typing.Dict
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.or_
- sqlalchemy.func
- store_management.database.sqlalchemy.models.base.Base
- store_management.database.sqlalchemy.session.get_db_session

### Classes:

#### FilterMixin
```
Mixin providing advanced filtering functionality for managers.

This mixin expects the class to have:
- model_class attribute (SQLAlchemy model class)
```

Methods:
- filter_by_multiple(self, filters)
  ```
  Filter records by multiple criteria (AND condition).

Args:
    filters: Dictionary of field-value pairs

Returns:
    List of matching records
  ```
- filter_with_or(self, filters)
  ```
  Filter records with OR conditions for each field.

Args:
    filters: Dictionary of field-values pairs where values is a list
        Example: {'status': ['NEW', 'PENDING']}

Returns:
    List of matching records
  ```
- filter_complex(self, conditions, join_type)
  ```
  Execute a complex filter with custom conditions.

Args:
    conditions: List of condition dictionaries
        Example: [
            {'field': 'status', 'op': 'eq', 'value': 'NEW'},
            {'field': 'price', 'op': 'gt', 'value': 100}
        ]
    join_type: How to join conditions ('and' or 'or')

Returns:
    List of matching records
  ```

---

## database\sqlalchemy\mixins\paginated_query_mixin.py

### Imports:
- typing.List
- typing.Dict
- typing.Any
- typing.Optional
- typing.Tuple
- sqlalchemy.select
- sqlalchemy.func
- store_management.database.sqlalchemy.session.get_db_session

### Classes:

#### PaginatedQueryMixin
```
Mixin providing pagination functionality for managers.

This mixin expects the class to have:
- model_class attribute (SQLAlchemy model class)
```

Methods:
- get_paginated(self, page, page_size, order_by, filters)
  ```
  Get records with pagination.

Args:
    page: Page number (1-based)
    page_size: Number of records per page
    order_by: Optional column to order by
    filters: Optional filtering criteria

Returns:
    Dictionary containing pagination info and results:
    {
        'items': List of records,
        'page': Current page number,
        'page_size': Number of records per page,
        'total_items': Total number of records,
        'total_pages': Total number of pages
    }
  ```

---

## database\sqlalchemy\mixins\search_mixin.py

### Imports:
- typing.List
- typing.Optional
- typing.Type
- typing.Any
- typing.Dict
- sqlalchemy.select
- sqlalchemy.or_
- sqlalchemy.func
- store_management.database.sqlalchemy.models.base.Base
- store_management.database.sqlalchemy.session.get_db_session

### Classes:

#### SearchMixin
```
Mixin providing advanced search functionality for managers.

This mixin expects the class to have:
- model_class attribute (SQLAlchemy model class)
```

Methods:
- search(self, search_term, fields)
  ```
  Search for records across multiple fields.

Args:
    search_term: Term to search for
    fields: Optional list of fields to search in (defaults to all string fields)

Returns:
    List of matching records
  ```
- advanced_search(self, criteria)
  ```
  Perform an advanced search with multiple criteria.

Args:
    criteria: Dictionary of field-operator-value criteria
        Example: {'name': {'op': 'like', 'value': '%Widget%'},
                  'stock_level': {'op': 'gt', 'value': 10}}

Returns:
    List of matching records
  ```

---

## database\sqlalchemy\mixins\test_mixin.py

### Imports:
- pytest
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.create_engine
- sqlalchemy.orm.declarative_base
- sqlalchemy.orm.sessionmaker
- typing.Dict
- typing.Any
- typing.List
- store_management.database.sqlalchemy.mixins.base_mixins.BaseMixin
- store_management.database.sqlalchemy.mixins.base_mixins.SearchMixin
- store_management.database.sqlalchemy.mixins.base_mixins.FilterMixin
- store_management.database.sqlalchemy.mixins.base_mixins.PaginationMixin
- store_management.database.sqlalchemy.mixins.base_mixins.TransactionMixin

### Classes:

#### TestModel
Inherits from: TestBase
```
Test model for mixin testing.
```

#### TestModelManager
Inherits from: SearchMixin, FilterMixin, PaginationMixin, TransactionMixin
```
Test manager combining all mixins.
```

Methods:
- __init__(self, model_class, session_factory)

#### TestSearchMixin
```
Test suite for SearchMixin functionality.
```

Methods:
- test_basic_search(self, test_manager, sample_data)
  ```
  Test basic search across all string fields.
  ```
- test_advanced_search(self, test_manager, sample_data)
  ```
  Test advanced search with multiple criteria.
  ```

#### TestFilterMixin
```
Test suite for FilterMixin functionality.
```

Methods:
- test_filter_by_multiple(self, test_manager, sample_data)
  ```
  Test filtering by multiple exact match criteria.
  ```
- test_filter_with_or(self, test_manager, sample_data)
  ```
  Test filtering with OR conditions.
  ```
- test_filter_complex(self, test_manager, sample_data)
  ```
  Test complex filtering with multiple conditions.
  ```

#### TestPaginationMixin
```
Test suite for PaginationMixin functionality.
```

Methods:
- test_pagination_basic(self, test_manager, session_factory)
  ```
  Test basic pagination functionality.
  ```
- test_pagination_with_filters(self, test_manager, sample_data)
  ```
  Test pagination with filtering.
  ```

#### TestTransactionMixin
```
Test suite for TransactionMixin functionality.
```

Methods:
- test_run_in_transaction_success(self, test_manager)
  ```
  Test successful transaction.
  ```
- test_run_in_transaction_rollback(self, test_manager)
  ```
  Test transaction rollback on error.
  ```
- test_execute_with_result(self, test_manager)
  ```
  Test execute_with_result method.
  ```

### Functions:

#### test_engine()
```
Create an in-memory SQLite database for testing.
```

#### session_factory(test_engine)
```
Create a session factory for testing.
```

#### test_manager(session_factory)
```
Create a test manager instance.
```

#### sample_data(test_manager)
```
Populate test database with sample data.
```

### Global Variables:
- TestBase

---

## database\sqlalchemy\mixins\test_mixin_perormance.py

### Imports:
- pytest
- time
- sqlalchemy.Column
- sqlalchemy.Integer
- sqlalchemy.String
- sqlalchemy.create_engine
- sqlalchemy.select
- sqlalchemy.and_
- sqlalchemy.orm.declarative_base
- sqlalchemy.orm.sessionmaker
- typing.List
- typing.Dict
- typing.Any
- store_management.database.sqlalchemy.mixins.base_mixins.SearchMixin
- store_management.database.sqlalchemy.mixins.base_mixins.FilterMixin
- store_management.database.sqlalchemy.mixins.base_mixins.PaginationMixin

### Classes:

#### PerformanceTestModel
Inherits from: TestBase
```
Large test model for performance benchmarking.
```

#### PerformanceTestManager
Inherits from: SearchMixin, FilterMixin, PaginationMixin
```
Performance test manager combining mixins.
```

Methods:
- __init__(self, model_class, session_factory)

#### TestMixinPerformance
```
Performance benchmarking for database mixins.
```

Methods:
- test_search_performance(self, performance_manager, large_dataset)
  ```
  Benchmark search performance.
  ```
- test_advanced_search_performance(self, performance_manager, large_dataset)
  ```
  Benchmark advanced search performance.
  ```
- test_filter_performance(self, performance_manager, large_dataset)
  ```
  Benchmark filtering performance.
  ```
- test_pagination_performance(self, performance_manager, large_dataset)
  ```
  Benchmark pagination performance.
  ```
- test_complex_filter_performance(self, performance_manager, large_dataset)
  ```
  Benchmark complex filtering performance.
  ```
- test_native_sqlalchemy_performance_comparison(self, performance_manager, large_dataset)
  ```
  Compare mixin performance with native SQLAlchemy query.
  ```

### Functions:

#### test_engine()
```
Create an in-memory SQLite database for performance testing.
```

#### session_factory(test_engine)
```
Create a session factory for performance testing.
```

#### performance_manager(session_factory)
```
Create a performance test manager instance.
```

#### large_dataset(performance_manager)
```
Populate test database with a large dataset.
```

### Global Variables:
- TestBase

---

## database\sqlalchemy\mixins\transaction_mixin.py

### Imports:
- typing.Optional
- typing.Dict
- typing.Any
- typing.Type
- typing.TypeVar
- typing.Generic
- typing.Callable
- contextlib.contextmanager
- store_management.database.sqlalchemy.session.get_db_session

### Classes:

#### TransactionMixin
```
Mixin providing transaction handling for complex operations.

This mixin provides methods to run operations in transactions and handle errors.
```

Methods:
- run_in_transaction(self)
  ```
  Run operations in a transaction with error handling.

Usage:
    with self.run_in_transaction() as session:
        # Perform operations

Yields:
    SQLAlchemy session
  ```
- execute_with_result(self, operation)
  ```
  Execute an operation in a transaction and return a standard result.

Args:
    operation: Function to execute
    *args: Arguments for the operation
    **kwargs: Keyword arguments for the operation

Returns:
    Dictionary with operation result:
    {
        'success': True/False,
        'data': Result data (if successful),
        'error': Error message (if failed)
    }
  ```

### Global Variables:
- T

---

## database\sqlalchemy\mixins\__init__.py

### Imports:
- base_mixins.BaseMixin
- base_mixins.SearchMixin
- base_mixins.FilterMixin
- base_mixins.PaginationMixin
- base_mixins.TransactionMixin

### Global Variables:
- __all__

---

## database\sqlalchemy\migrations\versions\202402201_add_relationships.py

### Imports:
- alembic.op
- sqlalchemy
- datetime.datetime
- sqlalchemy.dialects.sqlite
- store_management.database.sqlalchemy.models.InventoryStatus
- store_management.database.sqlalchemy.models.ProductionStatus

### Functions:

#### upgrade()

#### downgrade()

### Global Variables:
- revision
- down_revision
- branch_labels
- depends_on

---

## database\sqlalchemy\migrations\versions\463698485_comprehensive_model_relationships.py

### Imports:
- alembic.op
- sqlalchemy
- sqlalchemy.dialects.sqlite
- enum.Enum
- store_management.database.sqlalchemy.models.InventoryStatus
- store_management.database.sqlalchemy.models.ProductionStatus
- store_management.database.sqlalchemy.models.TransactionType

### Functions:

#### upgrade()

#### downgrade()

---

## database\sqlalchemy\migrations\versions\__init__.py

---
