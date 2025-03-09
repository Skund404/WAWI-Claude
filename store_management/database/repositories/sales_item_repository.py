# database/repositories/sales_item_repository.py
"""
Repository for managing SalesItem entities.

This repository handles database operations for the SalesItem model,
including creation, retrieval, update, and deletion of sales item records.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, or_, func, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.sales_item import SalesItem
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError

# Setup logger
logger = logging.getLogger(__name__)


class SalesItemRepository(BaseRepository[SalesItem]):
    """Repository for managing SalesItem entities."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the SalesItem Repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session, SalesItem)
        logger.debug("SalesItemRepository initialized")

    def get_by_sales_id(self, sales_id: int) -> List[SalesItem]:
        """
        Get all items for a specific sale.

        Args:
            sales_id: The sale ID to query

        Returns:
            List[SalesItem]: List of items for the sale
        """
        try:
            query = select(SalesItem).filter(
                SalesItem.sales_id == sales_id
            )

            items = query.all()
            logger.debug(f"Retrieved {len(items)} items for sale ID {sales_id}")
            return items
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving items for sale ID {sales_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_by_product_id(self, product_id: int) -> List[SalesItem]:
        """
        Get all sales items for a specific product.

        Args:
            product_id: The product ID to query

        Returns:
            List[SalesItem]: List of sales items for the product
        """
        try:
            query = select(SalesItem).filter(
                SalesItem.product_id == product_id
            )

            items = query.all()
            logger.debug(f"Retrieved {len(items)} sales items for product ID {product_id}")
            return items
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving sales items for product ID {product_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_with_product(self, item_id: int) -> Optional[SalesItem]:
        """
        Get a sales item with its associated product eagerly loaded.

        Args:
            item_id: The item ID to retrieve

        Returns:
            Optional[SalesItem]: The sales item with product if found, None otherwise
        """
        try:
            query = select(SalesItem).filter(
                SalesItem.id == item_id
            ).options(
                joinedload(SalesItem.product)
            )

            item = query.first()
            if not item:
                logger.debug(f"No sales item found with ID {item_id}")
                return None

            logger.debug(f"Retrieved sales item ID {item_id} with product")
            return item
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving sales item ID {item_id} with product: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def update_quantity(self, item_id: int, quantity: int) -> SalesItem:
        """
        Update the quantity of a sales item.

        Args:
            item_id: The item ID to update
            quantity: The new quantity

        Returns:
            SalesItem: The updated sales item

        Raises:
            ModelNotFoundError: If the item doesn't exist
            ValueError: If the quantity is invalid
            DatabaseError: For other database errors
        """
        try:
            # Validate quantity
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero")

            # Get the item
            item = self.get_by_id(item_id)
            if not item:
                error_msg = f"No sales item found with ID {item_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)

            # Update the quantity
            old_quantity = item.quantity
            item.quantity = quantity

            # If the item is part of a sale, update the sale total
            if item.sale:
                item.sale.calculate_total()

            self.session.commit()

            logger.debug(f"Updated quantity of sales item ID {item_id} from {old_quantity} to {quantity}")
            return item
        except ModelNotFoundError:
            raise
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Validation error updating sales item ID {item_id}: {error_msg}")
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error updating quantity of sales item ID {item_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def update_price(self, item_id: int, price: float) -> SalesItem:
        """
        Update the price of a sales item.

        Args:
            item_id: The item ID to update
            price: The new price

        Returns:
            SalesItem: The updated sales item

        Raises:
            ModelNotFoundError: If the item doesn't exist
            ValueError: If the price is invalid
            DatabaseError: For other database errors
        """
        try:
            # Validate price
            if price < 0:
                raise ValueError("Price cannot be negative")

            # Get the item
            item = self.get_by_id(item_id)
            if not item:
                error_msg = f"No sales item found with ID {item_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)

            # Update the price
            old_price = item.price
            item.price = price

            # If the item is part of a sale, update the sale total
            if item.sale:
                item.sale.calculate_total()

            self.session.commit()

            logger.debug(f"Updated price of sales item ID {item_id} from {old_price} to {price}")
            return item
        except ModelNotFoundError:
            raise
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Validation error updating sales item ID {item_id}: {error_msg}")
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error updating price of sales item ID {item_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)