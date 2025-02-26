# path: services/interfaces/__init__.py
"""
Service interfaces package for the leatherworking store management application.

This package contains interface definitions for services used in the application.
"""
from abc import ABC, abstractmethod
import enum

# Import base service interface
from .base_service import IBaseService

# Import specific service interfaces
from .inventory_service import IInventoryService
from .material_service import IMaterialService, MaterialType
from .order_service import IOrderService
from .project_service import IProjectService, ProjectType, SkillLevel
from .storage_service import IStorageService

# Import base interface first to avoid circular dependencies
try:
    from services.interfaces.base_service import IBaseService
except ImportError:
    # Create a fallback if the real one can't be imported
    from abc import ABC


    class IBaseService(ABC):
        """Fallback base service interface if the real one can't be imported."""
        pass

# Import service interfaces with fallbacks
# Material Service
try:
    from services.interfaces.material_service import IMaterialService, MaterialService, MaterialType
except ImportError:
    # Create a minimal fallback for MaterialService
    from abc import ABC, abstractmethod
    import enum


    class MaterialType(enum.Enum):
        """Fallback enumeration of material types."""
        LEATHER = "leather"
        HARDWARE = "hardware"
        THREAD = "thread"
        OTHER = "other"


    class IMaterialService(ABC):
        """Fallback material service interface."""

        @abstractmethod
        def create_material(self, material_data):
            pass

        @abstractmethod
        def get_material(self, material_id):
            pass


    # Alias for backward compatibility
    MaterialService = IMaterialService

# Project Service
try:
    from services.interfaces.project_service import IProjectService, ProjectService, ProjectType, SkillLevel
except ImportError:
    # Create a minimal fallback for ProjectService
    from abc import ABC, abstractmethod
    import enum


    class ProjectType(enum.Enum):
        """Fallback enumeration of project types."""
        BAG = "bag"
        WALLET = "wallet"
        OTHER = "other"


    class SkillLevel(enum.Enum):
        """Fallback enumeration of skill levels."""
        BEGINNER = "beginner"
        INTERMEDIATE = "intermediate"
        ADVANCED = "advanced"


    class IProjectService(ABC):
        """Fallback project service interface."""

        @abstractmethod
        def create_project(self, project_data):
            pass

        @abstractmethod
        def get_project(self, project_id):
            pass


    # Alias for backward compatibility
    ProjectService = IProjectService

# Inventory Service
try:
    from services.interfaces.inventory_service import IInventoryService, InventoryService
except ImportError:
    # Create a minimal fallback for InventoryService
    from abc import ABC, abstractmethod


    class IInventoryService(ABC):
        """Fallback inventory service interface."""

        @abstractmethod
        def update_part_stock(self, part_id, quantity_change, transaction_type, notes=None):
            pass

        @abstractmethod
        def update_leather_area(self, leather_id, area_change, transaction_type, notes=None, wastage=0.0):
            pass

        @abstractmethod
        def get_low_stock_parts(self, include_out_of_stock=True):
            pass

        @abstractmethod
        def get_low_stock_leather(self, include_out_of_stock=True):
            pass


    # Alias for backward compatibility
    InventoryService = IInventoryService

# Order Service
try:
    from services.interfaces.order_service import IOrderService, OrderService
except ImportError:
    # Create a minimal fallback for OrderService
    from abc import ABC, abstractmethod


    class IOrderService(ABC):
        """Fallback order service interface."""

        @abstractmethod
        def get_all_orders(self):
            pass

        @abstractmethod
        def get_order_by_id(self, order_id):
            pass

        @abstractmethod
        def create_order(self, order_data):
            pass

        @abstractmethod
        def update_order(self, order_id, order_data):
            pass

        @abstractmethod
        def delete_order(self, order_id):
            pass


    # Alias for backward compatibility
    OrderService = IOrderService

# Define which symbols to expose
__all__ = [
    # Base interface
    'IBaseService',

    # Service interfaces
    'IInventoryService',
    'IMaterialService',
    'IOrderService',
    'IProjectService',
    'IStorageService',
    'ISupplierService',

    # Enums
    'MaterialType',
    'OrderStatus',
    'ProjectType',
    'SkillLevel'
]