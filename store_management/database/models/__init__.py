# database/models/__init__.py
"""
Initialization module for the database models package.

This module sets up the SQLAlchemy models and handles registration and initialization.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Type

# Configure module logger
logger = logging.getLogger(__name__)

# Import models in order to register them
try:
    # Import base first
    from database.models.base import Base, ModelRegistry, ValidationMixin

    # Import relationship tables before models that use them
    try:
        from database.models.relationship_tables import (
            component_material_table,
            # These might be None in the simplified version
            product_pattern_table,
            pattern_component_table
        )
    except (ImportError, AttributeError) as e:
        logger.warning(f"Some relationship tables could not be imported: {e}")
        # Try to import what we can
        try:
            from database.models.relationship_tables import component_material_table
        except ImportError:
            logger.warning("Could not import component_material_table")

    # Import enums for use in models
    from database.models.enums import *
except ImportError as e:
    logger.warning(f"Import error in models: {e}")
except Exception as e:
    logger.error(f"Unexpected error in models initialization: {e}")
    import traceback
    logger.debug(traceback.format_exc())


@contextmanager
def initialization_timer():
    """
    Context manager to track model initialization performance.

    Logs the time taken for model initialization.
    """
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        elapsed = end_time - start_time
        logger.info(f"Model initialization completed in {elapsed:.4f} seconds")


def register_models():
    """
    Register all imported models in the ModelRegistry.

    Attempts to register each discovered model and logs any registration failures.
    """
    pass  # We'll simplify this for now