# database/models/__init__.py
"""
Database models package initialization.

This module imports and registers all model classes and manages their initialization.
"""

import logging
import importlib

# Setup logger
logger = logging.getLogger(__name__)

# Base model classes
from database.models.base import Base, ModelValidationError

# Import utility for circular imports
from utils.circular_import_resolver import CircularImportResolver

# Import enums first as they don't have dependencies
from database.models.enums import (
    SaleStatus, PaymentStatus, CustomerStatus, CustomerTier, CustomerSource,
    HardwareType, HardwareMaterial, HardwareFinish, PickingListStatus,
    MaterialQualityGrade, InventoryStatus, ShoppingListStatus, SupplierStatus,
    StorageLocationType, MeasurementUnit, Priority, TransactionType,
    QualityCheckStatus, ComponentType, ProjectType, LeatherType, LeatherFinish,
    ProjectStatus, ToolCategory, MaterialType, SkillLevel, QualityGrade, EdgeFinishType,
    PurchaseStatus, ToolListStatus
)

# Entity models - order matters to reduce circular imports
# First import models with fewer dependencies
from database.models.customer import Customer
from database.models.supplier import Supplier
from database.models.material import Material
from database.models.leather import Leather
from database.models.hardware import Hardware
from database.models.tool import Tool

# Then import inventory models
from database.models.material_inventory import MaterialInventory
from database.models.leather_inventory import LeatherInventory
from database.models.hardware_inventory import HardwareInventory
from database.models.tool_inventory import ToolInventory

# Component and pattern models
from database.models.pattern import Pattern
from database.models.components import (
    Component, PatternComponent, ProjectComponent,
    ComponentMaterial, ComponentLeather, ComponentHardware, ComponentTool
)

# Product models
from database.models.product import Product
from database.models.product_inventory import ProductInventory
from database.models.product_pattern import ProductPattern

# Project and list models
from database.models.project import Project
from database.models.shopping_list import ShoppingList, ShoppingListItem
from database.models.tool_list import ToolList, ToolListItem
from database.models.storage import Storage
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem

# Transaction models
from database.models.transaction import (
    BaseTransaction, MaterialTransaction, LeatherTransaction, HardwareTransaction
)

# Import picking list models - these may depend on sales
from database.models.picking_list import PickingList, PickingListItem

# Sales models - import with special handling to avoid circular imports
try:
    # Use importlib to avoid direct import issues
    sales_module = importlib.import_module('database.models.sales')
    Sales = sales_module.Sales
    logger.debug("Successfully imported Sales model")
except ImportError as e:
    logger.error(f"Error importing Sales model: {e}")
    Sales = None

try:
    # Use importlib to avoid direct import issues
    sales_item_module = importlib.import_module('database.models.sales_item')
    SalesItem = sales_item_module.SalesItem
    logger.debug("Successfully imported SalesItem model")
except ImportError as e:
    logger.error(f"Error importing SalesItem model: {e}")
    SalesItem = None

# Initialize relationships for models with circular dependencies
def initialize_all_relationships():
    """Initialize all relationships for models with circular dependencies."""
    try:
        logger.info("Initializing all model relationships")

        # List of modules with relationship initialization
        modules_to_initialize = [
            'database.models.sales',
            'database.models.sales_item',
            'database.models.product',
            'database.models.pattern',
            'database.models.product_pattern',
            'database.models.picking_list',
            'database.models.transaction',
        ]

        # Initialize relationships for each module
        for module_path in modules_to_initialize:
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, 'initialize_relationships'):
                    logger.debug(f"Initializing relationships for {module_path}")
                    module.initialize_relationships()
            except Exception as e:
                logger.error(f"Error initializing relationships for {module_path}: {e}")
                import traceback
                logger.error(traceback.format_exc())

        logger.info("All model relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error during relationship initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Initialize relationships
initialize_all_relationships()