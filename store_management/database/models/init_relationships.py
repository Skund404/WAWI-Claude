# database/models/init_relationships.py
"""
Initialize relationships between models for Leatherworking Management System.

This module provides functions to initialize relationships between models
with circular dependencies. It should be imported after all models are loaded.
"""

import logging
import importlib
import traceback
from typing import List, Optional, Dict, Any, Type

from sqlalchemy.orm import relationship

# Setup logger
logger = logging.getLogger(__name__)


def initialize_all_relationships() -> None:
    """
    Initialize relationships for all models that need late binding
    due to circular dependencies.

    This function is called after all models are loaded to ensure
    relationships are properly established.
    """
    logger.info("Initializing all model relationships...")

    # List of modules that need relationship initialization
    models_to_initialize = [
        'database.models.sales',
        'database.models.sales_item',
        'database.models.product',
        'database.models.pattern',
        'database.models.product_pattern',
        'database.models.picking_list',
        'database.models.project',
        'database.models.transaction',
        'database.models.components',
        'database.models.storage'
    ]

    for model_path in models_to_initialize:
        try:
            # Import the module
            module = importlib.import_module(model_path)

            # Find all model classes that have initialize_relationships method
            if hasattr(module, 'initialize_relationships'):
                logger.debug(f"Initializing relationships for {model_path}")
                module.initialize_relationships()
            else:
                logger.debug(f"No initialize_relationships method found in {model_path}")
        except Exception as e:
            logger.error(f"Error initializing relationships for {model_path}: {e}")
            logger.error(traceback.format_exc())

    logger.info("All model relationships initialized.")


def init_sales_relationships() -> bool:
    """
    Initialize relationships between Sales and SalesItem.

    Returns:
        True if relationships were successfully initialized, False otherwise
    """
    try:
        # Import models explicitly
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem

        # Check and set up Sales->SalesItems relationship if needed
        if not hasattr(Sales, 'items'):
            Sales.items = relationship(
                'SalesItem',
                back_populates='sale',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added items relationship to Sales")

        # Check and set up SalesItem->Sales relationship if needed
        if not hasattr(SalesItem, 'sale'):
            SalesItem.sale = relationship(
                'Sales',
                back_populates='items',
                lazy='selectin'
            )
            logger.debug("Added sale relationship to SalesItem")

        logger.info("Sales relationships initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize sales relationships: {e}")
        logger.error(traceback.format_exc())
        return False


def init_project_relationships() -> bool:
    """
    Initialize relationships involving Project models.

    Returns:
        True if relationships were successfully initialized, False otherwise
    """
    try:
        # Import models
        from database.models.project import Project
        from database.models.picking_list import PickingList
        from database.models.tool_list import ToolList
        from database.models.components import ProjectComponent

        # Check and set up Project->PickingList relationship if needed
        if not hasattr(Project, 'picking_list'):
            Project.picking_list = relationship(
                'PickingList',
                back_populates='project',
                uselist=False,
                lazy='selectin'
            )
            logger.debug("Added picking_list relationship to Project")

        # Check and set up Project->ToolList relationship if needed
        if not hasattr(Project, 'tool_list'):
            Project.tool_list = relationship(
                'ToolList',
                back_populates='project',
                uselist=False,
                lazy='selectin'
            )
            logger.debug("Added tool_list relationship to Project")

        # Check and set up Project->ProjectComponent relationship if needed
        if not hasattr(Project, 'components'):
            Project.components = relationship(
                'ProjectComponent',
                back_populates='project',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added components relationship to Project")

        logger.info("Project relationships initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize project relationships: {e}")
        logger.error(traceback.format_exc())
        return False


def init_component_relationships() -> bool:
    """
    Initialize relationships involving Component models.

    Returns:
        True if relationships were successfully initialized, False otherwise
    """
    try:
        # Import models
        from database.models.components import (
            Component,
            ComponentMaterial,
            ComponentLeather,
            ComponentHardware,
            ComponentTool
        )

        # Check and set up Component->ComponentMaterial relationship if needed
        if not hasattr(Component, 'materials'):
            Component.materials = relationship(
                'ComponentMaterial',
                back_populates='component',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added materials relationship to Component")

        # Check and set up Component->ComponentLeather relationship if needed
        if not hasattr(Component, 'leathers'):
            Component.leathers = relationship(
                'ComponentLeather',
                back_populates='component',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added leathers relationship to Component")

        # Check and set up Component->ComponentHardware relationship if needed
        if not hasattr(Component, 'hardware_items'):
            Component.hardware_items = relationship(
                'ComponentHardware',
                back_populates='component',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added hardware_items relationship to Component")

        # Check and set up Component->ComponentTool relationship if needed
        if not hasattr(Component, 'tools'):
            Component.tools = relationship(
                'ComponentTool',
                back_populates='component',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added tools relationship to Component")

        logger.info("Component relationships initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize component relationships: {e}")
        logger.error(traceback.format_exc())
        return False


def init_inventory_relationships() -> bool:
    """
    Initialize relationships involving Inventory models.

    Returns:
        True if relationships were successfully initialized, False otherwise
    """
    try:
        # Import inventory models
        from database.models.material_inventory import MaterialInventory
        from database.models.leather_inventory import LeatherInventory
        from database.models.hardware_inventory import HardwareInventory
        from database.models.tool_inventory import ToolInventory

        # Import transaction models
        from database.models.transaction import (
            MaterialTransaction,
            LeatherTransaction,
            HardwareTransaction
        )

        # Set up LeatherInventory->LeatherTransaction relationship if needed
        if not hasattr(LeatherInventory, 'transactions'):
            LeatherInventory.transactions = relationship(
                'LeatherTransaction',
                back_populates='leather_inventory',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added transactions relationship to LeatherInventory")

        # Set up MaterialInventory->MaterialTransaction relationship if needed
        if not hasattr(MaterialInventory, 'transactions'):
            MaterialInventory.transactions = relationship(
                'MaterialTransaction',
                back_populates='material_inventory',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added transactions relationship to MaterialInventory")

        # Set up HardwareInventory->HardwareTransaction relationship if needed
        if not hasattr(HardwareInventory, 'transactions'):
            HardwareInventory.transactions = relationship(
                'HardwareTransaction',
                back_populates='hardware_inventory',
                cascade='all, delete-orphan',
                lazy='selectin'
            )
            logger.debug("Added transactions relationship to HardwareInventory")

        logger.info("Inventory relationships initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize inventory relationships: {e}")
        logger.error(traceback.format_exc())
        return False


# For testing purposes
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    initialize_all_relationships()