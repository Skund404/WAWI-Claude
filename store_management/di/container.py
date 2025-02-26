# di/container.py
"""
Dependency injection container for managing service dependencies.
"""

import logging
from typing import Any, Dict, Optional, Type

# Configure logger
logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Container for managing dependency injection.
    Provides registration and resolution of service dependencies.
    """

    _instance = None

    def __new__(cls):
        """
        Implement singleton pattern for the dependency container.

        Returns:
            DependencyContainer: Singleton instance of the container
        """
        if cls._instance is None:
            logger.debug("Creating new DependencyContainer instance")
            cls._instance = super().__new__(cls)
            cls._instance._registrations = {}
            cls._instance._instances = {}
        return cls._instance

    def __init__(self):
        """Initialize the container if it hasn't been initialized yet."""
        if not hasattr(self, '_registrations'):
            self._registrations = {}
            self._instances = {}
            logger.debug("Initialized DependencyContainer")

    def register(self, service_type: Type, service_impl: Type):
        """
        Register a service implementation for a given service type.

        Args:
            service_type (Type): Service interface or abstract base class
            service_impl (Type): Concrete service implementation
        """
        logger.info(f"Registered service: {service_type.__name__} -> {service_impl.__name__}")
        self._registrations[service_type] = service_impl
        # Clear any cached instances of this type when re-registering
        if service_type in self._instances:
            del self._instances[service_type]

    def resolve(self, service_type: Type) -> Any:
        """
        Resolve a service type to its implementation instance.

        Args:
            service_type (Type): Service interface or abstract base class to resolve

        Returns:
            Any: Instance of the registered implementation

        Raises:
            ValueError: If no implementation is registered for the requested type
        """
        # Check if already instantiated
        if service_type in self._instances:
            logger.debug(f"Returning cached instance of {service_type.__name__}")
            return self._instances[service_type]

        # Check if type is registered
        if service_type not in self._registrations:
            error_msg = f"No implementation registered for {service_type.__name__}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Get implementation class
        impl_class = self._registrations[service_type]
        logger.debug(f"Creating new instance of {impl_class.__name__} for {service_type.__name__}")

        # Create instance
        try:
            instance = impl_class()
            # Cache the instance
            self._instances[service_type] = instance
            logger.debug(f"Successfully created {impl_class.__name__} instance")

            # Debug instance
            logger.debug(f"Instance methods: {[method for method in dir(instance) if not method.startswith('_')]}")

            return instance
        except Exception as e:
            error_msg = f"Error creating instance of {impl_class.__name__}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def get_service(self, service_type: Type) -> Any:
        """
        Alternative name for resolve method, for compatibility with some views.

        Args:
            service_type (Type): Service interface or abstract base class to resolve

        Returns:
            Any: Instance of the registered implementation
        """
        return self.resolve(service_type)

    def reset(self):
        """
        Reset the container, clearing all registered services and instances.

        Useful for testing or reinitialization.
        """
        logger.debug("Resetting dependency container")
        self._registrations.clear()
        self._instances.clear()