"""
Dependency Injection (DI) package.

Provides tools for managing dependencies and service registrations.
"""

from di.container import (
    Container,
    Lifetime,
    get_container,
    set_container,
    create_container,
    clear_container
)
from di.inject import inject, resolve

# Lazy import to prevent circular imports
def initialize():
    """Initialize the DI container."""
    from di.setup import initialize as _initialize
    return _initialize()

def verify_container():
    """Verify the DI container configuration."""
    from di.setup import verify_container as _verify_container
    return _verify_container()

__all__ = [
    'Container',
    'Lifetime',
    'get_container',
    'set_container',
    'create_container',
    'clear_container',
    'inject',
    'resolve',
    'initialize',
    'verify_container'
]