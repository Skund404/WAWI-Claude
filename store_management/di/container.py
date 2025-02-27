# di/container.py
import importlib
import inspect
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from utils.circular_import_resolver import CircularImportResolver, get_class, lazy_import

T = TypeVar('T')


class DependencyContainer:
    """Dependency injection container that manages service registrations and resolutions."""

    _instance = None

    def __new__(cls):
        """Singleton pattern implementation.

        Returns:
            DependencyContainer: Singleton instance of the container
        """
        if cls._instance is None:
            cls._instance = super(DependencyContainer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the container with empty registrations."""
        self.registrations = {}
        self.lazy_registrations = {}
        self.logger = logging.getLogger("di.container")

    def register(self, service_type: Type[T], service_impl: Any):
        """Register a service implementation.

        Args:
            service_type: Interface/abstract base class
            service_impl: Concrete implementation
        """
        service_name = getattr(service_type, "__name__", service_type)
        self.registrations[service_name] = service_impl
        self.logger.debug(
            f"Registered {service_name} -> {service_impl.__class__.__name__ if not isinstance(service_impl, type) else service_impl.__name__}")

    def register_lazy(self, service_name: str, module_path: str, class_name: str):
        """Register a service with lazy loading.

        Args:
            service_name: Name of the service interface
            module_path: Path to the module containing the implementation
            class_name: Name of the implementation class
        """
        self.lazy_registrations[service_name] = (module_path, class_name)
        self.logger.info(f"Registered lazy resolution for {service_name} to {module_path}.{class_name}")

    def get(self, service_type):
        """Get a service implementation.

        Args:
            service_type: Type or name of the service to retrieve

        Returns:
            Any: The service implementation

        Raises:
            ValueError: If no implementation is registered for the service
        """
        service_name = getattr(service_type, "__name__", service_type)

        # Check if already instantiated
        service = self.registrations.get(service_name)
        if service is not None:
            return service

        # Try lazy loading
        if service_name in self.lazy_registrations:
            try:
                module_path, class_name = self.lazy_registrations[service_name]

                # Import the module and get the class
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)

                # Instantiate the service
                service = cls()

                # Cache the resolved service
                self.registrations[service_name] = service
                return service
            except Exception as e:
                self.logger.error(f"Failed to lazily resolve {service_name} from {module_path}.{class_name}: {str(e)}")
                raise e

        error_msg = f"No implementation found for {service_name}"
        self.logger.error(f"Error retrieving service {service_name}: {error_msg}")
        raise ValueError(error_msg)