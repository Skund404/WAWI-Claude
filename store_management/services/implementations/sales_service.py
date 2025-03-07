# services/implementations/sales_service.py
from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.models.customer import Customer
from database.models.product import Product
from database.models.enums import SaleStatus, PaymentStatus
from database.repositories.sales_repository import SalesRepository
from database.repositories.sales_item_repository import SalesItemRepository
from database.repositories.customer_repository import CustomerRepository
from database.repositories.product_repository import ProductRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.sales_service import ISalesService
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import uuid


class SalesService(BaseService, ISalesService):
    def __init__(
            self,
            session: Optional[Session] = None,
            sales_repository: Optional[SalesRepository] = None,
            sales_item_repository: Optional[SalesItemRepository] = None,
            customer_repository: Optional[CustomerRepository] = None,
            product_repository: Optional[ProductRepository] = None
    ):
        """
        Initialize the Sales Service.

        Args:
            session: SQLAlchemy database session
            sales_repository: Repository for sales data access
            sales_item_repository: Repository for sales item data access
            customer_repository: Repository for customer data access
            product_repository: Repository for product data access
        """
        self.session = session or get_db_session()
        self.sales_repository = sales_repository or SalesRepository(self.session)
        self.sales_item_repository = sales_item_repository or SalesItemRepository(self.session)
        self.customer_repository = customer_repository or CustomerRepository(self.session)
        self.product_repository = product_repository or ProductRepository(self.session)
        self.logger = logging.getLogger(self.__class__.__name__)

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
        """
        try:
            # Validate customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise ValidationError(f"Customer with ID {customer_id} not found")

            # Generate a unique sales identifier
            sales_uuid = str(uuid.uuid4())

            # Create sales transaction
            sale = Sales(
                customer_id=customer_id,
                total_amount=total_amount,
                status=status,
                payment_status=payment_status,
                created_at=datetime.now(),
                sales_uuid=sales_uuid
            )
            self.session.add(sale)
            self.session.flush()  # To get the generated ID

            # Add sales items
            sales_items = []
            for item in items:
                # Validate product exists
                product = self.product_repository.get_by_id(item['product_id'])
                if not product:
                    raise ValidationError(f"Product with ID {item['product_id']} not found")

                # Use the model's validation during initialization
                sales_item = SalesItem(
                    sales_id=sale.id,
                    product_id=item['product_id'],
                    quantity=item.get('quantity', 1),
                    price=item['price']
                )
                self.session.add(sales_item)
                sales_items.append(sales_item)

            # Use the Sales model's method to calculate total amount if available
            sale.calculate_total_amount()

            self.session.commit()

            self.logger.info(f"Created sales transaction {sale.id} for customer {customer_id}")
            return sale

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating sales transaction: {str(e)}")
            raise ValidationError(f"Failed to create sales transaction: {str(e)}")

    def get_sale_by_id(self, sale_id: int) -> Sales:
        """
        Retrieve a specific sales transaction.
        """
        try:
            sale = self.sales_repository.get_by_id(sale_id)
            if not sale:
                raise NotFoundError(f"Sales transaction with ID {sale_id} not found")
            return sale
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving sales transaction: {str(e)}")
            raise NotFoundError(f"Failed to retrieve sales transaction: {str(e)}")

    def update_sale_status(
            self,
            sale_id: int,
            status: SaleStatus
    ) -> Sales:
        """
        Update the status of a sales transaction.
        """
        try:
            sale = self.get_sale_by_id(sale_id)
            sale.status = status
            self.session.commit()

            self.logger.info(f"Updated sales transaction {sale_id} status to {status}")
            return sale

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating sales transaction status: {str(e)}")
            raise ValidationError(f"Failed to update sales transaction status: {str(e)}")

    def update_payment_status(
            self,
            sale_id: int,
            payment_status: PaymentStatus
    ) -> Sales:
        """
        Update the payment status of a sales transaction.
        """
        try:
            sale = self.get_sale_by_id(sale_id)
            sale.payment_status = payment_status
            self.session.commit()

            self.logger.info(f"Updated sales transaction {sale_id} payment status to {payment_status}")
            return sale

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating sales transaction payment status: {str(e)}")
            raise ValidationError(f"Failed to update sales transaction payment status: {str(e)}")

    def get_sales_by_customer(
            self,
            customer_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            status: Optional[SaleStatus] = None
    ) -> List[Sales]:
        """
        Retrieve sales transactions for a specific customer.
        """
        try:
            # Validate customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            return self.sales_repository.get_by_customer(
                customer_id,
                start_date,
                end_date,
                status
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving sales for customer: {str(e)}")
            raise NotFoundError(f"Failed to retrieve sales: {str(e)}")

    def add_sales_item(
            self,
            sale_id: int,
            product_id: int,
            quantity: int,
            price: float
    ) -> SalesItem:
        """
        Add an item to an existing sales transaction.
        """
        try:
            # Validate sale exists
            sale = self.get_sale_by_id(sale_id)

            # Validate product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise ValidationError(f"Product with ID {product_id} not found")

            # Create sales item using the model's validation
            sales_item = SalesItem(
                sales_id=sale_id,
                product_id=product_id,
                quantity=quantity,
                price=price
            )
            self.session.add(sales_item)

            # Use Sales model's method to recalculate total amount
            sale.calculate_total_amount()

            self.session.commit()

            self.logger.info(f"Added sales item to transaction {sale_id}")
            return sales_item

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error adding sales item: {str(e)}")
            raise ValidationError(f"Failed to add sales item: {str(e)}")

    def remove_sales_item(
            self,
            sale_id: int,
            sales_item_id: int
    ) -> None:
        """
        Remove an item from a sales transaction.
        """
        try:
            # Validate sale exists
            sale = self.get_sale_by_id(sale_id)

            # Find the sales item
            sales_item = self.sales_item_repository.get_by_id(sales_item_id)
            if not sales_item or sales_item.sales_id != sale_id:
                raise NotFoundError(f"Sales item {sales_item_id} not found in sale {sale_id}")

            # Remove the sales item
            self.session.delete(sales_item)

            # Recalculate total amount
            sale.calculate_total_amount()

            self.session.commit()

            self.logger.info(f"Removed sales item {sales_item_id} from transaction {sale_id}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing sales item: {str(e)}")
            raise ValidationError(f"Failed to remove sales item: {str(e)}")

    def calculate_total_sales(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate total sales within an optional date range.
        """
        try:
            return self.sales_repository.calculate_total_sales(start_date, end_date)
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating total sales: {str(e)}")
            raise NotFoundError(f"Failed to calculate total sales: {str(e)}")