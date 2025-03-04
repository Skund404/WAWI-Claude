# database/relationship_registration.py
"""
Utility module to manage model relationship registration and
resolve circular dependencies in the leatherworking application.
"""

import logging
from utils.circular_import_resolver import register_lazy_import, register_relationship

logger = logging.getLogger(__name__)


def register_all_model_relationships():
    """
    Register all model relationships to properly configure SQLAlchemy mappers.
    This function should be called during application startup.
    """
    logger.info("Registering model relationships...")

    # Register core model relationships

    # Pattern-related relationships
    register_lazy_import('database.models.pattern.Pattern.products',
                         'database.models.product.Product')
    register_lazy_import('database.models.product.Product.pattern',
                         'database.models.pattern.Pattern')

    register_lazy_import('database.models.pattern.Pattern.components',
                         'database.models.components.PatternComponent')
    register_lazy_import('database.models.components.PatternComponent.pattern',
                         'database.models.pattern.Pattern')

    register_lazy_import('database.models.pattern.Pattern.projects',
                         'database.models.project.Project')
    register_lazy_import('database.models.project.Project.pattern',
                         'database.models.pattern.Pattern')

    # Product-related relationships
    register_lazy_import('database.models.product.Product.supplier',
                         'database.models.supplier.Supplier')
    register_lazy_import('database.models.supplier.Supplier.products',
                         'database.models.product.Product')

    register_lazy_import('database.models.product.Product.storage',
                         'database.models.storage.Storage')
    register_lazy_import('database.models.storage.Storage.products',
                         'database.models.product.Product')

    register_lazy_import('database.models.product.Product.order_items',
                         'database.models.order.OrderItem')
    register_lazy_import('database.models.order.OrderItem.product',
                         'database.models.product.Product')

    # Other important relationships
    register_lazy_import('database.models.order.Order.items',
                         'database.models.order.OrderItem')
    register_lazy_import('database.models.order.OrderItem.order',
                         'database.models.order.Order')

    # Transaction relationships
    register_lazy_import('database.models.material.Material.transactions',
                         'database.models.transaction.MaterialTransaction')
    register_lazy_import('database.models.transaction.MaterialTransaction.material',
                         'database.models.material.Material')

    register_lazy_import('database.models.leather.Leather.transactions',
                         'database.models.transaction.LeatherTransaction')
    register_lazy_import('database.models.transaction.LeatherTransaction.leather',
                         'database.models.leather.Leather')

    register_lazy_import('database.models.hardware.Hardware.transactions',
                         'database.models.transaction.HardwareTransaction')
    register_lazy_import('database.models.transaction.HardwareTransaction.hardware',
                         'database.models.hardware.Hardware')

    logger.info("Model relationship registration completed")


def initialize_relationships():
    """
    Initialize all relationships safely with error handling.
    This should be called during application startup.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        register_all_model_relationships()
        logger.info("Model relationships initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize model relationships: {str(e)}")
        return False