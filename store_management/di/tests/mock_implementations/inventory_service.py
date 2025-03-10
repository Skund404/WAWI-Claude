# di/tests/mock_implementations/inventory_service.py
# Mock implementation of the inventory service

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from di.tests.mock_implementations.base_service import MockBaseService

class MockInventoryService(MockBaseService):
    """Mock implementation of the inventory service."""
    
    def __init__(self):
        """Initialize the mock inventory service."""
        super().__init__()
        self.transactions = {}  # Dictionary to store mock transactions
        self.next_transaction_id = 1  # Counter for generating transaction IDs
        
        # Seed with some test data
        self.seed_data([
            {
                'id': 1,
                'item_type': 'material',
                'item_id': 1,
                'quantity': 25.5,
                'status': 'IN_STOCK',
                'storage_location': 'Shelf A-1',
                'item_name': '[MOCK] Vegetable Tanned Leather'
            },
            {
                'id': 2,
                'item_type': 'material',
                'item_id': 2,
                'quantity': 3.0,
                'status': 'LOW_STOCK',
                'storage_location': 'Shelf A-2',
                'item_name': '[MOCK] Thread - Brown'
            },
            {
                'id': 3,
                'item_type': 'material',
                'item_id': 3,
                'quantity': 0.0,
                'status': 'OUT_OF_STOCK',
                'storage_location': 'Bin B-1',
                'item_name': '[MOCK] Brass Buckle - 1 inch'
            },
            {
                'id': 4,
                'item_type': 'tool',
                'item_id': 1,
                'quantity': 2,
                'status': 'IN_STOCK',
                'storage_location': 'Tool Cabinet C-1',
                'item_name': '[MOCK] Stitching Awl'
            }
        ])
    
    def get_by_item(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """Get inventory entry by item type and ID.
        
        Args:
            item_type: Type of the item (material, product, tool)
            item_id: ID of the item
            
        Returns:
            Dict representing the inventory entry
            
        Raises:
            KeyError: If inventory entry not found
        """
        for item in self.items.values():
            if item['item_type'] == item_type and item['item_id'] == item_id:
                return item
        
        raise KeyError(f"[MOCK] Inventory entry for {item_type} with ID {item_id} not found")
    
    def adjust_quantity(self, inventory_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust quantity for an inventory entry.
        
        Args:
            inventory_id: ID of the inventory entry
            quantity: Quantity to adjust (positive for increase, negative for decrease)
            reason: Reason for adjustment
            
        Returns:
            Dict representing the updated inventory entry
            
        Raises:
            KeyError: If inventory entry not found
            ValueError: If validation fails
        """
        if inventory_id not in self.items:
            raise KeyError(f"[MOCK] Inventory entry with ID {inventory_id} not found")
        
        item = self.items[inventory_id]
        new_quantity = item['quantity'] + quantity
        
        if new_quantity < 0:
            raise ValueError("[MOCK] Cannot reduce inventory below zero")
        
        # Update inventory quantity
        item['quantity'] = new_quantity
        
        # Update status based on new quantity
        if new_quantity <= 0:
            item['status'] = 'OUT_OF_STOCK'
        elif new_quantity < 5:
            item['status'] = 'LOW_STOCK'
        else:
            item['status'] = 'IN_STOCK'
        
        # Log transaction
        transaction_type = 'USAGE' if quantity < 0 else 'RESTOCK'
        self._create_transaction({
            'inventory_id': inventory_id,
            'item_type': item['item_type'],
            'item_id': item['item_id'],
            'quantity': abs(quantity),
            'type': transaction_type,
            'timestamp': datetime.now(),
            'notes': reason
        })
        
        return item
    
    def get_low_stock_items(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get inventory items with low stock levels.
        
        Args:
            threshold: Optional threshold for what's considered "low stock"
            
        Returns:
            List of inventory items with low stock
        """
        threshold = threshold or 5.0
        return [item for item in self.items.values() if item['quantity'] > 0 and item['quantity'] < threshold]
    
    def log_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an inventory transaction.
        
        Args:
            transaction_data: Dict containing transaction properties
            
        Returns:
            Dict representing the created transaction
        """
        return self._create_transaction(transaction_data)
    
    def get_transaction_history(self, 
                               item_type: Optional[str] = None, 
                               item_id: Optional[int] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get transaction history for an item or date range.
        
        Args:
            item_type: Optional type of the item (material, product, tool)
            item_id: Optional ID of the item
            start_date: Optional start date for the range
            end_date: Optional end date for the range
            
        Returns:
            List of transactions matching the criteria
        """
        filtered_transactions = []
        
        for transaction in self.transactions.values():
            # Apply filters
            if item_type and transaction['item_type'] != item_type:
                continue
                
            if item_id and transaction['item_id'] != item_id:
                continue
                
            if start_date and transaction['timestamp'] < start_date:
                continue
                
            if end_date and transaction['timestamp'] > end_date:
                continue
                
            filtered_transactions.append(transaction)
        
        return filtered_transactions
    
    def update_storage_location(self, inventory_id: int, location: str) -> Dict[str, Any]:
        """Update storage location for an inventory entry.
        
        Args:
            inventory_id: ID of the inventory entry
            location: New storage location
            
        Returns:
            Dict representing the updated inventory entry
            
        Raises:
            KeyError: If inventory entry not found
        """
        if inventory_id not in self.items:
            raise KeyError(f"[MOCK] Inventory entry with ID {inventory_id} not found")
        
        item = self.items[inventory_id]
        old_location = item.get('storage_location')
        
        # Update location
        item['storage_location'] = location
        item['updated_at'] = datetime.now()
        
        return item
    
    def update_status(self, inventory_id: int, status: str) -> Dict[str, Any]:
        """Update status for an inventory entry.
        
        Args:
            inventory_id: ID of the inventory entry
            status: New status
            
        Returns:
            Dict representing the updated inventory entry
            
        Raises:
            KeyError: If inventory entry not found
        """
        if inventory_id not in self.items:
            raise KeyError(f"[MOCK] Inventory entry with ID {inventory_id} not found")
        
        # Validate status
        valid_statuses = ['IN_STOCK', 'LOW_STOCK', 'OUT_OF_STOCK', 'DISCONTINUED', 'ON_ORDER']
        if status not in valid_statuses:
            raise ValueError(f"[MOCK] Invalid inventory status: {status}")
        
        # Update status
        item = self.items[inventory_id]
        item['status'] = status
        item['updated_at'] = datetime.now()
        
        return item
    
    def get_item_availability(self, item_type: str, item_id: int) -> Dict[str, Any]:
        """Get availability information for an item.
        
        Args:
            item_type: Type of the item (material, product, tool)
            item_id: ID of the item
            
        Returns:
            Dict with availability information
        """
        try:
            inventory = self.get_by_item(item_type, item_id)
            return {
                'item_type': item_type,
                'item_id': item_id,
                'item_name': inventory.get('item_name', f'[MOCK] {item_type.capitalize()} {item_id}'),
                'quantity': inventory.get('quantity', 0),
                'status': inventory.get('status', 'OUT_OF_STOCK'),
                'storage_location': inventory.get('storage_location'),
                'last_updated': inventory.get('updated_at', datetime.now())
            }
        except KeyError:
            # Return default availability info
            return {
                'item_type': item_type,
                'item_id': item_id,
                'item_name': f'[MOCK] {item_type.capitalize()} {item_id}',
                'quantity': 0,
                'status': 'OUT_OF_STOCK',
                'storage_location': None,
                'last_updated': None
            }
    
    # Helper methods
    
    def _create_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a transaction.
        
        Args:
            data: Transaction data
            
        Returns:
            Created transaction
        """
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = self.next_transaction_id
            self.next_transaction_id += 1
        
        # Set timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        
        # Store transaction
        self.transactions[data['id']] = data
        return data