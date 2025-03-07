# Integration Guide for Updated Services

## Import Error Resolution

The test module is failing to import the new services. This is expected as we've created new modules that don't yet exist in the actual codebase. Follow these steps to correctly integrate the new services:

### 1. Verify Directory Structure

Ensure your project directory follows this structure:

```
store_management/
├── database/
│   ├── models/
│   │   ├── enums.py
│   │   ├── picking_list.py
│   │   ├── tool_list.py
│   │   └── components.py
│   └── repositories/
│       ├── picking_list_repository.py
│       └── tool_list_repository.py
├── services/
│   ├── implementations/
│   │   ├── picking_list_service.py
│   │   ├── tool_list_service.py
│   │   └── project_component_service.py
│   ├── interfaces/
│   │   ├── picking_list_service.py
│   │   ├── tool_list_service.py
│   │   └── project_component_service.py
│   └── service_registration.py
└── tests/
    └── integration/
        └── test_updated_services.py
```

### 2. Check Import Paths

The error message suggests that the import path is not correct. Verify the actual import structure of your application. You may need to adjust the import statements in the following files:

1. `tests/integration/test_updated_services.py`
2. The service implementation files
3. The service interface files

### 3. Adjust Python Module Paths

If your application uses a different module structure, adjust the imports accordingly:

For example, if your application module structure is:

```python
# If your main module is "store_management", adjust imports like:
from store_management.services.implementations.tool_list_service import ToolListService
```

### 4. Create Required Repository Files

Make sure the repository classes referenced by the services exist:

1. Create `database/repositories/picking_list_repository.py`
2. Create `database/repositories/tool_list_repository.py`

Example implementation for `picking_list_repository.py`:

```python
"""
database/repositories/picking_list_repository.py
Repository for picking list data access.
"""
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from database.models.picking_list import PickingList, PickingListItem
from database.repositories.base_repository import BaseRepository


class PickingListRepository(BaseRepository):
    """Repository for accessing picking list data."""

    def __init__(self, session: Session):
        """
        Initialize the Picking List Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, PickingList)

    def add_item(self, item_data: Dict[str, Any]) -> PickingListItem:
        """
        Add an item to a picking list.

        Args:
            item_data: Dictionary containing item attributes

        Returns:
            Created PickingListItem
        """
        item = PickingListItem(**item_data)
        self.session.add(item)
        self.session.commit()
        return item

    def get_item_by_id(self, item_id: int) -> Optional[PickingListItem]:
        """
        Get a picking list item by ID.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            PickingListItem or None if not found
        """
        return self.session.query(PickingListItem).filter(
            PickingListItem.id == item_id
        ).first()

    def update_item(self, item_id: int, data: Dict[str, Any]) -> PickingListItem:
        """
        Update a picking list item.

        Args:
            item_id: ID of the item to update
            data: Dictionary containing attributes to update

        Returns:
            Updated PickingListItem
        """
        item = self.get_item_by_id(item_id)
        if item:
            for key, value in data.items():
                setattr(item, key, value)
            self.session.commit()
        return item

    def delete_item(self, item_id: int) -> None:
        """
        Delete a picking list item.

        Args:
            item_id: ID of the item to delete
        """
        item = self.get_item_by_id(item_id)
        if item:
            self.session.delete(item)
            self.session.commit()
```

Example implementation for `tool_list_repository.py`:

```python
"""
database/repositories/tool_list_repository.py
Repository for tool list data access.
"""
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from database.models.tool_list import ToolList, ToolListItem
from database.repositories.base_repository import BaseRepository


class ToolListRepository(BaseRepository):
    """Repository for accessing tool list data."""

    def __init__(self, session: Session):
        """
        Initialize the Tool List Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, ToolList)

    def add_item(self, item_data: Dict[str, Any]) -> ToolListItem:
        """
        Add an item to a tool list.

        Args:
            item_data: Dictionary containing item attributes

        Returns:
            Created ToolListItem
        """
        item = ToolListItem(**item_data)
        self.session.add(item)
        self.session.commit()
        return item

    def get_item_by_id(self, item_id: int) -> Optional[ToolListItem]:
        """
        Get a tool list item by ID.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            ToolListItem or None if not found
        """
        return self.session.query(ToolListItem).filter(
            ToolListItem.id == item_id
        ).first()

    def update_item(self, item_id: int, data: Dict[str, Any]) -> ToolListItem:
        """
        Update a tool list item.

        Args:
            item_id: ID of the item to update
            data: Dictionary containing attributes to update

        Returns:
            Updated ToolListItem
        """
        item = self.get_item_by_id(item_id)
        if item:
            for key, value in data.items():
                setattr(item, key, value)
            self.session.commit()
        return item

    def delete_item(self, item_id: int) -> None:
        """
        Delete a tool list item.

        Args:
            item_id: ID of the item to delete
        """
        item = self.get_item_by_id(item_id)
        if item:
            self.session.delete(item)
            self.session.commit()
```

### 5. Create Required Model Files

Ensure the model classes referenced by the services exist:

1. Create `database/models/picking_list.py`
2. Create `database/models/tool_list.py`

Example implementation for `picking_list.py`:

```python
"""
database/models/picking_list.py
Models for picking list functionality.
"""
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime

from database.models.base import Base
from database.models.enums import PickingListStatus


class PickingList(Base):
    """Model for tracking picking lists."""
    __tablename__ = "picking_lists"

    id = Column(Integer, primary_key=True)
    sales_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    status = Column(Enum(PickingListStatus), default=PickingListStatus.DRAFT, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    sales = relationship("Sales", back_populates="picking_lists")
    items = relationship("PickingListItem", back_populates="picking_list", cascade="all, delete-orphan")


class PickingListItem(Base):
    """Model for items in a picking list."""
    __tablename__ = "picking_list_items"

    id = Column(Integer, primary_key=True)
    picking_list_id = Column(Integer, ForeignKey("picking_lists.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=True)
    quantity_ordered = Column(Integer, default=1, nullable=False)
    quantity_picked = Column(Integer, default=0, nullable=False)

    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    component = relationship("Component", back_populates="picking_list_items")
    material = relationship("Material", back_populates="picking_list_items")
    leather = relationship("Leather", back_populates="picking_list_items")
    hardware = relationship("Hardware", back_populates="picking_list_items")
    project_components = relationship("ProjectComponent", back_populates="picking_list_item")
```

Example implementation for `tool_list.py`:

```python
"""
database/models/tool_list.py
Models for tool list functionality.
"""
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime

from database.models.base import Base
from database.models.enums import ToolListStatus


class ToolList(Base):
    """Model for tracking tool lists."""
    __tablename__ = "tool_lists"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(Enum(ToolListStatus), default=ToolListStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tool_lists")
    items = relationship("ToolListItem", back_populates="tool_list", cascade="all, delete-orphan")


class ToolListItem(Base):
    """Model for items in a tool list."""
    __tablename__ = "tool_list_items"

    id = Column(Integer, primary_key=True)
    tool_list_id = Column(Integer, ForeignKey("tool_lists.id"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    # Relationships
    tool_list = relationship("ToolList", back_populates="items")
    tool = relationship("Tool", back_populates="tool_list_items")
```

### 6. Update the Enums

Make sure your `database/models/enums.py` file includes the necessary enums:

```python
"""
database/models/enums.py
Enumeration types for the database models.
"""
from enum import Enum


class PickingListStatus(Enum):
    """Status values for picking lists."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ToolListStatus(Enum):
    """Status values for tool lists."""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
```

### 7. Test Integration Incrementally

1. First, add just the model files and verify they can be imported
2. Then add the repository files
3. Next, add the service interfaces
4. Finally, add the service implementations

Try importing each module separately to identify any additional import issues.

## Running the Tests in Development Mode

While integrating these changes, you can temporarily modify the test to use mocks more extensively to avoid import errors:

```python
# At the top of your test file
import unittest
from unittest.mock import MagicMock, patch

# Mock the imports that don't exist yet
mockPickingListService = MagicMock()
mockToolListService = MagicMock()
mockProjectComponentService = MagicMock()

# Apply patches
patch('services.implementations.picking_list_service.PickingListService', 
      mockPickingListService).start()
patch('services.implementations.tool_list_service.ToolListService', 
      mockToolListService).start()
patch('services.implementations.project_component_service.ProjectComponentService', 
      mockProjectComponentService).start()

# Continue with your tests using the mocks
```

This approach lets you develop the tests while you progressively integrate the real implementations.