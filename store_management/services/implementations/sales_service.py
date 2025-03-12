# services/implementations/sales_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from database.repositories.sales_repository import SalesRepository
from database.repositories.customer_repository import CustomerRepository
from database.repositories.product_repository import ProductRepository
from database.models.enums import SaleStatus, PaymentStatus

from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError, BusinessRuleError
from services.dto.sales_dto import SalesDTO, SalesItemDTO
from services.interfaces.sales_service import ISalesService

from di.inject import inject


class SalesService(BaseService, ISalesService):
    """Implementation of the sales service interface."""

    @inject
    def __init__(self, session: Session,
                 sales_repository: Optional[SalesRepository] = None,
                 customer_repository: Optional[CustomerRepository] = None,
                 product_repository: Optional[ProductRepository] = None):
        """Initialize the sales service.

        Args:
            session: SQLAlchemy database session
            sales_repository: Optional SalesRepository instance
            customer_repository: Optional CustomerRepository instance
            product_repository: Optional ProductRepository instance
        """
        super().__init__(session)
        self.sales_repository = sales_repository or SalesRepository(session)
        self.customer_repository = customer_repository or CustomerRepository(session)
        self.product_repository = product_repository or ProductRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, sales_id: int) -> Dict[str, Any]:
        """Get sale by ID.

        Args:
            sales_id: ID of the sale to retrieve

        Returns:
            Dict representing the sale

        Raises:
            NotFoundError: If sale not found
        """
        try:
            # Retrieve sales with full details including items
            sales_data = self.sales_repository.get_sales_with_items(sales_id)

            # Convert to DTO format
            return SalesDTO.from_model(sales_data,
                                       include_items=True,
                                       include_customer=True).to_dict()
        except Exception as e:
            self.logger.error(f"Error retrieving sale {sales_id}: {str(e)}")
            raise NotFoundError(f"Sale with ID {sales_id} not found")

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all sales, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing sales
        """
        try:
            # Use sales repository to get filtered sales
            sales_list = self.sales_repository.get_all(filters)
            return [SalesDTO.from_model(sale).to_dict() for sale in sales_list]
        except Exception as e:
            self.logger.error(f"Error retrieving sales: {str(e)}")
            raise

    def create(self, sales_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sale.

        Args:
            sales_data: Dict containing sale properties

        Returns:
            Dict representing the created sale

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate sales data
            self._validate_sales_data(sales_data)

            # Set default status if not provided
            if 'status' not in sales_data:
                sales_data['status'] = SaleStatus.QUOTE_REQUEST.value

            # Set default payment status if not provided
            if 'payment_status' not in sales_data:
                sales_data['payment_status'] = PaymentStatus.PENDING.value

            # Handle items separately
            items = sales_data.pop('items', []) if 'items' in sales_data else []

            # Create sale
            with self.transaction():
                # Create sale without items first
                sale = self.sales_repository.create(sales_data)

                # Add items if provided
                for item_data in items:
                    item_data['sales_id'] = sale.id
                    self._validate_sales_item_data(item_data)
                    self.sales_repository.add_item_to_sales(sale.id, item_data)

                # Get the complete sale with items
                result = self.sales_repository.get_sales_with_items(sale.id)
                return SalesDTO.from_model(result,
                                           include_items=True,
                                           include_customer=True).to_dict()
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating sale: {str(e)}")
            raise ValidationError(f"Failed to create sale: {str(e)}")

    def update(self, sales_id: int, sales_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing sale.

        Args:
            sales_id: ID of the sale to update
            sales_data: Dict containing updated sale properties

        Returns:
            Dict representing the updated sale

        Raises:
            NotFoundError: If sale not found
            ValidationError: If validation fails
        """
        try:
            # Check if sale exists
            existing_sale = self.sales_repository.get_by_id(sales_id)
            if not existing_sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Validate sales data
            self._validate_sales_data(sales_data, update=True)

            # Update sale
            with self.transaction():
                updated_sale = self.sales_repository.update(sales_id, sales_data)

                # Get updated sale with items
                result = self.sales_repository.get_sales_with_items(sales_id)
                return SalesDTO.from_model(result,
                                           include_items=True,
                                           include_customer=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating sale {sales_id}: {str(e)}")
            raise ValidationError(f"Failed to update sale: {str(e)}")

    def delete(self, sales_id: int) -> bool:
        """Delete a sale by ID.

        Args:
            sales_id: ID of the sale to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale not found
            BusinessRuleError: If sale cannot be deleted
        """
        try:
            # Check if sale exists
            existing_sale = self.sales_repository.get_by_id(sales_id)
            if not existing_sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Prevent deleting processed sales
            if existing_sale.status not in [SaleStatus.QUOTE_REQUEST.value, SaleStatus.DRAFT.value]:
                raise BusinessRuleError(f"Cannot delete sale with status {existing_sale.status}")

            # Delete sale
            with self.transaction():
                return self.sales_repository.delete(sales_id)
        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting sale {sales_id}: {str(e)}")
            raise BusinessRuleError(f"Failed to delete sale: {str(e)}")

    def add_item(self, sales_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add item to a sale.

        Args:
            sales_id: ID of the sale
            item_data: Dict containing item properties

        Returns:
            Dict representing the created sales item

        Raises:
            NotFoundError: If sale or product not found
            ValidationError: If validation fails
        """
        try:
            # Validate sale exists
            existing_sale = self.sales_repository.get_by_id(sales_id)
            if not existing_sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Validate sales status
            if existing_sale.status not in [SaleStatus.DRAFT.value, SaleStatus.QUOTE_REQUEST.value]:
                raise BusinessRuleError(f"Cannot add items to sale with status {existing_sale.status}")

            # Validate item data
            self._validate_sales_item_data(item_data)

            # Add item to sale
            with self.transaction():
                item = self.sales_repository.add_item_to_sales(sales_id, item_data)

                # Return formatted item
                return SalesItemDTO.from_model(item, include_product=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding item to sale {sales_id}: {str(e)}")
            raise ValidationError(f"Failed to add item to sale: {str(e)}")

    def remove_item(self, sales_id: int, item_id: int) -> bool:
        """Remove item from a sale.

        Args:
            sales_id: ID of the sale
            item_id: ID of the item

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale or item not found
        """
        try:
            # Validate sale exists
            existing_sale = self.sales_repository.get_by_id(sales_id)
            if not existing_sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Validate sales status
            if existing_sale.status not in [SaleStatus.DRAFT.value, SaleStatus.QUOTE_REQUEST.value]:
                raise BusinessRuleError(f"Cannot remove items from sale with status {existing_sale.status}")

            # Remove item from sale
            with self.transaction():
                self.sales_repository.remove_item_from_sales(sales_id, item_id)
                return True
        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error removing item {item_id} from sale {sales_id}: {str(e)}")
            raise NotFoundError(f"Failed to remove item from sale: {str(e)}")

    def update_item(self, sales_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update item in a sale.

        Args:
            sales_id: ID of the sale
            item_id: ID of the item
            item_data: Dict containing updated item properties

        Returns:
            Dict representing the updated item

        Raises:
            NotFoundError: If sale or item not found
            ValidationError: If validation fails
        """
        try:
            # Validate sale exists
            existing_sale = self.sales_repository.get_by_id(sales_id)
            if not existing_sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Validate sales status
            if existing_sale.status not in [SaleStatus.DRAFT.value, SaleStatus.QUOTE_REQUEST.value]:
                raise BusinessRuleError(f"Cannot update items for sale with status {existing_sale.status}")

            # Validate item data
            self._validate_sales_item_data(item_data, update=True)

            # Update item
            with self.transaction():
                updated_item = self.sales_repository.update_sales_item(sales_id, item_id, item_data)

                # Return formatted item
                return SalesItemDTO.from_model(updated_item, include_product=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating item {item_id} in sale {sales_id}: {str(e)}")
            raise ValidationError(f"Failed to update item in sale: {str(e)}")

    def update_status(self, sales_id: int, status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Update sale status.

        Args:
            sales_id: ID of the sale
            status: New status
            notes: Optional notes for status change

        Returns:
            Dict representing the updated sale

        Raises:
            NotFoundError: If sale not found
            ValidationError: If validation fails
        """
        try:
            # Validate status
            if not hasattr(SaleStatus, status):
                raise ValidationError(f"Invalid sale status: {status}")

            # Update sale status
            with self.transaction():
                updated_sale = self.sales_repository.update_sales_status(
                    sales_id,
                    SaleStatus[status],
                    notes
                )

                # Convert to DTO
                return SalesDTO.from_model(updated_sale,
                                           include_items=True,
                                           include_customer=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating status for sale {sales_id}: {str(e)}")
            raise ValidationError(f"Failed to update sale status: {str(e)}")

    def update_payment_status(self, sales_id: int, payment_status: str,
                              payment_amount: Optional[float] = None,
                              payment_notes: Optional[str] = None) -> Dict[str, Any]:
        """Update sale payment status.

        Args:
            sales_id: ID of the sale
            payment_status: New payment status
            payment_amount: Optional payment amount
            payment_notes: Optional notes for payment

        Returns:
            Dict representing the updated sale

        Raises:
            NotFoundError: If sale not found
            ValidationError: If validation fails
        """
        try:
            # Validate payment status
            if not hasattr(PaymentStatus, payment_status):
                raise ValidationError(f"Invalid payment status: {payment_status}")

            # Update payment status
            with self.transaction():
                updated_sale = self.sales_repository.update_payment_status(
                    sales_id,
                    PaymentStatus[payment_status],
                    payment_amount,
                    payment_notes
                )

                # Convert to DTO
                return SalesDTO.from_model(updated_sale,
                                           include_items=True,
                                           include_customer=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating payment status for sale {sales_id}: {str(e)}")
            raise ValidationError(f"Failed to update sale payment status: {str(e)}")

    def get_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get sales by customer ID.

        Args:
            customer_id: ID of the customer

        Returns:
            List of sales for the specified customer
        """
        try:
            # Validate customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Get sales for customer
            sales_list = self.sales_repository.get_by_customer(customer_id)
            return [SalesDTO.from_model(sale).to_dict() for sale in sales_list]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving sales for customer {customer_id}: {str(e)}")
            raise

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get sales within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of sales within the specified date range
        """
        try:
            # Get sales for the date range
            sales_list = self.sales_repository.get_by_date_range(start_date, end_date)
            return [SalesDTO.from_model(sale).to_dict() for sale in sales_list]
        except Exception as e:
            self.logger.error(f"Error retrieving sales between {start_date} and {end_date}: {str(e)}")
            raise

    def calculate_total(self, sales_id: int) -> float:
        """Calculate total amount for a sale.

        Args:
            sales_id: ID of the sale

        Returns:
            Total amount

        Raises:
            NotFoundError: If sale not found
        """
        try:
            # Get sale with items
            sales_data = self.sales_repository.get_sales_with_items(sales_id)

            # Calculate total from sales items
            total = sum(
                item.get('price', 0) * item.get('quantity', 0)
                for item in sales_data.get('items', [])
            )

            return total
        except Exception as e:
            self.logger.error(f"Error calculating total for sale {sales_id}: {str(e)}")
            raise NotFoundError(f"Sale with ID {sales_id} not found")

    def generate_sales_report(self,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive sales report.

        Args:
            start_date: Optional start date for the report
            end_date: Optional end date for the report

        Returns:
            Dictionary with sales report details
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=90)  # Default to last 90 days

            # Get sales by period (monthly breakdown)
            sales_by_month = self.sales_repository.get_sales_by_period('month', start_date, end_date)

            # Get product sales analysis
            product_sales = self.sales_repository.get_product_sales_analysis(start_date, end_date)

            # Aggregate summary data
            total_sales = sum(month['total_sales'] for month in sales_by_month)
            total_orders = sum(month['order_count'] for month in sales_by_month)

            # Prepare detailed report
            return {
                'report_period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_sales': total_sales,
                    'total_orders': total_orders,
                    'average_order_value': total_sales / total_orders if total_orders > 0 else 0
                },
                'sales_by_month': sales_by_month,
                'product_sales': product_sales
            }
        except Exception as e:
            self.logger.error(f"Error generating sales report: {str(e)}")
            raise

    def filter_sales(self,
                     search_term: Optional[str] = None,
                     customer_id: Optional[int] = None,
                     statuses: Optional[List[str]] = None,
                     payment_statuses: Optional[List[str]] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None,
                     sort_by: str = 'created_at',
                     sort_dir: str = 'desc',
                     page: int = 1,
                     page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate sales.

        Args:
            search_term: Optional search term
            customer_id: Optional customer ID to filter by
            statuses: Optional list of statuses to filter by
            payment_statuses: Optional list of payment statuses to filter by
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            page: Page number
            page_size: Page size

        Returns:
            Dict with paginated results and metadata
        """
        try:
            # Convert status strings to enum values if provided
            if statuses:
                statuses = [SaleStatus[status] for status in statuses]

            if payment_statuses:
                payment_statuses = [PaymentStatus[status] for status in payment_statuses]

            # Use repository method for filtering
            filtered_sales = self.sales_repository.filter_sales_for_gui(
                search_term=search_term,
                customer_id=customer_id,
                statuses=statuses,
                payment_statuses=payment_statuses,
                start_date=start_date,
                end_date=end_date,
                sort_by=sort_by,
                sort_dir=sort_dir,
                page=page,
                page_size=page_size
            )

            # Convert to DTO
            filtered_sales['items'] = [
                SalesDTO.from_model(sale, include_items=False, include_customer=True).to_dict()
                for sale in filtered_sales['items']
            ]

            return filtered_sales
        except Exception as e:
            self.logger.error(f"Error filtering sales: {str(e)}")
            raise

    def export_sales_data(self,
                          format: str = "csv",
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Export sales data to specified format.

        Args:
            format: Export format ("csv" or "json")
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dict with export data and metadata
        """
        try:
            # Use repository export method
            export_data = self.sales_repository.export_sales_data(
                format=format,
                start_date=start_date,
                end_date=end_date
            )

            # Convert sales to DTO format
            export_data['data'] = [
                SalesDTO.from_model(sale, include_items=True, include_customer=True).to_dict()
                for sale in export_data['data']
            ]

            return export_data
        except Exception as e:
            self.logger.error(f"Error exporting sales data: {str(e)}")
            raise

    def _validate_sales_data(self, sales_data: Dict[str, Any], update: bool = False) -> None:
        """Validate sales data.

        Args:
            sales_data: Sales data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Validate customer ID if provided
        if 'customer_id' in sales_data:
            customer_id = sales_data['customer_id']
            if customer_id:
                try:
                    self.customer_repository.get_by_id(customer_id)
                except Exception:
                    raise ValidationError(f"Customer with ID {customer_id} not found")

        # Validate status if provided
        if 'status' in sales_data:
            status = sales_data['status']
            if not hasattr(SaleStatus, status):
                raise ValidationError(f"Invalid sale status: {status}")

        # Validate payment status if provided
        if 'payment_status' in sales_data:
            payment_status = sales_data['payment_status']
            if not hasattr(PaymentStatus, payment_status):
                raise ValidationError(f"Invalid payment status: {payment_status}")

        # Validate total amount
        if 'total_amount' in sales_data:
            total_amount = sales_data['total_amount']
            if not isinstance(total_amount, (int, float)) or total_amount < 0:
                raise ValidationError("Total amount must be a non-negative number")

    def _validate_sales_item_data(self, item_data: Dict[str, Any], update: bool = False) -> None:
        """Validate sales item data.

        Args:
            item_data: Sales item data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields for new items
        if not update:
            required_fields = ['product_id', 'quantity', 'price']
            for field in required_fields:
                if field not in item_data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate product if provided
        if 'product_id' in item_data:
            product_id = item_data['product_id']
            try:
                self.product_repository.get_by_id(product_id)
            except Exception:
                raise ValidationError(f"Product with ID {product_id} not found")

        # Validate quantity
        if 'quantity' in item_data:
            quantity = item_data['quantity']
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                raise ValidationError("Quantity must be a positive number")

        # Validate price
        if 'price' in item_data:
            price = item_data['price']
            if not isinstance(price, (int, float)) or price < 0:
                raise ValidationError("Price cannot be negative")