# services/interfaces/customer_service.py
# Protocol definition for customer service

from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class ICustomerService(Protocol):
    """Interface for customer-related operations."""

    def get_by_id(self, customer_id: int) -> Dict[str, Any]:
        """Get customer by ID.

        Args:
            customer_id: ID of the customer to retrieve

        Returns:
            Dict representing the customer

        Raises:
            NotFoundError: If customer not found
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all customers, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing customers
        """
        ...

    def create(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer.

        Args:
            customer_data: Dict containing customer properties

        Returns:
            Dict representing the created customer

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update(self, customer_id: int, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing customer.

        Args:
            customer_id: ID of the customer to update
            customer_data: Dict containing updated customer properties

        Returns:
            Dict representing the updated customer

        Raises:
            NotFoundError: If customer not found
            ValidationError: If validation fails
        """
        ...

    def delete(self, customer_id: int) -> bool:
        """Delete a customer by ID.

        Args:
            customer_id: ID of the customer to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If customer not found
        """
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for customers by name, email, or other properties.

        Args:
            query: Search query string

        Returns:
            List of customers matching the search query
        """
        ...

    def get_sales_history(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get sales history for a customer.

        Args:
            customer_id: ID of the customer

        Returns:
            List of sales for the customer

        Raises:
            NotFoundError: If customer not found
        """
        ...

    def get_project_history(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get project history for a customer.

        Args:
            customer_id: ID of the customer

        Returns:
            List of projects for the customer

        Raises:
            NotFoundError: If customer not found
        """
        ...

    def update_status(self, customer_id: int, status: str) -> Dict[str, Any]:
        """Update customer status.

        Args:
            customer_id: ID of the customer
            status: New status

        Returns:
            Dict representing the updated customer

        Raises:
            NotFoundError: If customer not found
            ValidationError: If validation fails
        """
        ...

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get customers by status.

        Args:
            status: Status to filter by

        Returns:
            List of customers with the specified status
        """
        ...

    def get_by_tier(self, tier: str) -> List[Dict[str, Any]]:
        """Get customers by tier.

        Args:
            tier: Tier to filter by

        Returns:
            List of customers with the specified tier
        """
        ...