# database/repositories/order_repository.py

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from database.models.enums import OrderStatus
from database.models.order import Order, OrderItem
from database.models.product import Product
from database.repositories.base_repository import BaseRepository
from database.models.base import ModelValidationError
from database.exceptions import DatabaseError, ModelNotFoundError, RepositoryError
from utils.logger import get_logger

logger = get_logger(__name__)


class OrderRepository(BaseRepository[Order]):
    """
    Repository for Order model with enhanced querying capabilities.

    Provides data access methods for Order entities, including filtering,
    pagination, sorting, and complex aggregations.
    """

    def __init__(self, session: Session):
        """
        Initialize the Order Repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session, Order)
        self.logger = get_logger(__name__)
        self.logger.debug("Initializing OrderRepository")

    def get_all_with_pagination(
            self,
            filters: List[Any] = None,
            page: int = 1,
            page_size: int = 50,
            sort_by: str = "order_date",
            sort_desc: bool = True
    ) -> Tuple[List[Order], int]:
        """
        Get all orders with pagination and optional filtering.

        Args:
            filters: List of SQLAlchemy filter conditions
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order

        Returns:
            Tuple containing:
                - List of Order objects
                - Total count of orders matching the filters
        """
        try:
            self.logger.debug(
                f"Getting orders with pagination: page={page}, page_size={page_size}, sort_by={sort_by}, sort_desc={sort_desc}")

            # Create base query
            query = select(Order)

            # Apply filters if provided
            if filters:
                for filter_condition in filters:
                    query = query.where(filter_condition)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = self.session.execute(count_query).scalar() or 0

            # Apply sorting
            if hasattr(Order, sort_by):
                sort_field = getattr(Order, sort_by)
                if sort_desc:
                    sort_field = sort_field.desc()
                query = query.order_by(sort_field)

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # Add eager loading for related entities
            query = query.options(joinedload(Order.items))

            # Execute query
            orders = list(self.session.execute(query).scalars().all())

            self.logger.debug(f"Retrieved {len(orders)} orders out of {total_count} total")
            return orders, total_count

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_all_with_pagination: {str(e)}")
            raise RepositoryError(f"Failed to get orders with pagination: {str(e)}")

    def find_by(
            self,
            filters: List[Any],
            include_related: List[str] = None
    ) -> List[Order]:
        """
        Find orders matching the given filters.

        Args:
            filters: List of SQLAlchemy filter conditions
            include_related: List of relationship names to eager load

        Returns:
            List of matching Order objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Finding orders by filters: {filters}")

            # Create base query
            query = select(Order)

            # Apply filters
            for filter_condition in filters:
                query = query.where(filter_condition)

            # Add eager loading for related entities if specified
            if include_related:
                for relation in include_related:
                    if hasattr(Order, relation):
                        query = query.options(joinedload(getattr(Order, relation)))

            # Execute query
            orders = list(self.session.execute(query).scalars().all())

            self.logger.debug(f"Found {len(orders)} orders matching filters")
            return orders

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in find_by: {str(e)}")
            raise RepositoryError(f"Failed to find orders by filters: {str(e)}")

    def find_one_by(
            self,
            filters: List[Any],
            include_related: List[str] = None
    ) -> Optional[Order]:
        """
        Find a single order matching the given filters.

        Args:
            filters: List of SQLAlchemy filter conditions
            include_related: List of relationship names to eager load

        Returns:
            Matching Order object or None if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Finding one order by filters: {filters}")

            # Create base query
            query = select(Order)

            # Apply filters
            for filter_condition in filters:
                query = query.where(filter_condition)

            # Add eager loading for related entities if specified
            if include_related:
                for relation in include_related:
                    if hasattr(Order, relation):
                        query = query.options(joinedload(getattr(Order, relation)))

            # Execute query
            order = self.session.execute(query).scalars().first()

            if order:
                self.logger.debug(f"Found order {order.id} matching filters")
            else:
                self.logger.debug("No order found matching filters")

            return order

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in find_one_by: {str(e)}")
            raise RepositoryError(f"Failed to find order by filters: {str(e)}")

    def get_by_id(
            self,
            order_id: int,
            include_related: List[str] = None,
            include_deleted: bool = False
    ) -> Optional[Order]:
        """
        Get an order by ID with optional eager loading of relationships.

        Args:
            order_id: Order ID
            include_related: List of relationship names to eager load
            include_deleted: Whether to include soft-deleted orders

        Returns:
            Order object or None if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(
                f"Getting order by ID: {order_id}, include_related={include_related}, include_deleted={include_deleted}")

            # Create base query
            query = select(Order).where(Order.id == order_id)

            # Filter out deleted orders if not explicitly included
            if not include_deleted:
                query = query.where(Order.is_deleted == False)

            # Add eager loading for related entities if specified
            if include_related:
                for relation in include_related:
                    if hasattr(Order, relation):
                        query = query.options(joinedload(getattr(Order, relation)))

            # Execute query
            order = self.session.execute(query).scalars().first()

            if order:
                self.logger.debug(f"Found order {order.id}")
            else:
                self.logger.debug(f"No order found with ID {order_id}")

            return order

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_by_id: {str(e)}")
            raise RepositoryError(f"Failed to get order by ID: {str(e)}")

    def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """
        Get an order by order number.

        Args:
            order_number: Order number to look up

        Returns:
            Order object or None if not found

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Getting order by number: {order_number}")

            # Create and execute query
            query = select(Order).where(
                and_(
                    Order.order_number == order_number,
                    Order.is_deleted == False
                )
            ).options(
                joinedload(Order.items),
                joinedload(Order.supplier)
            )

            order = self.session.execute(query).scalars().first()

            if order:
                self.logger.debug(f"Found order {order.id} with number {order_number}")
            else:
                self.logger.debug(f"No order found with number {order_number}")

            return order

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_by_order_number: {str(e)}")
            raise RepositoryError(f"Failed to get order by number: {str(e)}")

    def get_by_customer(self, customer_name: str) -> List[Order]:
        """
        Get orders by customer name.

        Args:
            customer_name: Customer name (full or partial)

        Returns:
            List of matching Order objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Getting orders by customer name: {customer_name}")

            # Create and execute query
            query = select(Order).where(
                and_(
                    Order.customer_name.ilike(f"%{customer_name}%"),
                    Order.is_deleted == False
                )
            ).options(joinedload(Order.items))

            orders = list(self.session.execute(query).scalars().all())

            self.logger.debug(f"Found {len(orders)} orders for customer '{customer_name}'")
            return orders

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_by_customer: {str(e)}")
            raise RepositoryError(f"Failed to get orders by customer: {str(e)}")

    def get_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Get orders by status.

        Args:
            status: Order status to filter by

        Returns:
            List of matching Order objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Getting orders by status: {status}")

            # Create and execute query
            query = select(Order).where(
                and_(
                    Order.status == status,
                    Order.is_deleted == False
                )
            ).options(joinedload(Order.items))

            orders = list(self.session.execute(query).scalars().all())

            self.logger.debug(f"Found {len(orders)} orders with status {status}")
            return orders

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_by_status: {str(e)}")
            raise RepositoryError(f"Failed to get orders by status: {str(e)}")

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """
        Get orders within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of matching Order objects

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Getting orders by date range: {start_date} to {end_date}")

            # Create and execute query
            query = select(Order).where(
                and_(
                    Order.order_date >= start_date,
                    Order.order_date <= end_date,
                    Order.is_deleted == False
                )
            ).options(joinedload(Order.items))

            orders = list(self.session.execute(query).scalars().all())

            self.logger.debug(f"Found {len(orders)} orders in date range")
            return orders

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_by_date_range: {str(e)}")
            raise RepositoryError(f"Failed to get orders by date range: {str(e)}")

    def get_top_products(
            self,
            start_date: datetime,
            end_date: datetime,
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get top-selling products for a period.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of products to return

        Returns:
            List of dictionaries with product info and quantity sold

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Getting top products for period: {start_date} to {end_date}, limit={limit}")

            # Create query to get top products by quantity sold
            query = (
                select(
                    Product.id,
                    Product.name,
                    Product.sku,
                    func.sum(OrderItem.quantity).label("quantity_sold"),
                    func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_revenue")
                )
                .join(OrderItem, OrderItem.product_id == Product.id)
                .join(Order, and_(
                    OrderItem.order_id == Order.id,
                    Order.order_date >= start_date,
                    Order.order_date <= end_date,
                    Order.is_deleted == False
                ))
                .group_by(Product.id, Product.name, Product.sku)
                .order_by(func.sum(OrderItem.quantity).desc())
                .limit(limit)
            )

            # Execute query
            result = self.session.execute(query).all()

            # Format results
            top_products = []
            for row in result:
                top_products.append({
                    "id": row.id,
                    "name": row.name,
                    "sku": row.sku,
                    "quantity_sold": float(row.quantity_sold),
                    "total_revenue": float(row.total_revenue)
                })

            self.logger.debug(f"Retrieved {len(top_products)} top products")
            return top_products

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_top_products: {str(e)}")
            raise RepositoryError(f"Failed to get top products: {str(e)}")

    def get_revenue_by_period(
            self,
            start_date: datetime,
            end_date: datetime,
            group_by: str = "month"
    ) -> List[Dict[str, Any]]:
        """
        Get revenue aggregated by time period.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            group_by: Time period to group by ('day', 'week', 'month')

        Returns:
            List of dictionaries with period and revenue

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Getting revenue by period: {start_date} to {end_date}, group_by={group_by}")

            # Define the date grouping function based on the requested period
            if group_by == "day":
                date_group = func.date(Order.order_date)
                date_format = "%Y-%m-%d"
            elif group_by == "week":
                date_group = func.date_trunc("week", Order.order_date)
                date_format = "%Y-%m-%d"
            else:  # month is default
                date_group = func.date_trunc("month", Order.order_date)
                date_format = "%Y-%m"

            # Create query to get revenue by period
            query = (
                select(
                    date_group.label("period"),
                    func.sum(Order.total).label("revenue")
                )
                .where(
                    and_(
                        Order.order_date >= start_date,
                        Order.order_date <= end_date,
                        Order.is_deleted == False
                    )
                )
                .group_by(date_group)
                .order_by(date_group)
            )

            # Execute query
            result = self.session.execute(query).all()

            # Format results
            revenue_by_period = []
            for row in result:
                revenue_by_period.append({
                    "period": row.period.strftime(date_format),
                    "revenue": float(row.revenue)
                })

            self.logger.debug(f"Retrieved revenue for {len(revenue_by_period)} periods")
            return revenue_by_period

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in get_revenue_by_period: {str(e)}")
            raise RepositoryError(f"Failed to get revenue by period: {str(e)}")

    def add(self, order: Order) -> Order:
        """
        Add a new order to the database.

        Args:
            order: Order object to add

        Returns:
            Added Order object

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Adding new order: {order}")

            # Add order to session
            self.session.add(order)

            # Return the order
            return order

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in add: {str(e)}")
            raise RepositoryError(f"Failed to add order: {str(e)}")

    def update(self, order: Order) -> Order:
        """
        Update an existing order.

        Args:
            order: Order object to update

        Returns:
            Updated Order object

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Updating order: {order}")

            # Add order to session (for merge)
            self.session.add(order)

            # Return the order
            return order

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in update: {str(e)}")
            raise RepositoryError(f"Failed to update order: {str(e)}")

    def delete(self, order: Order) -> None:
        """
        Delete an order from the database.

        This is a permanent delete. For soft delete, use the order.soft_delete() method.

        Args:
            order: Order object to delete

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug(f"Deleting order: {order}")

            # Delete order from session
            self.session.delete(order)

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in delete: {str(e)}")
            raise RepositoryError(f"Failed to delete order: {str(e)}")

    def commit(self) -> None:
        """
        Commit the current transaction.

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug("Committing transaction")

            # Commit the transaction
            self.session.commit()

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in commit: {str(e)}")
            self.rollback()
            raise RepositoryError(f"Failed to commit transaction: {str(e)}")

    def rollback(self) -> None:
        """
        Roll back the current transaction.

        Raises:
            RepositoryError: If a database error occurs
        """
        try:
            self.logger.debug("Rolling back transaction")

            # Roll back the transaction
            self.session.rollback()

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in rollback: {str(e)}")
            raise RepositoryError(f"Failed to rollback transaction: {str(e)}")