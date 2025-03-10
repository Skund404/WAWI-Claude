from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IPurchaseService(Protocol):
    """Interface for purchase-related operations."""

    def get_by_id(self, purchase_id: int) -> Dict[str, Any]:
        """Get purchase by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all purchases, optionally filtered."""
        ...

    def create(self, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new purchase."""
        ...

    def update(self, purchase_id: int, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing purchase."""
        ...

    def delete(self, purchase_id: int) -> bool:
        """Delete a purchase by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for purchases by properties."""
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get purchases by supplier ID."""
        ...

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get purchases by status."""
        ...

    def add_item(self, purchase_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a purchase."""
        ...

    def update_item(self, purchase_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an item in a purchase."""
        ...

    def remove_item(self, purchase_id: int, item_id: int) -> bool:
        """Remove an item from a purchase."""
        ...

    def get_items(self, purchase_id: int) -> List[Dict[str, Any]]:
        """Get all items in a purchase."""
        ...

    def place_order(self, purchase_id: int) -> Dict[str, Any]:
        """Place an order for a purchase."""
        ...

    def receive_order(self, purchase_id: int, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Receive an order for a purchase."""
        ...

    def get_purchase_history(self, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get purchase history between dates."""
        ...

    def generate_purchase_report(self, start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate purchase report between dates."""
        ...

    def auto_generate_for_low_stock(self) -> Dict[str, Any]:
        """Auto-generate purchase orders for low stock items."""
        ...