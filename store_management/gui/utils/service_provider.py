# gui/utils/service_provider.py
"""
Service Provider for the Leatherworking ERP application.
Provides standardized access to services with caching and error handling.
"""

import logging
from typing import Any, Dict, Type, TypeVar, Callable, Optional, Union
import functools

from di import resolve

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.info("Loading gui.utils.service_provider module")

# Import service exceptions with fallbacks for missing exceptions
try:
    from services.exceptions import ValidationError, NotFoundError, ServiceError

    logger.info("Successfully imported service exceptions")

    # Check if PermissionError exists in services.exceptions
    try:
        from services.exceptions import PermissionError as ServicePermissionError
    except ImportError:
        # Create our own if it doesn't exist
        logger.warning("PermissionError not found in services.exceptions, using custom implementation")


        class ServicePermissionError(ServiceError):
            """Permission denied error in service operations."""
            pass
except ImportError as e:
    logger.error(f"Failed to import service exceptions: {str(e)}")


    # Define fallback exceptions
    class ValidationError(Exception):
        """Validation error in service operations."""
        pass


    class NotFoundError(Exception):
        """Resource not found error in service operations."""
        pass


    class ServiceError(Exception):
        """Generic service error."""
        pass


    class ServicePermissionError(ServiceError):
        """Permission denied error in service operations."""
        pass

# Type variable for service interfaces
T = TypeVar('T')


class ServiceProviderError(Exception):
    """Exception raised when a service cannot be resolved or an operation fails."""
    pass


class ServiceProvider:
    """
    Provides standardized access to services with caching and error handling.
    Acts as a façade to the DI system, adding caching and consistent error handling.
    """

    # Cache for resolved services
    _service_cache: Dict[str, Any] = {}

    @staticmethod
    def get_service(service_type: Union[str, Type]) -> Any:
        """
        Get a service instance from the DI container with caching.

        Args:
            service_type: The interface class or name of the service to resolve

        Returns:
            An instance of the requested service

        Raises:
            ServiceProviderError: If the service interface is not registered in the DI container
        """
        # Convert string service names to proper interface types if needed
        service_key = service_type if isinstance(service_type, str) else service_type.__name__

        # Ensure service keys are interface names (IServiceName)
        if not service_key.startswith("I") and not isinstance(service_type, str):
            service_key = f"I{service_key}"
            logger.debug(f"Converted service key to interface name: {service_key}")

        # Check cache first
        if service_key in ServiceProvider._service_cache:
            logger.debug(f"Service {service_key} found in cache")
            return ServiceProvider._service_cache[service_key]

        try:
            # If we have a string that's not an interface name, try adding the 'I' prefix
            if isinstance(service_type, str) and not service_type.startswith("I"):
                try_interface_name = f"I{service_type}"
                logger.debug(f"Trying to resolve with interface name: {try_interface_name}")
                try:
                    service = resolve(try_interface_name)
                    logger.debug(f"Successfully resolved with interface name: {try_interface_name}")
                    # Cache the resolved service
                    ServiceProvider._service_cache[service_key] = service
                    return service
                except Exception as e:
                    # If that fails, continue with the original name
                    logger.debug(f"Failed to resolve with interface name, trying original name: {e}")

            # Resolve from DI container
            logger.debug(f"Service {service_key} not in cache, resolving from DI container")
            service = resolve(service_type)

            # Cache the resolved service
            ServiceProvider._service_cache[service_key] = service
            logger.debug(f"Service {service_key} successfully resolved and cached")

            return service
        except Exception as e:
            # Log the detailed exception with stack trace
            error_msg = f"Failed to resolve service {service_key}: {str(e)}"
            logger.error(error_msg)
            logger.debug("Stack trace for service resolution error:", exc_info=True)

            # Re-raise with detailed information
            raise ServiceProviderError(error_msg) from e

    @staticmethod
    def execute_service_operation(service_type: Union[str, Type], operation: str, *args, **kwargs) -> Any:
        """
        Execute a service operation with standard error handling.

        Args:
            service_type: The service interface or name to use
            operation: The name of the operation/method to call
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the operation

        Raises:
            ServiceProviderError: If the operation fails for any reason
            ValidationError: If validation fails for the input
            NotFoundError: If a requested resource is not found
            ServicePermissionError: If permission is denied for the operation
        """
        # Log the operation being executed for diagnostics
        service_name = service_type if isinstance(service_type, str) else service_type.__name__
        logger.debug(f"Executing operation: {service_name}.{operation}")

        try:
            # Get the service
            service = ServiceProvider.get_service(service_type)

            # Get the operation method
            if not hasattr(service, operation):
                error = f"Operation '{operation}' not found on service {service_name}"
                logger.error(error)
                raise ServiceProviderError(error)

            service_method = getattr(service, operation)

            # Parameter adaptation for known mismatches
            adapted_kwargs = kwargs.copy()

            # Special case for InventoryService.get_all
            if service_name in ('IInventoryService', 'InventoryService') and operation == 'get_all':
                # Convert sort_column to sort_by if present
                if 'sort_column' in adapted_kwargs and 'sort_by' not in adapted_kwargs:
                    logger.debug(f"Adapting parameter: sort_column -> sort_by")
                    sort_column = adapted_kwargs.pop('sort_column')
                    sort_direction = adapted_kwargs.pop('sort_direction', 'asc')
                    adapted_kwargs['sort_by'] = (sort_column, sort_direction)

                # Handle other parameter mismatches as needed
                for old_param, new_param in [('search_term', 'search_criteria')]:
                    if old_param in adapted_kwargs and new_param not in adapted_kwargs:
                        logger.debug(f"Adapting parameter: {old_param} -> {new_param}")
                        adapted_kwargs[new_param] = adapted_kwargs.pop(old_param)

            # Execute the operation with adapted parameters
            result = service_method(*args, **adapted_kwargs)
            logger.debug(f"Operation {service_name}.{operation} executed successfully")
            return result

        except ValidationError as e:
            # Let validation errors pass through
            logger.warning(f"Validation error in {service_name}.{operation}: {str(e)}")
            raise

        except NotFoundError as e:
            # Let not found errors pass through
            logger.warning(f"Resource not found in {service_name}.{operation}: {str(e)}")
            raise

        except ServicePermissionError as e:
            # Let permission errors pass through
            logger.warning(f"Permission denied in {service_name}.{operation}: {str(e)}")
            raise

        except ServiceError as e:
            # Handle service-specific errors
            logger.error(f"Service error in {service_name}.{operation}: {str(e)}")
            raise

        except ServiceProviderError:
            # Let service provider errors pass through
            logger.error(f"Service provider error in {service_name}.{operation}", exc_info=True)
            raise

        except Exception as e:
            # Wrap other exceptions with detailed logging
            error_msg = f"Error executing {service_name}.{operation}: {str(e)}"
            logger.error(error_msg)
            logger.debug("Detailed stack trace:", exc_info=True)
            raise ServiceProviderError(error_msg) from e

    @staticmethod
    def clear_cache() -> None:
        """Clear the service cache."""
        count = len(ServiceProvider._service_cache)
        ServiceProvider._service_cache.clear()
        logger.info(f"Service cache cleared ({count} services removed)")

    @staticmethod
    def clear_service_from_cache(service_type: Union[str, Type]) -> None:
        """
        Remove a specific service from the cache.

        Args:
            service_type: The service interface or name to remove from cache
        """
        service_key = service_type if isinstance(service_type, str) else service_type.__name__

        if service_key in ServiceProvider._service_cache:
            del ServiceProvider._service_cache[service_key]
            logger.info(f"Service {service_key} removed from cache")
        else:
            logger.debug(f"Service {service_key} not found in cache, nothing to remove")


# Compatibility with existing code that may be using with_service decorator
def with_service(service_type):
    """
    Decorator to inject a service into a method.

    Args:
        service_type: The service interface or name to inject

    Returns:
        Decorator function
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Add service as a keyword argument
            try:
                service = ServiceProvider.get_service(service_type)
                kwargs['service'] = service

                # Detailed logging for debugging
                logger.debug(f"Injected service {service_type} for {func.__name__}")

                # Call the wrapped function
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in with_service({service_type}) for {func.__name__}: {str(e)}")
                logger.debug("Stack trace:", exc_info=True)
                # Re-raise the exception to be handled by the caller
                raise

        return wrapper

    return decorator


# Convenience function to clear service cache
def clear_service_cache():
    """Clear the service resolution cache."""
    ServiceProvider.clear_cache()