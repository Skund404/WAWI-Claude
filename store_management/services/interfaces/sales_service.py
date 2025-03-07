# services/interfaces/sales_service.py
from abc import ABC, abstractmethod
from database.models.sales import Sales, SalesItem
from database.models.customer import Customer
from database.models.enums import SaleStatus, PaymentStatus
from datetime import datetime
from typing import Any, Dict, List, Optional

class ISalesService(ABC):
    """
    Interface for Sales Service defining core operations for sales management.
    """

    @abstractmethod
    def create_sale(
        self,
        customer_id: int,
        total_amount: float,
        items: List[Dict[str, Any]],
        status: SaleStatus = SaleStatus.PENDING,
        payment_status: PaymentStatus = PaymentStatus.PENDING
    ) -> Sales:
        """
        Create a new sales transaction.

        Args:
            customer_id: ID of the customer making the purchase
            total_amount: Total amount of the sale
            items: List of sales item details
            status: Initial sale status
            payment_status: Initial payment status

        Returns:
            Created Sales instance
        """
        pass

    @abstractmethod
    def get_sale_by_id(self, sale_id: int) -> Sales:
        """
        Retrieve a specific sales transaction.

        Args:
            sale_id: ID of the sales transaction

        Returns:
            Sales instance
        """
        pass

    @abstractmethod
    def update_sale_status(
        self,
        sale_id: int,
        status: SaleStatus
    ) -> Sales:
        """
        Update the status of a sales transaction.

        Args:
            sale_id: ID of the sales transaction
            status: New status for the sale

        Returns:
            Updated Sales instance
        """
        pass

    @abstractmethod
    def update_payment_status(
        self,
        sale_id: int,
        payment_status: PaymentStatus
    ) -> Sales:
        """
        Update the payment status of a sales transaction.

        Args:
            sale_id: ID of the sales transaction
            payment_status: New payment status

        Returns:
            Updated Sales instance
        """
        pass

    @abstractmethod
    def get_sales_by_customer(
        self,
        customer_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[SaleStatus] = None
    ) -> List[Sales]:
        """
        Retrieve sales transactions for a specific customer.

        Args:
            customer_id: ID of the customer
            start_date: Optional start date for filtering sales
            end_date: Optional end date for filtering sales
            status: Optional status to filter sales

        Returns:
            List of Sales instances
        """
        pass

    @abstractmethod
    def add_sales_item(
        self,
        sale_id: int,
        product_id: int,
        quantity: int,
        price: float
    ) -> SalesItem:
        """
        Add an item to an existing sales transaction.

        Args:
            sale_id: ID of the sales transaction
            product_id: ID of the product being sold
            quantity: Quantity of the product
            price: Price of the product

        Returns:
            Created SalesItem instance
        """
        pass

    @abstractmethod
    def remove_sales_item(
        self,
        sale_id: int,
        sales_item_id: int
    ) -> None:
        """
        Remove an item from a sales transaction.

        Args:
            sale_id: ID of the sales transaction
            sales_item_id: ID of the sales item to remove
        """
        pass

    @abstractmethod
    def calculate_total_sales(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate total sales within an optional date range.

        Args:
            start_date: Optional start date for calculation
            end_date: Optional end date for calculation

        Returns:
            Total sales amount
        """
        pass