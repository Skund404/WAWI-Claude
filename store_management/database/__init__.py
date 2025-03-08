# database/__init__.py

import logging
import sys
from typing import Any, Optional, Tuple
from . import models
from database.models.enums import MeasurementUnit
from database.models.base import Base, BaseModel
from database.models import ModelValidationError, initialize_database
from database.models.components import ProjectComponent, PatternComponent, Component
from database.models.customer import Customer
from database.models.hardware import Hardware
from database.models.leather import Leather
from database.models.material import Material
from database.models.pattern import Pattern
from database.models.picking_list import PickingList, PickingListItem
from database.models.product import Product
from database.models.project import Project
from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.models.supplier import Supplier
from database.models.transaction import HardwareTransaction, LeatherTransaction, MaterialTransaction, Transaction
from initialize_database import add_minimal_sample_data, add_extra_demo_data, initialize_all_relationships, \
    add_sample_data
from utils.circular_import_resolver import (
    CircularImportResolver,
    register_lazy_import,
    lazy_import,
    resolve_lazy_relationships,
    get_module,
    get_class
)

logger = logging.getLogger(__name__)


class DatabaseModule:
    """
    Proxy module to handle lazy loading of database components.
    """

    def __init__(self):
        self._import_mappings = {
            # Models
            'Base': ('database.models.base', 'Base'),
            'BaseModel': ('database.models.base', 'Base'),
            'ModelValidationError': ('database.models.base', 'ModelValidationError'),

            # Core models
            'Customer': ('database.models.customer', 'Customer'),
            'Hardware': ('database.models.hardware', 'Hardware'),
            'Leather': ('database.models.leather', 'Leather'),
            'Material': ('database.models.material', 'Material'),
            'Pattern': ('database.models.pattern', 'Pattern'),
            'Product': ('database.models.product', 'Product'),
            'Project': ('database.models.project', 'Project'),
            'Sales': ('database.models.sales', 'Sales'),
            'SalesItem': ('database.models.sales_item', 'SalesItem'),
            'Supplier': ('database.models.supplier', 'Supplier'),

            # Inventory and List models
            'PickingList': ('database.models.picking_list', 'PickingList'),
            'PickingListItem': ('database.models.picking_list', 'PickingListItem'),

            # Transaction models
            'Transaction': ('database.models.transaction', 'Transaction'),
            'MaterialTransaction': ('database.models.transaction', 'MaterialTransaction'),
            'LeatherTransaction': ('database.models.transaction', 'LeatherTransaction'),
            'HardwareTransaction': ('database.models.transaction', 'HardwareTransaction'),

            # Component models
            'Component': ('database.models.components', 'Component'),
            'PatternComponent': ('database.models.components', 'PatternComponent'),
            'ProjectComponent': ('database.models.components', 'ProjectComponent'),
            'ComponentLeather': ('database.models.components', 'ComponentLeather'),
            'ComponentHardware': ('database.models.components', 'ComponentHardware'),
            'ComponentMaterial': ('database.models.components', 'ComponentMaterial'),

            # Initialization Functions
            'initialize_database': ('initialize_database', 'initialize_database'),
            'initialize_all_relationships': ('initialize_database', 'initialize_all_relationships'),
            'add_sample_data': ('initialize_database', 'add_sample_data'),
            'add_minimal_sample_data': ('initialize_database', 'add_minimal_sample_data'),
            'add_extra_demo_data': ('initialize_database', 'add_extra_demo_data')
        }

        # Enum mappings
        self._enum_mappings = {
            'LeatherType': ('database.models.enums', 'LeatherType'),
            'MaterialType': ('database.models.enums', 'MaterialType'),
            'SaleStatus': ('database.models.enums', 'SaleStatus'),
            'ProjectStatus': ('database.models.enums', 'ProjectStatus'),
            'PaymentStatus': ('database.models.enums', 'PaymentStatus'),
            'CustomerStatus': ('database.models.enums', 'CustomerStatus'),
            'InventoryStatus': ('database.models.enums', 'InventoryStatus'),
        }

    def __getattr__(self, name: str) -> Any:
        """
        Dynamic attribute access for lazy importing.

        Args:
            name: Name of the attribute to import

        Returns:
            Imported model, enum, or function
        """
        # Check model mappings first
        if name in self._import_mappings:
            module_path, class_name = self._import_mappings[name]
            return get_class(module_path, class_name)

        # Check enum mappings
        if name in self._enum_mappings:
            module_path, class_name = self._enum_mappings[name]
            return get_class(module_path, class_name)

        # If not found, raise attribute error
        raise AttributeError(f"Module 'database' has no attribute '{name}'")

    def __dir__(self):
        """
        Provide a list of available attributes.

        Returns:
            List of available attribute names
        """
        return list(set(
            list(self._import_mappings.keys()) +
            list(self._enum_mappings.keys()) +
            super().__dir__()
        ))

    def initialize_lazy_imports(self):
        """
        Initialize lazy imports and resolve relationships.
        """
        try:
            # Register lazy imports
            for name, (module_path, class_name) in {**self._import_mappings, **self._enum_mappings}.items():
                register_lazy_import(name, module_path, class_name)

            # Resolve lazy relationships
            resolve_lazy_relationships()
            logger.debug("Lazy imports and relationships initialized")
        except Exception as e:
            logger.error(f"Error initializing lazy imports: {e}")


# Create and set up the database module
database_module = DatabaseModule()

# Replace the current module with the proxy module
sys.modules[__name__] = database_module

# Initialize lazy imports
database_module.initialize_lazy_imports()

# Module exports
__all__ = [
    'Base', 'BaseModel', 'ModelValidationError',
    'Customer', 'Hardware', 'Leather', 'Material',
    'Pattern', 'Product', 'Project', 'Sales', 'SalesItem',
    'Supplier', 'PickingList', 'PickingListItem',
    'Transaction', 'MaterialTransaction', 'LeatherTransaction', 'HardwareTransaction',
    'Component', 'PatternComponent', 'ProjectComponent',
    'initialize_database', 'initialize_all_relationships',
    'add_sample_data', 'add_minimal_sample_data', 'add_extra_demo_data'
]


