# database/repositories/product_inventory_repository.py
"""
Repository for managing ProductInventory entities.

This repository handles database operations for the ProductInventory model,
including creation, retrieval, update, and deletion of product inventory records.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.product_inventory import ProductInventory
from database.models.enums import InventoryStatus
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError

# Setup logger
logger = logging.getLogger(__name__)


class ProductInventoryRepository(BaseRepository[ProductInventory]):
    """Repository for managing ProductInventory entities."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the ProductInventory Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, ProductInventory)
        logger.debug("ProductInventoryRepository initialized")

    def get_by_product_id(self, product_id: int) -> Optional[ProductInventory]:
        """
        Get inventory record for a specific product.

        Args:
            product_id (int): The product ID to query

        Returns:
            Optional[ProductInventory]: The inventory record if found, None otherwise
        """
        try:
            inventory = self.session.query(ProductInventory).filter(
                ProductInventory.product_id == product_id
            ).first()
            return inventory
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving inventory for product ID {product_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_all_by_status(self, status: InventoryStatus) -> List[ProductInventory]:
        """
        Get all inventory records with a specific status.

        Args:
            status (InventoryStatus): The inventory status to filter by

        Returns:
            List[ProductInventory]: List of inventory records matching the status
        """
        try:
            query = self.session.query(ProductInventory).filter(
                ProductInventory.status == status
            )
            inventories = query.all()
            logger.debug(f"Retrieved {len(inventories)} inventory records with status {status.name}")
            return inventories
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving inventory records by status '{status.name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_low_stock_items(self) -> List[ProductInventory]:
        """
        Get all inventory items that are low in stock or need reordering.

        Returns:
            List[ProductInventory]: List of inventory items that need attention
        """
        try:
            # Query for items with LOW_STOCK status or out of stock
            query = self.session.query(ProductInventory).filter(
                or_(
                    ProductInventory.status == InventoryStatus.LOW_STOCK,
                    ProductInventory.status == InventoryStatus.OUT_OF_STOCK
                )
            )

            # Also query for items that need reordering based on reorder point
            reorder_query = self.session.query(ProductInventory).filter(
                and_(
                    ProductInventory.reorder_point.isnot(None),
                    ProductInventory.quantity <= ProductInventory.reorder_point
                )
            )

            # Combine queries with UNION
            low_stock_items = query.union(reorder_query).all()
            logger.debug(f"Retrieved {len(low_stock_items)} low stock or reorder needed items")
            return low_stock_items
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving low stock items: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def update_quantity(self, product_id: int, quantity_change: int) -> ProductInventory:
        """
        Update the quantity of a product in inventory.

        Args:
            product_id (int): The product ID to update
            quantity_change (int): Amount to add (positive) or remove (negative)

        Returns:
            ProductInventory: The updated inventory record

        Raises:
            ModelNotFoundError: If the product inventory doesn't exist
            DatabaseError: For other database errors
        """
        try:
            # Get the inventory record
            inventory = self.get_by_product_id(product_id)
            if not inventory:
                error_msg = f"No inventory record found for product ID {product_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)

            # Update the quantity
            inventory.update_quantity(quantity_change)

            # Save to database
            self.session.commit()
            logger.debug(f"Updated inventory for product ID {product_id} by {quantity_change} to {inventory.quantity}")
            return inventory
        except ModelNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error updating inventory quantity for product ID {product_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_inventory_with_products(self) -> List[ProductInventory]:
        """
        Get all inventory records with their associated products eagerly loaded.

        Returns:
            List[ProductInventory]: List of inventory records with products loaded
        """
        try:
            query = self.session.query(ProductInventory).options(
                joinedload(ProductInventory.product)
            )
            inventory_records = query.all()
            logger.debug(f"Retrieved {len(inventory_records)} inventory records with products")
            return inventory_records
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving inventory records with products: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def create_or_update(self, product_id: int, **kwargs: Any) -> ProductInventory:
        """
        Create a new inventory record or update an existing one.

        Args:
            product_id (int): The product ID
            **kwargs: Other inventory attributes to set

        Returns:
            ProductInventory: The created or updated inventory record
        """
        try:
            # Check if an inventory record already exists
            inventory = self.get_by_product_id(product_id)

            if inventory:
                # Update existing record
                for key, value in kwargs.items():
                    if hasattr(inventory, key):
                        setattr(inventory, key, value)
                logger.debug(f"Updated existing inventory for product ID {product_id}")
            else:
                # Create new record
                kwargs['product_id'] = product_id
                inventory = ProductInventory(**kwargs)
                self.session.add(inventory)
                logger.debug(f"Created new inventory record for product ID {product_id}")

            self.session.commit()
            return inventory
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error creating/updating inventory for product ID {product_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)