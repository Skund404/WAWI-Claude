"""
Core Dependency Injection Container.

Provides a unified container for managing service registrations
and resolving dependencies with support for different lifetimes
and lazy loading to handle circular dependencies.
"""

import inspect
import importlib
import logging
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar, Union, get_type_hints

T = TypeVar('T')

# Configure logger
logger = logging.getLogger(__name__)

class DIException(Exception):
    """Base exception for dependency injection errors."""
    pass

class RegistrationError(DIException):
    """Exception raised when service registration fails."""
    pass

class ResolutionError(DIException):
    """Exception raised when service resolution fails."""
    pass

class Lifetime(str, Enum):
    """Service lifetime options."""
    SINGLETON = "singleton"  # Single instance for all resolutions
    TRANSIENT = "transient"  # New instance for each resolution
    SCOPED = "scoped"        # Single instance within a scope


class ServiceRegistration:
    """Registration information for a service."""

    def __init__(
        self,
        implementation: Any = None,
        lifetime: Lifetime = Lifetime.SINGLETON,
        factory: Optional[Callable[..., Any]] = None,
        import_path: Optional[str] = None
    ):
        """
        Initialize a service registration.

        Args:
            implementation: The concrete implementation class (can be None if factory is provided)
            lifetime: Lifetime of the service (singleton, transient, scoped)
            factory: Optional factory function to create the service
            import_path: Optional dotted path for lazy loading
        """
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.import_path = import_path


class Container:
    """
    Dependency injection container with service lifetime management.

    Supports singleton, transient, and scoped lifetimes, as well as
    lazy loading for circular dependency resolution.
    """

    def __init__(self, parent: Optional['Container'] = None):
        """
        Initialize a new container.

        Args:
            parent: Optional parent container for hierarchical resolution
        """
        self._registrations: Dict[str, ServiceRegistration] = {}
        self._instances: Dict[str, Any] = {}
        self._parent = parent
        self._logger = logging.getLogger(__name__)

    def register(
        self,
        service_type: Union[str, Type[T]],
        implementation: Optional[Union[Type[Any], str, Callable[..., Any]]] = None,
        lifetime: Lifetime = Lifetime.SINGLETON
    ) -> 'Container':
        """
        Register a service with the container.

        Args:
            service_type: Interface or service name
            implementation: Concrete implementation class, module path string, or factory function
            lifetime: Service lifetime

        Returns:
            The container instance for method chaining

        Raises:
            RegistrationError: If registration fails
        """
        try:
            # Normalize the service key
            key = self._get_key(service_type)

            # Handle registration based on implementation type
            factory = None
            import_path = None

            if implementation is None:
                # Self-registration (typically for concrete classes)
                implementation = service_type
            elif isinstance(implementation, str):
                # String is treated as an import path for lazy loading
                import_path = implementation
                factory = lambda c: self._import_implementation(implementation)
                implementation = None
            elif callable(implementation) and not isinstance(implementation, type):
                # Factory function
                factory = implementation
                implementation = None

            # Create registration
            self._registrations[key] = ServiceRegistration(
                implementation=implementation,
                lifetime=lifetime,
                factory=factory,
                import_path=import_path
            )

            self._logger.debug(f"Registered service: {key}")
            return self

        except Exception as e:
            error_msg = f"Failed to register service {service_type}: {str(e)}"
            self._logger.error(error_msg)
            raise RegistrationError(error_msg) from e

    def register_instance(self, service_type: Union[str, Type[T]], instance: Any) -> 'Container':
        """
        Register a pre-constructed instance with the container.

        Args:
            service_type: Interface or service name
            instance: Constructed instance

        Returns:
            The container instance for method chaining
        """
        key = self._get_key(service_type)
        self._instances[key] = instance
        self._logger.debug(f"Registered instance: {key}")
        return self

    def register_factory(
        self,
        service_type: Union[str, Type[T]],
        factory: Callable[['Container'], Any],
        lifetime: Lifetime = Lifetime.SINGLETON
    ) -> 'Container':
        """
        Register a factory function for creating service instances.

        Args:
            service_type: Interface or service name
            factory: Factory function that receives the container
            lifetime: Service lifetime

        Returns:
            The container instance for method chaining
        """
        key = self._get_key(service_type)
        self._registrations[key] = ServiceRegistration(
            implementation=None,
            lifetime=lifetime,
            factory=factory
        )
        self._logger.debug(f"Registered factory: {key}")
        return self

    def is_registered(self, service_type: Union[str, Type[T]]) -> bool:
        """
        Check if a service is registered.

        Args:
            service_type: Service type to check

        Returns:
            True if the service is registered, False otherwise
        """
        key = self._get_key(service_type)
        return key in self._registrations or key in self._instances

    def resolve(self, service_type: Union[str, Type[T]]) -> Any:
        """
        Resolve a service instance.

        Args:
            service_type: Interface or service name

        Returns:
            An instance of the requested service

        Raises:
            ResolutionError: If resolution fails
        """
        try:
            # Normalize the key
            key = self._get_key(service_type)

            # Return cached instance if already exists
            if key in self._instances:
                return self._instances[key]

            # Create new instance if registered
            if key in self._registrations:
                return self._create_instance(key)

            # Try parent container if it exists
            if self._parent:
                return self._parent.resolve(service_type)

            # Not found
            raise ResolutionError(f"No registration found for {key}")

        except ResolutionError:
            raise
        except Exception as e:
            error_msg = f"Failed to resolve service {service_type}: {str(e)}"
            self._logger.error(error_msg)
            raise ResolutionError(error_msg) from e

    def create_scope(self) -> 'Container':
        """
        Create a new scoped container that shares singleton registrations with this container.

        Returns:
            A new scoped container
        """
        return Container(parent=self)

    def reset(self, include_singletons: bool = False) -> None:
        """
        Reset the container by clearing cached instances.

        Args:
            include_singletons: Whether to clear singleton instances too
        """
        # Clear non-singleton instances or all instances based on flag
        keys_to_remove = []
        for key, registration in self._registrations.items():
            if include_singletons or registration.lifetime != Lifetime.SINGLETON:
                if key in self._instances:
                    keys_to_remove.append(key)

        # Remove identified keys
        for key in keys_to_remove:
            del self._instances[key]

    def _get_key(self, service_type: Union[str, Type[T]]) -> str:
        """
        Convert a service type to a string key.

        Args:
            service_type: Interface or service name

        Returns:
            String key for the service
        """
        return service_type if isinstance(service_type, str) else service_type.__name__

    def _create_instance(self, key: str) -> Any:
        """
        Create an instance of a registered service.

        Args:
            key: Service key

        Returns:
            Service instance
        """
        registration = self._registrations[key]

        # Use factory if available
        if registration.factory:
            instance = registration.factory(self)
        elif registration.import_path:
            implementation = self._import_implementation(registration.import_path)
            instance = self._create_with_injection(implementation)
        else:
            # Create instance with constructor injection
            instance = self._create_with_injection(registration.implementation)

        # Cache instance based on lifetime
        if registration.lifetime == Lifetime.SINGLETON:
            self._instances[key] = instance

        return instance

    def _create_with_injection(self, implementation: Type[Any]) -> Any:
        """
        Create an instance with constructor injection.

        Args:
            implementation: Class to instantiate

        Returns:
            New instance
        """
        # Get constructor parameters
        signature = inspect.signature(implementation.__init__)
        parameters = {}

        for name, param in signature.parameters.items():
            # Skip self
            if name == 'self':
                continue

            # Get parameter type hint
            type_hints = get_type_hints(implementation.__init__)
            if name in type_hints:
                param_type = type_hints[name]
                try:
                    parameters[name] = self.resolve(param_type)
                except ResolutionError:
                    # Skip parameters that can't be resolved - they might have defaults
                    if param.default is param.empty:
                        self._logger.warning(
                            f"Could not resolve parameter '{name}' with type "
                            f"'{param_type}' for {implementation.__name__}"
                        )

        # Create instance
        return implementation(**parameters)

    def _import_implementation(self, import_path: str) -> Any:
        """
        Import a class from a string path.

        Args:
            import_path: Dotted path to the class

        Returns:
            The imported class

        Raises:
            ResolutionError: If import fails
        """
        try:
            module_path, class_name = import_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ResolutionError(f"Failed to import {import_path}: {str(e)}") from e


# Global container instance
_global_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get the global container instance.

    Returns:
        The global container

    Raises:
        RuntimeError: If container is not initialized
    """
    global _global_container

    if _global_container is None:
        raise RuntimeError("DI container is not initialized. Call create_container() first.")

    return _global_container


def set_container(container: Container) -> None:
    """
    Set the global container instance.

    Args:
        container: The container to set globally
    """
    global _global_container
    _global_container = container
    logger.info("Global DI container has been set")


def create_container() -> Container:
    """
    Create a new container and set it as the global container.

    Returns:
        The newly created container
    """
    container = Container()
    set_container(container)
    return container


def clear_container() -> None:
    """Clear the global container."""
    global _global_container
    _global_container = None
    logger.info("Global DI container has been cleared")