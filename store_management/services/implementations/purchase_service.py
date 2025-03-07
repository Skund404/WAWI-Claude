# services/implementations/purchase_service.py
from database.models.purchase import Purchase, PurchaseItem
from database.models.enums import PurchaseStatus
from database.repositories.purchase_repository import PurchaseRepository
from database.repositories.purchase_item_repository import PurchaseItemRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.purchase_service import IPurchaseService
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import logging


class PurchaseService(BaseService, IPurchaseService):
    def __init__(
            self,
            session: Optional[Session] = None,
            purchase_repository: Optional[PurchaseRepository] = None,
            purchase_item_repository: Optional[PurchaseItemRepository] = None
    ):
        """
        Initialize the Purchase Service.

        Args:
            session: SQLAlchemy database session
            purchase_repository: Repository for purchase data access
            purchase_item_repository: Repository for purchase item data access
        """
        self.session = session or get_db_session()
        self.purchase_repository = purchase_repository or PurchaseRepository(self.session)
        self.purchase_item_repository = purchase_item_repository or PurchaseItemRepository(self.session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_purchase(
            self,
            supplier_id: int,
            total_amount: float,
            items: List[Dict[str, Any]]
    ) -> Purchase:
        """
        Create a new purchase with associated purchase items.

        Args:
            supplier_id: ID of the supplier
            total_amount: Total purchase amount
            items: List of purchase item details

        Returns:
            Created Purchase instance
        """
        try:
            # Create purchase
            purchase = Purchase(
                supplier_id=supplier_id,
                total_amount=total_amount,
                status=PurchaseStatus.PENDING,
                created_at=datetime.now()
            )

            # Save purchase
            self.session.add(purchase)
            self.session.flush()

            # Create purchase items
            purchase_items = []
            for item in items:
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    quantity=item.get('quantity'),
                    price=item.get('price'),
                    material_id=item.get('material_id'),
                    leather_id=item.get('leather_id'),
                    hardware_id=item.get('hardware_id'),
                    tool_id=item.get('tool_id')
                )
                self.session.add(purchase_item)
                purchase_items.append(purchase_item)

            self.session.commit()
            self.logger.info(f"Created purchase {purchase.id} for supplier {supplier_id}")
            return purchase

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating purchase: {str(e)}")
            raise ValidationError(f"Failed to create purchase: {str(e)}")

    def get_purchase_by_id(self, purchase_id: int) -> Purchase:
        """
        Retrieve a purchase by its ID.

        Args:
            purchase_id: ID of the purchase to retrieve

        Returns:
            Purchase instance

        Raises:
            NotFoundError: If purchase is not found
        """
        try:
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")
            return purchase
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving purchase: {str(e)}")
            raise NotFoundError(f"Failed to retrieve purchase: {str(e)}")

    def update_purchase_status(
            self,
            purchase_id: int,
            status: PurchaseStatus
    ) -> Purchase:
        """
        Update the status of a purchase.

        Args:
            purchase_id: ID of the purchase to update
            status: New status for the purchase

        Returns:
            Updated Purchase instance
        """
        try:
            purchase = self.get_purchase_by_id(purchase_id)
            purchase.status = status
            self.session.commit()
            self.logger.info(f"Updated purchase {purchase_id} status to {status}")
            return purchase
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating purchase status: {str(e)}")
            raise ValidationError(f"Failed to update purchase status: {str(e)}")

    def get_purchases_by_supplier(
            self,
            supplier_id: int,
            status: Optional[PurchaseStatus] = None
    ) -> List[Purchase]:
        """
        Retrieve purchases for a specific supplier, optionally filtered by status.

        Args:
            supplier_id: ID of the supplier
            status: Optional status to filter purchases

        Returns:
            List of Purchase instances
        """
        try:
            return self.purchase_repository.get_by_supplier(supplier_id, status)
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving purchases for supplier: {str(e)}")
            raise NotFoundError(f"Failed to retrieve purchases: {str(e)}")