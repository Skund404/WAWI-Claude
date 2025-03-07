"""
services/service_registration_update.py
Updates service registration to include new services for the updated data model.
"""
from di.core import DependencyContainer

# Import service interfaces
from services.interfaces.picking_list_service import IPickingListService
from services.interfaces.tool_list_service import IToolListService

# Import service implementations
from services.implementations.picking_list_service import PickingListService
from services.implementations.tool_list_service import ToolListService


def register_updated_services(container: DependencyContainer) -> None:
    """
    Register updated services with the dependency injection container.

    Args:
        container: The dependency injection container
    """
    # Register new services
    container.register(IPickingListService, PickingListService)
    container.register(IToolListService, ToolListService)


def apply_service_updates() -> None:
    """
    Apply service updates to the application's dependency injection system.
    This should be called during application initialization.
    """
    # Get the container instance
    container = DependencyContainer.instance()

    # Register services
    register_updated_services(container)

    print("Updated services registered successfully")