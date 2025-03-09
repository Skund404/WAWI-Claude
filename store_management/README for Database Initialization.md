# Database Initialization

## Overview

This script provides a comprehensive solution for initializing and seeding the leatherworking application database. It supports flexible database setup, sample data generation, and validation.

## Features

- Automatic database schema creation
- Multiple sample data modes
- Environment variable and command-line configuration
- Dry run support
- Detailed logging
- Error handling and validation

## Prerequisites

- Python 3.8+
- SQLAlchemy
- Required project dependencies

## Usage

### Command-Line Options

```bash
python initialize_database.py [OPTIONS]
```

Options:
- `--recreate`: Drop and recreate all database tables
- `--seed`: Add sample data to the database
- `--mode {minimal,standard,demo}`: Control the amount of sample data
  - `minimal`: Bare minimum data for basic functionality
  - `standard`: Comprehensive set of sample data
  - `demo`: Extended dataset for demonstration purposes
- `--dry-run`: Validate database setup without committing changes

### Environment Variables

You can also control the initialization using environment variables:

- `RECREATE_DB`: Set to `true` to drop and recreate tables
- `SEED_DB`: Set to `true` to add sample data
- `SEED_MODE`: Set to `minimal`, `standard`, or `demo`
- `DRY_RUN`: Set to `true` for validation without changes

### Examples

1. Full database recreation with standard sample data:
```bash
python initialize_database.py --recreate --seed
```

2. Add minimal sample data:
```bash
python initialize_database.py --seed --mode minimal
```

3. Dry run with demo dataset:
```bash
python initialize_database.py --seed --mode demo --dry-run
```

4. Using environment variables:
```bash
RECREATE_DB=true SEED_DB=true SEED_MODE=demo python initialize_database.py
```

## Sample Data

### Data Sources

- `sample_data.json`: Comprehensive sample data for standard initialization
- `minimal_sample_data.json`: Minimal dataset for basic testing

### Customization

You can modify the JSON files to customize the sample data without changing the initialization script.

## Logging

The script provides detailed logging to help you understand the initialization process. Logs include:
- Database connection details
- Table creation status
- Sample data loading
- Performance metrics
- Validation results

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure you have the necessary database drivers
   - Check database file permissions
   - Verify connection string

2. **Model Import Failures**
   - Confirm all required models are correctly defined
   - Check import paths
   - Verify no circular dependencies

3. **Sample Data Loading Problems**
   - Validate JSON file syntax
   - Ensure enum values match model definitions
   - Check for data type mismatches

### Debugging

- Use `--dry-run` to validate configuration without changes
- Check log output for detailed error messages
- Verify database model implementations

## Performance

The initialization script is designed to be efficient:
- Minimal database roundtrips
- Batch processing for sample data
- Comprehensive error handling
- Configurable logging levels

## Security Considerations

- Avoid committing sensitive information in sample data
- Use environment-specific configurations
- Implement appropriate access controls

## Development and Contribution

### Adding New Sample Data

1. Update `sample_data.json` or create new JSON files
2. Ensure data matches model definitions
3. Add appropriate enum mappings in the loader functions

### Extending Initialization Logic

- Modify `create_sample_*` functions to support new data types
- Implement additional validation in the `main()` function
- Enhance error handling and logging

