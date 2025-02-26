# store_management/di/config.py
"""
Dependency Injection Configuration Management.

Provides configuration and management for service containers.
"""

import logging
import importlib
from typing import Any, Dict, Optional, Type

from utils.circular_import_resolver import CircularImportResolver


class ServiceContainer:
    """
    Centralized service container for managing and retrieving service implementations.
    """
    _instance = None
    _services: Dict[str, Any] = {}

    def __new__(cls):
        """
        Implement singleton pattern to ensure only one instance exists.

        Returns:
            ServiceContainer: The singleton instance of the service container
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
        return cls._instance

    def register_service(
            self,
            service_type: str,
            service_impl: Optional[Type[Any]] = None,
            import_path: Optional[str] = None
    ):
        """
        Register a service implementation.

        Args:
            service_type (str): The type of service to register
            service_impl (Optional[Type[Any]], optional): Direct service implementation
            import_path (Optional[str], optional): Module path for lazy import
        """
        try:
            if service_impl:
                self._services[service_type] = service_impl
            elif import_path:
                # Register lazy import
                self._services[service_type] = lambda: CircularImportResolver.lazy_import(
                    import_path,
                    service_type
                )

            logging.info(f"Registered service: {service_type}")
        except Exception as e:
            logging.error(f"Failed to register service {service_type}: {e}")

    def get_service(self, service_type: str) -> Any:
        """
        Retrieve a service implementation.

        Args:
            service_type (str): The type of service to retrieve

        Returns:
            Any: The service implementation instance
        """
        try:
            service_factory = self._services.get(service_type)
            if service_factory is None:
                raise ValueError(f"No implementation found for {service_type}")

            # Handle lazy import or direct instantiation
            return service_factory() if callable(service_factory) else service_factory
        except Exception as e:
            logging.error(f"Failed to retrieve service {service_type}: {e}")
            raise


def get_service_container() -> ServiceContainer:
    """
    Get the singleton service container instance.

    Returns:
        ServiceContainer: The service container
    """
    container = ServiceContainer()

    # Register known services with their import paths
    services_to_register = {
        'MaterialService': 'services.implementations.material_service.MaterialService',
        'ProjectService': 'services.implementations.project_service.ProjectService',
        'InventoryService': 'services.implementations.inventory_service.InventoryService',
        'OrderService': 'services.implementations.order_service.OrderService',
    }

    for service_name, import_path in services_to_register.items():
        container.register_service(service_name, import_path=import_path)

    return container


# Create a singleton instance for easy access
SERVICE_CONTAINER = get_service_container()