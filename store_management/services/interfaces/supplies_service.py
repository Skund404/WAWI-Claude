from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class ISuppliesService(Protocol):
    """Interface for supplies-specific operations."""

    def get_by_id(self, supplies_id: int) -> Dict[str, Any]:
        """Get supplies by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all supplies materials, optionally filtered."""
        ...

    def create(self, supplies_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplies material."""
        ...

    def update(self, supplies_id: int, supplies_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplies material."""
        ...

    def delete(self, supplies_id: int) -> bool:
        """Delete a supplies material by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for supplies materials by properties."""
        ...

    def get_by_type(self, supplies_type: str) -> List[Dict[str, Any]]:
        """Get supplies materials by type (thread, adhesive, etc.)."""
        ...

    def get_by_color(self, color: str) -> List[Dict[str, Any]]:
        """Get supplies by color."""
        ...

    def get_inventory_status(self, supplies_id: int) -> Dict[str, Any]:
        """Get inventory status for a supplies material."""
        ...

    def adjust_inventory(self, supplies_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a supplies material."""
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get supplies materials by supplier ID."""
        ...

    def get_threads(self) -> List[Dict[str, Any]]:
        """Get all thread supplies."""
        ...

    def get_adhesives(self) -> List[Dict[str, Any]]:
        """Get all adhesive supplies."""
        ...

    def get_dyes(self) -> List[Dict[str, Any]]:
        """Get all dye supplies."""
        ...

    def get_finishes(self) -> List[Dict[str, Any]]:
        """Get all finish supplies."""
        ...