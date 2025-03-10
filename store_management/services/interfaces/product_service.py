from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IProductService(Protocol):
    """Interface for product-related operations."""

    def get_by_id(self, product_id: int) -> Dict[str, Any]:
        """Get product by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all products, optionally filtered."""
        ...

    def create(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        ...

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product."""
        ...

    def delete(self, product_id: int) -> bool:
        """Delete a product by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for products by name or other properties."""
        ...

    def get_by_pattern(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Get products using a specific pattern."""
        ...

    def get_inventory_status(self, product_id: int) -> Dict[str, Any]:
        """Get inventory status for a product."""
        ...

    def adjust_inventory(self, product_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a product."""
        ...

    def get_sales_history(self, product_id: int,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get sales history for a product."""
        ...

    def add_pattern_to_product(self, product_id: int, pattern_id: int) -> Dict[str, Any]:
        """Associate a pattern with a product."""
        ...

    def remove_pattern_from_product(self, product_id: int, pattern_id: int) -> bool:
        """Remove a pattern association from a product."""
        ...

    def calculate_production_cost(self, product_id: int) -> Dict[str, Any]:
        """Calculate the production cost for a product."""
        ...

    def get_best_sellers(self, limit: int = 10,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get the best-selling products."""
        ...