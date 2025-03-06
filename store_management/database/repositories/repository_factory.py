# database/repositories/repository_factory.py
"""
Factory for creating repository instances.

This module provides a centralized factory for creating repository instances,
ensuring consistent repository creation and configuration throughout the application.
"""

import logging
from typing import Dict, Optional, Type

from sqlalchemy.orm import Session

from .base_repository import BaseRepository
from .hardware_repository import HardwareRepository
from .product_repository import ProductRepository
from .project_repository import ProjectRepository
from .shopping_list_repository import ShoppingListRepository
from .storage_repository import StorageRepository
from .supplier_repository import SupplierRepository
from .pattern_repository import PatternRepository
from .product_pattern_repository import ProductPatternRepository
from .product_inventory_repository import ProductInventoryRepository
from .sales_repository import SalesRepository
from .sales_item_repository import SalesItemRepository
from .picking_list_repository import PickingListRepository

# Setup logger
logger = logging.getLogger(__name__)


class RepositoryFactory:
    """Factory for creating repository instances."""

    # Mapping of repository types to their classes
    _repository_types: Dict[str, Type[BaseRepository]] = {
        'hardware': HardwareRepository,
        'product': ProductRepository,
        'project': ProjectRepository,
        'shopping_list': ShoppingListRepository,
        'storage': StorageRepository,
        'supplier': SupplierRepository,
        'pattern': PatternRepository,
        'product_pattern': ProductPatternRepository,
        'product_inventory': ProductInventoryRepository,
        'sales': SalesRepository,
        'sales_item': SalesItemRepository,
        'picking_list': PickingListRepository,
    }

    @classmethod
    def create(cls, repo_type: str, session: Session) -> BaseRepository:
        """
        Create a repository of the specified type.

        Args:
            repo_type: Type of repository to create
            session: SQLAlchemy database session

        Returns:
            BaseRepository: The created repository

        Raises:
            ValueError: If the repository type is not supported
        """
        if repo_type not in cls._repository_types:
            valid_types = ", ".join(cls._repository_types.keys())
            error_msg = f"Unsupported repository type '{repo_type}'. Valid types: {valid_types}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        repo_class = cls._repository_types[repo_type]
        repository = repo_class(session)
        logger.debug(f"Created repository of type '{repo_type}'")
        return repository

    @classmethod
    def register_repository_type(cls, name: str, repo_class: Type[BaseRepository]) -> None:
        """
        Register a new repository type.

        Args:
            name: Name to register the repository type under
            repo_class: The repository class

        Raises:
            ValueError: If the name is already registered
        """
        if name in cls._repository_types:
            error_msg = f"Repository type '{name}' is already registered"
            logger.error(error_msg)
            raise ValueError(error_msg)

        cls._repository_types[name] = repo_class
        logger.debug(f"Registered repository type '{name}'")