# conftest.py
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Ensure database models can be imported
from database.models import (
    Base, PickingList, PickingListItem,
    # Add other models you might need for testing
    Project, Tool, ToolList, ToolListItem
)