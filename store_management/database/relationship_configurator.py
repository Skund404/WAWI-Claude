# database/relationship_configurator.py
"""
Centralized configuration utility for managing SQLAlchemy model relationships.

This module helps resolve circular import issues and ensures proper
relationship configuration during application startup.
"""

import logging
import importlib
import sqlalchemy
from sqlalchemy.orm import configure_mappers

logger = logging.getLogger(__name__)


def import_all_models():
    """
    Dynamically import all models to ensure they are registered.

    This helps resolve circular import issues and ensures all models
    are loaded before mapper configuration.
    """
    model_modules = [
        'database.models.base',
        'database.models.pattern',
        'database.models.project',
        'database.models.components',
        'database.models.material',
        'database.models.product',
        'database.models.order',
        'database.models.leather',
        'database.models.hardware',
        'database.models.storage',
        'database.models.supplier',
        # Add other model modules as needed
    ]

    imported_models = []
    for module_path in model_modules:
        try:
            module = importlib.import_module(module_path)

            # Attempt to find and import all model classes
            for name, obj in module.__dict__.items():
                if isinstance(obj, type) and hasattr(obj, '__tablename__'):
                    imported_models.append(obj)
                    logger.info(f"Imported model: {obj.__name__}")

        except Exception as e:
            logger.error(f"Error importing module {module_path}: {e}")

    return imported_models


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

        # Import all models first
        models = import_all_models()

        if not models:
            logger.error("No models found for configuration")
            return False

        # Attempt to configure mappers
        try:
            configure_mappers()
            logger.info("Successfully configured all mappers")
        except sqlalchemy.exc.InvalidRequestError as config_error:
            logger.error(f"Mapper configuration error: {config_error}")

            # Detailed error diagnostics
            try:
                # Try to identify specific configuration issues
                from database.models.base import Base
                Base.debug_registered_models()
            except Exception as diag_error:
                logger.error(f"Error during diagnostic logging: {diag_error}")

            return False

        # Additional validation
        for model in models:
            try:
                # Verify mapper exists for each model
                mapper = sqlalchemy.inspect(model)
                logger.debug(f"Validated mapper for {model.__name__}")
            except Exception as mapper_error:
                logger.error(f"Mapper validation failed for {model.__name__}: {mapper_error}")

        logger.info("Model relationship configuration completed successfully")
        return True

    except Exception as e:
        logger.critical(f"Catastrophic error in model relationship configuration: {e}", exc_info=True)
        return False


def initialize_database_models():
    """
    Comprehensive initialization of database models.

    This method should be called during application startup to ensure
    all models are properly imported, configured, and ready for use.

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        logger.info("Initializing database models")

        # Import all models
        models = import_all_models()
        if not models:
            logger.error("No models found during initialization")
            return False

        # Configure relationships
        relationship_success = configure_model_relationships()

        if not relationship_success:
            logger.error("Failed to configure model relationships")
            return False

        logger.info("Database models initialized successfully")
        return True

    except Exception as e:
        logger.critical(f"Fatal error during database model initialization: {e}", exc_info=True)
        return False