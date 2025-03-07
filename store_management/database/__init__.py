# database/__init__.py

import logging
from typing import Callable, Optional

from utils.circular_import_resolver import (
    CircularImportResolver,
    register_lazy_import,
    lazy_import,
    resolve_lazy_relationships
)

logger = logging.getLogger(__name__)

try:
    # First, import Base from models.base
    from database.models.base import Base, ModelValidationError

    # Define BaseModel as an alias for Base
    BaseModel = Base

    # Import transaction models directly
    from database.models.transaction import (
        Transaction,
        HardwareTransaction,
        LeatherTransaction,
        MaterialTransaction
    )

    # Import high-level models that are referenced frequently
    from database.models.components import (
        Component,
        PatternComponent,
        ProjectComponent,
        ComponentLeather,
        ComponentHardware,
        ComponentMaterial
    )

    # Import enum values that may be needed throughout the application
    from database.models.enums import (
        LeatherType, MaterialType, SaleStatus,
        ProjectStatus, PaymentStatus, CustomerStatus,
        CustomerTier, CustomerSource, MaterialQualityGrade,
        HardwareMaterial, HardwareFinish, HardwareType,
        ProjectType, SkillLevel, InventoryStatus,
        PurchaseStatus, PickingListStatus, ToolListStatus,
        ToolCategory, ComponentType, MeasurementUnit
    )

    # Import remaining core models
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
    from database.models.tool import Tool
    from database.models.tool_list import ToolList, ToolListItem

    # Import key functions
    from initialize_database import (
        initialize_database,
        initialize_all_relationships,
        add_sample_data,
        add_minimal_sample_data,
        add_extra_demo_data
    )

except ImportError as e:
    logger.error(f"Import error in database module: {e}")
    import traceback

    logger.error(traceback.format_exc())

# Register lazy imports for core models to facilitate circular import resolution
register_lazy_import("database.models.customer.Customer", "database.models.customer", "Customer")
register_lazy_import("database.models.hardware.Hardware", "database.models.hardware", "Hardware")
register_lazy_import("database.models.leather.Leather", "database.models.leather", "Leather")
register_lazy_import("database.models.material.Material", "database.models.material", "Material")
register_lazy_import("database.models.pattern.Pattern", "database.models.pattern", "Pattern")
register_lazy_import("database.models.product.Product", "database.models.product", "Product")
register_lazy_import("database.models.project.Project", "database.models.project", "Project")
register_lazy_import("database.models.sales.Sales", "database.models.sales", "Sales")
register_lazy_import("database.models.supplier.Supplier", "database.models.supplier", "Supplier")
register_lazy_import("database.models.transaction.Transaction", "database.models.transaction", "Transaction")
register_lazy_import("database.models.transaction.MaterialTransaction", "database.models.transaction",
                     "MaterialTransaction")
register_lazy_import("database.models.transaction.LeatherTransaction", "database.models.transaction",
                     "LeatherTransaction")
register_lazy_import("database.models.transaction.HardwareTransaction", "database.models.transaction",
                     "HardwareTransaction")

# Lazily initialize relationships after all imports are complete
try:
    resolve_lazy_relationships()
except Exception as e:
    logger.warning(f"Error initializing lazy relationships: {e}")

# Add logging to help debug import issues
logger.debug("database package initialization complete")

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