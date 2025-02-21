# Database Access Guide

## Overview

This application uses a standardized approach to database access through manager classes.
All database operations should follow this pattern to ensure consistency and proper transaction management.

## Key Components

1. **BaseManager**: Generic class for database operations
2. **get_db_session()**: Context manager for transaction handling
3. **get_manager()**: Factory function to get manager instances

## Best Practices

### Using Managers

```python
from store_management.database.sqlalchemy.manager_factory import get_manager
from store_management.database.sqlalchemy.models.part import Part

# Get a manager for the Part model
part_manager = get_manager(Part)

# Create a new part
new_part = part_manager.create({
    "name": "Widget",
    "stock_level": 100,
    "min_stock_level": 10
})

# Get all parts
all_parts = part_manager.get_all()

# Update a part
part_manager.update(part_id, {"stock_level": 50})

# Delete a part
part_manager.delete(part_id)