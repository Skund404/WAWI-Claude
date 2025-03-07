# database/services/interfaces/inventory_service.py
"""
Interface definition for Inventory Service.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union

from database.models.enums import (
    MaterialType,
    InventoryStatus,
    InventoryAdjustmentType
)
from database.models.product_inventory import ProductInventory
from database.models.material_inventory import MaterialInventory
from database.models.leather_inventory import LeatherInventory
from database.models.hardware_inventory import HardwareInventory
from database.models.tool_inventory import ToolInventory


class IInventoryService(ABC):
    """
    Interface defining contract for Inventory Service operations.
    """

    @abstractmethod
    def add_inventory(
        self,
        item_id: str,
        inventory_type: MaterialType,
        quantity: float,
        storage_location: Optional[str] = None,
        status: InventoryStatus = InventoryStatus.IN_STOCK
    ) -> Union[
        ProductInventory,
        MaterialInventory,
        LeatherInventory,
        HardwareInventory,
        ToolInventory
    ]:
        """
        Add or update inventory for a specific item.

        Args:
            item_id: Unique identifier of the item
            inventory_type: Type of material/item
            quantity: Quantity to add or update
            storage_location: Optional storage location
            status: Inventory status (default: IN_STOCK)

        Returns:
            Corresponding inventory instance
        """
        pass

    @abstractmethod
    def adjust_inventory(
        self,
        item_id: str,
        inventory_type: MaterialType,
        quantity_change: float,
        adjustment_type: InventoryAdjustmentType,
        storage_location: Optional[str] = None
    ) -> Union[
        ProductInventory,
        MaterialInventory,
        LeatherInventory,
        HardwareInventory,
        ToolInventory
    ]:
        """
        Adjust inventory quantity with specific adjustment type.

        Args:
            item_id: Unique identifier of the item
            inventory_type: Type of material/item
            quantity_change: Quantity to add or subtract
            adjustment_type: Type of inventory adjustment
            storage_location: Optional storage location

        Returns:
            Updated inventory instance
        """
        pass

    @abstractmethod
    def get_inventory_status(
        self,
        item_id: str,
        inventory_type: MaterialType
    ) -> Union[
        ProductInventory,
        MaterialInventory,
        LeatherInventory,
        HardwareInventory,
        ToolInventory
    ]:
        """
        Retrieve inventory status for a specific item.

        Args:
            item_id: Unique identifier of the item
            inventory_type: Type of material/item

        Returns:
            Inventory instance
        """
        pass

    @abstractmethod
    def get_low_stock_inventory(
        self,
        inventory_type: Optional[MaterialType] = None
    ) -> List[Union[
        ProductInventory,
        MaterialInventory,
        LeatherInventory,
        HardwareInventory,
        ToolInventory
    ]]:
        """
        Retrieve inventory items with low stock.

        Args:
            inventory_type: Optional specific inventory type to filter

        Returns:
            List of low stock inventory items
        """
        pass