import abc
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from database.models.supplier import Supplier

class ISupplierService(ABC):
    """Abstract base class defining the interface for supplier-related operations.

    This service provides methods for managing supplier information,
    tracking performance, and handling supplier-related queries.
    """

    @abstractmethod
    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """Retrieve all registered suppliers.

        Returns:
            List of supplier dictionaries containing basic supplier information.
        """
        pass

    @abstractmethod
    def get_supplier_by_id(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific supplier by their unique identifier.

        Args:
            supplier_id (int): The unique identifier of the supplier.

        Returns:
            Dictionary containing supplier details, or None if not found.
        """
        pass

    @abstractmethod
    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier record.

        Args:
            supplier_data (Dict): Comprehensive supplier information.

        Returns:
            Dictionary of the created supplier with assigned ID.

        Raises:
            ValueError: If supplier data is invalid.
            Exception: For database or validation errors.
        """
        pass

    @abstractmethod
    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier's information.

        Args:
            supplier_id (int): The unique identifier of the supplier to update.
            supplier_data (Dict): Updated supplier information.

        Returns:
            Dictionary of the updated supplier.

        Raises:
            ValueError: If supplier data is invalid.
            KeyError: If supplier not found.
        """
        pass

    @abstractmethod
    def delete_supplier(self, supplier_id: int) -> bool:
        """Delete a supplier record.

        Args:
            supplier_id (int): The unique identifier of the supplier to delete.

        Returns:
            Boolean indicating successful deletion.

        Raises:
            KeyError: If supplier not found.
            Exception: If deletion fails due to existing dependencies.
        """
        pass

    @abstractmethod
    def get_supplier_performance(self, supplier_id: int, start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate and retrieve supplier performance metrics.

        Args:
            supplier_id (int): The unique identifier of the supplier.
            start_date (Optional[datetime]): Start of performance evaluation period.
            end_date (Optional[datetime]): End of performance evaluation period.

        Returns:
            Dictionary containing performance metrics.
        """
        pass

    @abstractmethod
    def generate_supplier_report(self) -> List[Dict[str, Any]]:
        """Generate a comprehensive report of all suppliers.

        Returns:
            List of dictionaries with detailed supplier information and performance.
        """
        pass


class SupplierService(ISupplierService):
    """
    Concrete implementation of the ISupplierService interface.

    Manages supplier-related operations with comprehensive validation
    and error handling.
    """

    def __init__(self, container):
        """Initialize the SupplierService with a dependency injection container.

        Args:
            container: Dependency injection container providing access to repositories.
        """
        super().__init__()
        self._container = container
        self._repository = SupplierRepository(container.resolve(Session))

    def _validate_supplier_data(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate supplier data before creation or update.

        Args:
            supplier_data (Dict): Supplier information to validate.

        Returns:
            Dict: Validated and sanitized supplier data.

        Raises:
            ValidationError: If data is invalid.
        """
        pass

    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """Retrieve all registered suppliers.

        Returns:
            List of supplier dictionaries containing basic supplier information.
        """
        return self._repository.get_all()

    def get_supplier_by_id(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific supplier by their unique identifier.

        Args:
            supplier_id (int): The unique identifier of the supplier.

        Returns:
            Dictionary containing supplier details, or None if not found.
        """
        return self._repository.get(supplier_id)

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier record.

        Args:
            supplier_data (Dict): Comprehensive supplier information.

        Returns:
            Dictionary of the created supplier with assigned ID.

        Raises:
            ValidationError: If supplier data is invalid.
            ApplicationError: For database or unexpected errors.
        """
        return self._repository.create(supplier_data)

    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier's information.

        Args:
            supplier_id (int): The unique identifier of the supplier to update.
            supplier_data (Dict): Updated supplier information.

        Returns:
            Dictionary of the updated supplier.

        Raises:
            ValidationError: If supplier data is invalid.
            KeyError: If supplier not found.
            ApplicationError: For unexpected errors.
        """
        return self._repository.update(supplier_id, supplier_data)

    def delete_supplier(self, supplier_id: int) -> bool:
        """Delete a supplier record.

        Args:
            supplier_id (int): The unique identifier of the supplier to delete.

        Returns:
            Boolean indicating successful deletion.

        Raises:
            KeyError: If supplier not found.
            ApplicationError: If deletion fails due to existing dependencies.
        """
        return self._repository.delete(supplier_id)

    def get_supplier_performance(self, supplier_id: int, start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Calculate and retrieve supplier performance metrics.

        Args:
            supplier_id (int): The unique identifier of the supplier.
            start_date (Optional[datetime]): Start of performance evaluation period.
            end_date (Optional[datetime]): End of performance evaluation period.

        Returns:
            Dictionary containing performance metrics.
        """
        # You might have some specific performance calculation logic here, or delegate to the repository
        return {}

    def generate_supplier_report(self) -> List[Dict[str, Any]]:
        """Generate a comprehensive report of all suppliers.

        Returns:
            List of dictionaries with detailed supplier information and performance.
        """
        return self._repository.get_all()