# store_management/database/repositories/supplier_repository.py
"""
Repository for Supplier model database access.

Provides specialized operations for retrieving, creating, and managing
supplier information with advanced querying capabilities.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces import MaterialService
from models.supplier import Supplier
from models.order import Order

# Configure logging
logger = logging.getLogger(__name__)


class SupplierRepository:
    """
    Repository for Supplier model database operations.

    Provides methods to interact with suppliers, including
    retrieval, filtering, and comprehensive management.
    """

    @inject(MaterialService)
    def __init__(self, session):
        """
        Initialize the SupplierRepository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def search(
            self,
            search_term: str,
            fields: Optional[List[str]] = None,
            limit: Optional[int] = None
    ) -> List[Supplier]:
        """
        Search for suppliers by a search term in specified fields.

        Args:
            search_term (str): The search term
            fields (Optional[List[str]], optional): Fields to search in
            limit (Optional[int], optional): Maximum number of results

        Returns:
            List[Supplier]: Suppliers matching the search criteria
        """
        try:
            # Validate inputs
            if not search_term or not fields:
                return []

            # Build search conditions
            query = self.session.query(Supplier)
            conditions = []

            for field in fields:
                if hasattr(Supplier, field):
                    attr = getattr(Supplier, field)
                    conditions.append(attr.ilike(f'%{search_term}%'))

            # Apply search conditions
            if not conditions:
                return []

            query = query.filter(func.or_(*conditions))

            # Apply limit if specified
            if limit:
                query = query.limit(limit)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching suppliers for '{search_term}' in {fields}: {e}")
            raise

    def get_supplier_orders(
            self,
            supplier_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Order]:
        """
        Retrieve orders for a specific supplier within an optional date range.

        Args:
            supplier_id (int): The ID of the supplier
            start_date (Optional[datetime], optional): Start of date range
            end_date (Optional[datetime], optional): End of date range

        Returns:
            List[Order]: Orders for the supplier
        """
        try:
            # Base query for supplier orders
            query = self.session.query(Order).filter(Order.supplier_id == supplier_id)

            # Apply date range filtering if provided
            if start_date:
                query = query.filter(Order.created_at >= start_date)
            if end_date:
                query = query.filter(Order.created_at <= end_date)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error getting orders for supplier ID {supplier_id}: {e}')
            raise

    def get_top_suppliers(
            self,
            limit: int = 10,
            performance_metric: str = 'rating'
    ) -> List[Supplier]:
        """
        Retrieve top suppliers based on a performance metric.

        Args:
            limit (int, optional): Maximum number of suppliers to return. Defaults to 10.
            performance_metric (str, optional): Metric to sort by. Defaults to 'rating'.

        Returns:
            List[Supplier]: Top suppliers sorted by the specified metric
        """
        try:
            # Validate performance metric
            if not hasattr(Supplier, performance_metric):
                logger.warning(f'Invalid performance metric: {performance_metric}')
                performance_metric = 'rating'

            # Retrieve top suppliers
            return (
                self.session.query(Supplier)
                .filter(Supplier.is_active == True)
                .order_by(desc(getattr(Supplier, performance_metric)))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error getting top suppliers by {performance_metric}: {e}')
            raise

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Optional[Supplier]:
        """
        Create a new supplier.

        Args:
            supplier_data (Dict[str, Any]): Data for creating a supplier

        Returns:
            Optional[Supplier]: Created supplier
        """
        try:
            # Validate required fields
            if not supplier_data.get('name'):
                raise ValueError('Supplier name is required')

            # Create supplier instance
            supplier = Supplier(**supplier_data)

            # Set default active status if not provided
            if 'is_active' not in supplier_data:
                supplier.is_active = True

            # Add to session and commit
            self.session.add(supplier)
            self.session.commit()

            logger.info(f'Created supplier: {supplier.name}')
            return supplier
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error creating supplier: {e}')
            raise
        except ValueError as e:
            logger.error(f'Validation error creating supplier: {e}')
            raise

    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Optional[Supplier]:
        """
        Update an existing supplier.

        Args:
            supplier_id (int): ID of the supplier to update
            supplier_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Supplier]: Updated supplier
        """
        try:
            # Retrieve existing supplier
            supplier = self.session.query(Supplier).get(supplier_id)

            if not supplier:
                logger.warning(f'Supplier with ID {supplier_id} not found for update')
                return None

            # Update attributes
            for key, value in supplier_data.items():
                if hasattr(supplier, key):
                    setattr(supplier, key, value)
                else:
                    logger.warning(f'Attempted to set non-existent attribute {key} on Supplier')

            # Commit changes
            self.session.commit()

            logger.info(f'Updated supplier: {supplier.name}')
            return supplier
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error updating supplier with ID {supplier_id}: {e}')
            raise

    def delete_supplier(self, supplier_id: int) -> bool:
        """
        Soft delete a supplier by marking as inactive.

        Args:
            supplier_id (int): ID of the supplier to delete

        Returns:
            bool: True if deletion was successful
        """
        try:
            # Retrieve supplier
            supplier = self.session.query(Supplier).get(supplier_id)

            if not supplier:
                logger.warning(f'Supplier with ID {supplier_id} not found for deletion')
                return False

            # Mark as inactive instead of hard delete
            supplier.is_active = False

            # Commit changes
            self.session.commit()

            logger.info(f'Marked supplier as inactive: {supplier.name}')
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error deactivating supplier with ID {supplier_id}: {e}')
            raise

    def generate_supplier_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive supplier performance report.

        Returns:
            Dict[str, Any]: Supplier performance metrics
        """
        try:
            # Active suppliers
            active_suppliers = (
                self.session.query(Supplier)
                .filter(Supplier.is_active == True)
                .count()
            )

            # Total suppliers
            total_suppliers = self.session.query(Supplier).count()

            # Supplier order performance
            supplier_order_performance = (
                self.session.query(
                    Supplier.id,
                    Supplier.name,
                    func.count(Order.id).label('total_orders'),
                    func.avg(Order.total_amount).label('avg_order_value')
                )
                .outerjoin(Order, Supplier.id == Order.supplier_id)
                .group_by(Supplier.id, Supplier.name)
                .order_by(func.count(Order.id).desc())
                .limit(10)
                .all()
            )

            return {
                'total_suppliers': total_suppliers,
                'active_suppliers': active_suppliers,
                'top_suppliers_by_order_volume': [
                    {
                        'supplier_id': sup.id,
                        'supplier_name': sup.name,
                        'total_orders': sup.total_orders,
                        'avg_order_value': float(sup.avg_order_value) if sup.avg_order_value else 0.0
                    }
                    for sup in supplier_order_performance
                ]
            }
        except SQLAlchemyError as e:
            logger.error(f'Error generating supplier performance report: {e}')
            raise