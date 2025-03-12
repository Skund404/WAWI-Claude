# Documentation for the Leatherworking Application GUI

## Root Folder (`gui/`)

### Purpose
The root folder contains the main application files that initialize and configure the GUI application. These files serve as the entry point for the application and provide global configurations.

### Files
- `__init__.py`: Package initialization file that exports version information and key components
- `app.py`: Application entry point that initializes the UI, sets up dependency injection, and starts the main loop
- `main_window.py`: Main application window implementation with navigation and layout structure
- `config.py`: Application-wide configuration settings including window sizes, pagination options, and formats
- `theme.py`: Centralized styling definitions including colors, fonts, and widget styles

### Usage
The main application is started by running `app.py`, which initializes all necessary components:

```python
from gui.app import main

if __name__ == "__main__":
    main()
```

### Key Components
- `LeatherworkingApp`: Main application class that orchestrates initialization and UI setup
- `MainWindow`: Central UI container that manages views and navigation
- Application-wide styling and configuration through `theme.py` and `config.py`

### Guidelines
- All new views should be registered in `main_window.py` to appear in the navigation
- Use theme constants from `theme.py` for consistent styling
- Configuration parameters should be centralized in `config.py`

## Base Folder (`gui/base/`)

### Purpose
The base folder contains abstract base classes that define common functionality and structure for UI components. These classes provide the foundation for creating consistent views and forms throughout the application.

### Files
- `base_view.py`: Abstract view class that all view components inherit from
- `base_list_view.py`: Base class for list views with filtering, pagination, and CRUD operations
- `base_form_view.py`: Base class for data entry forms with validation and service integration
- `base_dialog.py`: Base class for modal dialogs with standardized layout and behavior
- `service_connector.py`: Utility for accessing services via dependency injection

### Usage
To create a new view, inherit from the appropriate base class:

```python
from gui.base.base_list_view import BaseListView

class CustomerListView(BaseListView):
    def __init__(self, parent):
        super().__init__(parent)
        self.title = "Customers"
        self.service_name = "ICustomerService"
        self.columns = [
            ("id", "ID", 50),
            ("name", "Name", 200),
            ("email", "Email", 250),
            ("status", "Status", 100)
        ]
        self.search_fields = [
            {"name": "name", "label": "Name", "type": "text"},
            {"name": "email", "label": "Email", "type": "text"},
            {"name": "status", "label": "Status", "type": "select",
             "options": ["ACTIVE", "INACTIVE"]}
        ]
```

### Key Components
- `BaseView`: Provides service access, error handling, and basic view structure
- `BaseListView`: Implements filtering, pagination, and standard CRUD operations
- `BaseFormView`: Implements field generation, validation, and form submission
- `FormField`: Configuration class for form fields

### Guidelines
- Always inherit from the appropriate base class when creating new views
- Override methods like `extract_item_values()` for custom data handling
- Use the provided error handling methods for consistent error presentation

## Widgets Folder (`gui/widgets/`)

### Purpose
The widgets folder contains specialized custom widgets that extend standard Tkinter widgets with additional functionality. These widgets provide consistent styling and enhanced features used throughout the application.

### Files
- `enhanced_treeview.py`: Extended treeview with sorting, filtering, and improved styling
- `enum_combobox.py`: Combobox specialized for selecting enum values
- `search_frame.py`: Reusable search interface for filtering list views
- `status_badge.py`: Visual indicator for status values

### Usage
These widgets can be used directly in views:

```python
from gui.widgets.enum_combobox import EnumCombobox
from database.models.enums import ProjectStatus

# Create an enum combobox for project status
status_var = tk.StringVar()
status_combo = EnumCombobox(
    parent_frame,
    enum_class=ProjectStatus,
    textvariable=status_var,
    width=20
)
status_combo.pack(padx=5, pady=5)
```

### Key Components
- `EnhancedTreeview`: Core list display component with sorting and styling
- `EnumCombobox`: Specialized combobox for enum handling
- `StatusBadge`: Visual indicator for status values
- `SearchFrame`: Configurable search interface

### Guidelines
- Use these widgets instead of standard Tkinter widgets when applicable
- Follow the widget API conventions for consistent behavior
- Consult theme settings when creating new widgets to maintain style consistency

## Utils Folder (`gui/utils/`)

### Purpose
The utils folder contains utility functions and classes that support the GUI application. These utilities handle cross-cutting concerns such as logging, service access, and event handling.

### Files
- `service_access.py`: Utilities for accessing services through dependency injection
- `gui_logger.py`: Configuration and utilities for GUI-specific logging
- `event_bus.py`: Event system for communication between UI components

### Usage
The utilities can be imported and used throughout the application:

```python
from gui.utils.service_access import get_service
from gui.utils.event_bus import subscribe, publish

# Access a service
inventory_service = get_service("IInventoryService")

# Subscribe to an event
subscribe("inventory_updated", self.refresh_inventory)

# Publish an event
publish("inventory_updated", {"item_id": 123})
```

### Key Components
- Service access functions for dependency injection
- Event bus for publish-subscribe communication
- Logging configuration specialized for GUI needs

### Guidelines
- Use `get_service()` for accessing services instead of direct DI when needed
- Use the event bus for loose coupling between components
- Configure logging through `setup_gui_logger()` to ensure consistent logging

## Views Folder (`gui/views/`)

### Purpose
The views folder contains the actual view implementations organized by functional area. Each subfolder represents a different module of the application with specific views for that domain.

### Subfolders
- `dashboard/`: Main dashboard views
- `inventory/`: Inventory management views
- `materials/`: Material management views
- `projects/`: Project management views
- `patterns/`: Pattern management views
- `sales/`: Sales and customer management views
- `purchases/`: Purchase order and supplier management views
- `products/`: Product catalog views
- `reports/`: Reporting and analytics views

### Structure
Each view module follows a consistent pattern:
- List views for displaying collections of items
- Detail views for editing individual items
- Specialized views for domain-specific operations

### Guidelines
- Organize views by functional domain in appropriate subfolders
- Follow naming conventions: `*_list_view.py`, `*_details_view.py`
- Reuse base classes and widgets for consistency
- Use service access through dependency injection

## Dialogs Folder (`gui/dialogs/`)

### Purpose
The dialogs folder contains reusable dialog implementations for common operations throughout the application. These dialogs provide consistent user interaction patterns for frequent tasks.

### Files
- `add_dialog.py`: Generic dialog for adding new items
- `edit_dialog.py`: Generic dialog for editing existing items
- `confirmation_dialog.py`: Dialog for confirming important actions
- `message_dialog.py`: Enhanced message display dialog
- `filter_dialog.py`: Advanced filtering dialog
- `export_dialog.py`: Dialog for exporting data to different formats

### Usage
Dialogs can be created and shown as needed:

```python
from gui.dialogs.confirmation_dialog import ConfirmationDialog

# Show a confirmation dialog
dialog = ConfirmationDialog(
    self.parent,
    title="Confirm Delete",
    message="Are you sure you want to delete this item?",
    ok_text="Delete",
    cancel_text="Cancel"
)
if dialog.show():
    # User confirmed, perform delete
    self.delete_item()
```

### Key Components
- Standard dialog templates with consistent styling
- Common interaction patterns
- Reusable layout components

### Guidelines
- Use standard dialogs for common operations instead of creating custom ones
- Follow the dialog API conventions for consistent behavior
- Use `BaseDialog` when creating new specialized dialogs

---

These documentation files provide an overview of each folder's purpose, contents, and how to use the components. Each folder serves a specific role in the application's architecture, working together to create a cohesive and maintainable user interface.