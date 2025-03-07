# database/models/models.py
"""
Central Index for Leatherworking Management System Models

This module serves as the central import and initialization point
for all models in the application, providing convenient access and
initialization of models and their relationships.
"""

import logging
from typing import Dict, Any, Type, List, Optional, Union, Set

# Import base classes and metadata
from database.models.base import Base
from database.models.model_metaclass import BaseModelMetaclass

# Import interfaces
from database.models.interfaces import IModel, IProject, IInventoryItem, ISalesItem

# Import primary models
from database.models.customer import Customer
from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.models.product import Product
from database.models.pattern import Pattern
from database.models.project import Project
from database.models.components import (
    Component,
    ProjectComponent,
    ComponentMaterial,
    ComponentLeather,
    ComponentHardware,
    ComponentTool
)
# Note: PatternComponent is actually missing from components.py and should be implemented there

# Import inventory models
from database.models.material import Material
from database.models.material_inventory import MaterialInventory
from database.models.leather import Leather
from database.models.leather_inventory import LeatherInventory
from database.models.hardware import Hardware
from database.models.hardware_inventory import HardwareInventory
from database.models.tool import Tool
from database.models.inventory import Inventory

# Import support models
from database.models.supplier import Supplier
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem  # Corrected import
from database.models.storage import Storage
from database.models.picking_list import PickingList, PickingListItem
from database.models.tool_list import ToolList, ToolListItem
from database.models.metrics import MetricSnapshot, MaterialUsageLog, EfficiencyReport
from database.models.transaction import (
    Transaction,
    MaterialTransaction,
    LeatherTransaction,
    HardwareTransaction
)

# Import enums for convenience
from database.models.enums import (
    SaleStatus,
    PaymentStatus,
    ProjectStatus,
    ProjectType,
    ComponentType,
    InventoryStatus,
    MaterialType,
    LeatherType,
    HardwareType,
    TransactionType,
    InventoryAdjustmentType,
    SkillLevel,
    QualityGrade,
    MeasurementUnit
)

# Import model factories
from database.models.factories import (
    ProjectFactory,
    PatternFactory,
    ComponentFactory,
    SalesFactory,
    HardwareFactory,
    MaterialFactory,
    LeatherFactory,
    ToolFactory,        # Added missing factory
    SupplierFactory,    # Added missing factory
    ProductFactory      # Added missing factory
)

# Setup logger
logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Central registry for model management and initialization.

    This class provides utility methods for working with models, including
    initialization, registration tracking, and relationship management.
    """

    # Track models for easy lookup
    _models: Dict[str, Type] = {}
    _model_instances: Dict[str, Dict[int, Any]] = {}

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize all models and their relationships.

        This method should be called during application startup to ensure
        all models and their relationships are properly initialized.
        """
        try:
            logger.info("Initializing model registry...")

            # Register primary models
            cls._register_models()

            # Initialize all relationships
            cls._initialize_relationships()

            logger.info("Model registry initialization completed successfully")
        except Exception as e:
            logger.error(f"Error initializing model registry: {e}")
            raise

    @classmethod
    def _register_models(cls) -> None:
        """
        Register all models in the central registry.
        """
        # Collect all model classes from BaseModelMetaclass registry
        if hasattr(BaseModelMetaclass, '_registered_models'):
            cls._models.update(BaseModelMetaclass._registered_models)
            logger.debug(f"Registered {len(cls._models)} models from metaclass registry")
        else:
            # Register models manually if metaclass registry not available
            models = [
                Customer, Sales, SalesItem, Product, Pattern, Project,
                Component, ProjectComponent,
                ComponentMaterial, ComponentLeather, ComponentHardware, ComponentTool,
                Material, MaterialInventory, Leather, LeatherInventory,
                Hardware, HardwareInventory, Tool, Inventory,
                Supplier, Purchase, PurchaseItem, Storage,
                PickingList, PickingListItem, ToolList, ToolListItem,
                MetricSnapshot, MaterialUsageLog, EfficiencyReport,
                Transaction, MaterialTransaction, LeatherTransaction, HardwareTransaction
            ]

            for model in models:
                cls._models[model.__name__] = model

            logger.debug(f"Manually registered {len(cls._models)} models")

    @classmethod
    def _initialize_relationships(cls) -> None:
        """
        Initialize all model relationships.
        """
        # Use metaclass relationship initialization if available
        if hasattr(BaseModelMetaclass, 'initialize_all_relationships'):
            BaseModelMetaclass.initialize_all_relationships()
            logger.debug("Initialized relationships using metaclass")
        else:
            # Otherwise, call individual relationship initializers
            for model_name, model_class in cls._models.items():
                if hasattr(model_class, 'initialize_relationships'):
                    try:
                        model_class.initialize_relationships()
                        logger.debug(f"Initialized relationships for {model_name}")
                    except Exception as e:
                        logger.error(f"Error initializing relationships for {model_name}: {e}")

    @classmethod
    def get_model(cls, model_name: str) -> Optional[Type]:
        """
        Get a model class by name.

        Args:
            model_name: Name of the model to retrieve

        Returns:
            The model class or None if not found
        """
        return cls._models.get(model_name)

    @classmethod
    def get_instance(cls, model_name: str, instance_id: int) -> Optional[Any]:
        """
        Get a cached model instance by name and ID.

        Note: This is primarily used for in-memory caching during
        application runtime, not for database retrieval.

        Args:
            model_name: Name of the model
            instance_id: ID of the instance

        Returns:
            The model instance or None if not found
        """
        return cls._model_instances.get(model_name, {}).get(instance_id)

    @classmethod
    def cache_instance(cls, instance: Any) -> None:
        """
        Cache a model instance for later retrieval.

        Args:
            instance: The model instance to cache
        """
        if not hasattr(instance, 'id') or not hasattr(instance, '__class__'):
            return

        model_name = instance.__class__.__name__

        if model_name not in cls._model_instances:
            cls._model_instances[model_name] = {}

        cls._model_instances[model_name][instance.id] = instance

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the instance cache.
        """
        cls._model_instances.clear()

    @classmethod
    def get_model_dependencies(cls, model_name: str) -> Set[str]:
        """
        Get all models that depend on the specified model.

        Args:
            model_name: Name of the model

        Returns:
            Set of model names that depend on the specified model
        """
        dependencies = set()

        # Check each model for relationships to the target model
        for name, model in cls._models.items():
            if hasattr(model, '__mapper__') and hasattr(model.__mapper__, 'relationships'):
                for relationship in model.__mapper__.relationships:
                    if relationship.target.name == model_name:
                        dependencies.add(name)

        return dependencies


# Initialize model registry during module import
# This ensures models are registered but relationships
# will be initialized when explicitly called
ModelRegistry._register_models()

# Convenience exports
__all__ = [
    # Base classes
    'Base',
    'IModel',
    'IProject',
    'IInventoryItem',
    'ISalesItem',

    # Primary models
    'Customer',
    'Sales',
    'SalesItem',
    'Product',
    'Pattern',
    'Project',
    'Component',
    'ProjectComponent',
    # 'PatternComponent', # Removed as it doesn't exist in components.py

    # Inventory models
    'Material',
    'MaterialInventory',
    'Leather',
    'LeatherInventory',
    'Hardware',
    'HardwareInventory',
    'Tool',
    'Inventory',

    # Support models
    'Supplier',
    'Purchase',
    'PurchaseItem',
    'Storage',
    'PickingList',
    'PickingListItem',
    'ToolList',
    'ToolListItem',
    'MetricSnapshot',
    'MaterialUsageLog',
    'EfficiencyReport',
    'Transaction',
    'MaterialTransaction',
    'LeatherTransaction',
    'HardwareTransaction',

    # Factories
    'ProjectFactory',
    'PatternFactory',
    'ComponentFactory',
    'SalesFactory',
    'HardwareFactory',
    'MaterialFactory',
    'LeatherFactory',
    'ToolFactory',        # Added missing factory
    'SupplierFactory',    # Added missing factory
    'ProductFactory',     # Added missing factory

    # Enums
    'SaleStatus',
    'PaymentStatus',
    'ProjectStatus',
    'ProjectType',
    'ComponentType',
    'InventoryStatus',
    'MaterialType',
    'LeatherType',
    'HardwareType',
    'TransactionType',
    'InventoryAdjustmentType',
    'SkillLevel',
    'QualityGrade',
    'MeasurementUnit',

    # Registry
    'ModelRegistry'
]


def initialize_models() -> None:
    """
    Convenience function to initialize all models during application startup.
    """
    ModelRegistry.initialize()