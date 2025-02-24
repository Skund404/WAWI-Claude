# database/initialize.py

import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base
from database.models.order import Order, OrderItem
from database.models.pattern import Project, ProjectComponent
from database.models.shopping_list import ShoppingList, ShoppingListItem
from database.models.enums import OrderStatus, PaymentStatus
from database.config import get_database_config

logger = logging.getLogger(__name__)


def create_tables(engine) -> None:
    """
    Create all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def add_sample_data(session: Session) -> None:
    """
    Add sample data to the database for testing.

    Args:
        session: SQLAlchemy session
    """
    try:
        # Sample Order
        order = Order(
            order_number="ORD-2024-001",
            customer_name="John Doe",
            status=OrderStatus.NEW,
            payment_status=PaymentStatus.PENDING,
            notes="Sample order"
        )
        order_item = OrderItem(
            product_name="Leather Wallet",
            quantity=1,
            unit_price=49.99,
            total_price=49.99
        )
        order.items.append(order_item)
        session.add(order)

        # Sample Project
        pattern = Project(
            name="Basic Leather Wallet",
            description="Simple bifold wallet design",
            total_cost=20.00,
            preparation_time=120
        )
        recipe_item = ProjectComponent(
            material_name="Vegetable Tanned Leather",
            quantity=2.5,
            unit="sqft"
        )
        pattern.items.append(recipe_item)
        session.add(pattern)

        # Sample Shopping List
        shopping_list = ShoppingList(
            name="Weekly Supplies",
            description="Regular materials restock",
            status="active"
        )
        shopping_item = ShoppingListItem(
            item_name="Thread",
            quantity=5,
            unit="spools",
            priority="high"
        )
        shopping_list.items.append(shopping_item)
        session.add(shopping_list)

        session.commit()
        logger.info("Sample data added successfully")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error adding sample data: {str(e)}")
        raise


def initialize_database(drop_existing: bool = False) -> None:
    """
    Initialize the database with tables and optional sample data.

    Args:
        drop_existing: If True, drop existing tables before creation
    """
    config = get_database_config()
    engine = create_engine(config['database_url'])
    Session = sessionmaker(bind=engine)

    try:
        if drop_existing:
            logger.info("Dropping existing tables...")
            Base.metadata.drop_all(engine)

        create_tables(engine)

        with Session() as session:
            # Check if database is empty
            order_count = session.query(Order).count()
            if order_count == 0:
                logger.info("Adding sample data...")
                add_sample_data(session)

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_database(drop_existing=True)