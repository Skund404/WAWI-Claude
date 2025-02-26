# di/container.py
"""
Dependency Injection Container for managing service registrations and instantiations.

This module provides a flexible dependency injection mechanism
for the leatherworking store management application.
"""

import logging
from typing import Any, Callable, Dict, Optional, Type


class DependencyContainer:
    """
    A singleton dependency injection container for managing service registrations.

    Provides methods to register, retrieve, and manage service implementations
    across the application.
    """

    _instance = None
    _service_registry: Dict[Type, Any] = {}
    _service_instances: Dict[Type, Any] = {}

    def __new__(cls):
        """
        Implement singleton pattern for the dependency container.

        Returns:
            DependencyContainer: Singleton instance of the container
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the dependency container's internal state.
        """
        self._service_registry = {}
        self._service_instances = {}
        self._logger = logging.getLogger(__name__)

    def register(self, service_type: Type, service_impl: Any):
        """
        Register a service implementation for a given service type.

        Args:
            service_type (Type): Service interface or abstract base class
            service_impl (Any): Concrete service implementation or factory
        """
        try:
            self._service_registry[service_type] = service_impl
            self._logger.info(f"Registered service: {service_type.__name__} -> {service_impl}")
        except Exception as e:
            self._logger.error(f"Error registering service {service_type}: {e}")

    def get(self, service_type: Type):
        """
        Retrieve a service instance, creating it if not already instantiated.

        Alias for get_service to match the error log expectations.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance

        Raises:
            ValueError: If no implementation is registered for the service type
        """
        return self.get_service(service_type)

    def resolve(self, service_type: Type):
        """
        Resolve a service instance, creating it if not already instantiated.

        Alias for get_service to match the error log expectations.

        Args:
            service_type (Type): Service interface to resolve

        Returns:
            Any: Service implementation instance

        Raises:
            ValueError: If no implementation is registered for the service type
        """
        return self.get_service(service_type)

    def get_service(self, service_type: Type):
        """
        Retrieve a service instance, creating it if not already instantiated.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance

        Raises:
            ValueError: If no implementation is registered for the service type
        """
        try:
            # Check if an instance already exists
            if service_type in self._service_instances:
                return self._service_instances[service_type]

            # Find the implementation
            if service_type not in self._service_registry:
                raise ValueError(f"No implementation registered for {service_type.__name__}")

            # Get the implementation
            impl = self._service_registry[service_type]

            # If it's a lambda or callable, invoke it
            if callable(impl):
                service_instance = impl()
            else:
                # Otherwise, assume it's a class and instantiate
                service_instance = impl

            # Cache the instance
            self._service_instances[service_type] = service_instance

            return service_instance
        except Exception as e:
            self._logger.error(f"Error getting service {service_type}: {e}")
            raise

    def reset(self):
        """
        Reset the container, clearing all registered services and instances.

        Useful for testing or reinitialization.
        """
        self._service_registry.clear()
        self._service_instances.clear()
        self._logger.info("Dependency container reset")