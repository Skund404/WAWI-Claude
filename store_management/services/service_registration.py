# services/service_registration.py
from di.container import DependencyContainer
from services.implementations.sales_service import SalesService
from services.interfaces.sales_service import ISalesService

def register_sales_service(container: DependencyContainer):
    """
    Register the Sales Service in the dependency injection container.

    Args:
        container: Dependency injection container to register the service
    """
    # Using service name for registration
    container.register('SalesService', SalesService)