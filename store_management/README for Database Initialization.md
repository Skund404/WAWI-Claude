# Leatherworking Management System

This repository contains a comprehensive leatherworking shop management system with tools for managing inventory, sales, projects, and tool maintenance.

## Features

- **Complete Database Schema**: Fully normalized relational database design with tables for materials, tools, products, sales, projects, customers, and more
- **Tool Management**: Track tools, their maintenance schedules, and checkout status
- **Inventory Management**: Track materials, products, and tools in inventory
- **Project Management**: Manage custom projects from initial design to completion
- **Sales Tracking**: Record and analyze sales data
- **Diagnostics Tools**: Comprehensive database validation and reporting

## Database Structure

The database follows the ER diagram and includes the following main entities:

- Customers
- Products and Patterns
- Materials (Leather, Hardware, Supplies)
- Tools and Tool Management
- Projects
- Sales
- Inventory

## New Features: Tool Management

Recent additions to the system include:

- **Tool Maintenance Tracking**: Record maintenance history, schedule future maintenance, and track costs
- **Tool Checkout System**: Track which tools are checked out, by whom, and for which projects
- **Tool Usage Analytics**: Report on most-used tools, maintenance frequency, and checkout patterns

## Setup Instructions

### Prerequisites

- Python 3.7+
- SQLAlchemy
- SQLite (installed by default with Python)

### Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install sqlalchemy
   ```

### Database Initialization

To initialize the database with tables:

```
python initialize_database.py
```

Options:
- `--recreate`: Drop and recreate all tables (WARNING: This will delete all data)
- `--seed`: Add minimal sample data to the database
- `--load-sample /path/to/sample_data.json`: Load comprehensive sample data from a JSON file

Example:
```
python initialize_database.py --recreate --load-sample sample_data.json
```

### Running Diagnostics

To run diagnostics on the database:

```
python database/diagnostics.py
```

Options:
- `--silent`: Run diagnostics without console output
- `--report-file filename`: Save the diagnostic report to a file (generates both JSON and TXT formats)

Example:
```
python database/diagnostics.py --report-file diagnostic_report
```

## Sample Data

The repository includes a comprehensive sample data file (`sample_data.json`) that can be used to populate the database with realistic data for testing and development. This includes:

- Suppliers and customers
- Various materials (leather, hardware, supplies)
- Tools with maintenance records and checkout history
- Products and patterns
- Projects

## Tool Maintenance Module

The tool maintenance module allows you to:

1. Record maintenance activities for each tool
2. Schedule future maintenance based on intervals
3. Track maintenance costs and parts used
4. Monitor tool condition before and after maintenance

## Tool Checkout System

The tool checkout system allows you to:

1. Check out tools for specific projects
2. Track who has each tool and when it's due back
3. Record tool condition before and after checkout
4. Monitor overdue checkouts

## Diagnostics and Reporting

The diagnostic system provides comprehensive checks and reports including:

- Table existence verification
- Record count per model
- Relationship validation
- Data integrity checks
- Inventory status analysis
- Sales trend analysis
- Tool usage analysis

## Customization

The system is designed to be extensible. To add new features:

1. Create new model classes in the `database/models` directory
2. Update the relevant repository classes in `database/repositories`
3. Update the initialization script to include your new models
4. Add diagnostic checks for your new features

## Contributing

Contributions to improve the system are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.