# gui/leatherworking/leather_inventory_patch.py
"""
Patch for leather_inventory.py to fix Enum handling.
"""

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def patch_leather_inventory():
    """Patch LeatherInventoryView to fix Enum handling."""
    try:
        # Import the module to patch
        from gui.leatherworking.leather_inventory import LeatherInventoryView
        from database.models.enums import MaterialType

        # Store the original method
        original_load_data = LeatherInventoryView.load_data

        # Define the patched method
        def patched_load_data(self):
            """Patched method that correctly passes Enum values."""
            try:
                # Instead of passing MaterialType.LEATHER, pass just the value 'LEATHER'
                leathers = self.material_service.get_materials(material_type='LEATHER')

                if leathers:
                    # Continue with original implementation
                    # Populate your UI with the leather data
                    self.populate_inventory(leathers)
                else:
                    logger.warning("No leather materials found in database")
                    # Handle empty result case
            except Exception as e:
                logger.error(f"Error loading leather inventory data: {str(e)}")

        # Replace the original method with our patched version
        LeatherInventoryView.load_data = patched_load_data
        logger.info("Successfully patched LeatherInventoryView.load_data method")
        return True

    except Exception as e:
        logger.error(f"Error patching LeatherInventoryView: {str(e)}")
        return False


# Apply the patch when imported
success = patch_leather_inventory()