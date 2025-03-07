# Data Model Update Integration Guide

This document outlines the changes made to the service layer to support the updated data model for the leatherworking application.

## Overview of Changes

The application has been updated with new services to support the enhanced data model, particularly for:

1. **Picking List Management**: Tracking and managing lists of materials and components for production
2. **Tool List Management**: Tracking tools required for specific projects
3. **Project Component Management**: Enhanced handling of components within projects

## New Services

The following new services have been implemented:

### 1. PickingListService

Handles the creation and management of picking lists that track the materials needed for production.

**Key Functionality**:
- Create picking lists associated with sales orders
- Add items to picking lists (materials, leathers, hardware, components)
- Update picking list status and track progress
- Process completed picking lists to update inventory

### 2. ToolListService

Manages lists of tools required for specific projects.

**Key Functionality**:
- Create tool lists for projects
- Add tool items with quantities
- Update and track tool list status
- Link tool lists with projects

### 3. ProjectComponentService

Provides enhanced management of components within projects, including linking to picking lists.

**Key Functionality**:
- Create and manage project components
- Link components to picking list items
- Calculate material requirements for projects
- Track component quantities and status

## Integration Steps

To integrate these changes into the existing application:

1. Add the new service interfaces and implementations to the codebase
2. Update the dependency injection registration by replacing the existing `service_registration.py` with the updated version
3. Initialize the updated services during application startup

## Code Usage Examples

### Working with Picking Lists

```python
# Assuming the DI container has been initialized
from di.core import DependencyContainer
from services.interfaces.picking_list_service import IPickingListService

# Get the picking list service
picking_list_service = DependencyContainer.instance().resolve(IPickingListService)

# Create a new picking list for a sales order
picking_list = picking_list_service.create_picking_list(sales_id=123)

# Add materials to the picking list
picking_list_service.add_item(
    picking_list_id=picking_list["id"],
    material_id=456,
    quantity_ordered=2
)

# Update picking list status
picking_list_service.update_status(picking_list["id"], PickingListStatus.IN_PROGRESS)

# Process a completed picking list
picking_list_service.process_picking_list(picking_list["id"])
```

### Working with Tool Lists

```python
from di.core import DependencyContainer
from services.interfaces.tool_list_service import IToolListService

# Get the tool list service
tool_list_service = DependencyContainer.instance().resolve(IToolListService)

# Create a new tool list for a project
tool_list = tool_list_service.create_tool_list(project_id=789)

# Add tools to the list
tool_list_service.add_item(
    tool_list_id=tool_list["id"],
    tool_id=101,
    quantity=1
)

# Get the active tool list for a project
active_tool_list = tool_list_service.get_tool_list_for_project(project_id=789)
```

### Managing Project Components

```python
from di.core import DependencyContainer
from services.interfaces.project_component_service import IProjectComponentService

# Get the project component service
component_service = DependencyContainer.instance().resolve(IProjectComponentService)

# Create a project component
component = component_service.create_component(
    project_id=789,
    component_id=202,
    quantity=3
)

# Link to a picking list item
component_service.link_to_picking_list_item(
    project_component_id=component["id"],
    picking_list_item_id=303
)

# Calculate material requirements for a project
requirements = component_service.get_material_requirements(project_id=789)
```

## Testing

Unit tests for the new services should be added to maintain code quality:

1. Create test cases for each service method
2. Test edge cases and error handling
3. Verify that service interactions work correctly
4. Test integration with the database models

## Troubleshooting

Common issues and their solutions:

1. **Circular Import Errors**: Use the `lazy_import` utility from `utils.circular_import_resolver` to resolve circular dependencies.

2. **Database Model Access Issues**: Ensure all required models are properly imported and that repositories are correctly initialized.

3. **Dependency Injection Errors**: Verify that all services are properly registered with the DI container.

4. **Repository Interface Mismatches**: Make sure repository methods match the expectations of the services that use them.