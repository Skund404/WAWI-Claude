# database/services/implementations/purchase_service.py
"""
Service implementation for managing Purchase entities and their relationships.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
import logging
from datetime import datetime

from database.models.enums import PurchaseStatus, MaterialType
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem
from database.models.material import Material
from database.models.hardware import Hardware
from database.models.leather import Leather
from database.models.tool import Tool
from database.repositories.purchase_repository import PurchaseRepository
from database.repositories.purchase_item_repository import PurchaseItemRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.hardware_repository import HardwareRepository
from database.repositories.leather_repository import LeatherRepository
from database.repositories.tool_repository import ToolRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.purchase_service import IPurchaseService


class PurchaseService(BaseService[Purchase], IPurchaseService):
    """
    Service for managing Purchase-related operations.

    Handles creation, retrieval, updating, and deletion of purchases,
    along with purchase item management.
    """

    def __init__(
        self,
        session=None,
        purchase_repository: Optional[PurchaseRepository] = None,
        purchase_item_repository: Optional[PurchaseItemRepository] = None,
        material_repository: Optional[MaterialRepository] = None,
        hardware_repository: Optional[HardwareRepository] = None,
        leather_repository: Optional[LeatherRepository] = None,
        tool_repository: Optional[ToolRepository] = None
    ):
        """
        Initialize the Purchase Service.

        Args:
            session: SQLAlchemy database session
            purchase_repository: Repository for purchase data access
            purchase_item_repository: Repository for purchase item data access
            material_repository: Repository for material data access
            hardware_repository: Repository for hardware data access
            leather_repository: Repository for leather data access
            tool_repository: Repository for tool data access
        """
        self.session = session or get_db_session()
        self.purchase_repository = purchase_repository or PurchaseRepository(self.session)
        self.purchase_item_repository = (
                purchase_item_repository or
                PurchaseItemRepository(self.session)
        )
        self.material_repository = material_repository or MaterialRepository(self.session)
        self.hardware_repository = hardware_repository or HardwareRepository(self.session)
        self.leather_repository = leather_repository or LeatherRepository(self.session)
        self.tool_repository = tool_repository or ToolRepository(self.session)

        self.logger = logging.getLogger(__name__)

    def create_purchase(
        self,
        supplier_id: str,
        total_amount: float,
        status: PurchaseStatus = PurchaseStatus.PENDING,
        **kwargs
    ) -> Purchase:
        """
        Create a new purchase.

        Args:
            supplier_id: Unique identifier of the supplier
            total_amount: Total purchase amount
            status: Purchase status (default: PENDING)
            **kwargs: Additional purchase attributes

        Returns:
            Created Purchase instance

        Raises:
            ValidationError: If purchase creation fails validation
        """
        try:
            # Validate required fields
            if not supplier_id or total_amount < 0:
                raise ValidationError("Invalid supplier or total amount")

            # Generate a unique identifier
            purchase_id = str(uuid.uuid4())

            # Create purchase
            purchase_data = {
                'id': purchase_id,
                'supplier_id': supplier_id,
                'total_amount': total_amount,
                'status': status,
                'created_at': datetime.utcnow(),
                **kwargs
            }

            purchase = Purchase(**purchase_data)

            # Save purchase
            with self.session:
                self.session.add(purchase)
                self.session.commit()
                self.session.refresh(purchase)

            self.logger.info(f"Created purchase: {purchase_id}")
            return purchase

        except Exception as e:
            self.logger.error(f"Error creating purchase: {str(e)}")
            raise ValidationError(f"Purchase creation failed: {str(e)}")

    def get_purchase_by_id(self, purchase_id: str) -> Purchase:
        """
        Retrieve a purchase by its ID.

        Args:
            purchase_id: Unique identifier of the purchase

        Returns:
            Purchase instance

        Raises:
            NotFoundError: If purchase is not found
        """
        try:
            purchase = self.purchase_repository.get(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")
            return purchase
        except Exception as e:
            self.logger.error(f"Error retrieving purchase: {str(e)}")
            raise NotFoundError(f"Purchase retrieval failed: {str(e)}")

    def update_purchase_status(
        self,
        purchase_id: str,
        new_status: PurchaseStatus
    ) -> Purchase:
        """
        Update the status of a purchase.

        Args:
            purchase_id: Unique identifier of the purchase
            new_status: New purchase status

        Returns:
            Updated Purchase instance

        Raises:
            NotFoundError: If purchase is not found
            ValidationError: If status update fails
        """
        try:
            # Retrieve existing purchase
            purchase = self.get_purchase_by_id(purchase_id)

            # Update purchase status
            purchase.status = new_status
            purchase.updated_at = datetime.utcnow()

            # Save updates
            with self.session:
                self.session.add(purchase)
                self.session.commit()
                self.session.refresh(purchase)

            self.logger.info(f"Updated purchase status: {purchase_id} to {new_status}")
            return purchase

        except Exception as e:
            self.logger.error(f"Error updating purchase status: {str(e)}")
            raise ValidationError(f"Purchase status update failed: {str(e)}")

    def add_purchase_item(
        self,
        purchase_id: str,
        item_type: MaterialType,
        item_id: str,
        quantity: float,
        price: float,
        **kwargs
    ) -> PurchaseItem:
        """
        Add an item to a purchase.

        Args:
            purchase_id: Unique identifier of the purchase
            item_type: Type of material/item being purchased
            item_id: Unique identifier of the item
            quantity: Quantity of the item
            price: Price per unit
            **kwargs: Additional purchase item attributes

        Returns:
            Created PurchaseItem instance

        Raises:
            NotFoundError: If purchase or item is not found
            ValidationError: If item addition fails
        """
        try:
            # Verify purchase exists
            purchase = self.get_purchase_by_id(purchase_id)

            # Validate item based on type
            if item_type == MaterialType.LEATHER:
                item = self.leather_repository.get(item_id)
            elif item_type == MaterialType.HARDWARE:
                item = self.hardware_repository.get(item_id)
            elif item_type == MaterialType.THREAD:
                item = self.material_repository.get(item_id)
            elif item_type == MaterialType.TOOL:
                item = self.tool_repository.get(item_id)
            else:
                raise ValidationError(f"Unsupported material type: {item_type}")

            if not item:
                raise NotFoundError(f"Item with ID {item_id} of type {item_type} not found")

            # Validate quantity and price
            if quantity <= 0 or price < 0:
                raise ValidationError("Invalid quantity or price")

            # Create purchase item
            purchase_item_data = {
                'id': str(uuid.uuid4()),
                'purchase_id': purchase_id,
                'item_type': item_type,
                'item_id': item_id,
                'quantity': quantity,
                'price': price,
                'created_at': datetime.utcnow(),
                **kwargs
            }

            purchase_item = PurchaseItem(**purchase_item_data)

            # Save purchase item
            with self.session:
                self.session.add(purchase_item)
                self.session.commit()
                self.session.refresh(purchase_item)

            self.logger.info(f"Added purchase item: {purchase_item.id}")
            return purchase_item

        except Exception as e:
            self.logger.error(f"Error adding purchase item: {str(e)}")
            raise ValidationError(f"Purchase item addition failed: {str(e)}")

    def get_purchase_items(self, purchase_id: str) -> List[PurchaseItem]:
        """
        Retrieve all items for a specific purchase.

        Args:
            purchase_id: Unique identifier of the purchase

        Returns:
            List of PurchaseItem instances

        Raises:
            NotFoundError: If purchase is not found
        """
        try:
            # Verify purchase exists
            self.get_purchase_by_id(purchase_id)

            # Retrieve purchase items
            purchase_items = self.purchase_item_repository.get_by_purchase_id(purchase_id)

            return purchase_items

        except Exception as e:
            self.logger.error(f"Error retrieving purchase items: {str(e)}")
            raise NotFoundError(f"Purchase items retrieval failed: {str(e)}")

    def get_purchases_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[PurchaseStatus] = None
    ) -> List[Purchase]:
        """
        Retrieve purchases within a specified date range and optional status.

        Args:
            start_date: Optional start date for filtering purchases
            end_date: Optional end date for filtering purchases
            status: Optional purchase status to filter

        Returns:
            List of Purchase instances
        """
        try:
            # Retrieve purchases based on filters
            purchases = self.purchase_repository.get_by_date_range(
                start_date=start_date,
                end_date=end_date,
                status=status
            )

            return purchases

        except Exception as e:
            self.logger.error(f"Error retrieving purchases by date range: {str(e)}")
            raise ValidationError(f"Purchases retrieval failed: {str(e)}")

    def delete_purchase(self, purchase_id: str) -> bool:
        """
        Delete a purchase and its associated items.

        Args:
            purchase_id: Unique identifier of the purchase

        Returns:
            Boolean indicating successful deletion

        Raises:
            NotFoundError: If purchase is not found
            ValidationError: If deletion fails
        """
        try:
            # Verify purchase exists
            purchase = self.get_purchase_by_id(purchase_id)

            # Delete associated purchase items
            with self.session:
                # First, delete related purchase items
                self.session.query(PurchaseItem).filter_by(purchase_id=purchase_id).delete()

                # Then delete the purchase
                self.session.delete(purchase)
                self.session.commit()

            self.logger.info(f"Deleted purchase: {purchase_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting purchase: {str(e)}")
            raise ValidationError(f"Purchase deletion failed: {str(e)}")