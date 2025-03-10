from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IHardwareService(Protocol):
    """Interface for hardware-specific operations."""

    def get_by_id(self, hardware_id: int) -> Dict[str, Any]:
        """Get hardware by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all hardware materials, optionally filtered."""
        ...

    def create(self, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new hardware material."""
        ...

    def update(self, hardware_id: int, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing hardware material."""
        ...

    def delete(self, hardware_id: int) -> bool:
        """Delete a hardware material by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for hardware materials by properties."""
        ...

    def get_by_type(self, hardware_type: str) -> List[Dict[str, Any]]:
        """Get hardware materials by type."""
        ...

    def get_by_material(self, hardware_material: str) -> List[Dict[str, Any]]:
        """Get hardware by material type (brass, steel, etc.)."""
        ...

    def get_by_finish(self, finish: str) -> List[Dict[str, Any]]:
        """Get hardware by finish type."""
        ...

    def get_inventory_status(self, hardware_id: int) -> Dict[str, Any]:
        """Get inventory status for a hardware material."""
        ...

    def adjust_inventory(self, hardware_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a hardware material."""
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get hardware materials by supplier ID."""
        ...