# di/tests/mock_implementations/base_service.py
# Base implementation for mock services

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class MockBaseService:
    """Base class for mock service implementations.
    
    Provides a simple in-memory implementation for testing and development.
    """
    
    def __init__(self):
        """Initialize the mock service with an empty data store."""
        self.items = {}  # Dictionary to store mock data
        self.next_id = 1  # Counter for generating IDs
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Initialized mock service: {self.__class__.__name__}")
    
    def get_by_id(self, item_id: int) -> Dict[str, Any]:
        """Get item by ID.
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            Dict representing the item
            
        Raises:
            KeyError: If item not found
        """
        if item_id not in self.items:
            raise KeyError(f"[MOCK] Item with ID {item_id} not found")
        return self.items[item_id]
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all items, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of dicts representing items
        """
        if not filters:
            return list(self.items.values())
        
        # Apply simple filtering
        filtered_items = []
        for item in self.items.values():
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered_items.append(item)
        
        return filtered_items
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item.
        
        Args:
            data: Dict containing item properties
            
        Returns:
            Dict representing the created item
        """
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = self.next_id
            self.next_id += 1
        
        # Add timestamps
        now = datetime.now()
        data['created_at'] = now
        data['updated_at'] = now
        
        # Store item
        self.items[data['id']] = data
        return data
    
    def update(self, item_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item.
        
        Args:
            item_id: ID of the item to update
            data: Dict containing updated item properties
            
        Returns:
            Dict representing the updated item
            
        Raises:
            KeyError: If item not found
        """
        if item_id not in self.items:
            raise KeyError(f"[MOCK] Item with ID {item_id} not found")
        
        # Update the item
        item = self.items[item_id]
        for key, value in data.items():
            if key != 'id' and key != 'created_at':
                item[key] = value
        
        # Update timestamp
        item['updated_at'] = datetime.now()
        
        return item
    
    def delete(self, item_id: int) -> bool:
        """Delete an item by ID.
        
        Args:
            item_id: ID of the item to delete
            
        Returns:
            True if successful
            
        Raises:
            KeyError: If item not found
        """
        if item_id not in self.items:
            raise KeyError(f"[MOCK] Item with ID {item_id} not found")
        
        del self.items[item_id]
        return True
    
    def seed_data(self, items: List[Dict[str, Any]]) -> None:
        """Seed the mock service with initial data.
        
        Args:
            items: List of items to add
        """
        for item in items:
            self.create(item)