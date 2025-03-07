# database/models/relationship_helper.py
"""
Relationship Helper Utilities for SQLAlchemy Models

This module provides utilities to help with common relationship management
issues, particularly to help with circular import resolution and relationship
initialization problems.
"""

import logging
from typing import Any, Dict, Type, Optional, List, Callable, Union, Set, Tuple
from functools import wraps

from sqlalchemy import inspect, MetaData
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm.relationships import RelationshipProperty

# Setup logger
logger = logging.getLogger(__name__)


def safe_relationship(*args, **kwargs):
    """
    A wrapper around SQLAlchemy's relationship function that ensures
    relationships are properly initialized and don't cause issues during
    model bootstrapping.

    This is a drop-in replacement for relationship() that helps avoid
    common issues with relationship initialization and circular dependencies.

    Args:
        *args: Arguments to pass to SQLAlchemy's relationship function
        **kwargs: Keyword arguments to pass to SQLAlchemy's relationship function

    Returns:
        The result of SQLAlchemy's relationship function
    """
    # Add _enable_typechecking=False to prevent parent relationship errors
    kwargs['_enable_typechecking'] = False

    # Set link_to_name=True to help with string target resolution
    if 'link_to_name' not in kwargs:
        kwargs['link_to_name'] = True

    # Set overlaps="_*" to help with backref conflicts
    if 'overlaps' not in kwargs and 'back_populates' in kwargs:
        kwargs['overlaps'] = f"_{kwargs['back_populates']}"

    # Create the relationship with our protective settings
    rel = relationship(*args, **kwargs)

    return rel


def initialize_relationships(cls):
    """
    Decorator for model classes to automatically initialize relationships
    after the class is defined.

    Args:
        cls: The model class to initialize relationships for

    Returns:
        The model class with relationships initialized
    """
    # Store the original __init__ method
    original_init = cls.__init__

    @wraps(original_init)
    def init_wrapper(self, *args, **kwargs):
        # Call the original __init__
        original_init(self, *args, **kwargs)

        # Ensure relationships are initialized
        if hasattr(cls, 'initialize_relationships') and callable(cls.initialize_relationships):
            try:
                cls.initialize_relationships()
            except Exception as e:
                logger.warning(f"Error initializing relationships for {cls.__name__}: {e}")

    # Replace the __init__ method
    cls.__init__ = init_wrapper

    # Register with metadata if available
    if hasattr(cls, '__table__') and hasattr(cls.__table__, 'metadata'):
        _register_model_with_metadata(cls)

    return cls


def _register_model_with_metadata(cls):
    """
    Register a model class with its metadata to ensure proper initialization.

    Args:
        cls: The model class to register
    """
    try:
        # Get the metadata for the class
        metadata = cls.__table__.metadata

        # Add the class to the metadata's info dictionary if not already there
        if not hasattr(metadata, 'info'):
            metadata.info = {}

        if 'models' not in metadata.info:
            metadata.info['models'] = set()

        metadata.info['models'].add(cls)
    except Exception as e:
        logger.warning(f"Error registering model {cls.__name__} with metadata: {e}")


def fix_relationship_conflicts(metadata):
    """
    Fix relationship conflicts in a metadata object.

    This function attempts to resolve common relationship conflicts that can
    occur during model initialization, particularly with circular imports
    and parent-child relationships.

    Args:
        metadata: The SQLAlchemy MetaData object to fix

    Returns:
        The fixed MetaData object
    """
    if not isinstance(metadata, MetaData):
        logger.warning(f"fix_relationship_conflicts requires a MetaData object, got {type(metadata)}")
        return metadata

    try:
        # Process each table in the metadata
        for table in metadata.tables.values():
            # Get the mapped class for this table if it exists
            mapper = None
            try:
                mapper = inspect(table).mapper
            except Exception:
                continue

            if not mapper:
                continue

            # Process each relationship in the mapper
            for relationship_property in mapper.relationships:
                # Ensure the parent attribute is set
                if not hasattr(relationship_property, 'parent') or relationship_property.parent is None:
                    # Set parent to the mapper
                    relationship_property.parent = mapper
    except Exception as e:
        logger.warning(f"Error fixing relationship conflicts: {e}")

    return metadata


def ensure_relationships_initialized(metadata):
    """
    Ensure all relationships in a metadata object are properly initialized.

    Args:
        metadata: The SQLAlchemy MetaData object to process

    Returns:
        The processed MetaData object
    """
    # First fix any conflicts
    metadata = fix_relationship_conflicts(metadata)

    # Check for any models registered with the metadata
    if hasattr(metadata, 'info') and 'models' in metadata.info:
        for cls in metadata.info['models']:
            # Initialize relationships if the method exists
            if hasattr(cls, 'initialize_relationships') and callable(cls.initialize_relationships):
                try:
                    cls.initialize_relationships()
                except Exception as e:
                    logger.warning(f"Error initializing relationships for {cls.__name__}: {e}")

    return metadata


# Alias for compatibility with different naming conventions
safe_rel = safe_relationship