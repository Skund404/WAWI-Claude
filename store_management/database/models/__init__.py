# database/models/__init__.py
"""
Centralized model initialization for the leatherworking management system.
Provides comprehensive model registration and relationship setup.
"""
import importlib
import logging
from contextlib import contextmanager
import time
from typing import List, Type, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# First import base and enums
from database.models.base import (
    Base, AbstractBase, ModelValidationError, ModelRegistry,
    ValidationMixin, TimestampMixin, CostingMixin,
    TrackingMixin, ComplianceMixin, AuditMixin, metadata
)
from database.models.enums import *

# Import relationship tables before entity models
from database.models.relationship_tables import (
    component_material_table, product_pattern_table, pattern_component_table
)

# Predefined import order that minimizes circular dependencies
IMPORT_ORDER = [
    "supplier",
    "material",
    "inventory",
    "component",
    "component_material",
    "pattern",
    "product",
    "customer",
    "sales",
    "sales_item",
    "purchase",
    "purchase_item",
    "project",
    "project_component",
    "picking_list",
    "picking_list_item",
    "tool",
    "tool_list",
    "tool_list_item"
]

def import_models() -> Dict[str, Any]:
    """
    Import all models in a predefined order that minimizes circular dependencies.

    Returns:
        Dictionary of successfully imported models
    """
    imported_models = {}

    for module_name in IMPORT_ORDER:
        try:
            module = importlib.import_module(f"database.models.{module_name}")

            # Find all model classes in the module (subclasses of Base)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Base) and attr != AbstractBase:
                    imported_models[attr_name] = attr
                    logger.debug(f"Successfully imported {attr_name}")

        except Exception as e:
            logger.error(f"Error importing module {module_name}: {e}")

    return imported_models


# Import and register models
MODELS = import_models()


def get_model(model_name: str) -> Type:
    """
    Get a model by name.

    Args:
        model_name: Name of the model to retrieve

    Returns:
        The model class or raises KeyError
    """
    if model_name not in MODELS:
        raise KeyError(f"Model {model_name} not found. Available models: {list(MODELS.keys())}")
    return MODELS[model_name]


@contextmanager
def initialization_timer():
    """Context manager to track model initialization performance."""
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        logger.info(f"Model initialization completed in {end_time - start_time:.4f} seconds")


def register_models():
    """Register all imported models in ModelRegistry."""
    for model_name, model in MODELS.items():
        try:
            ModelRegistry.register(model)
            logger.debug(f"Registered model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to register model {model_name}: {e}")


# Perform initialization
with initialization_timer():
    register_models()

# Expose key components
__all__ = [
    # Base classes and mixins
    'Base', 'AbstractBase', 'ModelValidationError', 'metadata',
    'ValidationMixin', 'TimestampMixin', 'CostingMixin',
    'TrackingMixin', 'ComplianceMixin', 'AuditMixin',

    # Utility functions
    'ModelRegistry', 'get_model',

    # All models
    *list(MODELS.keys())
]