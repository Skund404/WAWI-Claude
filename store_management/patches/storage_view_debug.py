from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

"""
Patch for the StorageView class to add debugging information.
This can help identify why the view is empty.
"""
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("storage_view_debug")
original_load_data = StorageView.load_data


@inject(MaterialService)
        def debug_load_data(self) -> None:
    """
    Enhanced load_data method with debugging.
    """
    logger.info("StorageView.load_data() called")
    try:
        storage_service = self.get_service(None)
        logger.info(f"Got storage service: {storage_service}")
        storage_locations = storage_service.get_all_storage_locations()
        logger.info(f"Retrieved {len(storage_locations)} storage locations")
        original_load_data(self)
        if hasattr(self, "tree") and self.tree is not None:
            items = self.tree.get_children()
            logger.info(f"Treeview has {len(items)} items after load_data()")
        else:
            logger.warning("Treeview not found or is None")
    except Exception as e:
        logger.error(f"Error in load_data: {str(e)}", exc_info=True)
        raise


StorageView.load_data = debug_load_data
logger.info("StorageView.load_data patched with debugging version")
