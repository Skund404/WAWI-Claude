# Pattern Management System Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
   - [Pattern List View](#pattern-list-view)
   - [Pattern Detail View](#pattern-detail-view)
   - [Component Dialog](#component-dialog)
   - [Pattern File Viewer](#pattern-file-viewer)
   - [Pattern Export Dialog](#pattern-export-dialog)
   - [Print Dialog](#print-dialog)
4. [User Workflows](#user-workflows)
   - [Creating a New Pattern](#creating-a-new-pattern)
   - [Editing Existing Patterns](#editing-existing-patterns)
   - [Managing Components](#managing-components)
   - [Working with Materials](#working-with-materials)
   - [File Management](#file-management)
   - [Printing Patterns](#printing-patterns)
   - [Exporting Patterns](#exporting-patterns)
5. [Technical Details](#technical-details)
   - [File Support](#file-support)
   - [Event System](#event-system)
   - [Service Integration](#service-integration)
   - [Dependencies](#dependencies)
6. [Customization and Extension](#customization-and-extension)
   - [Adding New Component Types](#adding-new-component-types)
   - [Supporting New File Formats](#supporting-new-file-formats)
   - [Extending Material Management](#extending-material-management)
7. [Troubleshooting](#troubleshooting)

## Introduction

The Pattern Management System is a comprehensive module within the Leatherworking Application that enables users to create, edit, organize, and utilize patterns for leatherworking projects. It provides tools for defining patterns with components, specifying material requirements, and managing pattern files in various formats.

This system is designed to support the complete workflow of pattern creation and usage, from initial design through component definition and material calculation to final printing and production.

## System Architecture

The Pattern Management System follows the established application architecture with a clear separation of concerns:

- **Views**: User interface components that display data and capture user input
- **Services**: Business logic layer that processes data and performs operations
- **Repositories**: Data access layer that interacts with the database
- **Models**: Data structures that represent domain entities

The system integrates with the application's dependency injection framework, event bus, and service layer to maintain modularity and extensibility.

### Module Structure

```
gui/
├── views/
│   └── patterns/
│       ├── __init__.py                 # Package initialization
│       ├── pattern_list_view.py        # List of available patterns
│       ├── pattern_detail_view.py      # Detailed pattern editor
│       ├── component_dialog.py         # Component creation/editing
│       ├── pattern_file_viewer.py      # File viewer for patterns
│       ├── pattern_export_dialog.py    # Export options dialog
│       └── print_dialog.py             # Print settings dialog
```

## Core Components

### Pattern List View

The Pattern List View (`pattern_list_view.py`) provides a central hub for managing all patterns in the system. It displays patterns in a sortable, filterable list with columns for key attributes.

**Key Features:**
- Listing patterns with sorting and filtering
- Creating new patterns
- Viewing and editing existing patterns
- Duplicating patterns
- Exporting patterns in various formats
- Printing patterns
- Deleting patterns with confirmation

**Implementation Details:**
- Extends `BaseListView` from the application framework
- Provides specialized buttons for pattern-specific actions
- Integrates with the Pattern Service for data operations

### Pattern Detail View

The Pattern Detail View (`pattern_detail_view.py`) is a comprehensive editor for patterns that provides a tabbed interface for managing different aspects of a pattern.

**Key Features:**
- Information tab for basic pattern details
- Components tab for managing pattern components
- Materials tab showing aggregated material requirements
- Files tab for managing attachments and diagrams
- Support for both creating new patterns and editing existing ones

**Tab Details:**
1. **Information Tab**: Contains form fields for pattern name, description, skill level, project type, and notes
2. **Components Tab**: Lists all components with type, dimensions, and material usage
3. **Materials Tab**: Shows aggregated material requirements from all components
4. **Files Tab**: Lists attached files with preview capabilities

**Implementation Details:**
- Creates a flexible UI with notebook tabs for organization
- Manages relationships between patterns, components, and materials
- Supports both creation and editing modes through parameters
- Provides a consistent user experience with appropriate actions

### Component Dialog

The Component Dialog (`component_dialog.py`) provides a dedicated interface for creating and editing pattern components with dynamic form fields based on component type.

**Key Features:**
- Information tab for basic component details
- Dimensions tab with dynamic fields based on component type
- Materials tab for assigning materials with quantities
- Support for multiple component shapes (rectangular, circular, strap, etc.)
- Material browser for selecting materials from inventory

**Implementation Details:**
- Dynamic form creation based on component type
- Integration with material service for browsing available materials
- Support for different measurement units
- Validation of dimensions and requirements

### Pattern File Viewer

The Pattern File Viewer (`pattern_file_viewer.py`) provides specialized viewing capabilities for pattern files in various formats (SVG, PDF, images).

**Key Features:**
- Support for SVG, PDF, PNG, and JPG/JPEG files
- Zoom and pan functionality
- Measurement tools for precise dimensions
- File export and printing capabilities
- Status information and coordinate display

**Implementation Details:**
- Integrated support for multiple file formats
- Graceful fallbacks when specific libraries aren't available
- Platform-specific file handling for cross-platform compatibility
- Tools for interactive measuring and analysis

### Pattern Export Dialog

The Pattern Export Dialog (`pattern_export_dialog.py`) provides options for exporting patterns in various formats with customizable settings.

**Key Features:**
- Support for PDF, SVG, PNG, and ZIP archive formats
- Options for content inclusion (components, materials, instructions)
- Customizable scaling and file naming
- Destination selection

**Implementation Details:**
- Format-specific options for different export types
- Integration with file system for saving exports
- Validation of settings and paths
- Consistent preview of export results

### Print Dialog

The Print Dialog (`print_dialog.py`) provides a comprehensive interface for printing patterns with various settings.

**Key Features:**
- Paper size and orientation options
- Scaling controls (actual size, fit to page, custom scale)
- Component selection for targeted printing
- Print preview with page navigation
- Print to file option for PDF generation

**Implementation Details:**
- Preview rendering of pattern components
- Page layout simulation
- Integration with system printing services
- Platform-specific print handling

## User Workflows

### Creating a New Pattern

1. From the Pattern List View, click **Add** to create a new pattern
2. Enter basic information in the Information tab
3. Save the pattern to enable component creation
4. Add components using the Components tab
5. Review aggregated materials in the Materials tab
6. Attach files or diagrams in the Files tab
7. Save the completed pattern

### Editing Existing Patterns

1. From the Pattern List View, select a pattern and click **Edit**
2. Modify pattern information as needed
3. Add, edit, or remove components
4. Update files and attachments
5. Save changes

### Managing Components

1. From the Pattern Detail View, navigate to the Components tab
2. Click **Add Component** to create a new component
3. Select component type and enter dimensions
4. Add material requirements
5. Save the component to update the pattern

**Component Types and Dimensions:**
- **Rectangular**: Width, height, and thickness
- **Circular**: Diameter and thickness
- **Strap/Strip**: Length, width, and thickness
- **Other types**: Custom dimension sets

### Working with Materials

1. From the Component Dialog, navigate to the Materials tab
2. Click **Add Material** to browse available materials
3. Search for materials by name or type
4. Select a material and specify quantity
5. Add notes for special considerations
6. Save to add the material to the component

The Pattern Detail View's Materials tab shows aggregated material requirements from all components, with options to:
- Check inventory status
- Create purchase orders for missing materials
- Export material lists

### File Management

1. From the Pattern Detail View, navigate to the Files tab
2. Add files using the **Add File** button
3. View files by selecting them and clicking **View File**
4. Download files for external use
5. Delete files when no longer needed

The Pattern File Viewer provides specialized tools for working with pattern files:
- Zoom controls for detailed examination
- Pan tool for navigating large files
- Measurement tool for precise dimensions
- Export options for saving copies

### Printing Patterns

1. From the Pattern List View, select a pattern and click **Print**
2. Configure paper size and orientation
3. Set scaling options (actual size, fit to page, custom scale)
4. Select components to include
5. Choose additional content (materials list, notes, etc.)
6. Preview the print layout
7. Print directly or save as PDF

### Exporting Patterns

1. From the Pattern List View, select a pattern and click **Export**
2. Choose the export format (PDF, SVG, PNG, ZIP)
3. Select content to include
4. Configure naming and destination
5. Set scaling options
6. Click **Export** to create the files

## Technical Details

### File Support

The Pattern Management System supports several file formats:

| Format | View | Export | Print | Notes |
|--------|------|--------|-------|-------|
| SVG    | ✓    | ✓      | ✓     | Vector graphics, ideal for patterns |
| PDF    | ✓    | ✓      | ✓     | Document format with multiple pages |
| PNG    | ✓    | ✓      | ✓     | Raster graphics with transparency |
| JPG    | ✓    | ✓      | ✓     | Compressed raster format |
| ZIP    | -    | ✓      | -     | Archive containing multiple files |

**Implementation Details:**
- SVG viewing utilizes the cairosvg library for rendering
- PDF support uses pdf2image and Poppler for rendering
- Image support leverages PIL/Pillow with tkinter integration
- Fallback mechanisms provide graceful degradation when libraries are unavailable

### Event System

The Pattern Management System uses the application's event bus for communication between components:

| Event | Description | Published By | Subscribed By |
|-------|-------------|--------------|---------------|
| `pattern_updated` | Pattern has been updated | Pattern Detail View | Pattern List View |
| `component_created` | New component added | Component Dialog | Pattern Detail View |
| `component_updated` | Component modified | Component Dialog | Pattern Detail View |
| `material_updated` | Material updated | Other components | Material viewers |

### Service Integration

The system integrates with several application services:

| Service | Purpose | Key Methods |
|---------|---------|------------|
| `IPatternService` | Pattern CRUD operations | `get_patterns`, `create_pattern`, `update_pattern`, `delete_pattern` |
| `IComponentService` | Component management | `get_component_by_id`, `create_component`, `update_component`, `delete_component` |
| `IMaterialService` | Material access | `get_materials`, `search_materials` |
| `IInventoryService` | Inventory checking | `check_material_inventory` |
| `IEnumService` | Enumeration values | `get_component_types`, `get_measurement_units` |

### Dependencies

The Pattern Management System has the following dependencies:

**Required:**
- Core tkinter and ttk modules
- Application framework (BaseView, BaseDialog, etc.)
- Service layer integration

**Optional:**
- PIL/Pillow for image processing
- cairosvg for SVG rendering
- pdf2image and Poppler for PDF functionality

## Customization and Extension

### Adding New Component Types

To add a new component type:

1. Update the `ComponentType` enum in `database/models/enums.py`
2. Add a new method in `component_dialog.py` to create the appropriate dimension fields
3. Update the `on_type_changed` method to handle the new type
4. Add dimension extraction logic in `collect_form_data`
5. Update validation in `validate_form`

Example for adding a "Triangular" component type:

```python
def _create_triangular_dimensions(self):
    """Create dimension fields for triangular components."""
    # Create grid layout
    form_frame = ttk.Frame(self.dimensions_container, padding=10)
    form_frame.pack(fill=tk.BOTH, expand=True)

    # Base
    ttk.Label(form_frame, text="Base:").grid(
        row=0, column=0, sticky="w", padx=5, pady=5)

    self.dimension_vars["base"] = tk.StringVar()
    base_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["base"], width=10)
    base_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(form_frame, text="mm").grid(
        row=0, column=2, sticky="w", padx=(0, 10))

    # Height
    ttk.Label(form_frame, text="Height:").grid(
        row=1, column=0, sticky="w", padx=5, pady=5)

    self.dimension_vars["height"] = tk.StringVar()
    height_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["height"], width=10)
    height_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(form_frame, text="mm").grid(
        row=1, column=2, sticky="w", padx=(0, 10))

    # Thickness
    ttk.Label(form_frame, text="Thickness:").grid(
        row=2, column=0, sticky="w", padx=5, pady=5)

    self.dimension_vars["thickness"] = tk.StringVar()
    thickness_entry = ttk.Entry(form_frame, textvariable=self.dimension_vars["thickness"], width=10)
    thickness_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(form_frame, text="mm").grid(
        row=2, column=2, sticky="w", padx=(0, 10))
```

### Supporting New File Formats

To add support for a new file format:

1. Update the file type detection in `pattern_file_viewer.py`
2. Add a new display method (e.g., `_display_dxf`)
3. Integrate with appropriate libraries for rendering
4. Add export support in `pattern_export_dialog.py`
5. Add print support if applicable

### Extending Material Management

To enhance material management:

1. Expand the material browser in `component_dialog.py`
2. Add filtering by material properties
3. Implement material usage optimization
4. Add inventory integration and alerts
5. Create material substitution suggestions

## Troubleshooting

### Common Issues

**Issue**: Component dimensions not saving correctly
- Ensure numeric values are entered in dimension fields
- Check unit conversions if using non-default units
- Verify component type is correctly selected

**Issue**: Pattern files not displaying
- Check if required libraries are installed (PIL, cairosvg, pdf2image)
- Verify file format is supported
- Check file permissions and access

**Issue**: Print preview not showing
- Ensure pattern has components defined
- Check paper size and orientation settings
- Verify scale settings are valid

**Issue**: Material not available in browser
- Check if material exists in the database
- Verify material service is functioning
- Check search criteria for filtering issues

### Logging

The Pattern Management System uses the application's logging system with the following components:

- `pattern_list_view`: Logs pattern list operations and user actions
- `pattern_detail_view`: Logs pattern editing and component operations
- `component_dialog`: Logs component creation and material assignments
- `pattern_file_viewer`: Logs file operations and rendering issues
- `pattern_export_dialog`: Logs export operations and settings
- `print_dialog`: Logs print configuration and execution

To enable detailed logging, adjust the logger level in `utils/gui_logger.py`.

### Dependency Issues

If the system has missing dependencies:

1. Install required Python packages:
   ```
   pip install pillow cairosvg pdf2image
   ```

2. For PDF support on Linux, install Poppler:
   ```
   sudo apt-get install poppler-utils  # Debian/Ubuntu
   sudo yum install poppler-utils      # CentOS/RHEL
   ```

3. For SVG support, ensure Cairo is installed:
   ```
   sudo apt-get install libcairo2-dev  # Debian/Ubuntu
   sudo yum install cairo-devel        # CentOS/RHEL
   ```

The system is designed to gracefully handle missing dependencies by showing appropriate error messages and providing alternative workflows when possible.