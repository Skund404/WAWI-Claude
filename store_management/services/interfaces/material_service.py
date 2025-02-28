from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

class MaterialType(Enum):
    """Types of materials used in leatherworking."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    LINING = "lining"
    ADHESIVE = "adhesive"
    OTHER = "other"

class IMaterialService(ABC):
    """Interface for the Material Service."""

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        """Create a new material."""
        pass

    @abstractmethod
    def get_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Get material by ID."""
        pass

    @abstractmethod
    def update(self, material_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing material."""
        pass

    @abstractmethod
    def delete(self, material_id: str) -> bool:
        """Delete a material."""
        pass

    @abstractmethod
    def get_materials(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """Get all materials, optionally filtered by type."""
        pass

    @abstractmethod
    def record_material_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a material transaction."""
        pass

    @abstractmethod
    def get_material_transactions(self, material_id: Optional[str] = None, transaction_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get material transactions with optional filtering."""
        pass

    @abstractmethod
    def calculate_material_cost(self, material_id: str, quantity: float) -> float:
        """Calculate cost for a given material quantity."""
        pass

    @abstractmethod
    def get_material_types(self) -> List[str]:
        """Get all available material types."""
        pass