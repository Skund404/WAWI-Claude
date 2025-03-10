from typing import Protocol, Dict, List, Optional, Union
from datetime import datetime

from database.models.enums import (
    CustomerStatus,
    CustomerTier,
    CustomerSource,
    SaleStatus,
    PaymentStatus
)


class ICustomerService(Protocol):
    """
    Comprehensive interface for Customer Service operations.
    Defines the contract for customer-related business logic across the system.
    """

    def create_customer(self, **kwargs) -> Dict:
        """
        Create a new customer with comprehensive details.

        Args:
            **kwargs: Detailed customer information

        Returns:
            Dict: Created customer information
        """
        ...

    def update_customer(self, customer_id: int, **kwargs) -> Dict:
        """
        Update an existing customer's information.

        Args:
            customer_id: Unique identifier for the customer
            **kwargs: Customer details to update

        Returns:
            Dict: Updated customer information
        """
        ...

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """
        Retrieve comprehensive customer details by ID.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            Detailed customer information including sales history, projects, etc.
        """
        ...

    def list_customers(
            self,
            status: Optional[CustomerStatus] = None,
            tier: Optional[CustomerTier] = None,
            source: Optional[CustomerSource] = None,
            min_total_sales: Optional[float] = None,
            date_range: Optional[tuple[datetime, datetime]] = None
    ) -> List[Dict]:
        """
        Advanced customer listing with multiple filtering options.

        Args:
            status: Filter by customer status
            tier: Filter by customer tier
            source: Filter by customer source
            min_total_sales: Minimum total sales amount
            date_range: Date range for customer activity

        Returns:
            List of customer details with advanced filtering
        """
        ...

    def delete_customer(self, customer_id: int) -> bool:
        """
        Soft or hard delete a customer.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            Boolean indicating successful deletion
        """
        ...

    def validate_customer_data(self, customer_data: Dict) -> bool:
        """
        Comprehensive validation of customer data.

        Args:
            customer_data: Customer information to validate

        Returns:
            Boolean indicating data validity
        """
        ...

    def get_customer_sales_history(
            self,
            customer_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            status: Optional[SaleStatus] = None,
            payment_status: Optional[PaymentStatus] = None
    ) -> List[Dict]:
        """
        Retrieve a customer's sales history with detailed filtering.

        Args:
            customer_id: Unique identifier for the customer
            start_date: Optional start date for sales history
            end_date: Optional end date for sales history
            status: Optional sales status filter
            payment_status: Optional payment status filter

        Returns:
            List of sales records for the customer
        """
        ...

    def calculate_customer_lifetime_value(self, customer_id: int) -> float:
        """
        Calculate the total lifetime value of a customer.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            Total lifetime sales value
        """
        ...

    def update_customer_tier(self, customer_id: int) -> CustomerTier:
        """
        Automatically update customer tier based on sales history.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            Updated customer tier
        """
        ...

    def get_customer_projects(
            self,
            customer_id: int,
            include_completed: bool = False
    ) -> List[Dict]:
        """
        Retrieve projects associated with a customer.

        Args:
            customer_id: Unique identifier for the customer
            include_completed: Whether to include completed projects

        Returns:
            List of customer's projects
        """
        ...