# database/repositories/repository_factory.py
"""
Factory for creating repository instances.
Centralizes repository instantiation and session management.
"""

import logging
from typing import Dict, Optional, Type
from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from .leather_repository import LeatherRepository
from .hardware_repository import HardwareRepository
from .supplies_repository import SuppliesRepository
from .material_repository import MaterialRepository
from .component_repository import ComponentRepository
from .customer_repository import CustomerRepository
from .inventory_repository import InventoryRepository
from .pattern_repository import PatternRepository
from .picking_list_repository import PickingListRepository
from .product_repository import ProductRepository
from .project_component_repository import ProjectComponentRepository
from .project_repository import ProjectRepository
from .purchase_item_repository import PurchaseItemRepository
from .purchase_repository import PurchaseRepository
from .sales_item_repository import SalesItemRepository
from .sales_repository import SalesRepository

from .supplier_repository import SupplierRepository
from .tool_list_repository import ToolListRepository
from .tool_repository import ToolRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class RepositoryFactory:
    """
    Factory for creating repository instances.

    Provides centralized repository creation, caching, and session management.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository factory.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self._repositories: Dict[str, BaseRepository] = {}
        logger.debug("Initialized RepositoryFactory")

    def get_repository(self, repository_class: Type[BaseRepository]) -> BaseRepository:
        """
        Get or create a repository instance of the specified type.

        Args:
            repository_class: Repository class to instantiate

        Returns:
            BaseRepository: Repository instance
        """
        repository_name = repository_class.__name__

        # Return cached repository if exists
        if repository_name in self._repositories:
            return self._repositories[repository_name]

        # Create new repository instance
        repository = repository_class(self.session)
        self._repositories[repository_name] = repository
        logger.debug(f"Created new {repository_name} instance")

        return repository

    def get_leather_repository(self) -> LeatherRepository:
        """Get the leather repository."""
        return self.get_repository(LeatherRepository)

    def get_hardware_repository(self) -> HardwareRepository:
        """Get the hardware repository."""
        return self.get_repository(HardwareRepository)

    def get_supplies_repository(self) -> SuppliesRepository:
        """Get the supplies repository."""
        return self.get_repository(SuppliesRepository)

    def get_material_repository(self) -> MaterialRepository:
        """Get the general material repository."""
        return self.get_repository(MaterialRepository)

    def get_component_repository(self) -> ComponentRepository:
        """Get the component repository."""
        return self.get_repository(ComponentRepository)

    def get_customer_repository(self) -> CustomerRepository:
        """Get the customer repository."""
        return self.get_repository(CustomerRepository)

    def get_inventory_repository(self) -> InventoryRepository:
        """Get the inventory repository."""
        return self.get_repository(InventoryRepository)

    def get_pattern_repository(self) -> PatternRepository:
        """Get the pattern repository."""
        return self.get_repository(PatternRepository)

    def get_picking_list_repository(self) -> PickingListRepository:
        """Get the picking list repository."""
        return self.get_repository(PickingListRepository)

    def get_product_repository(self) -> ProductRepository:
        """Get the product repository."""
        return self.get_repository(ProductRepository)

    def get_project_repository(self) -> ProjectRepository:
        """Get the project repository."""
        return self.get_repository(ProjectRepository)

    def get_project_component_repository(self) -> ProjectComponentRepository:
        """Get the project component repository."""
        return self.get_repository(ProjectComponentRepository)

    def get_purchase_repository(self) -> PurchaseRepository:
        """Get the purchase repository."""
        return self.get_repository(PurchaseRepository)

    def get_purchase_item_repository(self) -> PurchaseItemRepository:
        """Get the purchase item repository."""
        return self.get_repository(PurchaseItemRepository)

    def get_sales_repository(self) -> SalesRepository:
        """Get the sales repository."""
        return self.get_repository(SalesRepository)

    def get_sales_item_repository(self) -> SalesItemRepository:
        """Get the sales item repository."""
        return self.get_repository(SalesItemRepository)

    def get_supplier_repository(self) -> SupplierRepository:
        """Get the supplier repository."""
        return self.get_repository(SupplierRepository)

    def get_tool_repository(self) -> ToolRepository:
        """Get the tool repository."""
        return self.get_repository(ToolRepository)

    def get_tool_list_repository(self) -> ToolListRepository:
        """Get the tool list repository."""
        return self.get_repository(ToolListRepository)

    def clear_cache(self) -> None:
        """
        Clear the repository cache.

        Useful for testing or when repository instances need to be refreshed.
        """
        self._repositories.clear()
        logger.debug("Cleared repository cache")