# services/interfaces/inventory_services.py
from abc import ABC, abstractmethod
from database.models.enums import InventoryStatus, MaterialType
from typing import Any, Dict, List, Optional
from datetime import datetime


class IGenericInventoryService(ABC):
    """Base interface for inventory services."""

    @abstractmethod
    def update_inventory(
            self,
            item_id: int,
            quantity: float,
            status: Optional[InventoryStatus] = None,
            storage_location: Optional[str] = None
    ) -> bool:
        """Update inventory details."""
        pass

    @abstractmethod
    def get_inventory_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve inventory item details."""
        pass

    @abstractmethod
    def list_inventory(
            self,
            status: Optional[InventoryStatus] = None,
            storage_location: Optional[str] = None,
            **filters
    ) -> List[Dict[str, Any]]:
        """List inventory items with optional filtering."""
        pass


class IProductInventoryService(IGenericInventoryService):
    """Interface for product inventory management."""

    @abstractmethod
    def update_product_stock(
            self,
            product_id: int,
            quantity: int,
            storage_location: Optional[str] = None
    ) -> bool:
        """Update stock for a specific product."""
        pass


class IMaterialInventoryService(IGenericInventoryService):
    """Interface for material inventory management."""

    @abstractmethod
    def get_materials_by_type(
            self,
            material_type: Optional[MaterialType] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve materials by type."""
        pass


class ILeatherInventoryService(IGenericInventoryService):
    """Interface for leather inventory management."""
    pass


class IHardwareInventoryService(IGenericInventoryService):
    """Interface for hardware inventory management."""
    pass


class IToolInventoryService(IGenericInventoryService):
    """Interface for tool inventory management."""
    pass