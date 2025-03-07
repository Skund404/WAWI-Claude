# database/services/implementations/inventory_service.py
"""
Service implementation for managing Inventory entities across different types.
"""

from typing import Any, Dict, List, Optional, Union
import logging
from datetime import datetime

from database.models.enums import (
    InventoryStatus,
    MaterialType,
    InventoryAdjustmentType,
)
from database.models.product_inventory import ProductInventory
from database.models.material_inventory import MaterialInventory
from database.models.leather_inventory import LeatherInventory
from database.models.hardware_inventory import HardwareInventory
from database.models.tool_inventory import ToolInventory

from database.repositories.product_inventory_repository import (
    ProductInventoryRepository,
)
from database.repositories.material_inventory_repository import (
    MaterialInventoryRepository,
)
from database.repositories.leather_inventory_repository import (
    LeatherInventoryRepository,
)
from database.repositories.hardware_inventory_repository import (
    HardwareInventoryRepository,
)
from database.repositories.tool_inventory_repository import ToolInventoryRepository

from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.inventory_service import IInventoryService


class InventoryService(BaseService, IInventoryService):
    """
    Comprehensive service for managing inventory across different entity types.

    Handles inventory tracking, status updates, and adjustments for:
    - Products
    - Materials
    - Leather
    - Hardware
    - Tools
    """

    def __init__(
        self,
        session=None,
        product_inventory_repository: Optional[ProductInventoryRepository] = None,
        material_inventory_repository: Optional[MaterialInventoryRepository] = None,
        leather_inventory_repository: Optional[LeatherInventoryRepository] = None,
        hardware_inventory_repository: Optional[HardwareInventoryRepository] = None,
        tool_inventory_repository: Optional[ToolInventoryRepository] = None,
    ):
        """
        Initialize the Inventory Service.

        Args:
            session: SQLAlchemy database session
            product_inventory_repository: Repository for product inventory
            material_inventory_repository: Repository for material inventory
            leather_inventory_repository: Repository for leather inventory
            hardware_inventory_repository: Repository for hardware inventory
            tool_inventory_repository: Repository for tool inventory
        """
        self.session = session or get_db_session()
        self.product_inventory_repo = (
            product_inventory_repository
            or ProductInventoryRepository(self.session)
        )
        self.material_inventory_repo = (
            material_inventory_repository
            or MaterialInventoryRepository(self.session)
        )
        self.leather_inventory_repo = (
            leather_inventory_repository
            or LeatherInventoryRepository(self.session)
        )
        self.hardware_inventory_repo = (
            hardware_inventory_repository
            or HardwareInventoryRepository(self.session)
        )
        self.tool_inventory_repo = (
            tool_inventory_repository
            or ToolInventoryRepository(self.session)
        )

        self.logger = logging.getLogger(__name__)

    def _get_inventory_repository(self, inventory_type: MaterialType):
        """
        Get the appropriate inventory repository based on material type.

        Args:
            inventory_type: Type of inventory

        Returns:
            Corresponding inventory repository
        """
        repositories = {
            MaterialType.THREAD: self.material_inventory_repo,
            MaterialType.LEATHER: self.leather_inventory_repo,
            MaterialType.HARDWARE: self.hardware_inventory_repo,
            MaterialType.OTHER: self.material_inventory_repo,
        }
        return repositories.get(inventory_type, self.material_inventory_repo)

    def _get_inventory_model(self, inventory_type: MaterialType):
        """
        Get the appropriate inventory model based on material type.

        Args:
            inventory_type: Type of inventory

        Returns:
            Corresponding inventory model class
        """
        models = {
            MaterialType.THREAD: MaterialInventory,
            MaterialType.LEATHER: LeatherInventory,
            MaterialType.HARDWARE: HardwareInventory,
            MaterialType.OTHER: MaterialInventory,
        }
        return models.get(inventory_type, MaterialInventory)

    def add_inventory(
        self,
        item_id: str,
        inventory_type: MaterialType,
        quantity: float,
        storage_location: Optional[str] = None,
        status: InventoryStatus = InventoryStatus.IN_STOCK,
    ) -> Union[
        ProductInventory,
        MaterialInventory,
        LeatherInventory,
        HardwareInventory,
        ToolInventory,
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

        Raises:
            NotFoundError: If item is not found
            ValidationError: If inventory addition fails
        """
        try:
            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be positive")

            # Get appropriate repository and model
            inventory_repo = self._get_inventory_repository(inventory_type)
            inventory_model = self._get_inventory_model(inventory_type)

            # Create inventory entry
            inventory_data = {
                f"{inventory_type.value}_id": item_id,
                "quantity": quantity,
                "storage_location": storage_location,
                "status": status,
            }

            inventory = inventory_model(**inventory_data)

            # Save inventory
            with self.session:
                self.session.add(inventory)
                self.session.commit()
                self.session.refresh(inventory)

            self.logger.info(f"Added inventory for {inventory_type}: {item_id}")
            return inventory

        except Exception as e:
            self.logger.error(f"Error adding inventory: {str(e)}")
            raise ValidationError(f"Inventory addition failed: {str(e)}")

    def adjust_inventory(
        self,
        item_id: str,
        inventory_type: MaterialType,
        quantity_change: float,
        adjustment_type: InventoryAdjustmentType,
        storage_location: Optional[str] = None,
    ) -> Union[
        ProductInventory,
        MaterialInventory,
        LeatherInventory,
        HardwareInventory,
        ToolInventory,
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

        Raises:
            NotFoundError: If inventory is not found
            ValidationError: If inventory adjustment fails
        """
        try:
            # Get appropriate repository
            inventory_repo = self._get_inventory_repository(inventory_type)

            # Find existing inventory
            item_key = f"{inventory_type.value}_id"
            existing_inventory = inventory_repo.get_by_item_id(item_id)

            if not existing_inventory:
                # If no existing inventory, create new
                return self.add_inventory(
                    item_id,
                    inventory_type,
                    abs(quantity_change),
                    storage_location,
                )

            # Adjust quantity based on adjustment type
            if adjustment_type in [
                InventoryAdjustmentType.INITIAL_STOCK,
                InventoryAdjustmentType.RESTOCK,
                InventoryAdjustmentType.RETURN,
                InventoryAdjustmentType.FOUND,
            ]:
                existing_inventory.quantity += abs(quantity_change)
            elif adjustment_type in [
                InventoryAdjustmentType.USAGE,
                InventoryAdjustmentType.DAMAGE,
                InventoryAdjustmentType.LOST,
            ]:
                if existing_inventory.quantity < abs(quantity_change):
                    raise ValidationError("Insufficient inventory for adjustment")
                existing_inventory.quantity -= abs(quantity_change)

            # Update storage location if provided
            if storage_location:
                existing_inventory.storage_location = storage_location

            # Update inventory status based on quantity
            if existing_inventory.quantity == 0:
                existing_inventory.status = InventoryStatus.OUT_OF_STOCK
            elif existing_inventory.quantity < 10:  # Adjust threshold as needed
                existing_inventory.status = InventoryStatus.LOW_STOCK
            else:
                existing_inventory.status = InventoryStatus.IN_STOCK

            # Save updated inventory
            with self.session:
                self.session.add(existing_inventory)
                self.session.commit()
                self.session.refresh(existing_inventory)

            self.logger.info(f"Adjusted inventory for {inventory_type}: {item_id}")
            return existing_inventory

        except Exception as e:
            self.logger.error(f"Error adjusting inventory: {str(e)}")
            raise ValidationError(f"Inventory adjustment failed: {str(e)}")

    def get_inventory_status(
        self, item_id: str, inventory_type: MaterialType
    ) -> Union[
        ProductInventory,
        MaterialInventory,
        LeatherInventory,
        HardwareInventory,
        ToolInventory,
    ]:
        """
        Retrieve inventory status for a specific item.

        Args:
            item_id: Unique identifier of the item
            inventory_type: Type of material/item

        Returns:
            Inventory instance

        Raises:
            NotFoundError: If inventory is not found
        """
        try:
            # Get appropriate repository
            inventory_repo = self._get_inventory_repository(inventory_type)

            # Find inventory
            inventory = inventory_repo.get_by_item_id(item_id)

            if not inventory:
                raise NotFoundError(
                    f"Inventory not found for {inventory_type}: {item_id}"
                )

            return inventory

        except Exception as e:
            self.logger.error(f"Error retrieving inventory status: {str(e)}")
            raise NotFoundError(f"Inventory status retrieval failed: {str(e)}")

    def get_low_stock_inventory(
        self, inventory_type: Optional[MaterialType] = None
    ) -> List[
        Union[
            ProductInventory,
            MaterialInventory,
            LeatherInventory,
            HardwareInventory,
            ToolInventory,
        ]
    ]:
        """
        Retrieve inventory items with low stock.

        Args:
            inventory_type: Optional specific inventory type to filter

        Returns:
            List of low stock inventory items
        """
        try:
            low_stock_inventories = []

            # Check each repository if no specific type is given
            if inventory_type is None:
                repositories = [
                    self.product_inventory_repo,
                    self.material_inventory_repo,
                    self.leather_inventory_repo,
                    self.hardware_inventory_repo,
                    self.tool_inventory_repo,
                ]
                for repo in repositories:
                    low_stock_inventories.extend(repo.get_low_stock_items())
            else:
                # Get specific repository
                inventory_repo = self._get_inventory_repository(inventory_type)
                low_stock_inventories = inventory_repo.get_low_stock_items()

            return low_stock_inventories

        except Exception as e:
            self.logger.error(f"Error retrieving low stock inventory: {str(e)}")
            return []