# Project Management Module Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [User Guides](#user-guides)
   - [Project List View](#project-list-view)
   - [Project Details View](#project-details-view)
   - [Project Components](#project-components)
   - [Material Picking Lists](#material-picking-lists)
5. [Technical Implementation](#technical-implementation)
6. [Integration Points](#integration-points)
7. [Customization & Extension](#customization--extension)

## Overview

The Project Management module for the Leatherworking ERP system provides comprehensive tools for managing leather crafting projects from initial design through production. It supports tracking multiple projects simultaneously, managing components and materials requirements, monitoring project status, and coordinating resource allocation.

This module integrates with the inventory, material, and customer modules to provide a seamless workflow from project creation to completion. The system is designed to handle the unique requirements of custom leatherworking, including detailed component specifications, material picking lists, and project status tracking.

## Architecture

The Project Management module follows the Model-View-Controller (MVC) pattern within the application's broader architecture. It implements:

- **Views**: GUI components for displaying and interacting with project data
- **Services**: Business logic for handling project operations
- **Models**: Data structures representing projects, components, and related entities
- **Repositories**: Data access layer for persistent storage

### Module Components:

1. **Project List View**: Main entry point displaying all projects with filtering and dashboard metrics
2. **Project Details View**: Comprehensive view with tabs for different project aspects
3. **Project Component View**: Interface for managing individual project components
4. **Picking List View**: Interface for managing material requirements and picking operations

### Code Organization:

```
gui/views/projects/
├── project_list_view.py       # Main project listing and dashboard
├── project_details_view.py    # Detailed project editor and viewer
├── project_component_view.py  # Component management interface
├── picking_list_view.py       # Materials picking list interface
└── tool_list_view.py          # Tool requirements management
```

## Key Features

### Project Management
- Create, view, edit, and delete projects
- Track project status and progress
- Manage project timeline and deadlines
- Associate projects with customers
- Visualize project timeline and status history

### Component Management
- Add and configure components for each project
- Track component dimensions and specifications
- Assign materials to components
- Monitor component assembly status

### Resource Planning
- Generate material picking lists from project components
- Track material availability and inventory status
- Support for picking workflow with status tracking
- Manage tool requirements for projects

### Reporting & Visibility
- Project dashboard with key metrics
- Status-based filtering and searching
- Timeline visualization
- Material requirements summary

## User Guides

### Project List View

The Project List View provides an overview of all projects with status-based filtering and a project metrics dashboard.

#### Features:
- **Project Dashboard**: Displays counts by status, upcoming deadlines, and progress metrics
- **Filtering Options**: Filter by status, type, date range, and text search
- **Timeline View**: Visualize projects on a timeline to manage workload
- **Quick Actions**: Add, edit, view projects, and access related resources

#### Usage:
1. **Add Project**: Click "Add Project" to create a new project
2. **View/Edit Project**: Select a project and click "View Project" or "Edit Project"
3. **Access Resources**: Select a project and use "Picking List" or "Tool List" buttons
4. **Update Status**: Select a project and click "Update Status" to change status

### Project Details View

The Project Details View provides comprehensive project information and management across multiple tabs.

#### Features:
- **General Info**: Basic project details, customer information, and dates
- **Components**: Manage project components and their materials
- **Status History**: Track status changes over the project lifecycle
- **Resources**: Manage picking lists and tool lists
- **Timeline**: Visual representation of project timeline

#### Usage:
1. **Edit Basic Info**: Update project name, type, dates, and customer information
2. **Manage Components**: Add, edit, or remove components in the Components tab
3. **Track Status**: View status history or update project status
4. **Manage Resources**: Create and manage picking lists and tool lists
5. **View Timeline**: Monitor project progress and timeline

### Project Components

The Project Component View allows detailed management of individual components within a project.

#### Features:
- **Component Details**: Specify name, type, dimensions, and other properties
- **Material Requirements**: Associate materials with specific quantities
- **Assembly Instructions**: Document assembly steps and notes
- **Inventory Integration**: Check material availability

#### Usage:
1. **Add Component**: Create a new component from the Project Details view
2. **Edit Properties**: Update component specifications and dimensions
3. **Manage Materials**: Add or remove materials and specify quantities
4. **Document Assembly**: Add assembly instructions and notes

### Material Picking Lists

The Picking List View manages material allocation and retrieval for projects.

#### Features:
- **Automated Generation**: Create picking lists from project components
- **Material Tracking**: Show material requirements, locations, and availability
- **Picking Workflow**: Support for draft, in-progress, and completed states
- **Inventory Integration**: Check and update inventory quantities

#### Usage:
1. **Create Picking List**: Generate from project or components
2. **Start Picking**: Change status to "In Progress" to begin material retrieval
3. **Update Quantities**: Record picked quantities for each material
4. **Complete Picking**: Finalize the picking operation and update inventory

## Technical Implementation

### Dependency Injection

The Project Management module utilizes the application's DI system for service access:

```python
# Service access
self.project_service = get_service("project_service")
self.picking_list_service = get_service("picking_list_service")
```

### Event Publishing

The module uses an event bus to communicate between components:

```python
# Publish event when component is updated
publish("component_updated", {
    "project_id": self.project_id, 
    "component_id": component.id
})
```

### Data Transfer Objects

DTOs are used for transferring data between UI and services:

```python
# ProjectDTO contains all necessary project data
project = self.project_service.get_project(
    self.project_id,
    include_components=True,
    include_status_history=True,
    include_picking_lists=True
)
```

### Status Management

Project and resource status is tracked using enums with state transitions:

```python
# Update project status
self.project_service.update_project_status(
    self.project_id, status_value, notes
)
```

## Integration Points

### Inventory System
- Material availability checking
- Inventory quantity updates on picking completion
- Storage location information

### Material Management
- Material specifications and properties
- Supplier information for material sourcing
- Material cost calculations

### Customer Management
- Customer association with projects
- Customer communication history
- Delivery tracking

### Reporting
- Project status reports
- Material usage reports
- Production timeline and scheduling

## Customization & Extension

### Adding New Project Statuses

To add a new project status:

1. Add the status to the `ProjectStatus` enum in `database/models/enums.py`
2. Update UI components in `project_list_view.py` and `project_details_view.py`
3. Add status transition logic to the project service implementation

### Adding Component Types

To add a new component type:

1. Add the type to the `ComponentType` enum in `database/models/enums.py`
2. Update the component form in `project_component_view.py` to handle new type
3. Consider adding specific validation or fields for the new component type

### Custom Fields

The module supports custom fields for projects and components:

1. Add fields to the corresponding model classes
2. Update DTO classes to include the new fields
3. Add UI elements to display and edit the custom fields

---

This documentation provides an overview of the Project Management module, its features, implementation details, and usage guidelines. For additional technical details, refer to the code documentation in each file.