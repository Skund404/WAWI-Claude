from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Container for managing dependencies and service instances
    using dependency injection pattern.
    """

    @inject(MaterialService)
        def __init__(self) -> None:
        """Initialize the dependency container."""
        self._registrations: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._singleton_flags: Dict[str, bool] = {}
        logger.debug('DependencyContainer initialized')

        @inject(MaterialService)
            def register(self, interface_type: str, implementation_factory:
                     Callable[['DependencyContainer'], Any], singleton: bool = False) -> None:
        """
        Register a service implementation with the container.

        Args:
            interface_type: String identifier for the service type
            implementation_factory: Factory function to create service instances
            singleton: Whether service should be a singleton

        Raises:
            ValueError: If interface_type is already registered
        """
        if interface_type in self._registrations:
            raise ValueError(f'Type {interface_type} is already registered')
        self._registrations[interface_type] = implementation_factory
        self._singleton_flags[interface_type] = singleton
        logger.debug(
            f'Registered service: {interface_type} (singleton={singleton})')

        @inject(MaterialService)
            def resolve(self, interface_type: str) -> Any:
        """
        Resolve and return a service instance.

        Args:
            interface_type: String identifier for the service type

        Returns:
            Service instance

        Raises:
            ValueError: If interface_type is not registered
        """
        if interface_type not in self._registrations:
            raise ValueError(f'No registration found for type {interface_type}'
                             )
        if self._singleton_flags.get(interface_type):
            if interface_type not in self._singletons:
                self._singletons[interface_type] = self._registrations[
                    interface_type](self)
            return self._singletons[interface_type]
        return self._registrations[interface_type](self)

        @inject(MaterialService)
            def get_service(self, interface_type: Type) -> Any:
        """
        Get a service instance by its type.

        Args:
            interface_type: Type of service to retrieve

        Returns:
            Service instance

        Raises:
            ValueError: If service type is not registered
        """
        type_name = interface_type.__name__
        try:
            return self.resolve(type_name)
        except Exception as e:
            logger.error(f'Error resolving service {type_name}: {str(e)}')
            raise ValueError(f'Could not resolve service {type_name}') from e

        @inject(MaterialService)
            def is_registered(self, interface_type: str) -> bool:
        """
        Check if a service type is registered.

        Args:
            interface_type: String identifier for the service type

        Returns:
            bool: True if service is registered, False otherwise
        """
        return interface_type in self._registrations

        @inject(MaterialService)
            def clear(self) -> None:
        """Clear all registrations and instances from the container."""
        self._registrations.clear()
        self._singletons.clear()
        self._singleton_flags.clear()
        logger.debug('Container cleared')

        @inject(MaterialService)
            def __repr__(self) -> str:
        """String representation of the container."""
        services = ', '.join(self._registrations.keys())
        return f'DependencyContainer(services=[{services}])'
