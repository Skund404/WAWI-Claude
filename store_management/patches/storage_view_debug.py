# Path: patches/storage_view_debug.py
"""
Patch for the StorageView class to add debugging information.
This can help identify why the view is empty.
"""
import logging
from typing import Any

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("storage_view_debug")

# Store the original load_data method
from gui.storage.storage_view import StorageView

original_load_data = StorageView.load_data


def debug_load_data(self) -> None:
    """
    Enhanced load_data method with debugging.
    """
    logger.info("StorageView.load_data() called")

    try:
        # Check if we can get the service
        storage_service = self.get_service(None)  # Fill in the correct interface here
        logger.info(f"Got storage service: {storage_service}")

        # Get the data
        storage_locations = storage_service.get_all_storage_locations()
        logger.info(f"Retrieved {len(storage_locations)} storage locations")

        # Call the original method
        original_load_data(self)

        # Check the treeview
        if hasattr(self, 'tree') and self.tree is not None:
            items = self.tree.get_children()
            logger.info(f"Treeview has {len(items)} items after load_data()")
        else:
            logger.warning("Treeview not found or is None")

    except Exception as e:
        logger.error(f"Error in load_data: {str(e)}", exc_info=True)
        raise


# Patch the method
StorageView.load_data = debug_load_data

logger.info("StorageView.load_data patched with debugging version")