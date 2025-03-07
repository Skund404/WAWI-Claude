# services/implementations/supplier_service.py
from database.models.supplier import Supplier
from database.models.enums import SupplierStatus
from database.repositories.supplier_repository import SupplierRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.supplier_service import ISupplierService
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Dict, List, Optional
import logging
import re


class SupplierService(BaseService, ISupplierService):
    def __init__(
            self,
            session: Optional[Session] = None,
            supplier_repository: Optional[SupplierRepository] = None
    ):
        """
        Initialize the Supplier Service.

        Args:
            session: SQLAlchemy database session
            supplier_repository: Repository for supplier data access
        """
        self.session = session or get_db_session()
        self.supplier_repository = supplier_repository or SupplierRepository(self.session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _validate_email(self, email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            Boolean indicating email validity
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    def create_supplier(
            self,
            name: str,
            contact_email: str,
            status: SupplierStatus = SupplierStatus.ACTIVE
    ) -> Supplier:
        """
        Create a new supplier.

        Args:
            name: Supplier name
            contact_email: Supplier contact email
            status: Supplier status (default: ACTIVE)

        Returns:
            Created Supplier instance
        """
        try:
            # Validate email
            if not self._validate_email(contact_email):
                raise ValidationError(f"Invalid email format: {contact_email}")

            # Check if supplier with this email already exists
            existing_supplier = self.supplier_repository.get_by_email(contact_email)
            if existing_supplier:
                raise ValidationError(f"Supplier with email {contact_email} already exists")

            supplier = Supplier(
                name=name,
                contact_email=contact_email,
                status=status
            )

            self.session.add(supplier)
            self.session.commit()

            self.logger.info(f"Created supplier {supplier.id}: {name}")
            return supplier

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating supplier: {str(e)}")
            raise ValidationError(f"Failed to create supplier: {str(e)}")

    def get_supplier_by_id(self, supplier_id: int) -> Supplier:
        """
        Retrieve a supplier by its ID.

        Args:
            supplier_id: ID of the supplier to retrieve

        Returns:
            Supplier instance

        Raises:
            NotFoundError: If supplier is not found
        """
        try:
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")
            return supplier
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving supplier: {str(e)}")
            raise NotFoundError(f"Failed to retrieve supplier: {str(e)}")

    def update_supplier(
            self,
            supplier_id: int,
            name: Optional[str] = None,
            contact_email: Optional[str] = None,
            status: Optional[SupplierStatus] = None
    ) -> Supplier:
        """
        Update an existing supplier.

        Args:
            supplier_id: ID of the supplier to update
            name: Optional new supplier name
            contact_email: Optional new contact email
            status: Optional new supplier status

        Returns:
            Updated Supplier instance
        """
        try:
            supplier = self.get_supplier_by_id(supplier_id)

            # Validate email if provided
            if contact_email is not None:
                if not self._validate_email(contact_email):
                    raise ValidationError(f"Invalid email format: {contact_email}")

                # Check if email is already in use by another supplier
                existing_supplier = self.supplier_repository.get_by_email(contact_email)
                if existing_supplier and existing_supplier.id != supplier_id:
                    raise ValidationError(f"Email {contact_email} is already in use")

                supplier.contact_email = contact_email

            if name is not None:
                supplier.name = name

            if status is not None:
                supplier.status = status

            self.session.commit()

            self.logger.info(f"Updated supplier {supplier_id}")
            return supplier

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating supplier: {str(e)}")
            raise ValidationError(f"Failed to update supplier: {str(e)}")

    def delete_supplier(self, supplier_id: int) -> None:
        """
        Delete a supplier.

        Args:
            supplier_id: ID of the supplier to delete
        """
        try:
            supplier = self.get_supplier_by_id(supplier_id)

            # Mark as inactive instead of hard delete
            supplier.status = SupplierStatus.INACTIVE
            self.session.commit()

            self.logger.info(f"Deleted (inactivated) supplier {supplier_id}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting supplier: {str(e)}")
            raise ValidationError(f"Failed to delete supplier: {str(e)}")

    def list_suppliers(
            self,
            status: Optional[SupplierStatus] = None,
            page: int = 1,
            per_page: int = 20
    ) -> List[Supplier]:
        """
        List suppliers with optional status filtering and pagination.

        Args:
            status: Optional status to filter suppliers
            page: Page number
            per_page: Number of suppliers per page

        Returns:
            List of Supplier instances
        """
        try:
            return self.supplier_repository.list_suppliers(status, page, per_page)
        except SQLAlchemyError as e:
            self.logger.error(f"Error listing suppliers: {str(e)}")
            raise NotFoundError(f"Failed to list suppliers: {str(e)}")

    def get_supplier_by_email(self, email: str) -> Supplier:
        """
        Retrieve a supplier by their email address.

        Args:
            email: Email address of the supplier

        Returns:
            Supplier instance

        Raises:
            NotFoundError: If no supplier is found with the given email
        """
        try:
            supplier = self.supplier_repository.get_by_email(email)
            if not supplier:
                raise NotFoundError(f"Supplier with email {email} not found")
            return supplier
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving supplier by email: {str(e)}")
            raise NotFoundError(f"Failed to retrieve supplier: {str(e)}")