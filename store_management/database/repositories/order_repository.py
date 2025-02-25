# database/repositories/order_repository.py
"""
Repository for managing order-related database operations.

Provides specialized methods for retrieving, creating, and managing
orders with advanced querying capabilities.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta  # Added timedelta here
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from utils.circular_import_resolver import CircularImportResolver

# Dynamically import models
Order = CircularImportResolver.get_module('models.order').Order
OrderItem = CircularImportResolver.get_module('models.order').OrderItem
OrderStatus = CircularImportResolver.get_module('database.models.enums').OrderStatus
Supplier = CircularImportResolver.get_module('models.supplier').Supplier

# Configure logging
logger = logging.getLogger(__name__)


class OrderRepository:
    """
    Repository for managing order-related database operations.

    Provides methods to interact with orders, including
    retrieval, creation, and advanced querying.
    """

    def __init__(self, session):
        """
        Initialize the OrderRepository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

        # ... [Previous methods remain the same] ...

        except SQLAlchemyError as e:
        logger.error(f'Error searching orders: {e}')
        raise


def get_orders_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[
    str, Any]:
    """
    Generate a summary of orders within an optional date range.

    Args:
        start_date (Optional[datetime], optional): Start of date range
        end_date (Optional[datetime], optional): End of date range

    Returns:
        Dict[str, Any]: Order summary statistics

    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Base query
        query = self.session.query(Order)

        # Apply date range filter if provided
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)

        # Calculate summary metrics
        total_orders = query.count()
        total_amount = query.with_entities(func.sum(Order.total_amount)).scalar() or 0

        # Order status breakdown
        status_breakdown = (
            query.with_entities(
                Order.status,
                func.count(Order.id).label('count')
            )
            .group_by(Order.status)
            .all()
        )

        # Top customers
        top_customers = (
            query.with_entities(
                Order.customer_name,
                func.sum(Order.total_amount).label('total_spent')
            )
            .group_by(Order.customer_name)
            .order_by(func.sum(Order.total_amount).desc())
            .limit(5)
            .all()
        )

        return {
            'total_orders': total_orders,
            'total_amount': float(total_amount),
            'status_breakdown': {
                status.name: count for status, count in status_breakdown
            },
            'top_customers': [
                {'customer_name': name, 'total_spent': float(spent)}
                for name, spent in top_customers
            ]
        }
    except SQLAlchemyError as e:
        logger.error(f'Error generating order summary: {e}')
        raise


def get_revenue_by_period(self,
                          period: str = 'monthly',
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Calculate revenue for a specified period.

    Args:
        period (str, optional): Period for grouping. Defaults to 'monthly'.
        start_date (Optional[datetime], optional): Start of date range
        end_date (Optional[datetime], optional): End of date range

    Returns:
        List[Dict[str, Any]]: Revenue breakdown by specified period

    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Base query
        query = self.session.query(Order)

        # Apply date range filter if provided
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)

        # Group by period
        if period == 'monthly':
            revenue_by_period = (
                query.with_entities(
                    func.date_trunc('month', Order.order_date).label('period'),
                    func.sum(Order.total_amount).label('total_revenue')
                )
                .group_by(func.date_trunc('month', Order.order_date))
                .order_by('period')
                .all()
            )
        elif period == 'quarterly':
            revenue_by_period = (
                query.with_entities(
                    func.date_trunc('quarter', Order.order_date).label('period'),
                    func.sum(Order.total_amount).label('total_revenue')
                )
                .group_by(func.date_trunc('quarter', Order.order_date))
                .order_by('period')
                .all()
            )
        elif period == 'yearly':
            revenue_by_period = (
                query.with_entities(
                    func.date_trunc('year', Order.order_date).label('period'),
                    func.sum(Order.total_amount).label('total_revenue')
                )
                .group_by(func.date_trunc('year', Order.order_date))
                .order_by('period')
                .all()
            )
        else:
            raise ValueError(f"Unsupported period: {period}")

        return [
            {
                'period': period.strftime('%Y-%m-%d'),
                'total_revenue': float(revenue)
            }
            for period, revenue in revenue_by_period
        ]
    except SQLAlchemyError as e:
        logger.error(f'Error calculating revenue by period: {e}')
        raise


def cleanup_old_orders(self, retention_days: int = 730) -> int:
    """
    Remove orders older than the specified retention period.

    Args:
        retention_days (int, optional): Number of days to retain orders. Defaults to 730 (2 years).

    Returns:
        int: Number of orders deleted

    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Calculate the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Find and delete old orders
        old_orders = self.session.query(Order).filter(Order.order_date < cutoff_date).all()

        # Count orders to be deleted
        order_count = len(old_orders)

        # Delete old orders
        for order in old_orders:
            self.session.delete(order)

        # Commit the transaction
        self.session.commit()

        logger.info(f'Cleaned up {order_count} old orders')
        return order_count
    except SQLAlchemyError as e:
        self.session.rollback()
        logger.error(f'Error cleaning up old orders: {e}')
        raise