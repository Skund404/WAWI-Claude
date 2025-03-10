# test_di.py
"""
Sample application to test the DI system.

This script demonstrates how to use the new DI system to:
1. Initialize the container
2. Verify service registrations
3. Resolve services
4. Use the @inject decorator
"""

import logging
from di import initialize, verify_container, resolve, inject, Container, set_container

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Example service consumer using injection
@inject
def process_material(material_id: int, material_service: 'IMaterialService'):
    """
    Process a material using injected material service.

    Args:
        material_id: ID of the material to process
        material_service: Injected material service

    Returns:
        Result of processing
    """
    logger.info(f"Processing material {material_id}")
    material = material_service.get_material(material_id)

    if not material:
        logger.warning(f"Material {material_id} not found")
        return None

    logger.info(f"Found material: {material}")
    return f"Processed {material.get('name', 'Unknown')}"


# Example service consumer using direct resolution
def analyze_inventory():
    """
    Analyze inventory using directly resolved inventory service.

    Returns:
        Analysis result
    """
    logger.info("Analyzing inventory")

    # Directly resolve the service
    inventory_service = resolve('IInventoryService')

    # Use the service
    low_stock = inventory_service.get_low_stock_items()

    logger.info(f"Found {len(low_stock)} low stock items")
    return {
        'low_stock_count': len(low_stock),
        'items': low_stock
    }


# Test with mocked services
def test_with_mocks():
    """Test DI with manually registered mocks."""
    logger.info("Testing with mocks")

    # Create a test container
    container = Container()

    # Create mock services
    class MockMaterialService:
        def get_material(self, material_id):
            logger.info(f"[MOCK] Getting material {material_id}")
            return {'id': material_id, 'name': f'Test Material {material_id}'}

    class MockInventoryService:
        def get_low_stock_items(self):
            logger.info("[MOCK] Getting low stock items")
            return [
                {'id': 1, 'name': 'Low Stock Item 1'},
                {'id': 2, 'name': 'Low Stock Item 2'}
            ]

    # Register mocks
    container.register_instance('IMaterialService', MockMaterialService())
    container.register_instance('IInventoryService', MockInventoryService())

    # Set as global container
    set_container(container)

    # Test functions that use DI
    material_result = process_material(123)
    inventory_result = analyze_inventory()

    logger.info(f"Material processing result: {material_result}")
    logger.info(f"Inventory analysis result: {inventory_result}")


def main():
    """Main entry point for the sample application."""
    logger.info("Starting DI sample application")

    # Initialize the DI container with real services
    logger.info("Initializing DI container")
    container = initialize()

    # Verify the container
    logger.info("Verifying DI container")
    is_valid = verify_container()
    logger.info(f"Container verification: {'Passed' if is_valid else 'Failed'}")

    if not is_valid:
        logger.error("Container verification failed, testing with mocks instead")
        test_with_mocks()
        return

    # Try resolving and using some services
    try:
        logger.info("Testing service resolution")

        # Example 1: Function with injected dependency
        material_result = process_material(1)
        logger.info(f"Material processing result: {material_result}")

        # Example 2: Direct resolution
        inventory_result = analyze_inventory()
        logger.info(f"Inventory analysis result: {inventory_result}")

        logger.info("All tests completed successfully")

    except Exception as e:
        logger.error(f"Error testing services: {str(e)}")
        logger.info("Testing with mocks instead")
        test_with_mocks()


if __name__ == "__main__":
    main()