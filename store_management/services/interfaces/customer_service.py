# services/interfaces/customer_service.py
"""
Interface for customer-related operations providing business logic for managing customers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import datetime


class CustomerStatus(Enum):
    """Status values for customer accounts."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    POTENTIAL = "potential"


class CustomerTier(Enum):
    """Tier levels for customer classification."""
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"


class CustomerSource(Enum):
    """Sources of customer acquisition."""
    WEBSITE = "website"
    RETAIL = "retail"
    REFERRAL = "referral"
    MARKETING = "marketing"
    SOCIAL_MEDIA = "social_media"
    TRADE_SHOW = "trade_show"
    WORD_OF_MOUTH = "word_of_mouth"
    EMAIL_CAMPAIGN = "email_campaign"
    OTHER = "other"


class ICustomerService(ABC):
    """
    Interface for customer management operations.
    Provides methods for creating, retrieving, updating, and deleting customer records.
    """

    @abstractmethod
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new customer record.

        Args:
            customer_data: Dictionary containing customer information

        Returns:
            Dictionary representing the created customer

        Raises:
            ValidationError: If customer data is invalid
            ServiceError: If an error occurs during creation
        """
        pass

    @abstractmethod
    def get_customer(self, customer_id: Union[str, int]) -> Dict[str, Any]:
        """
        Retrieve a customer by ID.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            Dictionary with customer information

        Raises:
            NotFoundError: If customer does not exist
            ServiceError: If an error occurs during retrieval
        """
        pass

    @abstractmethod
    def update_customer(self, customer_id: Union[str, int], customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing customer record.

        Args:
            customer_id: Unique identifier for the customer
            customer_data: Dictionary containing updated customer information

        Returns:
            Dictionary representing the updated customer

        Raises:
            NotFoundError: If customer does not exist
            ValidationError: If updated data is invalid
            ServiceError: If an error occurs during update
        """
        pass

    @abstractmethod
    def delete_customer(self, customer_id: Union[str, int]) -> bool:
        """
        Delete a customer record.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            True if deletion was successful

        Raises:
            NotFoundError: If customer does not exist
            ServiceError: If an error occurs during deletion
        """
        pass

    @abstractmethod
    def list_customers(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve a list of customers with optional filtering.

        Args:
            filters: Optional dictionary of filter criteria

        Returns:
            List of dictionaries representing customers

        Raises:
            ServiceError: If an error occurs during retrieval
        """
        pass

    @abstractmethod
    def get_customer_sales_history(self, customer_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Retrieve the sales history for a customer.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            List of dictionaries representing sales

        Raises:
            NotFoundError: If customer does not exist
            ServiceError: If an error occurs during retrieval
        """
        pass

    @abstractmethod
    def update_customer_status(self, customer_id: Union[str, int], status: CustomerStatus) -> Dict[str, Any]:
        """
        Update the status of a customer.

        Args:
            customer_id: Unique identifier for the customer
            status: New customer status

        Returns:
            Dictionary representing the updated customer

        Raises:
            NotFoundError: If customer does not exist
            ValidationError: If status is invalid
            ServiceError: If an error occurs during update
        """
        pass

    @abstractmethod
    def update_customer_tier(self, customer_id: Union[str, int], tier: CustomerTier) -> Dict[str, Any]:
        """
        Update the tier/level of a customer.

        Args:
            customer_id: Unique identifier for the customer
            tier: New customer tier

        Returns:
            Dictionary representing the updated customer

        Raises:
            NotFoundError: If customer does not exist
            ValidationError: If tier is invalid
            ServiceError: If an error occurs during update
        """
        pass

    @abstractmethod
    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for customers by name, email, or other attributes.

        Args:
            query: Search query string

        Returns:
            List of dictionaries representing matching customers

        Raises:
            ServiceError: If an error occurs during search
        """
        pass