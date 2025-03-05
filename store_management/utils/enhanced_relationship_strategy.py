"""
utils/enhanced_relationship_strategy.py - Enhanced relationship configuration utilities for SQLAlchemy models.

This module provides sophisticated tools to handle complex relationship configurations with proper
circular import resolution and flexible loading strategies.
"""

import logging
from typing import Any, Dict, Optional, Type, Union, List, Callable

from sqlalchemy.orm import relationship, RelationshipProperty

from utils.circular_import_resolver import lazy_import, register_lazy_import

logger = logging.getLogger(__name__)


class RelationshipLoadingStrategy:
    """Enumeration of available relationship loading strategies."""

    # Loading strategies
    LAZY = 'select'
    EAGER = 'joined'
    SUBQUERY = 'subquery'
    SELECTIN = 'selectin'
    IMMEDIATE = 'immediate'
    NOLOAD = 'noload'
    RAISE = 'raise'


class RelationshipConfiguration:
    """Handles sophisticated configuration of SQLAlchemy relationships with enhanced features."""

    _registered_models = {}
    _pending_relationships = []

    @classmethod
    def register_model(cls, model_name: str, model_class: Type) -> None:
        """Register a model class for future relationship resolution.

        Args:
            model_name: String name of the model
            model_class: The actual model class
        """
        cls._registered_models[model_name] = model_class
        logger.debug(f"Registered model {model_name} for relationship resolution")

        # Resolve any pending relationships for this model
        cls._resolve_pending_relationships(model_name)

    @classmethod
    def _resolve_pending_relationships(cls, model_name: str) -> None:
        """Resolve any pending relationships for a newly registered model.

        Args:
            model_name: Name of the model that was just registered
        """
        remaining_pending = []

        for pending in cls._pending_relationships:
            if pending.get('target_model_name') == model_name:
                # This pending relationship can now be resolved
                try:
                    source_class = cls._registered_models.get(pending.get('source_model_name'))
                    target_class = cls._registered_models.get(model_name)

                    if source_class and target_class:
                        # Create the relationship
                        rel_prop = relationship(
                            target_class,
                            **pending.get('kwargs', {})
                        )

                        # Set the relationship on the source class
                        setattr(source_class, pending.get('relationship_name'), rel_prop)

                        logger.debug(
                            f"Resolved pending relationship: {pending.get('source_model_name')}."
                            f"{pending.get('relationship_name')} -> {model_name}"
                        )
                    else:
                        # Keep in pending if either class is not yet available
                        remaining_pending.append(pending)
                except Exception as e:
                    logger.error(f"Error resolving pending relationship: {e}")
                    remaining_pending.append(pending)
            else:
                remaining_pending.append(pending)

        # Update the pending relationships list
        cls._pending_relationships = remaining_pending

    @classmethod
    def get_model_class(cls, model_name: str) -> Optional[Type]:
        """Get a registered model class by name.

        Args:
            model_name: Name of the model to retrieve

        Returns:
            The model class or None if not found
        """
        return cls._registered_models.get(model_name)

    @classmethod
    def configure_relationship(
            cls,
            source_model: str,
            target_model: str,
            relationship_name: str,
            back_populates: Optional[str] = None,
            loading_strategy: str = RelationshipLoadingStrategy.LAZY,
            **kwargs
    ) -> RelationshipProperty:
        """Configure a SQLAlchemy relationship with circular import resolution.

        Args:
            source_model: Source model class path
            target_model: Target model class path
            relationship_name: Name of the relationship
            back_populates: Optional back_populates parameter
            loading_strategy: Loading strategy to use
            **kwargs: Additional arguments to pass to relationship()

        Returns:
            Configured SQLAlchemy relationship
        """
        try:
            # Extract model names from paths
            source_model_name = source_model.split('.')[-1]
            target_model_name = target_model.split('.')[-1]

            # Register the source model for lazy import
            register_lazy_import(source_model, source_model_name)

            # Register the target model for lazy import
            register_lazy_import(target_model, target_model_name)

            # Set back_populates if provided
            if back_populates:
                kwargs['back_populates'] = back_populates

            # Set loading strategy
            kwargs['lazy'] = loading_strategy

            # Attempt to get the target model class
            target_class = None

            # First try the registered models cache
            if target_model_name in cls._registered_models:
                target_class = cls._registered_models[target_model_name]
                logger.debug(f"Found {target_model_name} in registered models cache")
            else:
                # Try lazy import
                try:
                    target_class = lazy_import(target_model)
                    logger.debug(f"Lazy imported {target_model}")
                except ImportError as e:
                    logger.debug(f"Could not lazy import {target_model}: {e}")

            # If we got the target class, create the relationship
            if target_class:
                logger.debug(f"Creating relationship to {target_model_name} with args: {kwargs}")
                return relationship(target_class, **kwargs)

            # Otherwise, add to pending relationships for later resolution
            logger.debug(f"Adding pending relationship: {source_model_name}.{relationship_name} -> {target_model_name}")
            cls._pending_relationships.append({
                'source_model_name': source_model_name,
                'source_model': source_model,
                'target_model_name': target_model_name,
                'target_model': target_model,
                'relationship_name': relationship_name,
                'kwargs': kwargs
            })

            # Return a relationship with the string name that SQLAlchemy will resolve later
            # This is a fallback for Declarative Base initialization
            logger.debug(f"Using string-based relationship for now: {target_model_name}")
            return relationship(target_model_name, **kwargs)

        except Exception as e:
            logger.error(f"Error configuring relationship {source_model}.{relationship_name} -> {target_model}: {e}")

            # Fallback to string-based relationship as a last resort
            if isinstance(target_model, str) and "." in target_model:
                target_model_name = target_model.split(".")[-1]
            else:
                target_model_name = target_model

            logger.warning(f"Falling back to string-based relationship: {target_model_name}")
            if back_populates:
                kwargs['back_populates'] = back_populates

            kwargs['lazy'] = loading_strategy
            return relationship(target_model_name, **kwargs)

    @classmethod
    def initialize_relationships(cls) -> bool:
        """Initialize all pending relationships.

        This method should be called during application startup
        after all models have been registered.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Process any remaining pending relationships
            if cls._pending_relationships:
                logger.warning(f"There are {len(cls._pending_relationships)} unresolved relationships")
                for pending in cls._pending_relationships:
                    logger.debug(
                        f"Unresolved: {pending.get('source_model_name')}."
                        f"{pending.get('relationship_name')} -> {pending.get('target_model_name')}"
                    )

            return True
        except Exception as e:
            logger.error(f"Error initializing relationships: {e}")
            return False