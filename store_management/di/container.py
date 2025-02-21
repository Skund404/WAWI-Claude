# Path: store_management\store_management\di\container.py
from typing import Any, Type, Callable, Dict, Optional, TypeVar

T = TypeVar('T')


class DependencyContainer:
    """
    Advanced dependency injection container with comprehensive capabilities.

    Provides:
    - Singleton and transient dependency registration
    - Lazy initialization
    - Type-safe dependency resolution
    - Circular dependency detection
    - Flexible dependency management
    """

    def __init__(self):
        """Initialize the dependency container with empty registries."""
        self._dependencies: Dict[str, Dict[str, Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._resolving: Dict[str, bool] = {}

    def _get_type_key(self, type_: Type) -> str:
        """
        Generate a unique string key for a given type.

        Args:
            type_: The type to generate a key for

        Returns:
            A unique string representation of the type
        """
        return f"{type_.__module__}.{type_.__name__}"

    def register(
            self,
            interface_type: Type[T],
            implementation_factory: Callable[..., T],
            singleton: bool = True,
            dependencies: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a dependency with advanced configuration options.

        Args:
            interface_type: The interface or base type to register
            implementation_factory: Factory function to create the implementation
            singleton: Whether to cache the instance (default: True)
            dependencies: Optional dictionary of dependencies to inject

        Raises:
            ValueError: If the dependency is already registered
        """
        key = self._get_type_key(interface_type)

        if key in self._dependencies:
            raise ValueError(f"Dependency for {interface_type} is already registered")

        self._dependencies[key] = {
            'factory': implementation_factory,
            'singleton': singleton,
            'dependencies': dependencies or {}
        }

    def resolve(self, interface_type: Type[T]) -> T:
        """
        Resolve a dependency with advanced resolution strategy.

        Args:
            interface_type: The type/interface to resolve

        Returns:
            Instance of the requested dependency

        Raises:
            ValueError: If dependency is not registered or circular dependency is detected
        """
        key = self._get_type_key(interface_type)

        # Check if dependency is registered
        if key not in self._dependencies:
            raise ValueError(f"No implementation registered for {interface_type}")

        # Check for circular dependency
        if self._resolving.get(key, False):
            raise ValueError(f"Circular dependency detected for {interface_type}")

        # If singleton and already created, return cached instance
        if self._dependencies[key]['singleton'] and key in self._singletons:
            return self._singletons[key]

        # Mark as resolving to detect circular dependencies
        self._resolving[key] = True

        try:
            # Create dependency
            dependency_info = self._dependencies[key]

            # Resolve dependencies if needed
            resolved_dependencies = {}
            for dep_name, dep_type in dependency_info['dependencies'].items():
                resolved_dependencies[dep_name] = self.resolve(dep_type)

            # Create instance
            instance = dependency_info['factory'](**resolved_dependencies)

            # Cache singleton if needed
            if dependency_info['singleton']:
                self._singletons[key] = instance

            return instance

        finally:
            # Clear resolving flag
            self._resolving[key] = False

    def get_service(self, interface_type: Type[T]) -> T:
        """
        Alias for resolve method to maintain compatibility.

        Args:
            interface_type: The type/interface to resolve

        Returns:
            Instance of the requested dependency
        """
        return self.resolve(interface_type)

    def clear(self) -> None:
        """Clear all registered dependencies, singleton instances, and resolving state."""
        self._dependencies.clear()
        self._singletons.clear()
        self._resolving.clear()

    def get_all_registered_types(self) -> list:
        """
        Retrieve all registered dependency types.

        Returns:
            List of registered type keys
        """
        return list(self._dependencies.keys())

    def is_registered(self, interface_type: Type) -> bool:
        """
        Check if a dependency is already registered.

        Args:
            interface_type: The type to check for registration

        Returns:
            bool: True if the dependency is registered, False otherwise
        """
        return self._get_type_key(interface_type) in self._dependencies