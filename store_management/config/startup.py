# config/startup.py
"""
Centralized application startup configuration and initialization.
"""

import logging
from typing import Optional, Callable

# Import diagnostic utilities
from database.relationship_diagnostics import (
    diagnose_relationship_issues,
    RelationshipDiagnostics
)

# Import patch loader before other database modules
from database.patch_loader import load_and_apply_patches

# Import database initialization modules
from database.relationship_configurator import initialize_database_models
from database.models.base import Base

# Configure logging
logger = logging.getLogger(__name__)


class ApplicationStartup:
    """
    Centralized application startup and initialization manager.
    """

    @classmethod
    def initialize(
            cls,
            debug_mode: bool = False,
            additional_init_callback: Optional[Callable[[], None]] = None
    ) -> bool:
        """
        Comprehensive application initialization method.

        Args:
            debug_mode (bool): Enable additional diagnostic logging
            additional_init_callback (Optional[Callable]): Optional additional
                initialization function to run during startup

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            logger.info("Starting application initialization...")

            # Step 0: Apply model patches to fix relationship issues
            logger.info("Applying model patches...")
            patch_success = load_and_apply_patches()
            if not patch_success and debug_mode:
                logger.warning("Some model patches failed to apply. Continuing with initialization...")

            # Step 1: Initialize database models
            logger.info("Initializing database models...")
            models_initialized = initialize_database_models()
            if not models_initialized:
                logger.error("Failed to initialize database models")
                return False

            # Step 2: Run relationship diagnostics in debug mode
            if debug_mode:
                logger.info("Running relationship diagnostics...")
                try:
                    diagnose_relationship_issues()

                    # Run model relationship diagnostic from our new module
                    from database.model_relationship_patch import find_all_relationship_definitions
                    find_all_relationship_definitions()
                except Exception as diag_error:
                    logger.warning(f"Diagnostic scan encountered an error: {diag_error}")

            # Step 3: Run any additional initialization callback
            if additional_init_callback:
                logger.info("Running additional initialization callback...")
                try:
                    additional_init_callback()
                except Exception as callback_error:
                    logger.error(f"Additional initialization callback failed: {callback_error}")
                    return False

            logger.info("Application initialization completed successfully")
            return True

        except Exception as e:
            logger.critical(f"Catastrophic error during application startup: {e}", exc_info=True)
            return False

    @classmethod
    def diagnose_database(cls):
        """
        Perform comprehensive database diagnostics.

        Useful for troubleshooting database and model configuration issues.
        """
        try:
            logger.info("Starting comprehensive database diagnostics...")

            # Clear existing mappers to ensure clean diagnostic environment
            RelationshipDiagnostics.clear_relationship_caches()

            # Generate full diagnostic report
            report = RelationshipDiagnostics.generate_diagnostic_report()

            # Log the full report
            logger.info("Database Diagnostic Report:\n" + report)

            # Identify and log any orphaned relationships
            orphaned = RelationshipDiagnostics.find_orphaned_relationships()
            if orphaned:
                logger.warning("Orphaned Relationships Detected:")
                for model, relationships in orphaned.items():
                    logger.warning(f"  {model}: {relationships}")

            # Run enhanced diagnostics from our patch module
            try:
                from database.model_relationship_patch import find_all_relationship_definitions
                logger.info("Running enhanced relationship diagnostics...")
                find_all_relationship_definitions()
            except ImportError:
                logger.warning("Enhanced diagnostics module not available")

        except Exception as e:
            logger.error(f"Error during database diagnostics: {e}", exc_info=True)

    @classmethod
    def diagnose_supplier_hardware_issue(cls):
        """
        Specific diagnostic method for troubleshooting the Supplier-Hardware relationship issue.
        """
        try:
            logger.info("Diagnosing Supplier-Hardware relationship issue...")

            # Try to import the models
            try:
                from database.models.supplier import Supplier
                from database.models.hardware import Hardware

                # Check for the problematic relationship
                if hasattr(Supplier, 'hardware'):
                    logger.warning("Problematic 'hardware' relationship found in Supplier model")
                    logger.warning("This relationship lacks a proper foreign key definition")
                else:
                    logger.info("No problematic 'hardware' relationship found in Supplier model")

                # Check Hardware model for supplier relationship
                if hasattr(Hardware, 'supplier'):
                    logger.info("Hardware model has 'supplier' relationship")
                    # Check for foreign key
                    if hasattr(Hardware, 'supplier_id'):
                        logger.info("Hardware model has 'supplier_id' foreign key - good!")
                    else:
                        logger.warning("Hardware model missing 'supplier_id' foreign key")
                else:
                    logger.warning("Hardware model missing 'supplier' relationship")

            except ImportError as e:
                logger.error(f"Could not import models: {e}")

        except Exception as e:
            logger.error(f"Error during Supplier-Hardware diagnostics: {e}", exc_info=True)


def configure_logging(log_level: str = 'INFO'):
    """
    Configure application-wide logging.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            # Uncomment and configure for file logging if needed
            # logging.FileHandler('application.log')
        ]
    )


def run_startup_diagnostics():
    """
    Convenience function to run startup diagnostics.
    Can be called during development or troubleshooting.
    """
    # Configure logging for detailed output
    configure_logging('DEBUG')

    # Run full initialization with debug mode
    success = ApplicationStartup.initialize(debug_mode=True)

    # Additional database diagnostics
    ApplicationStartup.diagnose_database()

    # Run specific diagnostics for the Supplier-Hardware issue
    ApplicationStartup.diagnose_supplier_hardware_issue()

    return success


# Example usage in main application startup
if __name__ == "__main__":
    # Configure logging
    configure_logging()

    # Initialize application
    ApplicationStartup.initialize(debug_mode=True)