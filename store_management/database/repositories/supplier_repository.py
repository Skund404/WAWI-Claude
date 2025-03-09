# database/repositories/supplier_repository.py
"""
Repository for Supplier model database access.

Provides specialized operations for retrieving, creating, and managing
supplier information with advanced querying capabilities.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import func, desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
import logging

from database.models.supplier import Supplier
from database.models.purchase import Purchase
from database.models.material import Material
from database.models.tool import Tool
from database.models.enums import SupplierStatus
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError, RepositoryError

# Configure logging
logger = logging.getLogger(__name__)


class SupplierRepository(BaseRepository[Supplier]):
    """
    Repository for Supplier model database operations.

    Provides methods to interact with suppliers, including
    retrieval, filtering, and comprehensive management.
    """

    def __init__(self, session: Session):
        """
        Initialize the SupplierRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Supplier)

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
            if not search_term:
                return []

            # Determine search fields
            if not fields:
                fields = ['name', 'contact_email']

            # Build search conditions
            query = select(Supplier)
            conditions = []

            for field in fields:
                if hasattr(Supplier, field):
                    attr = getattr(Supplier, field)
                    conditions.append(attr.ilike(f'%{search_term}%'))

            # Apply search conditions
            if not conditions:
                return []

            query = query.where(func.or_(*conditions))

            # Apply options for related data
            query = query.options(
                selectinload(Supplier.materials),
                selectinload(Supplier.tools),
                selectinload(Supplier.purchases)
            )

            # Apply limit if specified
            if limit:
                query = query.limit(limit)

            # Execute query
            results = self.session.execute(query).scalars().unique().all()

            logger.info(f"Found {len(results)} suppliers matching search term '{search_term}'")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Error searching suppliers for '{search_term}' in {fields}: {e}")
            raise RepositoryError(f"Failed to search suppliers: {str(e)}")

    def get_supplier_purchases(
            self,
            supplier_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            status: Optional[str] = None
    ) -> List[Purchase]:
        """
        Retrieve purchases for a specific supplier within an optional date range.

        Args:
            supplier_id (int): The ID of the supplier
            start_date (Optional[datetime], optional): Start of date range
            end_date (Optional[datetime], optional): End of date range
            status (Optional[str], optional): Filter by purchase status

        Returns:
            List[Purchase]: Purchases for the supplier
        """
        try:
            # Base query for supplier purchases
            query = select(Purchase).where(Purchase.supplier_id == supplier_id)

            # Apply date range filtering if provided
            if start_date:
                query = query.filter(Purchase.created_at >= start_date)
            if end_date:
                query = query.filter(Purchase.created_at <= end_date)

            # Apply status filtering if provided
            if status:
                query = query.filter(Purchase.status == status)

            # Include purchase items
            query = query.options(
                selectinload(Purchase.purchase_items)
            )

            # Execute query
            results = self.session.execute(query).scalars().unique().all()

            logger.info(f"Retrieved {len(results)} purchases for supplier ID {supplier_id}")
            return results

        except SQLAlchemyError as e:
            logger.error(f'Error getting purchases for supplier ID {supplier_id}: {e}')
            raise RepositoryError(f"Failed to retrieve supplier purchases: {str(e)}")

    def get_top_suppliers(
            self,
            limit: int = 10,
            performance_metric: str = 'total_purchases'
    ) -> List[Supplier]:
        """
        Retrieve top suppliers based on a performance metric.

        Args:
            limit (int, optional): Maximum number of suppliers to return. Defaults to 10.
            performance_metric (str, optional): Metric to sort by. Defaults to 'total_purchases'.

        Returns:
            List[Supplier]: Top suppliers sorted by the specified metric
        """
        try:
            # Base query for active suppliers
            query = select(Supplier).where(Supplier.status == SupplierStatus.ACTIVE)

            # Apply sorting based on performance metric
            if performance_metric == 'total_purchases':
                # Subquery to calculate total purchase amount
                subquery = (
                    select(
                        Purchase.supplier_id,
                        func.sum(Purchase.total_amount).label('total_purchase_amount')
                    )
                    .group_by(Purchase.supplier_id)
                    .alias('supplier_purchase_totals')
                )

                query = query.join(
                    subquery,
                    Supplier.id == subquery.c.supplier_id
                ).order_by(desc(subquery.c.total_purchase_amount))
            elif hasattr(Supplier, performance_metric):
                # Sort by a direct supplier attribute if it exists
                query = query.order_by(desc(getattr(Supplier, performance_metric)))
            else:
                logger.warning(f'Invalid performance metric: {performance_metric}')
                # Fallback to default sorting
                query = query.order_by(desc(Supplier.name))

            # Apply limit and include related data
            query = (
                query.limit(limit)
                .options(
                    selectinload(Supplier.materials),
                    selectinload(Supplier.tools),
                    selectinload(Supplier.purchases)
                )
            )

            # Execute query
            results = self.session.execute(query).scalars().unique().all()

            logger.info(f"Retrieved top {len(results)} suppliers by {performance_metric}")
            return results

        except SQLAlchemyError as e:
            logger.error(f'Error getting top suppliers by {performance_metric}: {e}')
            raise RepositoryError(f"Failed to retrieve top suppliers: {str(e)}")

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Supplier:
        """
        Create a new supplier.

        Args:
            supplier_data (Dict[str, Any]): Data for creating a supplier

        Returns:
            Supplier: Created supplier

        Raises:
            RepositoryError: If supplier creation fails
        """
        try:
            # Validate required fields
            if not supplier_data.get('name'):
                raise ValueError('Supplier name is required')

            # Create supplier instance
            supplier = Supplier(**supplier_data)

            # Set default status if not provided
            if 'status' not in supplier_data:
                supplier.status = SupplierStatus.ACTIVE

            # Add to session and commit
            self.session.add(supplier)
            self.session.commit()

            logger.info(f'Created supplier: {supplier.name}')
            return supplier

        except (ValueError, SQLAlchemyError) as e:
            self.session.rollback()
            logger.error(f'Error creating supplier: {e}')
            raise RepositoryError(f"Failed to create supplier: {str(e)}")

    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Optional[Supplier]:
        """
        Update an existing supplier.

        Args:
            supplier_id (int): ID of the supplier to update
            supplier_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Supplier]: Updated supplier or None if not found

        Raises:
            RepositoryError: If supplier update fails
        """
        try:
            # Retrieve existing supplier
            supplier = self.session.get(Supplier, supplier_id)

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
            raise RepositoryError(f"Failed to update supplier: {str(e)}")

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
            supplier = self.session.get(Supplier, supplier_id)

            if not supplier:
                logger.warning(f'Supplier with ID {supplier_id} not found for deletion')
                return False

            # Mark as inactive instead of hard delete
            supplier.status = SupplierStatus.INACTIVE

            # Commit changes
            self.session.commit()

            logger.info(f'Marked supplier as inactive: {supplier.name}')
            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error deactivating supplier with ID {supplier_id}: {e}')
            raise RepositoryError(f"Failed to delete supplier: {str(e)}")

    def generate_supplier_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive supplier performance report.

        Returns:
            Dict[str, Any]: Supplier performance metrics
        """
        try:
            # Active suppliers
            query_active = select(func.count()).select_from(Supplier).where(Supplier.status == SupplierStatus.ACTIVE)
            active_suppliers = self.session.execute(query_active).scalar_one()

            # Total suppliers
            query_total = select(func.count()).select_from(Supplier)
            total_suppliers = self.session.execute(query_total).scalar_one()

            # Supplier purchase performance
            query_purchase_performance = (
                select(
                    Supplier.id,
                    Supplier.name,
                    func.count(Purchase.id).label('total_purchases'),
                    func.coalesce(func.sum(Purchase.total_amount), 0).label('total_purchase_amount')
                )
                .outerjoin(Purchase, Supplier.id == Purchase.supplier_id)
                .group_by(Supplier.id, Supplier.name)
                .order_by(func.count(Purchase.id).desc())
                .limit(10)
            )
            supplier_purchase_performance = self.session.execute(query_purchase_performance).all()

            return {
                'total_suppliers': total_suppliers,
                'active_suppliers': active_suppliers,
                'inactive_suppliers': total_suppliers - active_suppliers,
                'top_suppliers_by_order_volume': [
                    {
                        'supplier_id': sup.id,
                        'supplier_name': sup.name,
                        'total_purchases': sup.total_purchases,
                        'total_purchase_amount': float(sup.total_purchase_amount)
                    }
                    for sup in supplier_purchase_performance
                ]
            }

        except SQLAlchemyError as e:
            logger.error(f'Error generating supplier performance report: {e}')
            raise RepositoryError(f"Failed to generate supplier performance report: {str(e)}")