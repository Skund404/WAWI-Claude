# di/container.py
import importlib
import inspect
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

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
        self.instance_cache = {}  # New cache for instances

    def register(self, service_type: Union[Type[T], str], service_impl: Any):
        """Register a service implementation.

        Args:
            service_type: Interface/abstract base class or service name
            service_impl: Concrete implementation
        """
        # Handle different ways to specify the service type
        if isinstance(service_type, str):
            service_name = service_type
        elif hasattr(service_type, "__name__"):
            service_name = service_type.__name__
        else:
            service_name = str(service_type)

        # Also register by full path if it's a class
        if inspect.isclass(service_type) and hasattr(service_type, "__module__"):
            full_path = f"{service_type.__module__}.{service_type.__name__}"
            self.registrations[full_path] = service_impl
            self.logger.debug(f"Registered by full path: {full_path}")

        self.registrations[service_name] = service_impl
        impl_name = (service_impl.__class__.__name__ if not isinstance(service_impl, type)
                     else service_impl.__name__) if not callable(service_impl) or inspect.isclass(
            service_impl) else "function"
        self.logger.debug(f"Registered {service_name} -> {impl_name}")

    def register_lazy(self, service_name: str, module_path: str, class_name: str):
        """Register a service with lazy loading.

        Args:
            service_name: Name of the service interface
            module_path: Path to the module containing the implementation
            class_name: Name of the implementation class
        """
        self.lazy_registrations[service_name] = (module_path, class_name)

        # Also register by expected interface paths
        if '.' not in service_name:
            # Try common interface paths
            potential_paths = [
                f"services.interfaces.{service_name}",
                f"services.interfaces.{service_name.lower()}_service.{service_name}",
                f"services.interfaces.{service_name.lower()}_service.I{service_name}"  # Handle 'I' prefix convention
            ]
            for path in potential_paths:
                self.lazy_registrations[path] = (module_path, class_name)

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
        # Check if we have a cached instance
        if service_type in self.instance_cache:
            return self.instance_cache[service_type]

        # Handle different ways to specify the service type
        if isinstance(service_type, str):
            service_name = service_type
        elif hasattr(service_type, "__name__"):
            service_name = service_type.__name__
        else:
            service_name = str(service_type)

        # Also try by full path
        full_path = None
        if hasattr(service_type, "__module__") and hasattr(service_type, "__name__"):
            full_path = f"{service_type.__module__}.{service_type.__name__}"

        # Try finding the service by name
        service = self.registrations.get(service_name)

        # If not found and full path is available, try by full path
        if service is None and full_path is not None:
            service = self.registrations.get(full_path)

        if service is not None:
            # If it's a factory function, call it
            if callable(service) and not inspect.isclass(service):
                try:
                    instance = service()
                    self.registrations[service_name] = instance  # Cache the instance
                    if full_path:
                        self.registrations[full_path] = instance  # Also cache by full path

                    # Store in instance cache
                    self.instance_cache[service_type] = instance

                    return instance
                except Exception as e:
                    self.logger.error(f"Error instantiating service {service_name}: {str(e)}")
                    raise e

            # Store in instance cache
            self.instance_cache[service_type] = service

            return service

        # Try lazy loading
        lazy_key = None
        for key in [service_name, full_path]:
            if key is not None and key in self.lazy_registrations:
                lazy_key = key
                break

        if lazy_key is not None:
            try:
                module_path, class_name = self.lazy_registrations[lazy_key]
                self.logger.debug(f"Lazy loading {lazy_key} from {module_path}.{class_name}")

                # Import the module and get the class
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)

                # Instantiate the service
                service = cls()

                # Cache the resolved service
                self.registrations[service_name] = service
                if full_path:
                    self.registrations[full_path] = service

                # Store in instance cache
                self.instance_cache[service_type] = service

                return service
            except Exception as e:
                self.logger.error(f"Failed to lazily resolve {lazy_key} from {module_path}.{class_name}: {str(e)}")
                raise e

        # Handle interface variations
        if isinstance(service_name, str):
            # Try with 'I' prefix for interfaces if not present
            if not service_name.startswith('I') and f"I{service_name}" in self.registrations:
                service = self.registrations[f"I{service_name}"]
                self.instance_cache[service_type] = service
                return service

            # Try without 'I' prefix if present
            if service_name.startswith('I') and service_name[1:] in self.registrations:
                service = self.registrations[service_name[1:]]
                self.instance_cache[service_type] = service
                return service

        # Check for partial matches in lazy registrations
        if isinstance(service_name, str):
            for key, value in self.lazy_registrations.items():
                if key.endswith(service_name) or key.endswith(f"I{service_name}"):
                    try:
                        module_path, class_name = value
                        self.logger.debug(f"Trying partial match: {key} for {service_name}")

                        # Import the module and get the class
                        module = importlib.import_module(module_path)
                        cls = getattr(module, class_name)

                        # Instantiate the service
                        service = cls()

                        # Cache the resolved service
                        self.registrations[service_name] = service
                        if full_path:
                            self.registrations[full_path] = service

                        # Store in instance cache
                        self.instance_cache[service_type] = service

                        return service
                    except Exception as e:
                        self.logger.warning(f"Failed to resolve partial match {key} for {service_name}: {str(e)}")
                        # Continue trying other matches

        error_msg = f"No implementation found for {service_name}"
        self.logger.error(f"Error retrieving service {service_name}: {error_msg}")
        self.logger.debug(f"Available registrations: {list(self.registrations.keys())}")
        self.logger.debug(f"Available lazy registrations: {list(self.lazy_registrations.keys())}")
        raise ValueError(error_msg)

    def clear_cache(self):
        """Clear the instance cache to force new instances on next get() call."""
        self.instance_cache.clear()
        self.logger.debug("Instance cache cleared")