# database/repositories/sales_repository.py
"""
Repository for managing Sales entities.

This repository handles database operations for the Sales model,
including creation, retrieval, update, and deletion of sales records.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.models.enums import SaleStatus, PaymentStatus
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError

# Setup logger
logger = logging.getLogger(__name__)


class SalesRepository(BaseRepository[Sales]):
    """Repository for managing Sales entities."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the Sales Repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session, Sales)
        logger.debug("SalesRepository initialized")

    def get_by_customer_id(self, customer_id: int) -> List[Sales]:
        """
        Get all sales for a specific customer.

        Args:
            customer_id: The customer ID to query

        Returns:
            List[Sales]: List of sales for the customer
        """
        try:
            query = select(Sales).filter(
                Sales.customer_id == customer_id
            ).order_by(Sales.created_at.desc())

            sales = query.all()
            logger.debug(f"Retrieved {len(sales)} sales for customer ID {customer_id}")
            return sales
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving sales for customer ID {customer_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_by_status(self, status: SaleStatus) -> List[Sales]:
        """
        Get all sales with a specific status.

        Args:
            status: The sale status to filter by

        Returns:
            List[Sales]: List of sales with the specified status
        """
        try:
            query = select(Sales).filter(
                Sales.status == status
            ).order_by(Sales.created_at.desc())

            sales = query.all()
            logger.debug(f"Retrieved {len(sales)} sales with status {status.name}")
            return sales
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving sales with status {status.name}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_by_payment_status(self, payment_status: PaymentStatus) -> List[Sales]:
        """
        Get all sales with a specific payment status.

        Args:
            payment_status: The payment status to filter by

        Returns:
            List[Sales]: List of sales with the specified payment status
        """
        try:
            query = select(Sales).filter(
                Sales.payment_status == payment_status
            ).order_by(Sales.created_at.desc())

            sales = query.all()
            logger.debug(f"Retrieved {len(sales)} sales with payment status {payment_status.name}")
            return sales
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving sales with payment status {payment_status.name}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def search_sales(self,
                     customer_id: Optional[int] = None,
                     status: Optional[SaleStatus] = None,
                     payment_status: Optional[PaymentStatus] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None,
                     limit: int = 100,
                     offset: int = 0) -> Tuple[List[Sales], int]:
        """
        Search for sales with filtering capabilities.

        Args:
            customer_id: Optional customer ID filter
            status: Optional sale status filter
            payment_status: Optional payment status filter
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of sales to return
            offset: Number of sales to skip for pagination

        Returns:
            Tuple[List[Sales], int]: List of matching sales and total count
        """
        try:
            # Start with base query
            query = select(Sales)
            count_query = select(func.count(Sales.id))

            # Apply filters
            if customer_id is not None:
                query = query.filter(Sales.customer_id == customer_id)
                count_query = count_query.filter(Sales.customer_id == customer_id)

            if status is not None:
                query = query.filter(Sales.status == status)
                count_query = count_query.filter(Sales.status == status)

            if payment_status is not None:
                query = query.filter(Sales.payment_status == payment_status)
                count_query = count_query.filter(Sales.payment_status == payment_status)

            if start_date is not None:
                query = query.filter(Sales.created_at >= start_date)
                count_query = count_query.filter(Sales.created_at >= start_date)

            if end_date is not None:
                query = query.filter(Sales.created_at <= end_date)
                count_query = count_query.filter(Sales.created_at <= end_date)

            # Get total count
            total_count = count_query.scalar()

            # Apply sorting and pagination
            query = query.order_by(Sales.created_at.desc())
            query = query.limit(limit).offset(offset)

            # Execute query
            sales = query.all()
            logger.debug(f"Retrieved {len(sales)} of {total_count} matching sales")

            return sales, total_count
        except SQLAlchemyError as e:
            error_msg = f"Error searching sales: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_with_items(self, sales_id: int) -> Optional[Sales]:
        """
        Get a sale with its items eagerly loaded.

        Args:
            sales_id: The sale ID to retrieve

        Returns:
            Optional[Sales]: The sale with items if found, None otherwise
        """
        try:
            query = select(Sales).filter(
                Sales.id == sales_id
            ).options(
                joinedload(Sales.items).joinedload(SalesItem.product)
            )

            sale = query.first()
            if not sale:
                logger.debug(f"No sale found with ID {sales_id}")
                return None

            logger.debug(f"Retrieved sale ID {sales_id} with {len(sale.items)} items")
            return sale
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving sale ID {sales_id} with items: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def add_item(self, sales_id: int, product_id: int, quantity: int, price: float) -> SalesItem:
        """
        Add an item to a sale.

        Args:
            sales_id: The sale ID
            product_id: The product ID
            quantity: The quantity to add
            price: The price per unit

        Returns:
            SalesItem: The created sales item

        Raises:
            ModelNotFoundError: If the sale doesn't exist
            DatabaseError: For other database errors
        """
        try:
            # Get the sale
            sale = self.get_by_id(sales_id)
            if not sale:
                error_msg = f"No sale found with ID {sales_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)

            # Create the sales item
            item = SalesItem(
                sales_id=sales_id,
                product_id=product_id,
                quantity=quantity,
                price=price
            )

            # Add to sale and database
            sale.add_item(item)
            self.session.add(item)
            self.session.commit()

            logger.debug(
                f"Added item to sale ID {sales_id}: product_id={product_id}, quantity={quantity}, price={price}")
            return item
        except ModelNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error adding item to sale ID {sales_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def remove_item(self, sales_id: int, item_id: int) -> bool:
        """
        Remove an item from a sale.

        Args:
            sales_id: The sale ID
            item_id: The item ID to remove

        Returns:
            bool: True if the item was removed, False otherwise

        Raises:
            ModelNotFoundError: If the sale doesn't exist
            DatabaseError: For other database errors
        """
        try:
            # Get the sale
            sale = self.get_with_items(sales_id)
            if not sale:
                error_msg = f"No sale found with ID {sales_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)

            # Find the item
            item_to_remove = None
            for item in sale.items:
                if item.id == item_id:
                    item_to_remove = item
                    break

            if not item_to_remove:
                logger.debug(f"No item with ID {item_id} found in sale ID {sales_id}")
                return False

            # Remove the item
            sale.remove_item(item_to_remove)
            self.session.delete(item_to_remove)
            self.session.commit()

            logger.debug(f"Removed item ID {item_id} from sale ID {sales_id}")
            return True
        except ModelNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error removing item ID {item_id} from sale ID {sales_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def update_status(self, sales_id: int, status: SaleStatus) -> Sales:
        """
        Update the status of a sale.

        Args:
            sales_id: The sale ID
            status: The new status

        Returns:
            Sales: The updated sale

        Raises:
            ModelNotFoundError: If the sale doesn't exist
            DatabaseError: For other database errors
        """
        try:
            # Get the sale
            sale = self.get_by_id(sales_id)
            if not sale:
                error_msg = f"No sale found with ID {sales_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)

            # Update the status
            sale.status = status
            self.session.commit()

            logger.debug(f"Updated status of sale ID {sales_id} to {status.name}")
            return sale
        except ModelNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error updating status of sale ID {sales_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)