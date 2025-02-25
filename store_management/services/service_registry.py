#!/usr/bin/env python3
# Path: service_registry.py
"""
Service Registry for managing service implementations.

This module implements the Service Locator pattern, providing a centralized
registry for service implementations.
"""

from typing import Dict, Type, TypeVar, Optional

from services.interfaces import IBaseService

# Generic type for service interfaces
T = TypeVar('T', bound=IBaseService)


class ServiceRegistry:
    """
    Service locator pattern implementation.

    Provides a singleton registry for storing and retrieving
    service implementations by their interface.
    """
    _instance = None
    _services: Dict[Type[IBaseService], IBaseService] = {}

    def __new__(cls):
        """
        Singleton pattern implementation.

        Returns:
            ServiceRegistry: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, interface: Type[T], implementation: T) -> None:
        """
        Register a service implementation.

        Args:
            interface (Type[T]): The service interface
            implementation (T): The concrete implementation
        """
        cls._services[interface] = implementation

    @classmethod
    def get(cls, interface: Type[T]) -> Optional[T]:
        """
        Get a service implementation.

        Args:
            interface (Type[T]): The service interface to retrieve

        Returns:
            Optional[T]: The implementation if registered, None otherwise
        """
        return cls._services.get(interface)

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered services.

        Useful for testing or when resetting the application state.
        """
        cls._services.clear()