# services/service_factory.py
from typing import Dict, Optional, Type, TypeVar

from database.sqlalchemy.session import get_db_session
from services.interfaces.material_service import IMaterialService
from services.implementations.material_service import MaterialService
from services.interfaces.leather_service import ILeatherService
from services.implementations.leather_service import LeatherService
from services.interfaces.project_service import IProjectService
from services.implementations.project_service import ProjectService

# Type variable for service interfaces
T = TypeVar('T')


class ServiceFactory:
    """Factory for creating service instances."""

    _instances: Dict[Type, object] = {}

    @classmethod
    def get_service(cls, service_interface: Type[T]) -> T:
        """Get a service instance based on interface type.

        Args:
            service_interface: The service interface class

        Returns:
            An instance of the requested service

        Raises:
            ValueError: If the service interface is not supported
        """
        # Check if we already have an instance
        if service_interface in cls._instances:
            return cls._instances[service_interface]

        # Create a new session
        session = get_db_session()

        # Create the appropriate service implementation
        if service_interface == IMaterialService:
            service = MaterialService(session)
        elif service_interface == ILeatherService:
            service = LeatherService(session)
        elif service_interface == IProjectService:
            service = ProjectService(session)
        else:
            raise ValueError(f"Unsupported service interface: {service_interface.__name__}")

        # Store the instance
        cls._instances[service_interface] = service

        return service