"""
Basic test script for the DI system.

This script demonstrates and tests the DI system functionality,
including container initialization, service resolution, and injection.
"""
import logging
from typing import Any
from di import initialize, verify_container, resolve, inject

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Function with direct resolution
def get_patterns_manual():
    """Function that uses direct resolution."""
    pattern_service = resolve('IPatternService')
    return pattern_service.get_all_patterns()

# Class with constructor injection
@inject
class PatternClient:
    def __init__(self, pattern_service=None):
        self.pattern_service = pattern_service or resolve('IPatternService')

    def get_patterns(self):
        return self.pattern_service.get_all_patterns()

def main():
    """Test the DI system."""
    logger.info("Testing DI system initialization...")

    # Initialize the container
    try:
        container = initialize()
        logger.info("Container initialized successfully")

        # Verify the container
        valid = verify_container()
        logger.info(f"Container verification result: {'Success' if valid else 'Failed'}")

        # Test with direct resolution
        try:
            patterns = get_patterns_manual()
            logger.info(f"Got patterns using direct resolution: {patterns}")
        except Exception as e:
            logger.error(f"Error using direct resolution: {str(e)}")

        # Test with constructor injection
        try:
            client = PatternClient()
            patterns = client.get_patterns()
            logger.info(f"Got patterns using constructor injection: {patterns}")
        except Exception as e:
            logger.error(f"Error using constructor injection: {str(e)}")

        # Test all critical services
        test_all_services()

    except Exception as e:
        logger.error(f"Error during DI initialization: {str(e)}")

def test_all_services():
    """Test all critical services to ensure they're working."""

    # List of services to test
    services = [
        'IPatternService',
        'IToolListService',
        'IMaterialService',
        'IInventoryService',
        'ICustomerService',
        'IProjectService',
        'ISalesService',
        'ISupplierService'
    ]

    # Test each service
    for service_name in services:
        try:
            service = resolve(service_name)
            logger.info(f"Testing {service_name}...")

            # Test common methods
            if hasattr(service, 'get_all'):
                items = service.get_all()
                logger.info(f"  ✓ get_all() returned {len(items)} items")

            if hasattr(service, 'get_by_id'):
                item = service.get_by_id(1)
                logger.info(f"  ✓ get_by_id(1) returned an item")

            # Test service-specific methods
            if service_name == 'IPatternService':
                patterns = service.get_all_patterns()
                logger.info(f"  ✓ get_all_patterns() returned {len(patterns)} patterns")

            if service_name == 'IMaterialService':
                materials = service.get_material(1)
                logger.info(f"  ✓ get_material(1) returned a material")

            if service_name == 'IInventoryService':
                low_stock = service.get_low_stock_items()
                logger.info(f"  ✓ get_low_stock_items() returned {len(low_stock)} items")

            logger.info(f"✓ {service_name} tests passed")

        except Exception as e:
            logger.error(f"✗ {service_name} tests failed: {str(e)}")

if __name__ == "__main__":
    main()