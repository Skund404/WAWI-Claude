# patches.py
"""
Import all patches to fix various issues.
"""

import logging

logger = logging.getLogger(__name__)


def apply_all_patches():
    """Apply all patches to the application."""
    logger.info("Applying patches...")

    # Import the material service patch
    try:
        import services.implementations.material_service_patch
        logger.info("Material service patch applied")
    except ImportError as e:
        logger.error(f"Failed to import material service patch: {str(e)}")

    logger.info("All patches applied")


# Apply patches when imported
apply_all_patches()