# services/implementations/sales_item_service.py
from datetime import datetime
from typing import List, Optional

from database.models.sales_item import SalesItem
from database.models.sales import Sales
from database.models.product import Product
from database.repositories.sales_item_repository import SalesItemRepository
from database.repositories.sales_repository import SalesRepository
from database.repositories.product_repository import ProductRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.sales_item_service import ISalesItemService
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging


class SalesItemService(BaseService, ISalesItemService):
    def __init__(
            self,
            session: Optional[Session] = None,
            sales_item_repository: Optional[SalesItemRepository] = None,
            sales_repository: Optional[SalesRepository] = None,
            product_repository: Optional[ProductRepository] = None
    ):
        """
        Initialize the Sales Item Service.

        Args:
            session: SQLAlchemy database session
            sales_item_repository: Repository for sales item data access
            sales_repository: Repository for sales data access
            product_repository: Repository for product data access
        """
        self.session = session or get_db_session()
        self.sales_item_repository = sales_item_repository or SalesItemRepository(self.session)
        self.sales_repository = sales_repository or SalesRepository(self.session)
        self.product_repository = product_repository or ProductRepository(self.session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_sales_item_by_id(self, sales_item_id: int) -> SalesItem:
        """
        Retrieve a specific sales item by its ID.
        """
        try:
            sales_item = self.sales_item_repository.get_by_id(sales_item_id)
            if not sales_item:
                raise NotFoundError(f"Sales item with ID {sales_item_id} not found")
            return sales_item
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving sales item: {str(e)}")
            raise NotFoundError(f"Failed to retrieve sales item: {str(e)}")

    def get_sales_items_by_sale(self, sale_id: int) -> List[SalesItem]:
        """
        Retrieve all sales items for a specific sales transaction.
        """
        try:
            # Validate sale exists
            sale = self.sales_repository.get_by_id(sale_id)
            if not sale:
                raise NotFoundError(f"Sales transaction with ID {sale_id} not found")

            return self.sales_item_repository.get_by_sale(sale_id)
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving sales items for sale: {str(e)}")
            raise NotFoundError(f"Failed to retrieve sales items: {str(e)}")

    def get_sales_items_by_product(
            self,
            product_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[SalesItem]:
        """
        Retrieve sales items for a specific product, optionally filtered by date range.
        """
        try:
            # Validate product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            return self.sales_item_repository.get_by_product(
                product_id,
                start_date,
                end_date
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving sales items for product: {str(e)}")
            raise NotFoundError(f"Failed to retrieve sales items: {str(e)}")

    def update_sales_item_quantity(
            self,
            sales_item_id: int,
            new_quantity: int
    ) -> SalesItem:
        """
        Update the quantity of a sales item.
        """
        try:
            # Retrieve the sales item
            sales_item = self.get_sales_item_by_id(sales_item_id)

            # Use the model's built-in quantity update method
            sales_item.update_quantity(new_quantity)

            self.session.commit()

            self.logger.info(f"Updated sales item {sales_item_id} quantity to {new_quantity}")
            return sales_item

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating sales item quantity: {str(e)}")
            raise ValidationError(f"Failed to update sales item quantity: {str(e)}")

    def update_sales_item_price(
            self,
            sales_item_id: int,
            new_price: float
    ) -> SalesItem:
        """
        Update the price of a sales item.
        """
        try:
            # Retrieve the sales item
            sales_item = self.get_sales_item_by_id(sales_item_id)

            # Use the model's built-in price update method
            sales_item.update_price(new_price)

            self.session.commit()

            self.logger.info(f"Updated sales item {sales_item_id} price to {new_price}")
            return sales_item

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating sales item price: {str(e)}")
            raise ValidationError(f"Failed to update sales item price: {str(e)}")

    def calculate_total_sales_for_product(
            self,
            product_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate total sales amount for a specific product.
        """
        try:
            # Validate product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Use repository method to calculate total sales
            return self.sales_item_repository.calculate_total_sales_for_product(
                product_id,
                start_date,
                end_date
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating total sales for product: {str(e)}")
            raise NotFoundError(f"Failed to calculate total sales: {str(e)}")

    def delete_sales_item(self, sales_item_id: int) -> None:
        """
        Delete a specific sales item.
        """
        try:
            # Retrieve the sales item
            sales_item = self.get_sales_item_by_id(sales_item_id)

            # Delete the sales item and recalculate sale total
            sale = sales_item.sale
            self.session.delete(sales_item)

            if sale:
                # Recalculate total amount for the associated sale
                sale.calculate_total_amount()

            self.session.commit()

            self.logger.info(f"Deleted sales item {sales_item_id}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting sales item: {str(e)}")
            raise ValidationError(f"Failed to delete sales item: {str(e)}")