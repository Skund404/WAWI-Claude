# database/repositories/repository_factory.py
"""Factory for creating and managing repository instances."""

import logging
from typing import Dict, Optional, Type

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from .component_repository import ComponentRepository
from .customer_repository import CustomerRepository
from .hardware_repository import HardwareRepository
from .hardware_inventory_repository import HardwareInventoryRepository
from .inventory_repository import InventoryRepository
from .leather_repository import LeatherRepository
from .leather_inventory_repository import LeatherInventoryRepository
from .material_repository import MaterialRepository
from .material_inventory_repository import MaterialInventoryRepository
from .pattern_repository import PatternRepository
from .picking_list_repository import PickingListRepository
from .product_repository import ProductRepository
from .product_inventory_repository import ProductInventoryRepository
from .product_pattern_repository import ProductPatternRepository
from .project_repository import ProjectRepository
from .project_component_repository import ProjectComponentRepository
from .purchase_repository import PurchaseRepository
from .purchase_item_repository import PurchaseItemRepository
from .sales_repository import SalesRepository
from .sales_item_repository import SalesItemRepository

from .storage_repository import StorageRepository
from .supplier_repository import SupplierRepository
from .tool_repository import ToolRepository
from .tool_inventory_repository import ToolInventoryRepository
from .tool_list_repository import ToolListRepository
from .transaction_repository import TransactionRepository


class RepositoryFactory:
    """Factory class for creating repository instances.

    This factory manages the creation and caching of repository instances
    to ensure consistent access to repositories throughout the application.
    """

    def __init__(self, session: Session):
        """Initialize the repository factory.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.logger = logging.getLogger(__name__)
        self._repositories: Dict[str, BaseRepository] = {}

    def get_component_repository(self) -> ComponentRepository:
        """Get or create a ComponentRepository instance.

        Returns:
            ComponentRepository instance
        """
        return self._get_repository('component', ComponentRepository)

    def get_customer_repository(self) -> CustomerRepository:
        """Get or create a CustomerRepository instance.

        Returns:
            CustomerRepository instance
        """
        return self._get_repository('customer', CustomerRepository)

    def get_hardware_repository(self) -> HardwareRepository:
        """Get or create a HardwareRepository instance.

        Returns:
            HardwareRepository instance
        """
        return self._get_repository('hardware', HardwareRepository)

    def get_hardware_inventory_repository(self) -> HardwareInventoryRepository:
        """Get or create a HardwareInventoryRepository instance.

        Returns:
            HardwareInventoryRepository instance
        """
        return self._get_repository('hardware_inventory', HardwareInventoryRepository)

    def get_inventory_repository(self) -> InventoryRepository:
        """Get or create an InventoryRepository instance.

        Returns:
            InventoryRepository instance
        """
        return self._get_repository('inventory', InventoryRepository)

    def get_leather_repository(self) -> LeatherRepository:
        """Get or create a LeatherRepository instance.

        Returns:
            LeatherRepository instance
        """
        return self._get_repository('leather', LeatherRepository)

    def get_leather_inventory_repository(self) -> LeatherInventoryRepository:
        """Get or create a LeatherInventoryRepository instance.

        Returns:
            LeatherInventoryRepository instance
        """
        return self._get_repository('leather_inventory', LeatherInventoryRepository)

    def get_material_repository(self) -> MaterialRepository:
        """Get or create a MaterialRepository instance.

        Returns:
            MaterialRepository instance
        """
        return self._get_repository('material', MaterialRepository)

    def get_material_inventory_repository(self) -> MaterialInventoryRepository:
        """Get or create a MaterialInventoryRepository instance.

        Returns:
            MaterialInventoryRepository instance
        """
        return self._get_repository('material_inventory', MaterialInventoryRepository)

    def get_pattern_repository(self) -> PatternRepository:
        """Get or create a PatternRepository instance.

        Returns:
            PatternRepository instance
        """
        return self._get_repository('pattern', PatternRepository)

    def get_picking_list_repository(self) -> PickingListRepository:
        """Get or create a PickingListRepository instance.

        Returns:
            PickingListRepository instance
        """
        return self._get_repository('picking_list', PickingListRepository)

    def get_product_repository(self) -> ProductRepository:
        """Get or create a ProductRepository instance.

        Returns:
            ProductRepository instance
        """
        return self._get_repository('product', ProductRepository)

    def get_product_inventory_repository(self) -> ProductInventoryRepository:
        """Get or create a ProductInventoryRepository instance.

        Returns:
            ProductInventoryRepository instance
        """
        return self._get_repository('product_inventory', ProductInventoryRepository)

    def get_product_pattern_repository(self) -> ProductPatternRepository:
        """Get or create a ProductPatternRepository instance.

        Returns:
            ProductPatternRepository instance
        """
        return self._get_repository('product_pattern', ProductPatternRepository)

    def get_project_repository(self) -> ProjectRepository:
        """Get or create a ProjectRepository instance.

        Returns:
            ProjectRepository instance
        """
        return self._get_repository('project', ProjectRepository)

    def get_project_component_repository(self) -> ProjectComponentRepository:
        """Get or create a ProjectComponentRepository instance.

        Returns:
            ProjectComponentRepository instance
        """
        return self._get_repository('project_component', ProjectComponentRepository)

    def get_purchase_repository(self) -> PurchaseRepository:
        """Get or create a PurchaseRepository instance.

        Returns:
            PurchaseRepository instance
        """
        return self._get_repository('purchase', PurchaseRepository)

    def get_purchase_item_repository(self) -> PurchaseItemRepository:
        """Get or create a PurchaseItemRepository instance.

        Returns:
            PurchaseItemRepository instance
        """
        return self._get_repository('purchase_item', PurchaseItemRepository)

    def get_sales_repository(self) -> SalesRepository:
        """Get or create a SalesRepository instance.

        Returns:
            SalesRepository instance
        """
        return self._get_repository('sales', SalesRepository)

    def get_sales_item_repository(self) -> SalesItemRepository:
        """Get or create a SalesItemRepository instance.

        Returns:
            SalesItemRepository instance
        """
        return self._get_repository('sales_item', SalesItemRepository)


    def get_storage_repository(self) -> StorageRepository:
        """Get or create a StorageRepository instance.

        Returns:
            StorageRepository instance
        """
        return self._get_repository('storage', StorageRepository)

    def get_supplier_repository(self) -> SupplierRepository:
        """Get or create a SupplierRepository instance.

        Returns:
            SupplierRepository instance
        """
        return self._get_repository('supplier', SupplierRepository)

    def get_tool_repository(self) -> ToolRepository:
        """Get or create a ToolRepository instance.

        Returns:
            ToolRepository instance
        """
        return self._get_repository('tool', ToolRepository)

    def get_tool_inventory_repository(self) -> ToolInventoryRepository:
        """Get or create a ToolInventoryRepository instance.

        Returns:
            ToolInventoryRepository instance
        """
        return self._get_repository('tool_inventory', ToolInventoryRepository)

    def get_tool_list_repository(self) -> ToolListRepository:
        """Get or create a ToolListRepository instance.

        Returns:
            ToolListRepository instance
        """
        return self._get_repository('tool_list', ToolListRepository)

    def get_transaction_repository(self) -> TransactionRepository:
        """Get or create a TransactionRepository instance.

        Returns:
            TransactionRepository instance
        """
        return self._get_repository('transaction', TransactionRepository)

    def _get_repository(self, key: str, repository_class: Type) -> BaseRepository:
        """Get an existing repository or create a new one.

        Args:
            key: Repository key for caching
            repository_class: Repository class to instantiate

        Returns:
            Repository instance
        """
        if key not in self._repositories:
            self._repositories[key] = repository_class(self.session)
            self.logger.debug(f"Created new {key} repository")
        return self._repositories[key]