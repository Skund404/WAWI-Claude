# Path: store_management/services/implementations/supplier_service.py
from typing import List, Optional, Dict, Any

from di.service import Service
from di.container import DependencyContainer
from services.interfaces.supplier_service import ISupplierService
from database.sqlalchemy.core.specialized.supplier_manager import SupplierManager


class SupplierService(Service, ISupplierService):
    """
    Concrete implementation of the ISupplierService interface.

    Provides methods for managing supplier-related operations using the SupplierManager.
    """

    def __init__(self, container: DependencyContainer):
        """
        Initialize the SupplierService with a dependency container.

        Args:
            container: Dependency injection container
        """
        super().__init__(container)
        self.supplier_manager = self.get_dependency(SupplierManager)

    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """
        Retrieve all suppliers.

        Returns:
            List of dictionaries containing supplier information
        """
        try:
            suppliers = self.supplier_manager.get_all()
            return [self._to_dict(supplier) for supplier in suppliers]
        except Exception as e:
            # Log the error and re-raise or handle as needed
            print(f"Error retrieving suppliers: {e}")
            return []

    def get_supplier_by_id(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a supplier by their ID.

        Args:
            supplier_id: The unique identifier of the supplier

        Returns:
            Dictionary containing supplier information or None if not found
        """
        try:
            supplier = self.supplier_manager.get(supplier_id)
            return self._to_dict(supplier) if supplier else None
        except Exception as e:
            print(f"Error retrieving supplier {supplier_id}: {e}")
            return None

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new supplier.

        Args:
            supplier_data: Dictionary containing the new supplier's information

        Returns:
            Dictionary containing the created supplier's information
        """
        try:
            new_supplier = self.supplier_manager.create(supplier_data)
            return self._to_dict(new_supplier)
        except Exception as e:
            print(f"Error creating supplier: {e}")
            return None

    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing supplier's information.

        Args:
            supplier_id: The unique identifier of the supplier to update
            supplier_data: Dictionary containing the updated supplier information

        Returns:
            Updated supplier information or None if update fails
        """
        try:
            updated_supplier = self.supplier_manager.update(supplier_id, supplier_data)
            return self._to_dict(updated_supplier)
        except Exception as e:
            print(f"Error updating supplier {supplier_id}: {e}")
            return None

    def delete_supplier(self, supplier_id: int) -> bool:
        """
        Delete a supplier by their ID.

        Args:
            supplier_id: The unique identifier of the supplier to delete

        Returns:
            True if the supplier was successfully deleted, False otherwise
        """
        try:
            result = self.supplier_manager.delete(supplier_id)
            return result
        except Exception as e:
            print(f"Error deleting supplier {supplier_id}: {e}")
            return False

    def _to_dict(self, supplier):
        """
        Convert a supplier model to a dictionary.

        Args:
            supplier: Supplier model instance

        Returns:
            Dictionary representation of the supplier
        """
        if not supplier:
            return {}

        return {
            'id': supplier.id,
            'name': getattr(supplier, 'name', ''),
            'contact_name': getattr(supplier, 'contact_name', ''),
            'email': getattr(supplier, 'email', ''),
            'phone': getattr(supplier, 'phone', ''),
            'address': getattr(supplier, 'address', ''),
            'rating': getattr(supplier, 'rating', None),
            'notes': getattr(supplier, 'notes', ''),
            'created_at': str(getattr(supplier, 'created_at', '')),
            'updated_at': str(getattr(supplier, 'updated_at', ''))
        }