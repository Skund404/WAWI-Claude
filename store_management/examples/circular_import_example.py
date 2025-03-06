# examples/circular_import_example.py
"""
Example usage of the circular_import_resolver module.

This file demonstrates how to use the circular import resolver to handle
circular dependencies between SQLAlchemy models in a leatherworking application.
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import directly from utils package
from utils import (
    register_lazy_import,
    resolve_lazy_import,
    lazy_import,
    register_relationship,
    resolve_relationship,
    resolve_lazy_relationships,
    lazy_relationship
)

from sqlalchemy import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, Session

# Create a base model
Base = declarative_base()


# Example: Define models with circular dependencies

class Order(Base):
    """Example Order model with a relationship to OrderItem."""
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    customer_name = Column(String(100), nullable=False)

    # The items relationship will be added later


class OrderItem(Base):
    """Example OrderItem model with a relationship to Order and Product."""
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    quantity = Column(Integer, default=1)

    # The sale relationship will be added later
    # The product relationship will be added later


class Product(Base):
    """Example Product model with a relationship to OrderItem."""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    # The order_items relationship will be added later


def main():
    """Demonstrate circular import resolution."""
    print("Registering lazy imports...")
    # Register lazy imports
    register_lazy_import('Order', __name__, 'Order')
    register_lazy_import('OrderItem', __name__, 'OrderItem')
    register_lazy_import('Product', __name__, 'Product')

    print("Registering relationships...")
    # Register relationships using lazy_relationship
    register_relationship(
        Sale,
        'items',
        lazy_relationship('OrderItem', back_populates='sale', lazy='selectin', cascade='all, delete-orphan')
    )

    register_relationship(
        SaleItem,
        'sale',
        lazy_relationship('Order', back_populates='items', lazy='selectin')
    )

    register_relationship(
        SaleItem,
        'product',
        lazy_relationship('Product', back_populates='order_items', lazy='selectin')
    )

    register_relationship(
        Product,
        'order_items',
        lazy_relationship('OrderItem', back_populates='product', lazy='selectin')
    )

    # Resolve all lazy relationships
    print("Resolving lazy relationships...")
    resolve_lazy_relationships()

    # Verify relationships were set correctly
    print(f"Order.items relationship: {getattr(Sale, 'items', None)}")
    print(f"OrderItem.sale relationship: {getattr(SaleItem, 'sale', None)}")
    print(f"OrderItem.product relationship: {getattr(SaleItem, 'product', None)}")
    print(f"Product.order_items relationship: {getattr(Product, 'order_items', None)}")

    # Create a simple in-memory database
    print("Setting up in-memory database...")
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    # Test the relationships with some data
    print("Testing relationships with data...")
    with Session(engine) as session:
        # Create a product
        product = Product(name="Leather Wallet")
        session.add(product)

        # Create an sale
        order = Sale(customer_name="John Doe")
        session.add(order)

        # Create an sale item linking the sale and product
        order_item = SaleItem(quantity=2)
        order_item.sale = order
        order_item.product = product
        session.add(order_item)

        # Commit the changes
        session.commit()

        # Retrieve and verify
        retrieved_order = session.query(Sale).first()
        print(f"Retrieved sale: {retrieved_order.customer_name}")
        print(f"Order has {len(retrieved_order.items)} items")
        print(f"First item is for product: {retrieved_order.items[0].product.name}")

        retrieved_product = session.query(Product).first()
        print(f"Retrieved product: {retrieved_product.name}")
        print(f"Product appears in {len(retrieved_product.order_items)} sale items")

    print("Example completed successfully!")


if __name__ == '__main__':
    main()