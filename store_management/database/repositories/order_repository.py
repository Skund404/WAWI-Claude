# Path: database/repositories/order_repository.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from database.interfaces.base_repository import BaseRepository
from database.models.order import Order, OrderItem, OrderStatus
from database.models.supplier import Supplier
from utils.error_handler import DatabaseError, ValidationError


class OrderRepository(BaseRepository):
    """
    Repository for managing order-related database operations.

    Provides specialized methods for retrieving, creating, and managing
    orders with advanced querying capabilities.
    """

    def __init__(self, session: Session):
        """
        Initialize the OrderRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Order)

    def get_with_items(self, order_id: int) -> Optional[Order]:
        """
        Retrieve an order with its associated items in a single query.

        Args:
            order_id (int): Unique identifier of the order

        Returns:
            Order instance with populated order items, or None if not found
        """
        try:
            return (
                self.session.query(Order)
                .options(joinedload(Order.order_items))
                .options(joinedload(Order.supplier))
                .filter(Order.id == order_id)
                .first()
            )
        except Exception as e:
            raise DatabaseError(f"Error retrieving order with items: {str(e)}")

    def get_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Retrieve orders filtered by their current status.

        Args:
            status (OrderStatus): Status to filter orders by

        Returns:
            List of Order instances matching the specified status
        """
        try:
            return (
                self.session.query(Order)
                .options(joinedload(Order.order_items))
                .options(joinedload(Order.supplier))
                .filter(Order.status == status)
                .all()
            )
        except Exception as e:
            raise DatabaseError(f"Error retrieving orders by status: {str(e)}")

    def get_by_supplier(self, supplier_id: int) -> List[Order]:
        """
        Retrieve all orders for a specific supplier.

        Args:
            supplier_id (int): Unique identifier of the supplier

        Returns:
            List of Order instances for the specified supplier
        """
        try:
            return (
                self.session.query(Order)
                .options(joinedload(Order.order_items))
                .options(joinedload(Order.supplier))
                .filter(Order.supplier_id == supplier_id)
                .all()
            )
        except Exception as e:
            raise DatabaseError(f"Error retrieving orders for supplier: {str(e)}")

    def get_by_date_range(self,
                          start_date: datetime,
                          end_date: datetime) -> List[Order]:
        """
        Retrieve orders within a specific date range.

        Args:
            start_date (datetime): Start of the date range
            end_date (datetime): End of the date range

        Returns:
            List of Order instances within the specified date range
        """
        try:
            return (
                self.session.query(Order)
                .options(joinedload(Order.order_items))
                .options(joinedload(Order.supplier))
                .filter(Order.order_date.between(start_date, end_date))
                .all()
            )
        except Exception as e:
            raise DatabaseError(f"Error retrieving orders by date range: {str(e)}")

    def search(self,
               search_term: str,
               fields: List[str] = None,
               limit: int = 10) -> List[Order]:
        """
        Search for orders using a flexible search across multiple fields.

        Args:
            search_term (str): Term to search for
            fields (Optional[List[str]]): Specific fields to search
            limit (int, optional): Maximum number of results. Defaults to 10.

        Returns:
            List of Order instances matching the search criteria
        """
        try:
            # Default search fields if not specified
            if not fields:
                fields = ['order_number', 'notes']

            # Prepare search conditions
            search_conditions = []
            normalized_term = f"%{search_term.lower().strip()}%"

            for field in fields:
                # Dynamically create search conditions for each field
                if field == 'order_number':
                    search_conditions.append(func.lower(Order.order_number).like(normalized_term))
                elif field == 'notes':
                    search_conditions.append(func.lower(Order.notes).like(normalized_term))

            # Add supplier name search
            supplier_subquery = (
                self.session.query(Supplier)
                .filter(func.lower(Supplier.name).like(normalized_term))
                .subquery()
            )

            # Combine queries
            query = (
                self.session.query(Order)
                .options(joinedload(Order.order_items))
                .options(joinedload(Order.supplier))
                .filter(or_(*search_conditions))
                .limit(limit)
            )

            return query.all()

        except Exception as e:
            raise DatabaseError(f"Error searching orders: {str(e)}")

    def create(self, order: Order) -> Order:
        """
        Create a new order with associated items.

        Args:
            order (Order): Order instance to create

        Returns:
            Created Order instance

        Raises:
            ValidationError: If order creation fails validation
            DatabaseError: For database-related errors
        """
        try:
            # Validate order items
            if not order.order_items:
                raise ValidationError("Order must have at least one item")

            # Validate total amount
            order.calculate_total_amount()

            # Add order to session
            self.session.add(order)

            # Add order items to session
            for item in order.order_items:
                self.session.add(item)

            # Commit transaction
            self.session.commit()

            return order

        except (ValidationError, DatabaseError):
            # Re-raise validation errors
            self.session.rollback()
            raise
        except Exception as e:
            # Rollback session on unexpected errors
            self.session.rollback()
            raise DatabaseError(f"Error creating order: {str(e)}")

    def update(self, order_id: int, order: Order) -> Order:
        """
        Update an existing order with new information.

        Args:
            order_id (int): ID of the order to update
            order (Order): Updated Order instance

        Returns:
            Updated Order instance

        Raises:
            ValidationError: If order update fails validation
            DatabaseError: For database-related errors
        """
        try:
            # Retrieve existing order
            existing_order = self.get(order_id)
            if not existing_order:
                raise ValidationError(f"Order with ID {order_id} not found")

            # Validate order items
            if not order.order_items:
                raise ValidationError("Order must have at least one item")

            # Recalculate total amount
            order.calculate_total_amount()

            # Update order attributes
            for key, value in order.__dict__.items():
                if not key.startswith('_') and key != 'id':
                    setattr(existing_order, key, value)

            # Clear existing order items and add new ones
            existing_order.order_items.clear()
            for item in order.order_items:
                item.order_id = existing_order.id
                self.session.add(item)

            # Commit transaction
            self.session.commit()

            return existing_order

        except (ValidationError, DatabaseError):
            # Re-raise validation errors
            self.session.rollback()
            raise
        except Exception as e:
            # Rollback session on unexpected errors
            self.session.rollback()
            raise DatabaseError(f"Error updating order: {str(e)}")

    def delete(self, order_id: int) -> bool:
        """
        Delete an order and its associated items.

        Args:
            order_id (int): ID of the order to delete

        Returns:
            Boolean indicating successful deletion

        Raises:
            ValidationError: If order cannot be deleted
            DatabaseError: For database-related errors
        """
        try:
            # Retrieve existing order
            order = self.get(order_id)
            if not order:
                raise ValidationError(f"Order with ID {order_id} not found")

            # Delete order items first
            for item in order.order_items:
                self.session.delete(item)

            # Delete order
            self.session.delete(order)

            # Commit transaction
            self.session.commit()

            return True

        except (ValidationError, DatabaseError):
            # Re-raise validation errors
            self.session.rollback()
            raise
        except Exception as e:
            # Rollback session on unexpected errors
            self.session.rollback()
            raise DatabaseError(f"Error deleting order: {str(e)}")