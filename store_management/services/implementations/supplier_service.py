# services/implementations/supplier_service.py
import logging
from typing import Any, Dict, List, Optional

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.supplier_service import ISupplierService, SupplierStatus
from utils.circular_import_resolver import lazy_import, resolve_lazy_import

logger = logging.getLogger(__name__)

# Lazily import models to avoid circular imports
Supplier = lazy_import('database.models.supplier', 'Supplier')


class SupplierService(BaseService, ISupplierService):
    """
    Implementation of the Supplier Service interface.
    Manages supplier data and operations in the leatherworking store management system.
    """

    def __init__(self):
        """Initialize the Supplier Service with in-memory storage."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.suppliers = {}
        self._create_sample_suppliers()
        self.logger.info("SupplierService initialized with sample data")

    def _create_sample_suppliers(self) -> None:
        """Create sample suppliers for testing."""
        sample_suppliers = [
            {
                'id': 1,
                'name': 'Premium Leathers Inc.',
                'contact': 'John Smith',
                'email': 'john@premiumleathers.com',
                'phone': '555-123-4567',
                'address': '123 Tannery Lane, Leatherburg, LT 12345',
                'notes': 'Excellent quality, sometimes delayed shipments',
                'status': SupplierStatus.ACTIVE.name,
                'rating': 4.5
            },
            {
                'id': 2,
                'name': 'Budget Hardware Supply',
                'contact': 'Sarah Johnson',
                'email': 'sales@budgethardware.com',
                'phone': '555-987-6543',
                'address': '456 Hardware Blvd, Buckleton, BK 67890',
                'notes': 'Good prices, variable quality',
                'status': SupplierStatus.ACTIVE.name,
                'rating': 3.5
            },
            {
                'id': 3,
                'name': 'Exotic Leathers Ltd.',
                'contact': 'Michael Wong',
                'email': 'michael@exoticleathers.com',
                'phone': '555-555-1212',
                'address': '789 Exotic Way, Hideville, HV 54321',
                'notes': 'Specialized in rare leathers, premium pricing',
                'status': SupplierStatus.ACTIVE.name,
                'rating': 4.8
            },
            {
                'id': 4,
                'name': 'Thread Masters Co.',
                'contact': 'Emily Davis',
                'email': 'emily@threadmasters.com',
                'phone': '555-222-3333',
                'address': '321 Thread Street, Sewington, SW 13579',
                'notes': 'High quality threads, good customer service',
                'status': SupplierStatus.ACTIVE.name,
                'rating': 4.2
            },
            {
                'id': 5,
                'name': 'Old Supplier LLC',
                'contact': 'Robert Brown',
                'email': 'robert@oldsupplier.com',
                'phone': '555-444-5555',
                'address': '555 Former Ave, Pastville, PV 97531',
                'notes': 'No longer in business',
                'status': SupplierStatus.INACTIVE.name,
                'rating': 2.0
            }
        ]

        for supplier in sample_suppliers:
            self.suppliers[supplier['id']] = supplier

    def _convert_to_dict(self, supplier) -> Dict[str, Any]:
        """
        Convert a Supplier model to a dictionary.

        Args:
            supplier: Supplier instance to convert

        Returns:
            Dict[str, Any]: Dictionary representation of the supplier
        """
        try:
            if isinstance(supplier, dict):
                return supplier

            return {
                "id": supplier.get("id", 0),
                "name": supplier.get("name", ""),
                "contact_name": supplier.get("contact_name", ""),
                "email": supplier.get("email", ""),
                "phone": supplier.get("phone", ""),
                "address": supplier.get("address", ""),
                "status": supplier.get("status", SupplierStatus.ACTIVE),
                "notes": supplier.get("notes", ""),
                "rating": supplier.get("rating", 0.0),
                "created_at": supplier.get("created_at", None),
                "updated_at": supplier.get("updated_at", None)
            }
        except Exception as e:
            logger.error(f"Error converting supplier to dict: {e}")
            return {"id": 0, "name": "Unknown", "status": SupplierStatus.INACTIVE}

    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """Get all suppliers.

        Returns:
            List of supplier dictionaries
        """
        self.logger.debug(f"Returning {len(self.suppliers)} suppliers")
        return list(self.suppliers.values())

    def get_supplier_by_id(self, supplier_id: int) -> Dict[str, Any]:
        """Get a supplier by ID.

        Args:
            supplier_id: ID of the supplier to retrieve

        Returns:
            Supplier dictionary

        Raises:
            NotFoundError: If supplier not found
        """
        if supplier_id not in self.suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        self.logger.debug(f"Retrieved supplier with ID {supplier_id}")
        return self.suppliers[supplier_id]

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier.

        Args:
            supplier_data: Supplier data dictionary

        Returns:
            Created supplier dictionary

        Raises:
            ValidationError: If required fields are missing
        """
        # Validate required fields
        if 'name' not in supplier_data:
            self.logger.error("Supplier name is required")
            raise ValidationError("Supplier name is required")

        # Generate new ID
        new_id = max(self.suppliers.keys() or [0]) + 1

        supplier = {
            'id': new_id,
            'name': supplier_data['name'],
            'contact': supplier_data.get('contact', ''),
            'email': supplier_data.get('email', ''),
            'phone': supplier_data.get('phone', ''),
            'address': supplier_data.get('address', ''),
            'notes': supplier_data.get('notes', ''),
            'status': supplier_data.get('status', SupplierStatus.ACTIVE.name),
            'rating': supplier_data.get('rating', 0)
        }

        self.suppliers[new_id] = supplier
        self.logger.info(f"Created new supplier with ID {new_id}")

        return supplier

    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier.

        Args:
            supplier_id: ID of the supplier to update
            supplier_data: Updated supplier data

        Returns:
            Updated supplier dictionary

        Raises:
            NotFoundError: If supplier not found
        """
        if supplier_id not in self.suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found for update")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        supplier = self.suppliers[supplier_id]

        # Update fields
        for key, value in supplier_data.items():
            if key != 'id':  # Don't update ID
                supplier[key] = value

        self.logger.info(f"Updated supplier with ID {supplier_id}")
        return supplier

    def delete_supplier(self, supplier_id: int) -> None:
        """Delete a supplier.

        Args:
            supplier_id: ID of the supplier to delete

        Raises:
            NotFoundError: If supplier not found
        """
        if supplier_id not in self.suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found for deletion")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        del self.suppliers[supplier_id]
        self.logger.info(f"Deleted supplier with ID {supplier_id}")

    def search_suppliers(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for suppliers by name, contact, or other fields.

        Args:
            search_term (str): Term to search for

        Returns:
            List[Dict[str, Any]]: List of matching suppliers
        """
        logger.info(f"Searching for suppliers with term: {search_term}")

        if not search_term:
            return self.get_all_suppliers()

        # Convert search term to lowercase for case-insensitive search
        search_term = search_term.lower()

        # Search in relevant fields
        results = []
        for supplier in self._suppliers.values():
            if (search_term in supplier.get("name", "").lower() or
                    search_term in supplier.get("contact_name", "").lower() or
                    search_term in supplier.get("email", "").lower() or
                    search_term in supplier.get("notes", "").lower()):
                results.append(supplier)

        logger.info(f"Found {len(results)} suppliers matching search term")
        return results

    def get_suppliers_by_status(self, status: SupplierStatus) -> List[Dict[str, Any]]:
        """
        Get suppliers by their status.

        Args:
            status (SupplierStatus): Status to filter suppliers

        Returns:
            List[Dict[str, Any]]: List of suppliers with the given status
        """
        logger.info(f"Getting suppliers with status: {status}")

        return [
            supplier for supplier in self._suppliers.values()
            if supplier.get("status") == status
        ]

    # Implementation of IBaseService abstract methods

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new supplier.

        Args:
            data (Dict[str, Any]): Data for creating the supplier

        Returns:
            Dict[str, Any]: Created supplier

        Raises:
            ValidationError: If data is invalid
        """
        return self.create_supplier(data)

    def get_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieve a supplier by its identifier.

        Args:
            entity_id (Any): Unique identifier for the supplier

        Returns:
            Optional[Dict[str, Any]]: Retrieved supplier or None if not found
        """
        try:
            return self.get_supplier_by_id(entity_id)
        except NotFoundError:
            return None

    def update(self, entity_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing supplier.

        Args:
            entity_id (Any): Unique identifier for the supplier
            data (Dict[str, Any]): Updated data for the supplier

        Returns:
            Dict[str, Any]: Updated supplier

        Raises:
            NotFoundError: If supplier doesn't exist
            ValidationError: If update data is invalid
        """
        return self.update_supplier(entity_id, data)

    def delete(self, entity_id: Any) -> bool:
        """
        Delete a supplier by its identifier.

        Args:
            entity_id (Any): Unique identifier for the supplier

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If supplier doesn't exist
        """
        return self.delete_supplier(entity_id)