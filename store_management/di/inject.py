"""
Dependency Injection Decorator.

Provides decorators for injecting dependencies into classes and functions.
"""

import functools
import inspect
from typing import Any, Callable, TypeVar, cast, get_type_hints, Optional, Type, Union

from di.container import get_container, Container, ResolutionError

T = TypeVar('T')


def inject(target: Optional[Union[Callable[..., Any], Type[T]]] = None) -> Any:
    """
    Decorator to inject dependencies into a callable or class.

    This decorator can be used on both class constructors and functions.
    It uses type hints to determine what dependencies to inject.

    Args:
        target: Function or class to inject dependencies into. If None, returns a decorator.

    Returns:
        Decorated function, class or a decorator
    """
    # Handle case where decorator is used without parentheses: @inject
    if target is not None:
        return _inject_impl(target)

    # Handle case where decorator is used with parentheses: @inject()
    return _inject_impl


def _inject_impl(target: Union[Callable[..., Any], Type[T]]) -> Union[Callable[..., Any], Type[T]]:
    """Implementation of the inject decorator."""
    # For classes, decorate __init__
    if inspect.isclass(target):
        original_init = target.__init__

        # Get signature and type hints
        sig = inspect.signature(original_init)
        type_hints = get_type_hints(original_init)

        @functools.wraps(original_init)
        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            # Get container
            try:
                container = get_container()

                # Prepare parameters dict by skipping already provided args
                param_keys = list(sig.parameters.keys())[1:]  # Skip 'self'
                params_to_inject = param_keys[len(args):]  # Skip positional args

                # Resolve parameters not provided in kwargs
                for param_name in params_to_inject:
                    if param_name not in kwargs and param_name in type_hints:
                        param_type = type_hints[param_name]
                        try:
                            # Try to resolve the parameter from the container
                            kwargs[param_name] = container.resolve(param_type)
                        except ResolutionError:
                            # Skip parameters that can't be resolved - they might have defaults
                            pass

                # Call original init
                original_init(self, *args, **kwargs)
            except Exception as e:
                # Fall back to regular init if DI fails
                original_init(self, *args, **kwargs)

        # Replace __init__ with new_init
        target.__init__ = new_init
        return target

    # For functions
    sig = inspect.signature(target)
    type_hints = get_type_hints(target)

    @functools.wraps(target)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Get container
            container = get_container()

            # Prepare parameters dict by skipping already provided args
            param_keys = list(sig.parameters.keys())
            params_to_inject = param_keys[len(args):]  # Skip positional args

            # Resolve parameters not provided in kwargs
            for param_name in params_to_inject:
                if param_name not in kwargs and param_name in type_hints:
                    param_type = type_hints[param_name]
                    try:
                        # Try to resolve the parameter from the container
                        kwargs[param_name] = container.resolve(param_type)
                    except ResolutionError:
                        # Skip parameters that can't be resolved - they might have defaults
                        pass

            # Call the function
            return target(*args, **kwargs)
        except Exception as e:
            # Fall back to regular call if DI fails
            return target(*args, **kwargs)

    return wrapper


def resolve(service_type: Union[str, Type[T]]) -> T:
    """
    Resolve a service from the container.

    This is a convenience function to resolve services without
    using the decorator.

    Args:
        service_type: Service type to resolve

    Returns:
        Resolved service instance
    """
    container = get_container()
    return container.resolve(service_type)