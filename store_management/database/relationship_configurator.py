# database/relationship_configurator.py
"""
Module for configuring SQLAlchemy model relationships.
Provides functionality to initialize and configure all database models.
"""

import importlib
import logging
import sqlalchemy
from sqlalchemy.orm import configure_mappers

from database.models.base import Base
from database.relationship_registration import initialize_relationships

# Set up logger
logger = logging.getLogger(__name__)


def import_all_models():
    """
    Dynamically import all models to ensure they are registered.

    This helps resolve circular import issues and ensures all models
    are loaded before mapper configuration.
    """
    try:
        # Import base models first
        logger.info("Importing model: Base")
        from database.models.base import Base, BaseModel
        logger.info("Imported model: BaseModel")

        # Import core domain models
        logger.info("Importing model: Pattern")
        from database.models.pattern import Pattern
        logger.info("Imported model: Pattern")

        logger.info("Importing model: Project")
        from database.models.project import Project
        logger.info("Imported model: Project")

        logger.info("Importing model: Component")
        from database.models.components import Component, ProjectComponent, PatternComponent
        logger.info("Imported model: Component")
        logger.info("Imported model: ProjectComponent")
        logger.info("Imported model: PatternComponent")

        logger.info("Importing model: Material")
        from database.models.material import Material
        logger.info("Imported model: Material")

        logger.info("Importing model: Product")
        from database.models.product import Product
        logger.info("Imported model: Product")

        logger.info("Importing model: Order")
        from database.models.order import Order, OrderItem
        logger.info("Imported model: Order")
        logger.info("Imported model: OrderItem")

        logger.info("Importing model: Leather")
        from database.models.leather import Leather
        logger.info("Imported model: Leather")

        logger.info("Importing model: Hardware")
        from database.models.hardware import Hardware
        logger.info("Imported model: Hardware")

        # Import supporting domain models
        logger.info("Importing model: Storage")
        from database.models.storage import Storage
        logger.info("Imported model: Storage")

        logger.info("Importing model: Supplier")
        from database.models.supplier import Supplier
        logger.info("Imported model: Supplier")

        # Import transaction models last to avoid circular imports
        logger.info("Importing model: Transaction")
        from database.models.transaction import (
            BaseTransaction,
            MaterialTransaction,
            LeatherTransaction,
            HardwareTransaction
        )
        logger.info("Imported transaction models")

        return True

    except ImportError as e:
        logger.error(f"Failed to import model: {str(e)}")
        return False


def configure_model_relationships():
    """
    Configure all model relationships with comprehensive error handling.

    This method attempts to resolve and configure all SQLAlchemy model
    relationships, providing detailed logging and error diagnostics.

    Returns:
        bool: True if configuration was successful, False otherwise
    """
    try:
        logger.info("Starting comprehensive model relationship configuration")

        # First import all models
        if not import_all_models():
            logger.error("Failed to import all models")
            return False

        # Register relationships using the new relationship registration module
        if not initialize_relationships():
            logger.error("Failed to register model relationships")
            return False

        # Configure mappers
        logger.info("Configuring SQLAlchemy mappers")
        configure_mappers()
        logger.info("Mappers configured successfully")

        return True

    except sqlalchemy.exc.InvalidRequestError as e:
        logger.error(f"Mapper configuration error: {str(e)}")

        # Try to provide more diagnostic information
        try:
            # Get information about the Base class
            table_names = [table.name for table in Base.metadata.sorted_tables]
            logger.error(f"Configured tables: {', '.join(table_names)}")

            # Try to get more information about the mapper that failed
            if hasattr(e, 'args') and len(e.args) > 0:
                error_message = e.args[0]
                logger.error(f"Error details: {error_message}")
        except Exception as diagnostic_error:
            logger.error(f"Failed to collect additional diagnostic information: {diagnostic_error}")

        return False
    except Exception as e:
        logger.error(f"Unexpected error during model configuration: {str(e)}")
        return False


def initialize_database_models():
    """
    Comprehensive initialization of database models.

    This method should be called during application startup to ensure
    all models are properly imported, configured, and ready for use.

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    logger.info("Initializing database models")

    try:
        # Apply model patches first before importing models
        logger.info("Applying model patches...")
        try:
            from database.patch_loader import load_and_apply_patches
            load_and_apply_patches()
        except ImportError as e:
            logger.warning(f"Could not import patch loader: {e}")
        except Exception as e:
            logger.warning(f"Error applying model patches: {e}")

        # Import all models
        if not import_all_models():
            logger.error("Failed to import models")
            return False

        # Configure relationships
        if not configure_model_relationships():
            logger.error("Failed to configure model relationships")
            return False

        logger.info("Database models initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database models: {str(e)}")
        return False