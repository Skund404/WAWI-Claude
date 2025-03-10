# services/__init__.py
# Service layer package initialization

from services.exceptions import (
    ServiceError,
    ValidationError,
    NotFoundError,
    ConcurrencyError,
    AuthorizationError,
    BusinessRuleError
)

# Import service interfaces to make them available through the package
from services.interfaces.customer_service import ICustomerService
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.sales_service import ISalesService


# Convenience function to get a service instance through DI
def get_service(service_name):
    """Get a service instance by name using dependency injection.

    Args:
        service_name: Name of the service to get

    Returns:
        Service instance
    """
    from di.core import resolve
    return resolve(service_name)