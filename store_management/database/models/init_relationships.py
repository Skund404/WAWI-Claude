# database/models/init_relationships.py
"""
Centralized Relationship Initialization for Leatherworking Management System

This module provides a comprehensive mechanism for initializing
relationships between models based on the entity-relationship diagram.
"""

import logging
import importlib
import traceback
from typing import Dict, Any, Optional, Type, List, Tuple, Set, Union
from enum import Enum, auto

from sqlalchemy.orm import relationship, Session
from sqlalchemy import select, ForeignKey

from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    resolve_lazy_import
)

# Setup logger
logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Enum defining different types of relationships for better classification."""
    ONE_TO_ONE = auto()
    ONE_TO_MANY = auto()
    MANY_TO_ONE = auto()
    MANY_TO_MANY = auto()


class RelationshipDefinition:
    """
    Structured relationship definition class to standardize relationship configurations.
    """

    def __init__(
            self,
            source_model: str,
            relationship_name: str,
            target_model: str,
            relationship_type: RelationshipType,
            back_populates: Optional[str] = None,
            backref: Optional[str] = None,
            lazy: str = "selectin",
            cascade: Optional[str] = None,
            uselist: Optional[bool] = None,
            secondary: Optional[str] = None,
            foreign_keys: Optional[List[str]] = None,
            **kwargs
    ):
        """
        Initialize a comprehensive relationship definition.

        Args:
            source_model: Name of the source model
            relationship_name: Name of the relationship attribute
            target_model: Name of the target model
            relationship_type: Type of relationship from RelationshipType enum
            back_populates: Optional name of attribute on target model for bidirectional relationships
            backref: Optional name for automatic bidirectional relationship
            lazy: Loading strategy (default: "selectin" for efficient loading)
            cascade: Cascade behavior
            uselist: Whether to use a list (True) or scalar (False)
            secondary: Optional secondary table for many-to-many relationships
            foreign_keys: Optional explicit foreign key specification
            **kwargs: Additional SQLAlchemy relationship parameters
        """
        self.source_model = source_model
        self.relationship_name = relationship_name
        self.target_model = target_model
        self.relationship_type = relationship_type
        self.back_populates = back_populates
        self.backref = backref
        self.lazy = lazy

        # Set default cascade behavior based on relationship type
        if cascade is None:
            if relationship_type in (RelationshipType.ONE_TO_MANY, RelationshipType.ONE_TO_ONE):
                self.cascade = "all, delete-orphan"
            else:
                self.cascade = "all"
        else:
            self.cascade = cascade

        # Auto-configure uselist based on relationship type if not explicitly provided
        if uselist is None:
            self.uselist = relationship_type in (
                RelationshipType.ONE_TO_MANY,
                RelationshipType.MANY_TO_MANY
            )
        else:
            self.uselist = uselist

        self.secondary = secondary
        self.foreign_keys = foreign_keys
        self.kwargs = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert relationship definition to a configuration dictionary.

        Returns:
            Dictionary of relationship configuration parameters
        """
        config = {
            'target_model': self.target_model,
            'config': {
                'lazy': self.lazy,
                'uselist': self.uselist,
                'cascade': self.cascade,
            }
        }

        # Add optional parameters only if they have values
        if self.back_populates:
            config['config']['back_populates'] = self.back_populates

        if self.backref:
            config['config']['backref'] = self.backref

        if self.secondary:
            config['config']['secondary'] = self.secondary

        if self.foreign_keys:
            config['config']['foreign_keys'] = self.foreign_keys

        # Add any additional kwargs
        config['config'].update(self.kwargs)

        return config


class RelationshipManager:
    """
    Advanced relationship management for database models.

    Provides comprehensive mechanisms for:
    - Lazy relationship loading
    - Circular dependency resolution
    - Dynamic relationship configuration
    - Dependency tracking for proper initialization order
    """

    _relationship_registry: Dict[str, Dict[str, Dict[str, Any]]] = {}
    _dependency_graph: Dict[str, Set[str]] = {}
    _initialization_order: List[str] = []
    _initialized: bool = False

    @classmethod
    def register_relationship(
            cls,
            source_model: str,
            relationship_name: str,
            target_model: str,
            config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a relationship configuration.

        Args:
            source_model: Name of the source model
            relationship_name: Name of the relationship
            target_model: Name of the target model
            config: Optional relationship configuration
        """
        if source_model not in cls._relationship_registry:
            cls._relationship_registry[source_model] = {}

        # Ensure configuration exists
        effective_config = config or {}

        cls._relationship_registry[source_model][relationship_name] = {
            'target_model': target_model,
            'config': effective_config
        }

        # Update dependency graph for initialization order
        if source_model not in cls._dependency_graph:
            cls._dependency_graph[source_model] = set()

        cls._dependency_graph[source_model].add(target_model)

        logger.debug(
            f"Registered relationship: {source_model}.{relationship_name} "
            f"-> {target_model}"
        )

    @classmethod
    def register_relationship_definition(cls, definition: RelationshipDefinition) -> None:
        """
        Register a relationship using a structured RelationshipDefinition.

        Args:
            definition: Complete relationship definition object
        """
        # Convert definition to configuration dictionary
        config_dict = definition.to_dict()

        # Register using standard method
        cls.register_relationship(
            definition.source_model,
            definition.relationship_name,
            definition.target_model,
            config_dict.get('config', {})
        )

    @classmethod
    def _determine_initialization_order(cls) -> List[str]:
        """
        Determine the optimal order for relationship initialization based on dependencies.

        Returns:
            List of model names in dependency order
        """
        visited: Set[str] = set()
        temp_visited: Set[str] = set()
        order: List[str] = []

        def visit(node: str) -> None:
            """Recursive depth-first traversal with cycle detection."""
            if node in temp_visited:
                # Cycle detected, break with current knowledge
                logger.warning(f"Circular dependency detected for model: {node}")
                return

            if node in visited:
                return

            temp_visited.add(node)

            # Visit dependencies first
            for dependency in cls._dependency_graph.get(node, set()):
                visit(dependency)

            temp_visited.remove(node)
            visited.add(node)
            order.append(node)

        # Start from each unvisited node
        for node in cls._dependency_graph:
            if node not in visited:
                visit(node)

        # Reverse for proper initialization order
        return list(reversed(order))

    @classmethod
    def resolve_relationships(cls) -> None:
        """
        Resolve all registered relationships across models.

        This method dynamically resolves and configures relationships
        for all registered models, handling circular dependencies.
        """
        if cls._initialized:
            logger.info("Relationships already initialized. Skipping.")
            return

        logger.info("Starting comprehensive relationship resolution...")

        # Import here to avoid circular imports
        from .base import ModelRegistry

        # Determine initialization order based on dependencies
        cls._initialization_order = cls._determine_initialization_order()
        logger.debug(f"Initialization order: {cls._initialization_order}")

        # First pass: resolve all available models
        available_models = {}
        for model_name in cls._initialization_order:
            try:
                model = ModelRegistry.get(model_name)
                if model:
                    available_models[model_name] = model
                else:
                    # Try lazy resolution
                    model = resolve_lazy_import(model_name)
                    if model:
                        available_models[model_name] = model
                    else:
                        logger.warning(f"Could not resolve model: {model_name}")
            except Exception as e:
                logger.warning(f"Error resolving model {model_name}: {e}")

        # Second pass: process relationships in dependency order
        for source_model_name in cls._initialization_order:
            if source_model_name not in available_models:
                continue

            source_model = available_models[source_model_name]
            relationships = cls._relationship_registry.get(source_model_name, {})

            for rel_name, rel_details in relationships.items():
                try:
                    target_model_name = rel_details['target_model']
                    if target_model_name not in available_models:
                        logger.warning(
                            f"Target model {target_model_name} for relationship "
                            f"{source_model_name}.{rel_name} not available"
                        )
                        continue

                    target_model = available_models[target_model_name]

                    # Prepare relationship configuration
                    rel_config = rel_details['config'].copy()

                    # Replace string-based model references
                    if 'secondary' in rel_config and isinstance(rel_config['secondary'], str):
                        secondary_model_name = rel_config['secondary']
                        if secondary_model_name in available_models:
                            rel_config['secondary'] = available_models[secondary_model_name].__table__
                        else:
                            logger.warning(
                                f"Secondary table {secondary_model_name} not found for "
                                f"{source_model_name}.{rel_name}"
                            )
                            continue

                    # Create the relationship
                    rel_prop = relationship(target_model, **rel_config)

                    # Add the relationship to the source model
                    setattr(source_model, rel_name, rel_prop)

                    logger.debug(
                        f"Configured relationship: {source_model_name}.{rel_name} "
                        f"-> {target_model_name}"
                    )

                except Exception as rel_err:
                    logger.error(
                        f"Failed to resolve relationship {source_model_name}.{rel_name}: {rel_err}"
                    )
                    logger.debug(traceback.format_exc())

        cls._initialized = True
        logger.info("Comprehensive relationship resolution complete.")

    @classmethod
    def reset(cls) -> None:
        """
        Reset the relationship manager.
        Useful for testing or re-initialization.
        """
        cls._relationship_registry.clear()
        cls._dependency_graph.clear()
        cls._initialization_order.clear()
        cls._initialized = False
        logger.info("RelationshipManager reset complete")


def register_one_to_many(
        source_model: str,
        relationship_name: str,
        target_model: str,
        back_populates: Optional[str] = None,
        cascade: str = "all, delete-orphan",
        lazy: str = "selectin",
        **kwargs
) -> None:
    """
    Convenience function to register a one-to-many relationship.

    Args:
        source_model: Name of the parent model (the "one" side)
        relationship_name: Name of the relationship collection on the parent
        target_model: Name of the child model (the "many" side)
        back_populates: Name of the parent reference on the child model
        cascade: Cascade behavior (default: "all, delete-orphan")
        lazy: Loading strategy (default: "selectin")
        **kwargs: Additional relationship parameters
    """
    definition = RelationshipDefinition(
        source_model=source_model,
        relationship_name=relationship_name,
        target_model=target_model,
        relationship_type=RelationshipType.ONE_TO_MANY,
        back_populates=back_populates,
        cascade=cascade,
        lazy=lazy,
        **kwargs
    )

    RelationshipManager.register_relationship_definition(definition)


def register_many_to_one(
        source_model: str,
        relationship_name: str,
        target_model: str,
        back_populates: Optional[str] = None,
        lazy: str = "selectin",
        **kwargs
) -> None:
    """
    Convenience function to register a many-to-one relationship.

    Args:
        source_model: Name of the child model (the "many" side)
        relationship_name: Name of the parent reference on the child
        target_model: Name of the parent model (the "one" side)
        back_populates: Name of the children collection on the parent
        lazy: Loading strategy (default: "selectin")
        **kwargs: Additional relationship parameters
    """
    definition = RelationshipDefinition(
        source_model=source_model,
        relationship_name=relationship_name,
        target_model=target_model,
        relationship_type=RelationshipType.MANY_TO_ONE,
        back_populates=back_populates,
        cascade=None,  # No cascade deletion from child to parent
        lazy=lazy,
        **kwargs
    )

    RelationshipManager.register_relationship_definition(definition)


def register_many_to_many(
        source_model: str,
        relationship_name: str,
        target_model: str,
        secondary: str,
        back_populates: Optional[str] = None,
        lazy: str = "selectin",
        **kwargs
) -> None:
    """
    Convenience function to register a many-to-many relationship.

    Args:
        source_model: Name of the first model
        relationship_name: Name of the relationship on the first model
        target_model: Name of the second model
        secondary: Name of the association table
        back_populates: Name of the relationship on the second model
        lazy: Loading strategy (default: "selectin")
        **kwargs: Additional relationship parameters
    """
    definition = RelationshipDefinition(
        source_model=source_model,
        relationship_name=relationship_name,
        target_model=target_model,
        relationship_type=RelationshipType.MANY_TO_MANY,
        back_populates=back_populates,
        secondary=secondary,
        lazy=lazy,
        **kwargs
    )

    RelationshipManager.register_relationship_definition(definition)


def register_one_to_one(
        source_model: str,
        relationship_name: str,
        target_model: str,
        back_populates: Optional[str] = None,
        lazy: str = "selectin",
        **kwargs
) -> None:
    """
    Convenience function to register a one-to-one relationship.

    Args:
        source_model: Name of the first model
        relationship_name: Name of the relationship on the first model
        target_model: Name of the second model
        back_populates: Name of the relationship on the second model
        lazy: Loading strategy (default: "selectin")
        **kwargs: Additional relationship parameters
    """
    definition = RelationshipDefinition(
        source_model=source_model,
        relationship_name=relationship_name,
        target_model=target_model,
        relationship_type=RelationshipType.ONE_TO_ONE,
        back_populates=back_populates,
        uselist=False,
        lazy=lazy,
        **kwargs
    )

    RelationshipManager.register_relationship_definition(definition)


def initialize_customer_sales_relationships() -> None:
    """
    Initialize customer and sales related relationships.
    """
    # Customer to Sales (one-to-many)
    register_one_to_many(
        source_model='Customer',
        relationship_name='sales',
        target_model='Sales',
        back_populates='customer'
    )

    register_many_to_one(
        source_model='Sales',
        relationship_name='customer',
        target_model='Customer',
        back_populates='sales'
    )

    # Sales to SalesItem (one-to-many)
    register_one_to_many(
        source_model='Sales',
        relationship_name='items',
        target_model='SalesItem',
        back_populates='sale'
    )

    register_many_to_one(
        source_model='SalesItem',
        relationship_name='sale',
        target_model='Sales',
        back_populates='items'
    )

    # Sales to PickingList (one-to-one)
    register_one_to_one(
        source_model='Sales',
        relationship_name='picking_list',
        target_model='PickingList',
        back_populates='sales'
    )

    register_one_to_one(
        source_model='PickingList',
        relationship_name='sales',
        target_model='Sales',
        back_populates='picking_list'
    )

    # Sales to Project (one-to-one/zero)
    register_one_to_one(
        source_model='Sales',
        relationship_name='project',
        target_model='Project',
        back_populates='sales'
    )

    register_one_to_one(
        source_model='Project',
        relationship_name='sales',
        target_model='Sales',
        back_populates='project'
    )


def initialize_product_relationships() -> None:
    """
    Initialize product and pattern related relationships.
    """
    # SalesItem to Product (many-to-one)
    register_many_to_one(
        source_model='SalesItem',
        relationship_name='product',
        target_model='Product',
        back_populates='sales_items'
    )

    register_one_to_many(
        source_model='Product',
        relationship_name='sales_items',
        target_model='SalesItem',
        back_populates='product'
    )

    # Product to Pattern (many-to-many)
    register_many_to_many(
        source_model='Product',
        relationship_name='patterns',
        target_model='Pattern',
        secondary='ProductPattern',
        back_populates='products'
    )

    register_many_to_many(
        source_model='Pattern',
        relationship_name='products',
        target_model='Product',
        secondary='ProductPattern',
        back_populates='patterns'
    )

    # Product to ProductInventory (one-to-many)
    register_one_to_many(
        source_model='Product',
        relationship_name='inventory',
        target_model='ProductInventory',
        back_populates='product'
    )

    register_many_to_one(
        source_model='ProductInventory',
        relationship_name='product',
        target_model='Product',
        back_populates='inventory'
    )


def initialize_inventory_relationships() -> None:
    """
    Initialize inventory related relationships.
    """
    # Material to MaterialInventory (one-to-many)
    register_one_to_many(
        source_model='Material',
        relationship_name='inventory',
        target_model='MaterialInventory',
        back_populates='material'
    )

    register_many_to_one(
        source_model='MaterialInventory',
        relationship_name='material',
        target_model='Material',
        back_populates='inventory'
    )

    # Leather to LeatherInventory (one-to-many)
    register_one_to_many(
        source_model='Leather',
        relationship_name='inventory',
        target_model='LeatherInventory',
        back_populates='leather'
    )

    register_many_to_one(
        source_model='LeatherInventory',
        relationship_name='leather',
        target_model='Leather',
        back_populates='inventory'
    )

    # Hardware to HardwareInventory (one-to-many)
    register_one_to_many(
        source_model='Hardware',
        relationship_name='inventory',
        target_model='HardwareInventory',
        back_populates='hardware'
    )

    register_many_to_one(
        source_model='HardwareInventory',
        relationship_name='hardware',
        target_model='Hardware',
        back_populates='inventory'
    )

    # Tool to ToolInventory (one-to-many)
    register_one_to_many(
        source_model='Tool',
        relationship_name='inventory',
        target_model='ToolInventory',
        back_populates='tool'
    )

    register_many_to_one(
        source_model='ToolInventory',
        relationship_name='tool',
        target_model='Tool',
        back_populates='inventory'
    )


def initialize_component_relationships() -> None:
    """
    Initialize component related relationships.
    """
    # Pattern to Component (one-to-many)
    register_one_to_many(
        source_model='Pattern',
        relationship_name='components',
        target_model='Component',
        back_populates='pattern'
    )

    register_many_to_one(
        source_model='Component',
        relationship_name='pattern',
        target_model='Pattern',
        back_populates='components'
    )

    # Component to Materials (many-to-many)
    register_many_to_many(
        source_model='Component',
        relationship_name='materials',
        target_model='Material',
        secondary='ComponentMaterial',
        back_populates='components'
    )

    register_many_to_many(
        source_model='Material',
        relationship_name='components',
        target_model='Component',
        secondary='ComponentMaterial',
        back_populates='materials'
    )

    # Component to Leathers (many-to-many)
    register_many_to_many(
        source_model='Component',
        relationship_name='leathers',
        target_model='Leather',
        secondary='ComponentLeather',
        back_populates='components'
    )

    register_many_to_many(
        source_model='Leather',
        relationship_name='components',
        target_model='Component',
        secondary='ComponentLeather',
        back_populates='leathers'
    )

    # Component to Hardware (many-to-many)
    register_many_to_many(
        source_model='Component',
        relationship_name='hardware_items',
        target_model='Hardware',
        secondary='ComponentHardware',
        back_populates='components'
    )

    register_many_to_many(
        source_model='Hardware',
        relationship_name='components',
        target_model='Component',
        secondary='ComponentHardware',
        back_populates='hardware_items'
    )

    # Component to Tools (many-to-many)
    register_many_to_many(
        source_model='Component',
        relationship_name='tools',
        target_model='Tool',
        secondary='ComponentTool',
        back_populates='components'
    )

    register_many_to_many(
        source_model='Tool',
        relationship_name='components',
        target_model='Component',
        secondary='ComponentTool',
        back_populates='tools'
    )


def initialize_project_relationships() -> None:
    """
    Initialize project related relationships.
    """
    # Project to ProjectComponent (one-to-many)
    register_one_to_many(
        source_model='Project',
        relationship_name='components',
        target_model='ProjectComponent',
        back_populates='project'
    )

    register_many_to_one(
        source_model='ProjectComponent',
        relationship_name='project',
        target_model='Project',
        back_populates='components'
    )

    # ProjectComponent to Component (many-to-one)
    register_many_to_one(
        source_model='ProjectComponent',
        relationship_name='component',
        target_model='Component',
        back_populates='project_components'
    )

    register_one_to_many(
        source_model='Component',
        relationship_name='project_components',
        target_model='ProjectComponent',
        back_populates='component'
    )

    # ProjectComponent to PickingListItem (one-to-one)
    register_one_to_one(
        source_model='ProjectComponent',
        relationship_name='picking_list_item',
        target_model='PickingListItem',
        back_populates='project_component'
    )

    register_one_to_one(
        source_model='PickingListItem',
        relationship_name='project_component',
        target_model='ProjectComponent',
        back_populates='picking_list_item'
    )

    # Project to ToolList (one-to-one)
    register_one_to_one(
        source_model='Project',
        relationship_name='tool_list',
        target_model='ToolList',
        back_populates='project'
    )

    register_one_to_one(
        source_model='ToolList',
        relationship_name='project',
        target_model='Project',
        back_populates='tool_list'
    )


def initialize_supplier_relationships() -> None:
    """
    Initialize supplier related relationships.
    """
    # Supplier to Material (one-to-many)
    register_one_to_many(
        source_model='Supplier',
        relationship_name='materials',
        target_model='Material',
        back_populates='supplier'
    )

    register_many_to_one(
        source_model='Material',
        relationship_name='supplier',
        target_model='Supplier',
        back_populates='materials'
    )

    # Supplier to Leather (one-to-many)
    register_one_to_many(
        source_model='Supplier',
        relationship_name='leathers',
        target_model='Leather',
        back_populates='supplier'
    )

    register_many_to_one(
        source_model='Leather',
        relationship_name='supplier',
        target_model='Supplier',
        back_populates='leathers'
    )

    # Supplier to Hardware (one-to-many)
    register_one_to_many(
        source_model='Supplier',
        relationship_name='hardware_items',
        target_model='Hardware',
        back_populates='supplier'
    )

    register_many_to_one(
        source_model='Hardware',
        relationship_name='supplier',
        target_model='Supplier',
        back_populates='hardware_items'
    )

    # Supplier to Tool (one-to-many)
    register_one_to_many(
        source_model='Supplier',
        relationship_name='tools',
        target_model='Tool',
        back_populates='supplier'
    )

    register_many_to_one(
        source_model='Tool',
        relationship_name='supplier',
        target_model='Supplier',
        back_populates='tools'
    )

    # Supplier to Purchase (one-to-many)
    register_one_to_many(
        source_model='Supplier',
        relationship_name='purchases',
        target_model='Purchase',
        back_populates='supplier'
    )

    register_many_to_one(
        source_model='Purchase',
        relationship_name='supplier',
        target_model='Supplier',
        back_populates='purchases'
    )


def initialize_purchase_relationships() -> None:
    """
    Initialize purchase related relationships.
    """
    # Purchase to PurchaseItem (one-to-many)
    register_one_to_many(
        source_model='Purchase',
        relationship_name='items',
        target_model='PurchaseItem',
        back_populates='purchase'
    )

    register_many_to_one(
        source_model='PurchaseItem',
        relationship_name='purchase',
        target_model='Purchase',
        back_populates='items'
    )

    # PurchaseItem to Material (many-to-one, optional)
    register_many_to_one(
        source_model='PurchaseItem',
        relationship_name='material',
        target_model='Material',
        back_populates='purchase_items',
        uselist=False
    )

    register_one_to_many(
        source_model='Material',
        relationship_name='purchase_items',
        target_model='PurchaseItem',
        back_populates='material'
    )

    # PurchaseItem to Leather (many-to-one, optional)
    register_many_to_one(
        source_model='PurchaseItem',
        relationship_name='leather',
        target_model='Leather',
        back_populates='purchase_items',
        uselist=False
    )

    register_one_to_many(
        source_model='Leather',
        relationship_name='purchase_items',
        target_model='PurchaseItem',
        back_populates='leather'
    )

    # PurchaseItem to Hardware (many-to-one, optional)
    register_many_to_one(
        source_model='PurchaseItem',
        relationship_name='hardware',
        target_model='Hardware',
        back_populates='purchase_items',
        uselist=False
    )

    register_one_to_many(
        source_model='Hardware',
        relationship_name='purchase_items',
        target_model='PurchaseItem',
        back_populates='hardware'
    )

    # PurchaseItem to Tool (many-to-one, optional)
    register_many_to_one(
        source_model='PurchaseItem',
        relationship_name='tool',
        target_model='Tool',
        back_populates='purchase_items',
        uselist=False
    )

    register_one_to_many(
        source_model='Tool',
        relationship_name='purchase_items',
        target_model='PurchaseItem',
        back_populates='tool'
    )


def initialize_picking_list_relationships() -> None:
    """
    Initialize picking list related relationships.
    """
    # PickingList to PickingListItem (one-to-many)
    register_one_to_many(
        source_model='PickingList',
        relationship_name='items',
        target_model='PickingListItem',
        back_populates='picking_list'
    )

    register_many_to_one(
        source_model='PickingListItem',
        relationship_name='picking_list',
        target_model='PickingList',
        back_populates='items'
    )

    # PickingListItem to Material (many-to-one, optional)
    register_many_to_one(
        source_model='PickingListItem',
        relationship_name='material',
        target_model='Material',
        back_populates='picking_list_items',
        uselist=False
    )

    register_one_to_many(
        source_model='Material',
        relationship_name='picking_list_items',
        target_model='PickingListItem',
        back_populates='material'
    )

    # PickingListItem to Leather (many-to-one, optional)
    register_many_to_one(
        source_model='PickingListItem',
        relationship_name='leather',
        target_model='Leather',
        back_populates='picking_list_items',
        uselist=False
    )

    register_one_to_many(
        source_model='Leather',
        relationship_name='picking_list_items',
        target_model='PickingListItem',
        back_populates='leather'
    )

    # PickingListItem to Hardware (many-to-one, optional)
    register_many_to_one(
        source_model='PickingListItem',
        relationship_name='hardware',
        target_model='Hardware',
        back_populates='picking_list_items',
        uselist=False
    )

    register_one_to_many(
        source_model='Hardware',
        relationship_name='picking_list_items',
        target_model='PickingListItem',
        back_populates='hardware'
    )


def initialize_tool_list_relationships() -> None:
    """
    Initialize tool list related relationships.
    """
    # ToolList to ToolListItem (one-to-many)
    register_one_to_many(
        source_model='ToolList',
        relationship_name='items',
        target_model='ToolListItem',
        back_populates='tool_list'
    )

    register_many_to_one(
        source_model='ToolListItem',
        relationship_name='tool_list',
        target_model='ToolList',
        back_populates='items'
    )

    # ToolListItem to Tool (many-to-one)
    register_many_to_one(
        source_model='ToolListItem',
        relationship_name='tool',
        target_model='Tool',
        back_populates='tool_list_items'
    )

    register_one_to_many(
        source_model='Tool',
        relationship_name='tool_list_items',
        target_model='ToolListItem',
        back_populates='tool'
    )


