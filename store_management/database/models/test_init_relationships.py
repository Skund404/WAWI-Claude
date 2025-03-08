# store_management/database/models/test_init_relationships.py
import os
import sys

# Dynamically add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

import pytest
import logging
import time
import traceback

# Absolute imports
from store_management.utils.circular_import_resolver import register_lazy_import, resolve_lazy_import
from store_management.database.models.init_relationships import (
    initialize_database_relationships,
    register_critical_model_lazy_imports,
    validate_relationship_configuration,
    RelationshipManager
)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_critical_model_lazy_imports():
    """
    Test registering critical model lazy imports
    """
    try:
        register_critical_model_lazy_imports()
        assert True, "Critical model lazy imports registered successfully"
    except Exception as e:
        logger.error(f"Lazy import registration failed: {e}")
        pytest.fail(f"Failed to register critical model lazy imports: {e}")


def test_relationship_configuration_validation():
    """
    Test relationship configuration validation
    """
    try:
        result = validate_relationship_configuration()
        assert result, "Relationship configuration validation failed"
    except Exception as e:
        logger.error(f"Relationship configuration validation failed: {e}")
        pytest.fail(f"Relationship configuration validation error: {e}")


def test_relationship_initialization():
    """
    Comprehensive test for relationship initialization
    """
    try:
        # Reset RelationshipManager to ensure clean state
        RelationshipManager.reset()

        # Start timing
        start_time = time.time()

        # Register critical lazy imports
        register_critical_model_lazy_imports()

        # Validate relationship configuration
        assert validate_relationship_configuration(), "Relationship configuration validation failed"

        # Perform full relationship initialization
        initialize_database_relationships()

        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time

        # Verify key relationship registrations
        registered_relationships = len(RelationshipManager._relationships)

        # Assertions
        assert registered_relationships > 0, "No relationships were registered"
        assert duration < 10, f"Initialization took too long: {duration} seconds"

        # Log successful initialization
        logger.info(f"Relationship initialization test completed successfully")
        logger.info(f"Total initialization time: {duration:.4f} seconds")
        logger.info(f"Total relationships registered: {registered_relationships}")

    except Exception as e:
        logger.error(f"Relationship initialization test failed: {e}")
        logger.error(traceback.format_exc())
        pytest.fail(f"Relationship initialization failed: {e}")


def test_relationship_manager_reset():
    """
    Test RelationshipManager reset functionality
    """
    # Reset RelationshipManager
    RelationshipManager.reset()

    # Check that everything was cleared
    assert len(RelationshipManager._relationship_registry) == 0, "Registry not cleared"
    assert len(RelationshipManager._dependency_graph) == 0, "Dependency graph not cleared"
    assert not RelationshipManager._initialized, "Initialization flag not reset"