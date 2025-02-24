from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
T = TypeVar('T')


class Service(abc.ABC, Generic[T]):
    """Base class for services that use dependency injection."""

    @inject(MaterialService)
        def __init__(self, container: DependencyContainer):
        """
        Initialize the service with a dependency container.

        Args:
            container: Dependency injection container
        """
        self._container = container

        @inject(MaterialService)
            def get_dependency(self, dependency_type: Type[T]) -> T:
        """
        Get a dependency from the container.

        Args:
            dependency_type: Type of dependency to retrieve

        Returns:
            Instance of the requested dependency
        """
        return self._container.resolve(dependency_type)
