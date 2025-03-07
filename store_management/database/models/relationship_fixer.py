# database/models/relationship_fixer.py
"""
Relationship Fixer Script for Leatherworking Management System

This script automatically fixes relationship issues in all models by
applying the safe_relationship utility and ensuring proper initialization.
Run this script after importing all models to resolve relationship problems.
"""

import logging
import importlib
import inspect
from typing import List, Dict, Any, Type

from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

from database.models.base import Base
from database.models.relationship_helper import fix_relationship_conflicts, ensure_relationships_initialized

# Setup logger
logger = logging.getLogger(__name__)


def fix_all_relationships():
    """
    Fix relationship issues across all models in the system.

    This function:
    1. Collects all Base-derived model classes
    2. Applies fixes to their relationships
    3. Ensures all relationships are properly initialized

    Returns:
        int: Number of model classes processed
    """
    logger.info("Starting relationship fixing process for all models...")

    # Collect all model classes
    model_classes = _collect_model_classes()
    logger.info(f"Found {len(model_classes)} model classes to process")

    # Fix metadata for each model
    for model_class in model_classes:
        try:
            _fix_model_relationships(model_class)
        except Exception as e:
            logger.error(f"Error fixing relationships for {model_class.__name__}: {e}")

    # Process the Base metadata
    if hasattr(Base, 'metadata'):
        # Fix any conflicts and ensure initialization
        fix_relationship_conflicts(Base.metadata)
        ensure_relationships_initialized(Base.metadata)

    logger.info("Relationship fixing process completed")
    return len(model_classes)


def _collect_model_classes() -> List[Type]:
    """
    Collect all model classes derived from Base.

    Returns:
        List[Type]: List of model classes
    """
    model_classes = []

    # Import all model modules
    model_modules = [
        "database.models.customer",
        "database.models.sales",
        "database.models.sales_item",
        "database.models.product",
        "database.models.pattern",
        "database.models.project",
        "database.models.components",
        "database.models.material",
        "database.models.material_inventory",
        "database.models.leather",
        "database.models.leather_inventory",
        "database.models.hardware",
        "database.models.hardware_inventory",
        "database.models.tool",
        "database.models.inventory",
        "database.models.supplier",
        "database.models.purchase",
        "database.models.purchase_item",
        "database.models.storage",
        "database.models.picking_list",
        "database.models.tool_list",
        "database.models.metrics",
        "database.models.transaction",
    ]

    # Import each module and collect model classes
    for module_name in model_modules:
        try:
            module = importlib.import_module(module_name)

            # Find all Base-derived classes in the module
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Base) and obj != Base:
                    model_classes.append(obj)
                    logger.debug(f"Found model class: {obj.__name__}")
        except Exception as e:
            logger.warning(f"Error importing module {module_name}: {e}")

    return model_classes


def _fix_model_relationships(model_class: Type) -> None:
    """
    Fix relationships for a specific model class.

    Args:
        model_class: The model class to fix relationships for
    """
    try:
        logger.debug(f"Fixing relationships for {model_class.__name__}")

        # Call the initialize_relationships method if it exists
        if hasattr(model_class, 'initialize_relationships') and callable(model_class.initialize_relationships):
            try:
                model_class.initialize_relationships()
                logger.debug(f"Called initialize_relationships for {model_class.__name__}")
            except Exception as e:
                logger.warning(f"Error calling initialize_relationships for {model_class.__name__}: {e}")

        # Check if the model has a __table__ attribute
        if hasattr(model_class, '__table__'):
            # Fix mapper relationships if they exist
            try:
                from sqlalchemy import inspect
                mapper = inspect(model_class)

                # Process each relationship in the mapper
                for relationship in mapper.relationships:
                    # Ensure the parent attribute is set
                    if not hasattr(relationship, 'parent') or relationship.parent is None:
                        relationship.parent = mapper

                logger.debug(f"Fixed mapper relationships for {model_class.__name__}")
            except Exception as e:
                logger.warning(f"Error fixing mapper relationships for {model_class.__name__}: {e}")
    except Exception as e:
        logger.error(f"Error in _fix_model_relationships for {model_class.__name__}: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the fix process
    num_models = fix_all_relationships()
    print(f"Processed {num_models} model classes")