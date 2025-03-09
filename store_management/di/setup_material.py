# di/setup_material.py
"""
Sets up dependency injection for the material-related services and repositories.
"""

from di.container import container

from database.repositories.leather_repository import LeatherRepository
from database.repositories.hardware_repository import HardwareRepository
from database.repositories.supplies_repository import SuppliesRepository
from database.repositories.material_repository import MaterialRepository

from services.interfaces.material_service import IMaterialService
from services.implementations.material_service import MaterialService


def setup_material_di():
    """
    Register material-related services and repositories with the DI container.
    """
    # Register repositories
    if not container.is_registered(LeatherRepository):
        container.register(LeatherRepository)

    if not container.is_registered(HardwareRepository):
        container.register(HardwareRepository)

    if not container.is_registered(SuppliesRepository):
        container.register(SuppliesRepository)

    if not container.is_registered(MaterialRepository):
        container.register(MaterialRepository)

    # Register services
    if not container.is_registered(IMaterialService):
        container.register(IMaterialService, MaterialService)