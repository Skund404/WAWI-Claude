# path: database/__init__.py
"""
Database package for the store management application.

This package provides database models, connection management,
and CRUD operations for the application's data.
"""

import logging
from typing import Optional, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import circular import resolver to handle import cycles
try:
    from utils.circular_import_resolver import CircularImportResolver
except ImportError:
    # Create a minimal implementation if the real one can't be imported
    class CircularImportResolver:
        @classmethod
        def register_pending_import(cls, module_name: str, exception: Exception) -> None:
            logger.error(f"Failed to import {module_name}: {exception}")

        @classmethod
        def get_module(cls, module_name: str) -> Optional[object]:
            return None

# Try to import models in a way that handles circular imports
try:
    # Import enums first as they don't depend on other modules
    from database.models.enums import MaterialType, LeatherType, OrderStatus, ProjectStatus

    # Then try to import other model modules
    from database.models.base import Base, BaseModel
    from database.models.material import Material
    from database.models.hardware import Hardware
    from database.models.components import Component, PatternComponent, ProjectComponent
    from database.models.pattern import Pattern  # Import Pattern instead of Recipe
except ImportError as e:
    # Register the import failure to be resolved later
    CircularImportResolver.register_pending_import(__name__, e)

# Import database initialization function
try:
    from database.initialize import initialize_database
except ImportError as e:
    logger.error(f"Failed to import database initialization: {e}")


    # Define a placeholder for the initialization function
    def initialize_database(drop_existing: bool = False) -> None:
        """
        Placeholder for the database initialization function.

        This function is meant to be replaced by the actual implementation
        from database.initialize.

        Args:
            drop_existing: Whether to drop existing tables
        """
        logger.error("Database initialization not available.")