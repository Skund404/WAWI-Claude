# store_management/database/repositories/repository_factory.py
"""
Factory for creating repository instances.

Provides a centralized mechanism for creating and managing 
repository instances with caching and dynamic registration capabilities.
"""

from typing import Dict, Type, Optional
from sqlalchemy.orm import Session
import logging

# Import specific repository classes
from .product_repository import ProductRepository
from .order_repository import OrderRepository
from .supplier_repository import SupplierRepository
from .storage_repository import StorageRepository
from .part_repository import PartRepository
from .project_repository import ProjectRepository
from .shopping_list_repository import ShoppingListRepository
from .hardware_repository import HardwareRepository

# Base repository type hint
from .base_repository import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)


class RepositoryFactory:
    """
    A factory class for creating and managing repository instances.

    Provides methods for registering, retrieving, and caching 
    repository instances with dynamic model support.

    Attributes:
        _repository_classes (Dict[str, Type[BaseRepository]]): 
            Registered repository classes
        _repositories (Dict[str, BaseRepository]): 
            Cached repository instances
    """

    # Default repository mappings
    _repository_classes: Dict[str, Type[BaseRepository]] = {
        'Supplier': SupplierRepository,
        'Storage': StorageRepository,
        'Product': ProductRepository,
        'Order': OrderRepository,
        'Part': PartRepository,
        'Project': ProjectRepository,
        'ShoppingList': ShoppingListRepository,
        'Hardware': HardwareRepository
    }

    # Instance cache
    _repositories: Dict[str, BaseRepository] = {}

    @classmethod
    def register_repository(
            cls,
            model_name: str,
            repository_class: Type[BaseRepository]
    ) -> None:
        """
        Register a custom repository class for a specific model.

        Args:
            model_name (str): The name of the model
            repository_class (Type[BaseRepository]): The repository class to register

        Example:
            RepositoryFactory.register_repository('CustomModel', CustomModelRepository)
        """
        try:
            cls._repository_classes[model_name] = repository_class
            logger.debug(
                f'Registered repository for {model_name}: {repository_class.__name__}'
            )
        except Exception as e:
            logger.error(f'Error registering repository for {model_name}: {e}')
            raise

    @classmethod
    def get_repository(
            cls,
            model_name: str,
            session: Session
    ) -> BaseRepository:
        """
        Retrieve a repository instance for a specific model.

        Args:
            model_name (str): The name of the model
            session (Session): SQLAlchemy database session

        Returns:
            BaseRepository: A repository instance for the specified model

        Raises:
            ValueError: If no repository is registered for the model
        """
        try:
            # Create a unique key for the repository instance
            key = f'{model_name}_{id(session)}'

            # Return cached repository if exists
            if key in cls._repositories:
                return cls._repositories[key]

            # Check if repository is registered
            if model_name not in cls._repository_classes:
                raise ValueError(f'No repository registered for model: {model_name}')

            # Create new repository instance
            repository_class = cls._repository_classes[model_name]
            repository = repository_class(session)

            # Cache the repository instance
            cls._repositories[key] = repository

            return repository
        except Exception as e:
            logger.error(f'Error getting repository for {model_name}: {e}')
            raise

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the repository instance cache.

        Useful for cleaning up resources or resetting the factory 
        between test cases or long-running processes.
        """
        try:
            cls._repositories.clear()
            logger.info('Repository cache cleared')
        except Exception as e:
            logger.error(f'Error clearing repository cache: {e}')
            raise

    @classmethod
    def get_all_repositories(cls) -> Dict[str, Type[BaseRepository]]:
        """
        Retrieve all registered repository classes.

        Returns:
            Dict[str, Type[BaseRepository]]: Mapping of model names to repository classes
        """
        return cls._repository_classes.copy()

    @classmethod
    def unregister_repository(cls, model_name: str) -> None:
        """
        Unregister a repository for a specific model.

        Args:
            model_name (str): The name of the model to unregister

        Raises:
            KeyError: If the model name is not registered
        """
        try:
            # Remove repository class
            del cls._repository_classes[model_name]

            # Remove any cached instances
            keys_to_remove = [
                key for key in cls._repositories
                if key.startswith(f'{model_name}_')
            ]
            for key in keys_to_remove:
                del cls._repositories[key]

            logger.debug(f'Unregistered repository for {model_name}')
        except KeyError:
            logger.warning(f'Cannot unregister non-existent repository: {model_name}')
        except Exception as e:
            logger.error(f'Error unregistering repository for {model_name}: {e}')
            raise