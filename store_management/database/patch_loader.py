# database/patch_loader.py
"""
Module to load and apply model patches during application startup.
Centralizes all patching operations to fix model or relationship issues.
"""

import logging
import importlib
import sys

logger = logging.getLogger(__name__)


def load_and_apply_patches():
    """
    Load and apply all model patches in the correct sale.
    This should be called early in the application startup process.

    Returns:
        bool: True if all patches were successfully applied, False otherwise
    """
    logger.info("Loading and applying model patches...")
    success = True

    # List of patch modules to load and functions to call
    patches = [
        # (module_name, function_name)
        ("database.models.supplier_patch", "apply_supplier_patch"),
        ("database.model_relationship_patch", "patch_problematic_relationships"),
    ]

    # Apply each patch
    for module_name, function_name in patches:
        try:
            logger.info(f"Loading patch module: {module_name}")

            # Import the module
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                module = importlib.import_module(module_name)

            # Get the patch function
            if hasattr(module, function_name):
                patch_function = getattr(module, function_name)

                # Apply the patch
                logger.info(f"Applying patch: {function_name}")
                result = patch_function()

                if result:
                    logger.info(f"Successfully applied patch: {function_name}")
                else:
                    logger.warning(f"Patch {function_name} returned False")
                    success = False
            else:
                logger.error(f"Could not find patch function {function_name} in module {module_name}")
                success = False
        except ImportError as e:
            logger.error(f"Could not import patch module {module_name}: {e}")
            success = False
        except Exception as e:
            logger.error(f"Error applying patch {function_name}: {e}")
            success = False

    if success:
        logger.info("All model patches applied successfully")
    else:
        logger.warning("Some model patches failed to apply")

    return success


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Apply patches
    load_and_apply_patches()