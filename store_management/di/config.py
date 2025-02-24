# di/config.py

from typing import Type, TypeVar
from .container import DependencyContainer

# Service interfaces
from services.interfaces.order_service import IOrderService
from database.repositories.interfaces.pattern_service import IRecipeService
from services.interfaces.shopping_list_service import IShoppingListService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService
from services.interfaces.supplier_service import ISupplierService
from services.interfaces.hardware_service import IHardwareService
from services.interfaces.material_service import IMaterialService

# Service implementations
from services.implementations.order_service import OrderService
from services.implementations.pattern_service import PatternService
from services.implementations.shopping_list_service import ShoppingListService
from services.implementations.project_service import ProjectService
from services.implementations.storage_service import StorageService
from services.implementations.supplier_service import SupplierService
from services.implementations.hardware_service import HardwareService
from services.implementations.material_service import MaterialService

T = TypeVar('T')


class ApplicationConfig:
    """
    Configuration class for dependency injection and service registration.

    Handles:
    - Service registration
    - Container configuration
    - Service resolution
    """

    _container: DependencyContainer = None

    @classmethod
    def configure_container(cls) -> None:
        """Configure the dependency injection container with all required services."""
        container = DependencyContainer()
        cls._register_services(container)
        ApplicationConfig._container = container

    @classmethod
    def _register_services(cls, container: DependencyContainer) -> None:
        """
        Register all application services.

        Args:
            container: Dependency container to register services with
        """
        # Register Order service
        container.register(
            IOrderService,
            lambda c: OrderService(c),
            singleton=True
        )

        # Register Pattern service
        container.register(
            IRecipeService,
            lambda c: RecipeService(c),
            singleton=True
        )

        # Register Shopping List service
        container.register(
            IShoppingListService,
            lambda c: ShoppingListService(c),
            singleton=True
        )

        # Register Project service
        container.register(
            IProjectService,
            lambda c: ProjectService(c),
            singleton=True
        )

        # Register Storage service
        container.register(
            IStorageService,
            lambda c: StorageService(c),
            singleton=True
        )

        # Register Supplier service
        container.register(
            ISupplierService,
            lambda c: SupplierService(c),
            singleton=True
        )

        # Register Hardware service
        container.register(
            IHardwareService,
            lambda c: HardwareService(c),
            singleton=True
        )

        # Register Material service
        container.register(
            IMaterialService,
            lambda c: MaterialService(c),
            singleton=True
        )

    @classmethod
    def get_container(cls) -> DependencyContainer:
        """
        Get the configured dependency container.

        Returns:
            DependencyContainer: Configured container instance

        Raises:
            RuntimeError: If container is not configured
        """
        if cls._container is None:
            raise RuntimeError("Container not configured. Call configure_container() first.")
        return cls._container

    @classmethod
    def get_service(cls, service_type: Type[T]) -> T:
        """
        Get a service instance of the specified type.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance

        Raises:
            RuntimeError: If container is not configured
            Exception: If service resolution fails
        """
        container = cls.get_container()
        return container.resolve(service_type)