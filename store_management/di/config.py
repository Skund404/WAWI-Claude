from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    A singleton class for managing service dependencies and configurations.

    This class provides a centralized way to register and resolve service
    implementations across the application.
    """
    _instance = None
    _services: Dict[str, Any] = {}

        def __new__(cls):
        """
        Ensure only one instance of ServiceContainer is created.

        Returns:
            ServiceContainer: The singleton instance of the service container.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._services = {}
        return cls._instance

        @classmethod
    def register_service(cls, interface: str, implementation: str,
        singleton: bool=True) ->None:
        """
        Register a service implementation for a given interface.

        Args:
            interface (str): The full import path of the interface
            implementation (str): The full import path of the implementation
            singleton (bool, optional): Whether to create a singleton. Defaults to True.
        """
        try:
            cls._services[interface] = {'implementation': implementation,
                'singleton': singleton}
            logger.info(f'Registered service: {interface} -> {implementation}')
        except Exception as e:
            logger.error(f'Error registering service {interface}: {e}')
            raise

        @classmethod
    def resolve(cls, interface: str) ->Any:
        """
        Resolve and instantiate a service implementation for a given interface.

        Args:
            interface (str): The full import path of the interface

        Returns:
            Any: An instance of the service implementation

        Raises:
            ValueError: If no implementation is registered for the interface
        """
        try:
            if interface not in cls._services:
                raise ValueError(
                    f'No implementation registered for {interface}')
            service_info = cls._services[interface]
            implementation_path = service_info['implementation']
            try:
                module_path, class_name = implementation_path.rsplit('.', 1)
            except ValueError:
                raise ValueError(
                    f'Invalid implementation path: {implementation_path}')
            module = importlib.import_module(module_path)
            implementation_class = getattr(module, class_name)
            if service_info.get('singleton', True):
                if not hasattr(cls, f'_{class_name}_instance'):
                    setattr(cls, f'_{class_name}_instance',
                        implementation_class())
                return getattr(cls, f'_{class_name}_instance')
            return implementation_class()
        except (ImportError, AttributeError) as e:
            logger.error(f'Error resolving service {interface}: {e}')
            raise ValueError(f'Could not resolve service {interface}: {e}')

        @classmethod
    def clear(cls) ->None:
        """
        Clear all registered services.
        """
        cls._services.clear()
        logger.info('All services cleared')


def import_interface(module_path: str, interface_name: str) ->Type:
    """
    Dynamically import an interface class.

    Args:
        module_path (str): The module path containing the interface
        interface_name (str): The name of the interface class

    Returns:
        Type: The imported interface class

    Raises:
        ImportError: If the interface cannot be imported
    """
    try:
        module = importlib.import_module(module_path)
        return getattr(module, interface_name)
    except (ImportError, AttributeError) as e:
        logger.error(f'Error importing interface {interface_name}: {e}')
        raise


def configure_application_services() ->None:
    """
    Configure and register application services.

    This function should be expanded with actual service registrations.
    """
    try:
        services_to_register = [(
            'services.interfaces.material_service.IMaterialService',
            'services.implementations.material_service.MaterialService'), (
            'services.interfaces.project_service.IProjectService',
            'services.implementations.project_service.ProjectService')]
        for interface, implementation in services_to_register:
            ServiceContainer.register_service(interface, implementation)
        logger.info('Application services configured successfully')
    except Exception as e:
        logger.error(f'Error configuring application services: {e}')
        raise


configure_application_services()
