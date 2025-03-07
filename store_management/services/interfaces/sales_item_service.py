# services/interfaces/sales_item_service.py
from abc import ABC, abstractmethod
from database.models.sales_item import SalesItem
from database.models.product import Product
from typing import List, Optional
from datetime import datetime

class ISalesItemService(ABC):
    """
    Interface for Sales Item Service defining core operations
    for managing individual sales items.
    """

    @abstractmethod
    def get_sales_item_by_id(self, sales_item_id: int) -> SalesItem:
        """
        Retrieve a specific sales item by its ID.

        Args:
            sales_item_id: ID of the sales item to retrieve

        Returns:
            SalesItem instance
        """
        pass

    @abstractmethod
    def get_sales_items_by_sale(self, sale_id: int) -> List[SalesItem]:
        """
        Retrieve all sales items for a specific sales transaction.

        Args:
            sale_id: ID of the sales transaction

        Returns:
            List of SalesItem instances
        """
        pass

    @abstractmethod
    def get_sales_items_by_product(
        self,
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SalesItem]:
        """
        Retrieve sales items for a specific product,
        optionally filtered by date range.

        Args:
            product_id: ID of the product
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            List of SalesItem instances
        """
        pass

    @abstractmethod
    def update_sales_item_quantity(
        self,
        sales_item_id: int,
        new_quantity: int
    ) -> SalesItem:
        """
        Update the quantity of a sales item.

        Args:
            sales_item_id: ID of the sales item
            new_quantity: New quantity to set

        Returns:
            Updated SalesItem instance
        """
        pass

    @abstractmethod
    def update_sales_item_price(
        self,
        sales_item_id: int,
        new_price: float
    ) -> SalesItem:
        """
        Update the price of a sales item.

        Args:
            sales_item_id: ID of the sales item
            new_price: New price to set

        Returns:
            Updated SalesItem instance
        """
        pass

    @abstractmethod
    def calculate_total_sales_for_product(
        self,
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate total sales amount for a specific product.

        Args:
            product_id: ID of the product
            start_date: Optional start date for calculation
            end_date: Optional end date for calculation

        Returns:
            Total sales amount for the product
        """
        pass

    @abstractmethod
    def delete_sales_item(self, sales_item_id: int) -> None:
        """
        Delete a specific sales item.

        Args:
            sales_item_id: ID of the sales item to delete
        """
        pass