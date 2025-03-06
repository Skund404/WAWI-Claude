# Path: database/sqlalchemy/managers/supplier_manager.py

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from models import (
    Supplier,
    Part,
    Leather,
    Order
)
from core.exceptions import DatabaseError


class SupplierManager:
    """
    Manager for handling supplier operations and relationships.

    Provides comprehensive methods for managing suppliers, 
    tracking performance, and handling supplier-related queries.
    """

    def __init__(self, session_factory):
        """
        Initialize SupplierManager with session factory.

        Args:
            session_factory (Callable): Factory function to create database sessions
        """
        self.session_factory = session_factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: Database session
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_supplier(self, data: Dict[str, Any]) -> Supplier:
        """
        Create a new supplier with comprehensive validation.

        Args:
            data (Dict[str, Any]): Supplier data including contact information

        Returns:
            Supplier: Created Supplier instance

        Raises:
            DatabaseError: If validation fails or creation fails
        """
        try:
            # Required field validation
            required_fields = ['name', 'contact_person', 'email', 'phone']
            missing_fields = [f for f in required_fields if f not in data]

            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Email validation
            if 'email' in data and not self._validate_email(data['email']):
                raise ValueError("Invalid email format")

            with self.session_scope() as session:
                # Check for existing supplier with same email
                existing_supplier = session.query(Supplier).filter(Supplier.email == data['email']).first()
                if existing_supplier:
                    raise ValueError(f"Supplier with email {data['email']} already exists")

                # Create supplier
                supplier = Supplier(
                    **{k: v for k, v in data.items() if k in [
                        'name', 'contact_person', 'email', 'phone',
                        'address', 'notes', 'status'
                    ]},
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    quality_rating=0.0,  # Initialize quality rating
                    status='active'  # Default status
                )

                session.add(supplier)
                return supplier

        except (SQLAlchemyError, ValueError) as e:
            error_msg = f'Failed to create supplier: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def _validate_email(self, email: str) -> bool:
        """
        Validate email format.

        Args:
            email (str): Email address to validate

        Returns:
            bool: True if email is valid, False otherwise
        """
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    def update_supplier(self, supplier_id: int, data: Dict[str, Any]) -> Optional[Supplier]:
        """
        Update supplier information.

        Args:
            supplier_id (int): Supplier ID
            data (Dict[str, Any]): Updated supplier data

        Returns:
            Optional[Supplier]: Updated Supplier instance or None if not found

        Raises:
            DatabaseError: If update fails
        """
        try:
            with self.session_scope() as session:
                # Find supplier
                supplier = session.get(Supplier, supplier_id)

                if not supplier:
                    self.logger.warning(f"Supplier {supplier_id} not found")
                    return None

                # Email validation if email is being updated
                if 'email' in data:
                    if not self._validate_email(data['email']):
                        raise ValueError("Invalid email format")

                    # Check for email conflict
                    existing_supplier = session.query(Supplier).filter(
                        Supplier.email == data['email'],
                        Supplier.id != supplier_id
                    ).first()
                    if existing_supplier:
                        raise ValueError(f"Email {data['email']} is already in use")

                # Update supplier attributes
                for key, value in data.items():
                    # Only update specific allowed fields
                    if key in ['name', 'contact_person', 'email', 'phone', 'address', 'notes', 'status']:
                        setattr(supplier, key, value)

                # Update modification timestamp
                supplier.modified_at = datetime.now()

                return supplier

        except (SQLAlchemyError, ValueError) as e:
            error_msg = f'Failed to update supplier {supplier_id}: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_supplier_with_orders(self, supplier_id: int) -> Optional[Supplier]:
        """
        Retrieve supplier with their sale history.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            Optional[Supplier]: Supplier instance with orders loaded
        """
        try:
            with self.session_scope() as session:
                query = (
                    select(Supplier)
                    .options(joinedload(Supplier.orders))
                    .filter(Supplier.id == supplier_id)
                )
                return session.execute(query).scalar_one_or_none()

        except SQLAlchemyError as e:
            error_msg = f'Failed to get supplier {supplier_id} with orders: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_supplier_products(self, supplier_id: int) -> Dict[str, List]:
        """
        Retrieve all products supplied by a specific supplier.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            Dict[str, List]: Dictionary containing parts and leather supplied
        """
        try:
            with self.session_scope() as session:
                # Verify supplier exists
                supplier = session.get(Supplier, supplier_id)
                if not supplier:
                    raise ValueError(f'Supplier {supplier_id} not found')

                # Fetch parts and leather for the supplier
                parts = session.query(Part).filter(Part.supplier_id == supplier_id).all()
                leather = session.query(Leather).filter(Leather.supplier_id == supplier_id).all()

                return {
                    'parts': parts,
                    'leather': leather
                }

        except (SQLAlchemyError, ValueError) as e:
            error_msg = f'Failed to get products for supplier {supplier_id}: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """
        Calculate and retrieve supplier performance metrics.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            Dict[str, Any]: Dictionary containing performance metrics
        """
        try:
            with self.session_scope() as session:
                # Verify supplier exists
                supplier = session.get(Supplier, supplier_id)
                if not supplier:
                    raise ValueError(f'Supplier {supplier_id} not found')

                # Fetch all orders for the supplier
                orders = session.query(Order).filter(Order.supplier_id == supplier_id).all()

                # Handle case with no orders
                total_orders = len(orders)
                if total_orders == 0:
                    return {
                        'total_orders': 0,
                        'on_time_delivery_rate': 0,
                        'average_delay_days': 0,
                        'order_fulfillment_rate': 0,
                        'quality_rating': supplier.quality_rating or 0
                    }

                # Calculate performance metrics
                on_time_deliveries = sum(
                    1 for o in orders
                    if o.delivery_date and o.delivery_date <= o.expected_delivery_date
                )

                delays = [
                    (o.delivery_date - o.expected_delivery_date).days
                    for o in orders
                    if o.delivery_date and o.delivery_date > o.expected_delivery_date
                ]

                fulfilled_orders = sum(1 for o in orders if o.status == 'completed')

                return {
                    'total_orders': total_orders,
                    'on_time_delivery_rate': on_time_deliveries / total_orders * 100,
                    'average_delay_days': sum(delays) / len(delays) if delays else 0,
                    'order_fulfillment_rate': fulfilled_orders / total_orders * 100,
                    'quality_rating': supplier.quality_rating or 0
                }

        except (SQLAlchemyError, ValueError) as e:
            error_msg = f'Failed to get performance for supplier {supplier_id}: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def update_supplier_rating(self, supplier_id: int, rating: float, notes: Optional[str] = None) -> Supplier:
        """
        Update supplier quality rating.

        Args:
            supplier_id (int): Supplier ID
            rating (float): New rating (0-5)
            notes (Optional[str], optional): Optional notes about the rating

        Returns:
            Supplier: Updated Supplier instance

        Raises:
            DatabaseError: If rating update fails
        """
        # Validate rating
        if not 0 <= rating <= 5:
            raise DatabaseError('Rating must be between 0 and 5')

        try:
            with self.session_scope() as session:
                # Find supplier
                supplier = session.get(Supplier, supplier_id)

                if not supplier:
                    raise ValueError(f'Supplier {supplier_id} not found')

                # Update rating
                supplier.quality_rating = rating
                supplier.rating_notes = notes
                supplier.modified_at = datetime.now()

                return supplier

        except (SQLAlchemyError, ValueError) as e:
            error_msg = f'Failed to update supplier rating for {supplier_id}: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_top_suppliers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve top suppliers based on performance metrics.

        Args:
            limit (int, optional): Number of top suppliers to return. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: List of top suppliers with performance metrics
        """
        try:
            with self.session_scope() as session:
                # Fetch all suppliers with their orders
                suppliers = session.query(Supplier).options(joinedload(Supplier.orders)).all()

                supplier_metrics = []
                for supplier in suppliers:
                    # Skip suppliers with no orders
                    total_orders = len(supplier.orders)
                    if total_orders == 0:
                        continue

                    # Calculate performance metrics
                    completed_orders = sum(1 for o in supplier.orders if o.status == 'completed')
                    on_time_orders = sum(
                        1 for o in supplier.orders if o.delivery_date and o.delivery_date <= o.expected_delivery_date)

                    # Calculate performance score
                    performance_score = (
                                                (completed_orders / total_orders * 0.4) +
                                                (on_time_orders / total_orders * 0.4) +
                                                ((supplier.quality_rating or 0) / 5 * 0.2)
                                        ) * 100

                    supplier_metrics.append({
                        'id': supplier.id,
                        'name': supplier.name,
                        'total_orders': total_orders,
                        'completed_orders': completed_orders,
                        'on_time_delivery_rate': on_time_orders / total_orders * 100,
                        'quality_rating': supplier.quality_rating or 0,
                        'performance_score': performance_score
                    })

                # Sort and return top suppliers
                return sorted(supplier_metrics, key=lambda x: x['performance_score'], reverse=True)[:limit]

        except SQLAlchemyError as e:
            error_msg = f'Failed to get top suppliers: {str(e)}'
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='supplier_manager.log'
)

# Additional imports for completeness
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from core.exceptions import DatabaseError
from models import Supplier, Part, Leather, Order