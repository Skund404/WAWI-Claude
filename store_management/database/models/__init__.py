# database/models/__init__.py
"""
Models Package Initialization for Leatherworking Management System

Provides centralized model registration, lazy loading, and relationship management
with optimized initialization and error handling.
"""

import logging
import time
import os
import sys
import importlib
import traceback
from typing import Optional, Callable, Dict, Any, List, Set, Tuple
from contextlib import contextmanager

from database import Base
from database.models.base import ModelRegistry, ModelFactory, ModelValidationError
# Import circular import resolver
from utils.circular_import_resolver import (
    CircularImportResolver,
    register_lazy_import,
    resolve_lazy_import
)

# Setup logging
logger = logging.getLogger(__name__)

# Keep track of initialization state
_initialized = False
_initialization_metrics = {
    'start_time': 0,
    'end_time': 0,
    'total_time': 0,
    'models_registered': 0,
    'models_failed': 0,
    'relationships_registered': 0
}


class ModelRegistrationError(Exception):
    """
    Exception raised when model registration fails.
    """

    def __init__(self, model_name: str, original_error: Exception):
        self.model_name = model_name
        self.original_error = original_error
        super().__init__(f"Failed to register model {model_name}: {original_error}")


@contextmanager
def initialization_timer():
    """
    Context manager to track initialization time.

    Yields:
        None
    """
    global _initialization_metrics
    start_time = time.time()
    _initialization_metrics['start_time'] = start_time

    try:
        yield
    finally:
        end_time = time.time()
        _initialization_metrics['end_time'] = end_time
        _initialization_metrics['total_time'] = end_time - start_time


class ImportGroup:
    """
    Manages a group of related model imports with dependency tracking.
    """

    def __init__(self, name: str, priority: int = 0):
        """
        Initialize an import group.

        Args:
            name: Name of the import group
            priority: Priority for initialization order (higher values initialized first)
        """
        self.name = name
        self.priority = priority
        self.models: Dict[str, Tuple[str, str]] = {}
        self.dependencies: Set[str] = set()

    def add_model(self, model_name: str, module_path: str, class_name: Optional[str] = None) -> None:
        """
        Add a model to this import group.

        Args:
            model_name: Name of the model
            module_path: Full module path
            class_name: Optional class name (defaults to model_name)
        """
        self.models[model_name] = (module_path, class_name or model_name)

    def add_dependency(self, group_name: str) -> None:
        """
        Add a dependency on another import group.

        Args:
            group_name: Name of the dependency group
        """
        self.dependencies.add(group_name)

    def register_models(self) -> Tuple[List[str], List[Tuple[str, Exception]]]:
        """
        Register all models in this group.

        Returns:
            Tuple of (successful registrations, failed registrations)
        """
        successful = []
        failed = []

        for model_name, (module_path, class_name) in self.models.items():
            try:
                register_model(model_name, module_path, class_name)
                successful.append(model_name)
            except Exception as e:
                failed.append((model_name, e))
                logger.error(f"Failed to register model {model_name}: {e}")

        return successful, failed


# Define import groups with dependencies
_import_groups = {
    'enums': ImportGroup('enums', priority=100),
    'base': ImportGroup('base', priority=90),
    'core': ImportGroup('core', priority=80),
    'inventory': ImportGroup('inventory', priority=70),
    'sales': ImportGroup('sales', priority=60),
    'projects': ImportGroup('projects', priority=50),
    'associations': ImportGroup('associations', priority=40),
    'utils': ImportGroup('utils', priority=30)
}

# Define group dependencies
_import_groups['core'].add_dependency('enums')
_import_groups['inventory'].add_dependency('core')
_import_groups['sales'].add_dependency('core')
_import_groups['projects'].add_dependency('core')
_import_groups['associations'].add_dependency('inventory')
_import_groups['associations'].add_dependency('sales')
_import_groups['associations'].add_dependency('projects')


# Import base configuration (deferred to ensure clean import)
def _import_base_components():
    """Import base components with error handling."""
    try:
        # Import base module
        from .base import (
            Base,
            ModelRegistry,
            ModelFactory,
            ModelValidationError,
            metadata,
            mapper_registry
        )

        # Add to global namespace
        globals().update({
            'Base': Base,
            'ModelRegistry': ModelRegistry,
            'ModelFactory': ModelFactory,
            'ModelValidationError': ModelValidationError,
            'metadata': metadata,
            'mapper_registry': mapper_registry
        })

        logger.debug("Imported base components")
        return True
    except ImportError as e:
        logger.error(f"Failed to import base components: {e}")
        return False


# Relationship management classes - defining them directly in this module to avoid circular imports
class RelationshipType:
    """Enum for relationship types."""
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    ONE_TO_ONE = "one_to_one"


class RelationshipDefinition:
    """Defines a relationship between models."""

    def __init__(self, relationship_type, parent_model, child_model, **kwargs):
        self.relationship_type = relationship_type
        self.parent_model = parent_model
        self.child_model = child_model
        self.options = kwargs


class RelationshipManager:
    """Manages model relationships."""
    _relationships = []

    @classmethod
    def register_relationship(cls, relationship_type, parent_model, child_model, **kwargs):
        """Register a relationship between models."""
        cls._relationships.append(
            RelationshipDefinition(relationship_type, parent_model, child_model, **kwargs)
        )
        logger.debug(f"Registered {relationship_type} relationship: {parent_model} -> {child_model}")

    @classmethod
    def get_relationships(cls):
        """Get all registered relationships."""
        return cls._relationships


# Register relationship helper functions
def register_one_to_many(parent_model, child_model, **kwargs):
    """Register a one-to-many relationship."""
    RelationshipManager.register_relationship(
        RelationshipType.ONE_TO_MANY, parent_model, child_model, **kwargs
    )


def register_many_to_one(child_model, parent_model, **kwargs):
    """Register a many-to-one relationship."""
    RelationshipManager.register_relationship(
        RelationshipType.MANY_TO_ONE, parent_model, child_model, **kwargs
    )


def register_many_to_many(model_a, model_b, **kwargs):
    """Register a many-to-many relationship."""
    RelationshipManager.register_relationship(
        RelationshipType.MANY_TO_MANY, model_a, model_b, **kwargs
    )


def register_one_to_one(model_a, model_b, **kwargs):
    """Register a one-to-one relationship."""
    RelationshipManager.register_relationship(
        RelationshipType.ONE_TO_ONE, model_a, model_b, **kwargs
    )


# Fallback implementation of relationship initialization
def initialize_database_relationships(session):
    """
    Initialize database relationships between models.

    This is a fallback implementation that can be overridden by the actual implementation in init_relationships.py.

    Args:
        session: SQLAlchemy session
    """
    logger.warning("Using fallback relationship initialization - no relationships will be initialized")
    return None


# Try to import the actual relationship components
def _import_relationship_components():
    """Import relationship management components."""
    try:
        # Import relationship components
        from .init_relationships import (
            RelationshipManager as ImportedRelationshipManager,
            initialize_database_relationships as imported_init_rel,
            RelationshipDefinition as ImportedRelationshipDefinition,
            RelationshipType as ImportedRelationshipType,
            register_one_to_many as imported_reg_one_to_many,
            register_many_to_one as imported_reg_many_to_one,
            register_many_to_many as imported_reg_many_to_many,
            register_one_to_one as imported_reg_one_to_one
        )

        # Add to global namespace
        globals().update({
            'RelationshipManager': ImportedRelationshipManager,
            'initialize_database_relationships': imported_init_rel,
            'RelationshipDefinition': ImportedRelationshipDefinition,
            'RelationshipType': ImportedRelationshipType,
            'register_one_to_many': imported_reg_one_to_many,
            'register_many_to_one': imported_reg_many_to_one,
            'register_many_to_many': imported_reg_many_to_many,
            'register_one_to_one': imported_reg_one_to_one
        })

        logger.debug("Imported relationship components")
        return True
    except ImportError as e:
        # We'll use the fallback implementations already defined above
        logger.error(f"Failed to import relationship components: {e}")
        logger.warning("Using fallback relationship implementations")
        return False


# Lazy import function
def register_model(
        model_name: str,
        module_path: str,
        class_name: Optional[str] = None
) -> None:
    """
    Register a model for lazy loading.

    Args:
        model_name: Unique identifier for the model
        module_path: Full module path
        class_name: Optional specific class name (defaults to model_name)
    """
    try:
        register_lazy_import(
            model_name,
            module_path,
            class_name or model_name
        )
        logger.debug(f"Registered model: {model_name}")
        _initialization_metrics['models_registered'] += 1
    except Exception as e:
        logger.error(f"Model registration failed for {model_name}: {e}")
        _initialization_metrics['models_failed'] += 1
        raise ModelRegistrationError(model_name, e)


# Populate import groups with models
def _populate_import_groups():
    """Populate import groups with models."""
    # Enums
    _import_groups['enums'].add_model('QualityGrade', 'database.models.enums', 'QualityGrade')
    _import_groups['enums'].add_model('MaterialType', 'database.models.enums', 'MaterialType')
    _import_groups['enums'].add_model('InventoryStatus', 'database.models.enums', 'InventoryStatus')
    _import_groups['enums'].add_model('SaleStatus', 'database.models.enums', 'SaleStatus')
    _import_groups['enums'].add_model('PaymentStatus', 'database.models.enums', 'PaymentStatus')
    _import_groups['enums'].add_model('PurchaseStatus', 'database.models.enums', 'PurchaseStatus')
    _import_groups['enums'].add_model('CustomerStatus', 'database.models.enums', 'CustomerStatus')
    _import_groups['enums'].add_model('CustomerTier', 'database.models.enums', 'CustomerTier')
    _import_groups['enums'].add_model('CustomerSource', 'database.models.enums', 'CustomerSource')
    _import_groups['enums'].add_model('ProjectType', 'database.models.enums', 'ProjectType')
    _import_groups['enums'].add_model('SkillLevel', 'database.models.enums', 'SkillLevel')
    _import_groups['enums'].add_model('ComponentType', 'database.models.enums', 'ComponentType')
    # Add missing enum types from ER diagram
    _import_groups['enums'].add_model('ProjectStatus', 'database.models.enums', 'ProjectStatus')
    _import_groups['enums'].add_model('LeatherType', 'database.models.enums', 'LeatherType')
    _import_groups['enums'].add_model('HardwareType', 'database.models.enums', 'HardwareType')
    _import_groups['enums'].add_model('ToolType', 'database.models.enums', 'ToolType')
    _import_groups['enums'].add_model('MeasurementUnit', 'database.models.enums', 'MeasurementUnit')
    _import_groups['enums'].add_model('PickingListStatus', 'database.models.enums', 'PickingListStatus')
    _import_groups['enums'].add_model('ToolListStatus', 'database.models.enums', 'ToolListStatus')
    _import_groups['enums'].add_model('SupplierStatus', 'database.models.enums', 'SupplierStatus')

    # Core models
    _import_groups['core'].add_model('Supplier', 'database.models.supplier', 'Supplier')
    _import_groups['core'].add_model('Customer', 'database.models.customer', 'Customer')
    _import_groups['core'].add_model('Material', 'database.models.material', 'Material')
    _import_groups['core'].add_model('Leather', 'database.models.leather', 'Leather')
    _import_groups['core'].add_model('Hardware', 'database.models.hardware', 'Hardware')
    _import_groups['core'].add_model('Tool', 'database.models.tool', 'Tool')

    # Inventory models
    _import_groups['inventory'].add_model('MaterialInventory', 'database.models.material_inventory',
                                          'MaterialInventory')
    _import_groups['inventory'].add_model('LeatherInventory', 'database.models.leather_inventory', 'LeatherInventory')
    _import_groups['inventory'].add_model('HardwareInventory', 'database.models.hardware_inventory',
                                          'HardwareInventory')
    _import_groups['inventory'].add_model('ToolInventory', 'database.models.tool_inventory', 'ToolInventory')
    _import_groups['inventory'].add_model('ProductInventory', 'database.models.product_inventory', 'ProductInventory')

    # Sales models
    _import_groups['sales'].add_model('Sales', 'database.models.sales', 'Sales')
    _import_groups['sales'].add_model('SalesItem', 'database.models.sales_item', 'SalesItem')
    _import_groups['sales'].add_model('Product', 'database.models.product', 'Product')
    _import_groups['sales'].add_model('Purchase', 'database.models.purchase', 'Purchase')
    _import_groups['sales'].add_model('PurchaseItem', 'database.models.purchase_item', 'PurchaseItem')

    # Project models
    _import_groups['projects'].add_model('Pattern', 'database.models.pattern', 'Pattern')
    _import_groups['projects'].add_model('Project', 'database.models.project', 'Project')
    _import_groups['projects'].add_model('Component', 'database.models.component', 'Component')
    _import_groups['projects'].add_model('PickingList', 'database.models.picking_list', 'PickingList')
    _import_groups['projects'].add_model('PickingListItem', 'database.models.picking_list_item', 'PickingListItem')
    _import_groups['projects'].add_model('ToolList', 'database.models.tool_list', 'ToolList')
    _import_groups['projects'].add_model('ToolListItem', 'database.models.tool_list_item', 'ToolListItem')

    # Association models
    _import_groups['associations'].add_model('ProjectComponent', 'database.models.project_component',
                                             'ProjectComponent')
    _import_groups['associations'].add_model('ProductPattern', 'database.models.product_pattern', 'ProductPattern')
    _import_groups['associations'].add_model('ComponentMaterial', 'database.models.component_material',
                                             'ComponentMaterial')
    _import_groups['associations'].add_model('ComponentLeather', 'database.models.component_leather',
                                             'ComponentLeather')
    _import_groups['associations'].add_model('ComponentHardware', 'database.models.component_hardware',
                                             'ComponentHardware')
    _import_groups['associations'].add_model('ComponentTool', 'database.models.component_tool', 'ComponentTool')

    # Utility models
    _import_groups['utils'].add_model('Storage', 'database.models.storage', 'Storage')
    _import_groups['utils'].add_model('ComplianceHistory', 'database.models.compliance_history', 'ComplianceHistory')
    _import_groups['utils'].add_model('StatusHistory', 'database.models.status_history', 'StatusHistory')


def _determine_import_order() -> List[str]:
    """
    Determine the order to import groups based on dependencies.

    Returns:
        List of group names in dependency order
    """
    # Sort groups by priority
    groups_by_priority = sorted(
        _import_groups.items(),
        key=lambda x: x[1].priority,
        reverse=True
    )

    # Initialize result
    result = []
    visited = set()

    def visit_group(group_name: str) -> None:
        """
        Visit a group and its dependencies.

        Args:
            group_name: Name of the group to visit
        """
        if group_name in visited:
            return

        # Visit dependencies first
        group = _import_groups[group_name]
        for dep in group.dependencies:
            visit_group(dep)

        # Add this group
        visited.add(group_name)
        result.append(group_name)

    # Visit all groups
    for group_name, _ in groups_by_priority:
        visit_group(group_name)

    return result


def _register_models_in_order() -> Tuple[int, int]:
    """
    Register all models in dependency order.

    Returns:
        Tuple of (successful registrations, failed registrations)
    """
    successful_count = 0
    failed_count = 0

    # Determine import order
    import_order = _determine_import_order()
    logger.debug(f"Importing groups in order: {import_order}")

    # Register models in each group
    for group_name in import_order:
        group = _import_groups[group_name]
        successful, failed = group.register_models()

        successful_count += len(successful)
        failed_count += len(failed)

        if successful:
            logger.info(f"Registered {len(successful)} models in group {group_name}")

        if failed:
            logger.warning(f"Failed to register {len(failed)} models in group {group_name}")

    return successful_count, failed_count


def _retry_failed_registrations(max_retries: int = 3) -> int:
    """
    Retry failed model registrations.

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        Number of successful retries
    """
    retry_success_count = 0
    retry_candidates = []

    # Collect retry candidates from all groups
    for group in _import_groups.values():
        for model_name, (module_path, class_name) in group.models.items():
            # Check if model exists in registry
            from .base import ModelRegistry
            if not ModelRegistry.get(model_name):
                retry_candidates.append((model_name, module_path, class_name))

    if not retry_candidates:
        return 0

    # Retry registration for each candidate
    logger.info(f"Attempting to retry {len(retry_candidates)} failed registrations")

    for attempt in range(max_retries):
        if not retry_candidates:
            break

        still_failed = []
        success_in_attempt = 0

        for model_name, module_path, class_name in retry_candidates:
            try:
                register_model(model_name, module_path, class_name)
                retry_success_count += 1
                success_in_attempt += 1
                logger.info(f"Successfully registered {model_name} on retry {attempt + 1}")
            except Exception as e:
                still_failed.append((model_name, module_path, class_name))
                logger.debug(f"Still failed to register {model_name} on retry {attempt + 1}: {e}")

        retry_candidates = still_failed

        if success_in_attempt == 0:
            # No progress in this attempt, stop trying
            break

        logger.info(f"Retry attempt {attempt + 1} recovered {success_in_attempt} models")

    if retry_candidates:
        logger.warning(f"Could not recover {len(retry_candidates)} models after {max_retries} retries")

    return retry_success_count


def initialize_models(retry_failed: bool = True) -> Dict[str, Any]:
    """
    Initialize all database models with comprehensive registration.

    Args:
        retry_failed: Whether to retry failed registrations

    Returns:
        Initialization metrics
    """
    global _initialized, _initialization_metrics

    if _initialized:
        logger.info("Models already initialized. Skipping.")
        return _initialization_metrics

    with initialization_timer():
        logger.info("Starting comprehensive model initialization")

        # Import base components first
        if not _import_base_components():
            logger.error("Failed to import base components, aborting initialization")
            return _initialization_metrics

        # Import relationship components
        _import_relationship_components()

        # Populate import groups with models
        _populate_import_groups()

        # Register models in order
        successful, failed = _register_models_in_order()

        # Update metrics
        _initialization_metrics['models_registered'] = successful
        _initialization_metrics['models_failed'] = failed

        # Retry failed registrations if enabled
        if retry_failed and failed > 0:
            recovery_count = _retry_failed_registrations()
            if recovery_count > 0:
                _initialization_metrics['models_registered'] += recovery_count
                _initialization_metrics['models_failed'] -= recovery_count
                logger.info(f"Recovered {recovery_count} models during retry")

        # Mark as initialized
        _initialized = True

        # Log completion
        duration = _initialization_metrics['total_time']
        logger.info(
            f"Model initialization complete in {duration:.2f}s: "
            f"{_initialization_metrics['models_registered']} models registered, "
            f"{_initialization_metrics['models_failed']} failed"
        )

    return _initialization_metrics


def initialize_database(
        connection_string: Optional[str] = None,
        echo: bool = False,
        create_tables: bool = True,
        initialize_relationships: bool = True
) -> Any:
    """
    Initialize the database with comprehensive setup.

    Args:
        connection_string: Optional database connection string
        echo: Enable SQLAlchemy logging
        create_tables: Whether to create tables automatically
        initialize_relationships: Whether to initialize relationships

    Returns:
        Session factory
    """
    try:
        # Import SQLAlchemy core components
        from sqlalchemy import create_engine, Integer
        from sqlalchemy.orm import sessionmaker, scoped_session

        # Default connection string (can be overridden)
        default_connection = connection_string or 'sqlite:///leatherworking.db'

        # Create engine with configuration
        engine = create_engine(
            default_connection,
            echo=echo,
            future=True
        )

        # Create session factory
        SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False
        )

        # Create scoped session
        Session = scoped_session(SessionLocal)

        # Initialize models (if not already done)
        initialize_models()

        # Create all tables if requested
        if create_tables:
            from .base import metadata
            metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")

        # Initialize database relationships
        if initialize_relationships:
            try:
                # Create a session for relationship initialization
                session = Session()
                initialize_database_relationships(session)
                logger.info("Database relationships initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize relationships: {e}")
                logger.debug(traceback.format_exc())

        logger.info("Database initialized successfully")

        return Session

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.debug(traceback.format_exc())
        raise


def get_initialization_metrics() -> Dict[str, Any]:
    """
    Get metrics about the model initialization process.

    Returns:
        Dictionary of initialization metrics
    """
    return _initialization_metrics


def get_model_registry_metrics() -> Dict[str, Any]:
    """
    Get metrics about the model registry.

    Returns:
        Dictionary of model registry metrics
    """
    try:
        from .base import ModelRegistry
        return ModelRegistry.get_model_metrics()
    except ImportError:
        return {}


# Export key components
__all__ = [
    # Base Classes
    'Base',
    'ModelRegistry',
    'ModelFactory',
    'ModelValidationError',

    # Relationship Management
    'RelationshipManager',
    'RelationshipDefinition',
    'RelationshipType',
    'register_one_to_many',
    'register_many_to_one',
    'register_many_to_many',
    'register_one_to_one',

    # Initialization Functions
    'initialize_database',
    'initialize_models',
    'initialize_database_relationships',
    'register_model',

    # Metrics Functions
    'get_initialization_metrics',
    'get_model_registry_metrics'
]

# Initialize models lazily on first access to the module
# Do not initialize database or relationships, those should be called explicitly
try:
    _import_base_components()
    _import_relationship_components()
except Exception as e:
    logger.warning(f"Deferred base component initialization: {e}")