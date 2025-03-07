# database/services/implementations/supplier_service.py
"""
Service implementation for managing Supplier entities and their relationships.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
import logging
import re

from database.models.enums import SupplierStatus
from database.models.supplier import Supplier
from database.models.purchase import Purchase
from database.repositories.supplier_repository import SupplierRepository
from database.repositories.purchase_repository import PurchaseRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.supplier_service import ISupplierService


class SupplierService(BaseService[Supplier], ISupplierService):
    """
    Service for managing Supplier-related operations.

    Handles creation, retrieval, updating, and deletion of suppliers,
    along with purchase and contact management.
    """

    def __init__(
        self,
        session=None,
        supplier_repository: Optional[SupplierRepository] = None,
        purchase_repository: Optional[PurchaseRepository] = None,
    ):
        """
        Initialize the Supplier Service.

        Args:
            session: SQLAlchemy database session
            supplier_repository: Repository for supplier data access
            purchase_repository: Repository for purchase data access
        """
        self.session = session or get_db_session()
        self.supplier_repository = supplier_repository or SupplierRepository(self.session)
        self.purchase_repository = purchase_repository or PurchaseRepository(self.session)
        self.logger = logging.getLogger(__name__)

    def _validate_email(self, email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            Boolean indicating email validity
        """
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_regex, email) is not None

    def create_supplier(
        self,
        name: str,
        contact_email: str,
        status: SupplierStatus = SupplierStatus.ACTIVE,
        **kwargs,
    ) -> Supplier:
        """
        Create a new supplier.

        Args:
            name: Supplier name
            contact_email: Contact email address
            status: Supplier status (default: ACTIVE)
            **kwargs: Additional supplier attributes

        Returns:
            Created Supplier instance

        Raises:
            ValidationError: If supplier creation fails validation
        """
        try:
            # Validate required fields
            if not name:
                raise ValidationError("Supplier name is required")

            # Validate email
            if not self._validate_email(contact_email):
                raise ValidationError("Invalid email format")

            # Generate a unique identifier
            supplier_id = str(uuid.uuid4())

            # Create supplier
            supplier_data = {
                "id": supplier_id,
                "name": name,
                "contact_email": contact_email,
                "status": status,
                **kwargs,
            }

            supplier = Supplier(**supplier_data)

            # Save supplier
            with self.session:
                self.session.add(supplier)
                self.session.commit()
                self.session.refresh(supplier)

            self.logger.info(f"Created supplier: {supplier.name}")
            return supplier

        except Exception as e:
            self.logger.error(f"Error creating supplier: {str(e)}")
            raise ValidationError(f"Supplier creation failed: {str(e)}")

    def get_supplier_by_id(self, supplier_id: str) -> Supplier:
        """
        Retrieve a supplier by its ID.

        Args:
            supplier_id: Unique identifier of the supplier

        Returns:
            Supplier instance

        Raises:
            NotFoundError: If supplier is not found
        """
        try:
            supplier = self.supplier_repository.get(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")
            return supplier
        except Exception as e:
            self.logger.error(f"Error retrieving supplier: {str(e)}")
            raise NotFoundError(f"Supplier retrieval failed: {str(e)}")

    def update_supplier(
        self,
        supplier_id: str,
        **update_data: Dict[str, Any],
    ) -> Supplier:
        """
        Update an existing supplier.

        Args:
            supplier_id: Unique identifier of the supplier
            update_data: Dictionary of fields to update

        Returns:
            Updated Supplier instance

        Raises:
            NotFoundError: If supplier is not found
            ValidationError: If update fails validation
        """
        try:
            # Retrieve existing supplier
            supplier = self.get_supplier_by_id(supplier_id)

            # Validate email if provided
            if "contact_email" in update_data:
                if not self._validate_email(update_data["contact_email"]):
                    raise ValidationError("Invalid email format")

            # Validate status if provided
            if "status" in update_data:
                if not isinstance(update_data["status"], SupplierStatus):
                    raise ValidationError("Invalid supplier status")

            # Update supplier attributes
            for key, value in update_data.items():
                setattr(supplier, key, value)

            # Save updates
            with self.session:
                self.session.add(supplier)
                self.session.commit()
                self.session.refresh(supplier)

            self.logger.info(f"Updated supplier: {supplier.name}")
            return supplier

        except Exception as e:
            self.logger.error(f"Error updating supplier: {str(e)}")
            raise ValidationError(f"Supplier update failed: {str(e)}")

    def delete_supplier(self, supplier_id: str) -> bool:
        """
        Delete a supplier.

        Args:
            supplier_id: Unique identifier of the supplier

        Returns:
            Boolean indicating successful deletion

        Raises:
            NotFoundError: If supplier is not found
            ValidationError: If supplier cannot be deleted
        """
        try:
            # Retrieve supplier
            supplier = self.get_supplier_by_id(supplier_id)

            # Check for active purchases
            active_purchases = self.purchase_repository.get_by_supplier(supplier_id)
            if active_purchases:
                raise ValidationError("Cannot delete supplier with active purchases")

            # Delete supplier
            with self.session:
                self.session.delete(supplier)
                self.session.commit()

            self.logger.info(f"Deleted supplier: {supplier_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting supplier: {str(e)}")
            raise ValidationError(f"Supplier deletion failed: {str(e)}")

    def get_suppliers_by_status(
        self,
        status: Optional[SupplierStatus] = None,
    ) -> List[Supplier]:
        """
        Retrieve suppliers filtered by status.

        Args:
            status: Optional supplier status to filter suppliers

        Returns:
            List of Supplier instances
        """
        try:
            # Use repository method to filter suppliers
            suppliers = self.supplier_repository.get_by_status(status)
            return suppliers
        except Exception as e:
            self.logger.error(f"Error retrieving suppliers: {str(e)}")
            return []

    def create_purchase_order(
        self,
        supplier_id: str,
        total_amount: float,
        **kwargs,
    ) -> Purchase:
        """
        Create a purchase order for a specific supplier.

        Args:
            supplier_id: Unique identifier of the supplier
            total_amount: Total amount of the purchase
            **kwargs: Additional purchase order attributes

        Returns:
            Created Purchase instance

        Raises:
            NotFoundError: If supplier is not found
            ValidationError: If purchase order creation fails
        """
        try:
            # Verify supplier exists
            supplier = self.get_supplier_by_id(supplier_id)

            # Generate a unique identifier
            purchase_id = str(uuid.uuid4())

            # Create purchase order
            purchase_data = {
                "id": purchase_id,
                "supplier_id": supplier_id,
                "total_amount": total_amount,
                **kwargs,
            }

            purchase = Purchase(**purchase_data)

            # Save purchase order
            with self.session:
                self.session.add(purchase)
                self.session.commit()
                self.session.refresh(purchase)

            self.logger.info(f"Created purchase order for supplier: {supplier.name}")
            return purchase

        except Exception as e:
            self.logger.error(f"Error creating purchase order: {str(e)}")
            raise ValidationError(f"Purchase order creation failed: {str(e)}")

    def get_supplier_purchase_history(
        self,
        supplier_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Purchase]:
        """
        Retrieve purchase history for a specific supplier.

        Args:
            supplier_id: Unique identifier of the supplier
            start_date: Optional start date for filtering purchases
            end_date: Optional end date for filtering purchases

        Returns:
            List of Purchase instances

        Raises:
            NotFoundError: If supplier is not found
        """
        try:
            # Verify supplier exists
            self.get_supplier_by_id(supplier_id)

            # Retrieve purchase history
            purchases = self.purchase_repository.get_by_supplier_and_date_range(
                supplier_id, start_date, end_date
            )
            return purchases

        except Exception as e:
            self.logger.error(f"Error retrieving supplier purchase history: {str(e)}")
            raise NotFoundError(f"Supplier purchase history retrieval failed: {str(e)}")