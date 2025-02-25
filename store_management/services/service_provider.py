#!/usr/bin/env python3
# Path: service_provider.py
"""
Service Provider module for dependency management.

This module provides a service locator pattern implementation for
managing service dependencies in the application.
"""

from typing import Type, TypeVar, Optional

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from services.service_registry import ServiceRegistry
from services.interfaces import IBaseService

# Generic type for service interfaces
T = TypeVar('T', bound=IBaseService)


class ServiceProvider:
    """
    Dependency injection container for services.

    Provides a central registry for service instances and
    a way to retrieve them throughout the application.
    """

    def __init__(self):
        """
        Initialize the service provider with a service registry.
        """
        self.registry = ServiceRegistry()

    def get_service(self, service_type: Type[T]) -> T:
        """
        Get service instance.

        Args:
            service_type (Type[T]): The type of service to retrieve

        Returns:
            T: An instance of the requested service

        Raises:
            ValueError: If the requested service is not registered
        """
        service = self.registry.get(service_type)
        if not service:
            raise ValueError(f'Service {service_type.__name__} not registered')
        return service

    def register_services(self) -> None:
        """
        Register all services.

        Imports and registers concrete implementations of services
        with their corresponding interfaces.
        """
        from .implementations.pattern_service import PatternService
        from .implementations.leather_inventory_service import LeatherInventoryService
        from .interfaces import IPatternService, ILeatherInventoryService

        self.registry.register(IPatternService, PatternService())
        self.registry.register(ILeatherInventoryService, LeatherInventoryService())