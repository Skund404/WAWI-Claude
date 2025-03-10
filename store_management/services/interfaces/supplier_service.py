from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class ISupplierService(Protocol):
    """Interface for supplier-related operations."""

    def get_by_id(self, supplier_id: int) -> Dict[str, Any]:
        """Get supplier by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all suppliers, optionally filtered."""
        ...

    def create(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier."""
        ...

    def update(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier."""
        ...

    def delete(self, supplier_id: int) -> bool:
        """Delete a supplier by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for suppliers by name or other properties."""
        ...

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get suppliers by status."""
        ...

    def get_materials_from_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get all materials supplied by a specific supplier."""
        ...

    def get_tools_from_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get all tools supplied by a specific supplier."""
        ...

    def get_purchase_history(self, supplier_id: int,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get purchase history for a supplier."""
        ...

    def get_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """Get performance metrics for a supplier."""
        ...