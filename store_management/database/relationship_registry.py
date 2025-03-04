# database/relationship_registry.py
"""
Centralized relationship registration for SQLAlchemy models.

This module ensures proper relationship configuration and helps
resolve circular import issues.
"""

import logging
from utils.circular_import_resolver import register_relationship, register_lazy_import

logger = logging.getLogger(__name__)


def register_all_relationships():
    """
    Register all model relationships to resolve circular import issues.

    This function should be called during application startup.
    """
    try:
        # Pattern relationships
        register_lazy_import('database.models.pattern.Pattern', 'database.models.pattern')
        register_lazy_import('database.models.project.Project', 'database.models.project')
        register_relationship(
            'database.models.pattern.Pattern',
            'projects',
            'database.models.project.Project'
        )

        # Project relationships
        register_relationship(
            'database.models.project.Project',
            'pattern',
            'database.models.pattern.Pattern'
        )

        # Add more relationship registrations as needed
        register_lazy_import('database.models.components.ProjectComponent', 'database.models.components')
        register_relationship(
            'database.models.pattern.Pattern',
            'components',
            'database.models.components.PatternComponent'
        )

        logger.info("Model relationships registered successfully")

    except Exception as e:
        logger.error(f"Error registering model relationships: {e}", exc_info=True)
        raise


def initialize_model_relationships():
    """
    Wrapper function to initialize all model relationships.

    Call this during application startup.
    """
    try:
        register_all_relationships()
    except Exception as e:
        logger.critical(f"Failed to initialize model relationships: {e}", exc_info=True)
        raise