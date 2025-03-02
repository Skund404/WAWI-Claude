# di/setup/project_service_setup.py
from di.container import DependencyContainer
from services.implementations.project_service import ProjectService
from services.interfaces.project_service import IProjectService
from database.repositories.project_repository import ProjectRepository


def setup_project_dependencies(container: DependencyContainer):
    """
    Set up dependency injection for project-related services and repositories.

    Args:
        container (DependencyContainer): Dependency injection container
    """
    # Register project repository
    container.register(ProjectRepository)

    # Register project service
    container.register(
        interface=IProjectService,
        implementation=ProjectService
    )


def create_lazy_project_service_registration(container: DependencyContainer):
    """
    Create a lazy registration function for project service to handle potential
    circular dependencies.

    Args:
        container (DependencyContainer): Dependency injection container
    """
    # Lazy import to handle potential circular dependencies
    from utils.circular_import_resolver import lazy_import

    lazy_import(
        'project_service',
        'services.implementations.project_service',
        'ProjectService'
    )

    lazy_import(
        'project_repository',
        'database.repositories.project_repository',
        'ProjectRepository'
    )


def register_project_services(container: DependencyContainer):
    """
    Comprehensive registration of project-related services.

    Args:
        container (DependencyContainer): Dependency injection container
    """
    # Setup basic dependencies
    setup_project_dependencies(container)

    # Create lazy registrations
    create_lazy_project_service_registration(container)