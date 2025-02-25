# File: run.py
# !/usr/bin/env python3

import sys
import os
import logging


def add_project_to_path():
    """
    Add the project root directory to Python path to ensure proper imports.
    """
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, project_root)


def main():
    """
    Main entry point for running the leatherworking store management application.
    """
    add_project_to_path()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    session = None
    session_factory = None

    try:
        # Import after path is set
        from database.initialize import initialize_database
        from di.setup import setup_dependency_injection
        from database.models.types import MaterialType, MaterialQualityGrade
        from database.models.material import Material
        from database.models.product import Product
        from database.models.order import Order, OrderItem, OrderStatus
        from services.interfaces import MaterialService
        from di.core import DependencyContainer

        # Initialize database
        engine, session_factory = initialize_database()

        # Set up dependency injection and get session
        session = setup_dependency_injection()

        # Retrieve the material service
        material_service = DependencyContainer.resolve(MaterialService)

        # Create a sample material
        sample_material = material_service.create_material(
            name="Full Grain Leather",
            material_type=MaterialType.LEATHER,
            quality_grade=MaterialQualityGrade.PREMIUM,
            current_stock=50.5,
            unit_price=25.00,
            is_active=True
        )

        logger.info(f"Sample material created: {sample_material}")

        # Demonstrate stock update
        updated_material = material_service.update_stock(
            material_id=sample_material.id,
            quantity_change=10.0,
            transaction_type='PURCHASE'
        )

        logger.info(f"Updated material stock: {updated_material}")

        # Create a sample product
        session.add(Product(
            name="Leather Wallet",
            description="Handcrafted leather wallet",
            price=79.99,
            stock_quantity=20,
            category=MaterialType.LEATHER,
            weight=0.2
        ))

        # Create a sample order
        order = Order(
            customer_name="John Doe",
            total_amount=159.98,
            status=OrderStatus.PENDING
        )
        session.add(order)
        session.flush()  # Ensure order gets an ID

        # Create order items
        order_item = OrderItem(
            order_id=order.id,
            product_id=1,  # Assumes the first product
            quantity=2,
            unit_price=79.99
        )
        session.add(order_item)

        # Commit changes
        session.commit()

        logger.info("Sample product and order created successfully")

    except Exception as e:
        logger.error(f"Error in leatherworking store application: {e}")
        if session:
            session.rollback()
        sys.exit(1)
    finally:
        # Ensure session is closed
        if session_factory:
            session_factory.remove()


if __name__ == "__main__":
    main()