# database/models/__init__.py
"""
Models package for Leatherworking Management System.

This initializes the models package and provides imports for key model classes.
"""

import logging
from typing import Callable, Optional

from utils.circular_import_resolver import CircularImportResolver, register_lazy_import

# Setup logger
logger = logging.getLogger(__name__)

# First, import Base from models.base
from database.models.base import Base

# Define BaseModel as an alias for Base
BaseModel = Base

# Import initialize_database function, but don't execute it yet
try:
    from initialize_database import initialize_database
except ImportError as e:
    logger.warning(f"Could not import initialize_database: {e}")


    def initialize_database(connection_string=None):
        """Placeholder for missing initialize_database function."""
        logger.error("initialize_database function not properly imported")

# Import and register models - import core models first to avoid circular dependencies
try:
    # Import enums first since many models depend on them
    from database.models.enums import (
        LeatherType, MaterialType, SaleStatus, ProjectStatus, PaymentStatus,
        CustomerStatus, CustomerTier, CustomerSource, InventoryStatus,
        TransactionType, ToolCategory, StorageLocationType
    )

    # Import base and middleware models
    from database.models.base import ModelValidationError
    from database.models.mixins import TimestampMixin, ValidationMixin, TrackingMixin, CostingMixin

    # Import transaction models
    from database.models.transaction import (
        BaseTransaction,
        HardwareTransaction,
        LeatherTransaction,
        MaterialTransaction
    )

    # Import main models
    from database.models.supplier import Supplier
    from database.models.customer import Customer
    from database.models.material import Material
    from database.models.leather import Leather
    from database.models.hardware import Hardware
    from database.models.tool import Tool

    # Import inventory models
    from database.models.material_inventory import MaterialInventory
    from database.models.leather_inventory import LeatherInventory
    from database.models.hardware_inventory import HardwareInventory
    from database.models.tool_inventory import ToolInventory

    # Import sales and project models
    from database.models.sales import Sales
    from database.models.sales_item import SalesItem
    from database.models.pattern import Pattern
    from database.models.product import Product
    from database.models.project import Project
    from database.models.picking_list import PickingList
    from database.models.tool_list import ToolList, ToolListItem

    # Import component models
    from database.models.components import (
        Component,
        ComponentMaterial,
        ComponentLeather,
        ComponentHardware,
        ComponentTool,
        PatternComponent,
        ProjectComponent
    )

    # Import storage model
    from database.models.storage import Storage

    # Import config
    from database.models.config import MaterialConfig, ComponentConfig, ModelConfiguration

except ImportError as e:
    # Log the import error and continue
    logger.error(f"Import error in database models package: {e}")

# Register lazy imports for model classes
register_lazy_import("Supplier", "database.models.supplier", "Supplier")
register_lazy_import("Customer", "database.models.customer", "Customer")
register_lazy_import("Material", "database.models.material", "Material")
register_lazy_import("Leather", "database.models.leather", "Leather")
register_lazy_import("Hardware", "database.models.hardware", "Hardware")
register_lazy_import("Tool", "database.models.tool", "Tool")

register_lazy_import("MaterialInventory", "database.models.material_inventory", "MaterialInventory")
register_lazy_import("LeatherInventory", "database.models.leather_inventory", "LeatherInventory")
register_lazy_import("HardwareInventory", "database.models.hardware_inventory", "HardwareInventory")
register_lazy_import("ToolInventory", "database.models.tool_inventory", "ToolInventory")

register_lazy_import("HardwareTransaction", "database.models.transaction", "HardwareTransaction")
register_lazy_import("LeatherTransaction", "database.models.transaction", "LeatherTransaction")
register_lazy_import("MaterialTransaction", "database.models.transaction", "MaterialTransaction")
register_lazy_import("BaseTransaction", "database.models.transaction", "BaseTransaction")

register_lazy_import("Sales", "database.models.sales", "Sales")
register_lazy_import("SalesItem", "database.models.sales_item", "SalesItem")
register_lazy_import("Pattern", "database.models.pattern", "Pattern")
register_lazy_import("Product", "database.models.product", "Product")
register_lazy_import("Project", "database.models.project", "Project")
register_lazy_import("PickingList", "database.models.picking_list", "PickingList")
register_lazy_import("ToolList", "database.models.tool_list", "ToolList")
register_lazy_import("ToolListItem", "database.models.tool_list", "ToolListItem")

register_lazy_import("Component", "database.models.components", "Component")
register_lazy_import("ComponentMaterial", "database.models.components", "ComponentMaterial")
register_lazy_import("ComponentLeather", "database.models.components", "ComponentLeather")
register_lazy_import("ComponentHardware", "database.models.components", "ComponentHardware")
register_lazy_import("ComponentTool", "database.models.components", "ComponentTool")
register_lazy_import("PatternComponent", "database.models.components", "PatternComponent")
register_lazy_import("ProjectComponent", "database.models.components", "ProjectComponent")

register_lazy_import("Storage", "database.models.storage", "Storage")

# Import relationship initializers
try:
    from database.models.init_relationships import initialize_all_relationships

    # Initialize relationships for all models
    initialize_all_relationships()
except ImportError as e:
    logger.error(f"Could not import initialize_all_relationships: {e}")


    def initialize_all_relationships():
        """Placeholder for missing initialize_all_relationships function."""
        logger.error("initialize_all_relationships function not properly imported")

# Add logging to help debug import issues
logger.info("Database models package initialization complete")

__all__ = [
    # Base models
    'Base', 'BaseModel', 'ModelValidationError',

    # Mixins
    'TimestampMixin', 'ValidationMixin', 'TrackingMixin', 'CostingMixin',

    # Main models
    'Supplier', 'Customer', 'Material', 'Leather', 'Hardware', 'Tool',

    # Inventory models
    'MaterialInventory', 'LeatherInventory', 'HardwareInventory', 'ToolInventory',

    # Transaction models
    'BaseTransaction', 'HardwareTransaction', 'LeatherTransaction', 'MaterialTransaction',

    # Sales and project models
    'Sales', 'SalesItem', 'Pattern', 'Product', 'Project', 'PickingList', 'ToolList', 'ToolListItem',

    # Component models
    'Component', 'ComponentMaterial', 'ComponentLeather', 'ComponentHardware', 'ComponentTool',
    'PatternComponent', 'ProjectComponent',

    # Storage model
    'Storage',

    # Configuration
    'MaterialConfig', 'ComponentConfig', 'ModelConfiguration',

    # Functions
    'initialize_database', 'initialize_all_relationships'
]