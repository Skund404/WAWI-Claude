"""
Mock Implementations Package

This package contains mock implementations of service interfaces for testing purposes.
These mocks should NOT be used in production.
"""

from di.tests.mock_implementations.base_service import MockBaseService
from di.tests.mock_implementations.pattern_service import MockPatternService
from di.tests.mock_implementations.tool_list_service import MockToolListService
from di.tests.mock_implementations.material_service import MockMaterialService
from di.tests.mock_implementations.inventory_service import MockInventoryService

__all__ = [
    'MockBaseService',
    'MockPatternService',
    'MockToolListService',
    'MockMaterialService',
    'MockInventoryService',
]

# Mock services map for easy access
MOCK_SERVICES = {
    'IPatternService': MockPatternService,
    'IToolListService': MockToolListService,
    'IMaterialService': MockMaterialService,
    'IInventoryService': MockInventoryService,
    'ICustomerService': MockBaseService,
    'IProjectService': MockBaseService,
    'ISalesService': MockBaseService,
    'ISupplierService': MockBaseService,
}