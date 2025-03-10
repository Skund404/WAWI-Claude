# services/implementations/supplier_service.py
import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from di.inject import inject
from sqlalchemy.orm import Session

from database.models.enums import InventoryStatus, SupplierStatus
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.purchase_repository import PurchaseRepository
from database.repositories.supplier_repository import SupplierRepository

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.supplier_service import ISupplierService


class SupplierService(BaseService, ISupplierService):
    """Implementation of the supplier service interface.

    This class provides functionality for managing suppliers,
    including creation, retrieval, updating, and supplier-related operations.
    """

    @inject
    def __init__(
            self,
            session: Session,
            supplier_repository: SupplierRepository,
            material_repository: MaterialRepository,
            purchase_repository: PurchaseRepository,
            inventory_repository: InventoryRepository
    ):
        """Initialize the SupplierService with required repositories.

        Args:
            session: SQLAlchemy database session
            supplier_repository: Repository for supplier operations
            material_repository: Repository for material operations
            purchase_repository: Repository for purchase operations
            inventory_repository: Repository for inventory operations
        """
        super().__init__(session)
        self._logger = logging.getLogger(__name__)
        self._supplier_repository = supplier_repository
        self._material_repository = material_repository
        self._purchase_repository = purchase_repository
        self._inventory_repository = inventory_repository

    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """Get all suppliers.

        Returns:
            List[Dict[str, Any]]: List of supplier dictionaries
        """
        self._logger.info("Retrieving all suppliers")
        suppliers = self._supplier_repository.get_all()
        return [self._to_dict(supplier) for supplier in suppliers]

    def get_supplier_by_id(self, supplier_id: int) -> Dict[str, Any]:
        """Get supplier by ID.

        Args:
            supplier_id: ID of the supplier

        Returns:
            Dict[str, Any]: Supplier dictionary

        Raises:
            NotFoundError: If supplier not found
        """
        self._logger.info(f"Retrieving supplier with ID: {supplier_id}")
        supplier = self._supplier_repository.get_by_id(supplier_id)
        if not supplier:
            self._logger.error(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")
        return self._to_dict(supplier)

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier.

        Args:
            supplier_data: Supplier data dictionary

        Returns:
            Dict[str, Any]: Created supplier dictionary

        Raises:
            ValidationError: If validation fails
        """
        self._logger.info("Creating new supplier")
        self._validate_supplier_data(supplier_data)

        # Ensure supplier has a status
        if 'status' not in supplier_data:
            supplier_data['status'] = SupplierStatus.ACTIVE.name

        # Check for duplicate email
        email = supplier_data.get('contact_email')
        if email and self._supplier_repository.get_by_email(email):
            self._logger.error(f"Supplier with email {email} already exists")
            raise ValidationError(f"Supplier with email {email} already exists")

        try:
            supplier = self._supplier_repository.create(supplier_data)
            self._session.commit()
            self._logger.info(f"Created supplier with ID: {supplier.id}")
            return self._to_dict(supplier)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to create supplier: {str(e)}")
            raise ValidationError(f"Failed to create supplier: {str(e)}")

    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier.

        Args:
            supplier_id: ID of the supplier to update
            supplier_data: Updated supplier data

        Returns:
            Dict[str, Any]: Updated supplier dictionary

        Raises:
            NotFoundError: If supplier not found
            ValidationError: If validation fails
        """
        self._logger.info(f"Updating supplier with ID: {supplier_id}")
        supplier = self._supplier_repository.get_by_id(supplier_id)
        if not supplier:
            self._logger.error(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        self._validate_supplier_data(supplier_data, is_update=True)

        # Check for duplicate email if email is being updated
        email = supplier_data.get('contact_email')
        if email and email != supplier.contact_email:
            existing_supplier = self._supplier_repository.get_by_email(email)
            if existing_supplier and existing_supplier.id != supplier_id:
                self._logger.error(f"Supplier with email {email} already exists")
                raise ValidationError(f"Supplier with email {email} already exists")

        try:
            updated_supplier = self._supplier_repository.update(supplier_id, supplier_data)
            self._session.commit()
            self._logger.info(f"Updated supplier with ID: {supplier_id}")
            return self._to_dict(updated_supplier)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to update supplier: {str(e)}")
            raise ValidationError(f"Failed to update supplier: {str(e)}")

    def delete_supplier(self, supplier_id: int) -> bool:
        """Delete a supplier.

        Args:
            supplier_id: ID of the supplier to delete

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If supplier not found
        """
        self._logger.info(f"Deleting supplier with ID: {supplier_id}")
        supplier = self._supplier_repository.get_by_id(supplier_id)
        if not supplier:
            self._logger.error(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Check if supplier can be deleted (no active purchases)
        active_purchases = self._purchase_repository.get_active_by_supplier_id(supplier_id)
        if active_purchases:
            self._logger.error(f"Cannot delete supplier with active purchases")
            raise ValidationError(f"Cannot delete supplier with active purchases")

        try:
            self._supplier_repository.delete(supplier_id)
            self._session.commit()
            self._logger.info(f"Deleted supplier with ID: {supplier_id}")
            return True
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to delete supplier: {str(e)}")
            raise ValidationError(f"Failed to delete supplier: {str(e)}")

    def get_supplier_materials(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get materials supplied by a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List[Dict[str, Any]]: List of material dictionaries

        Raises:
            NotFoundError: If supplier not found
        """
        self._logger.info(f"Retrieving materials for supplier with ID: {supplier_id}")
        supplier = self._supplier_repository.get_by_id(supplier_id)
        if not supplier:
            self._logger.error(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        materials = self._material_repository.get_by_supplier_id(supplier_id)

        result = []
        for material in materials:
            material_dict = {
                'id': material.id,
                'name': material.name,
                'material_type': material.material_type.name if material.material_type else None,
                'cost_per_unit': material.cost_per_unit
            }

            # Get inventory status and quantity
            inventory = self._inventory_repository.get_by_item('material', material.id)
            if inventory:
                material_dict['inventory_status'] = inventory.status.name if inventory.status else None
                material_dict['quantity'] = inventory.quantity

            result.append(material_dict)

        return result

    def get_supplier_purchase_history(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get purchase history for a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List[Dict[str, Any]]: List of purchase dictionaries

        Raises:
            NotFoundError: If supplier not found
        """
        self._logger.info(f"Retrieving purchase history for supplier with ID: {supplier_id}")
        supplier = self._supplier_repository.get_by_id(supplier_id)
        if not supplier:
            self._logger.error(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        purchases = self._purchase_repository.get_by_supplier_id(supplier_id)

        result = []
        for purchase in purchases:
            result.append({
                'id': purchase.id,
                'total_amount': round(purchase.total_amount, 2) if purchase.total_amount else 0,
                'status': purchase.status.name if purchase.status else None,
                'created_at': purchase.created_at.isoformat() if purchase.created_at else None
            })

        return result

    def search_suppliers(self, query: str) -> List[Dict[str, Any]]:
        """Search for suppliers by name or contact information.

        Args:
            query: Search query string

        Returns:
            List[Dict[str, Any]]: List of matching supplier dictionaries
        """
        self._logger.info(f"Searching suppliers with query: {query}")
        suppliers = self._supplier_repository.search(query)
        return [self._to_dict(supplier) for supplier in suppliers]

    def update_supplier_status(self, supplier_id: int, status: str) -> Dict[str, Any]:
        """Update the status of a supplier.

        Args:
            supplier_id: ID of the supplier
            status: New status value

        Returns:
            Dict[str, Any]: Updated supplier dictionary

        Raises:
            NotFoundError: If supplier not found
            ValidationError: If validation fails
        """
        self._logger.info(f"Updating status of supplier with ID: {supplier_id} to {status}")
        supplier = self._supplier_repository.get_by_id(supplier_id)
        if not supplier:
            self._logger.error(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Validate status value
        try:
            status_enum = SupplierStatus[status.upper()]
        except KeyError:
            self._logger.error(f"Invalid supplier status: {status}")
            raise ValidationError(f"Invalid supplier status: {status}")

        try:
            updated_supplier = self._supplier_repository.update(supplier_id, {'status': status_enum})
            self._session.commit()
            self._logger.info(f"Updated status of supplier with ID: {supplier_id} to {status_enum.name}")
            return self._to_dict(updated_supplier)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to update supplier status: {str(e)}")
            raise ValidationError(f"Failed to update supplier status: {str(e)}")

    def _validate_supplier_data(self, supplier_data: Dict[str, Any], is_update: bool = False) -> None:
        """Validate supplier data.

        Args:
            supplier_data: Supplier data to validate
            is_update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # For create operations, name is required
        if not is_update and 'name' not in supplier_data:
            raise ValidationError("name is required")

        # Validate email format if provided
        email = supplier_data.get('contact_email')
        if email and not self._is_valid_email(email):
            raise ValidationError(f"Invalid email format: {email}")

        # Validate status if provided
        if 'status' in supplier_data:
            try:
                SupplierStatus[supplier_data['status'].upper()]
            except KeyError:
                raise ValidationError(f"Invalid supplier status: {supplier_data['status']}")

    def _is_valid_email(self, email: str) -> bool:
        """Check if an email has a valid format.

        Args:
            email: Email to validate

        Returns:
            bool: True if the email format is valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _to_dict(self, supplier) -> Dict[str, Any]:
        """Convert supplier model to dictionary.

        Args:
            supplier: Supplier model object

        Returns:
            Dict[str, Any]: Supplier dictionary
        """
        return {
            'id': supplier.id,
            'name': supplier.name,
            'contact_email': supplier.contact_email,
            'contact_phone': getattr(supplier, 'contact_phone', None),
            'address': getattr(supplier, 'address', None),
            'website': getattr(supplier, 'website', None),
            'status': supplier.status.name if supplier.status else None,
            'notes': getattr(supplier, 'notes', None),
            'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
            'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None
        }