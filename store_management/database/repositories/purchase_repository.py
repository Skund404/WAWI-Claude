# database/repositories/purchase_repository.py
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem
from database.models.enums import PurchaseStatus
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, select
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging


class PurchaseRepository(BaseRepository):
    def __init__(self, session: Session):
        """
        Initialize the Purchase Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Purchase)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_purchase(self, purchase_data: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None) -> Purchase:
        """
        Create a new purchase with optional purchase items.

        Args:
            purchase_data (Dict[str, Any]): Data for creating a new purchase
            items (Optional[List[Dict[str, Any]]]): List of purchase items to associate with the purchase

        Returns:
            Created Purchase instance
        """
        try:
            # Create purchase
            purchase = Purchase(**purchase_data)
            self.session.add(purchase)

            # Add purchase items if provided
            if items:
                for item_data in items:
                    item_data['purchase_id'] = purchase.id
                    purchase_item = PurchaseItem(**item_data)
                    self.session.add(purchase_item)

            self.session.commit()
            return purchase
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error creating purchase: {e}")
            raise

    def find_by_status(self, status: PurchaseStatus) -> List[Purchase]:
        """
        Find purchases by their status.

        Args:
            status (PurchaseStatus): Purchase status to filter by

        Returns:
            List of purchases matching the status
        """
        try:
            return self.session.execute(select(Purchase).filter(Purchase.status == status)).scalars().all()
        except Exception as e:
            self.logger.error(f"Error finding purchases by status: {e}")
            raise

    def get_purchases_with_items(self,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 supplier_id: Optional[int] = None) -> List[Purchase]:
        """
        Retrieve purchases with their associated items, with optional filtering.

        Args:
            start_date (Optional[datetime]): Start date for purchase filter
            end_date (Optional[datetime]): End date for purchase filter
            supplier_id (Optional[int]): Supplier ID to filter purchases

        Returns:
            List of purchases with their items
        """
        try:
            query = select(Purchase).options(joinedload(Purchase.items))

            # Build filter conditions
            conditions = []
            if start_date:
                conditions.append(Purchase.created_at >= start_date)
            if end_date:
                conditions.append(Purchase.created_at <= end_date)
            if supplier_id:
                conditions.append(Purchase.supplier_id == supplier_id)

            # Apply filters if any
            if conditions:
                query = query.filter(and_(*conditions))

            return query.all()
        except Exception as e:
            self.logger.error(f"Error retrieving purchases with items: {e}")
            raise

    def get_total_purchase_value(self,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> float:
        """
        Calculate the total value of purchases within a given date range.

        Args:
            start_date (Optional[datetime]): Start date for purchase calculation
            end_date (Optional[datetime]): End date for purchase calculation

        Returns:
            Total purchase value
        """
        try:
            query = select(func.sum(Purchase.total_amount))

            # Build filter conditions
            conditions = []
            if start_date:
                conditions.append(Purchase.created_at >= start_date)
            if end_date:
                conditions.append(Purchase.created_at <= end_date)

            # Apply filters if any
            if conditions:
                query = query.filter(and_(*conditions))

            total = query.scalar() or 0.0
            return total
        except Exception as e:
            self.logger.error(f"Error calculating total purchase value: {e}")
            raise