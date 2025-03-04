# database/models/shopping_list_patch.py
"""
Patch for ShoppingListItem class to fix the hardware relationship.
Compatible with SQLAlchemy 2.0.
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def apply_patch():
    """
    Apply the patch to fix the ShoppingListItem hardware relationship.

    This is a temporary measure to allow the application to start up
    and create the database schema.
    """
    logger.info("Applying ShoppingListItem patch...")

    try:
        # Add parent directory to sys.path if needed
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            logger.info(f"Added {parent_dir} to sys.path")

        # Import the ShoppingListItem class
        from database.models.shopping_list import ShoppingListItem

        # Check if the hardware relationship exists
        if hasattr(ShoppingListItem, 'hardware'):
            logger.info("Setting ShoppingListItem.hardware to None to disable problematic relationship")
            # Set the hardware relationship to None to disable it
            ShoppingListItem.hardware = None
            return True
        else:
            logger.warning("ShoppingListItem.hardware relationship not found")
            return False
    except Exception as e:
        logger.error(f"Error applying patch: {str(e)}")
        return False


# Apply the patch when the module is imported
success = apply_patch()