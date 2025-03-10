from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class ILeatherService(Protocol):
    """Interface for leather-specific operations."""

    def get_by_id(self, leather_id: int) -> Dict[str, Any]:
        """Get leather by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all leather materials, optionally filtered."""
        ...

    def create(self, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new leather material."""
        ...

    def update(self, leather_id: int, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing leather material."""
        ...

    def delete(self, leather_id: int) -> bool:
        """Delete a leather material by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for leather materials by properties."""
        ...

    def get_by_type(self, leather_type: str) -> List[Dict[str, Any]]:
        """Get leather materials by type."""
        ...

    def get_by_finish(self, finish: str) -> List[Dict[str, Any]]:
        """Get leather materials by finish."""
        ...

    def get_by_thickness_range(self, min_thickness: float, max_thickness: float) -> List[Dict[str, Any]]:
        """Get leather materials within a thickness range."""
        ...

    def get_inventory_status(self, leather_id: int) -> Dict[str, Any]:
        """Get inventory status for a leather material."""
        ...

    def adjust_inventory(self, leather_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a leather material."""
        ...

    def calculate_area_remaining(self, leather_id: int) -> Dict[str, Any]:
        """Calculate the remaining area of a leather hide."""
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get leather materials by supplier ID."""
        ...