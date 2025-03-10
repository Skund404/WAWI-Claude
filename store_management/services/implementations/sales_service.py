# services/implementations/sales_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.sales_repository import SalesRepository
from database.repositories.sales_item_repository import SalesItemRepository
from database.repositories.customer_repository import CustomerRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.project_repository import ProjectRepository
from database.repositories.inventory_repository import InventoryRepository
from database.models.enums import SaleStatus, PaymentStatus, InventoryStatus, TransactionType
from services.base_service import BaseService, ValidationError, NotFoundError


class SalesService(BaseService):
    """Implementation of the sales service interface."""

    def __init__(self, session: Session,
                 sales_repository: Optional[SalesRepository] = None,
                 sales_item_repository: Optional[SalesItemRepository] = None,
                 customer_repository: Optional[CustomerRepository] = None,
                 product_repository: Optional[ProductRepository] = None,
                 project_repository: Optional[ProjectRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the sales service.

        Args:
            session: SQLAlchemy database session
            sales_repository: Optional SalesRepository instance
            sales_item_repository: Optional SalesItemRepository instance
            customer_repository: Optional CustomerRepository instance
            product_repository: Optional ProductRepository instance
            project_repository: Optional ProjectRepository instance
            inventory_repository: Optional InventoryRepository instance
        """
        super().__init__(session)
        self.sales_repository = sales_repository or SalesRepository(session)
        self.sales_item_repository = sales_item_repository or SalesItemRepository(session)
        self.customer_repository = customer_repository or CustomerRepository(session)
        self.product_repository = product_repository or ProductRepository(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)

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
            sale = self.sales_repository.get_by_id(sales_id)
            if not sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Get sale items
            sale_dict = self._to_dict(sale)
            sale_items = self.sales_item_repository.get_by_sales(sales_id)
            sale_dict['items'] = [self._to_dict(item) for item in sale_items]

            # Get customer details
            if sale.customer_id:
                customer = self.customer_repository.get_by_id(sale.customer_id)
                if customer:
                    sale_dict['customer'] = self._to_dict(customer)

            # Get associated project if any
            project = self.project_repository.get_by_sales(sales_id)
            if project:
                sale_dict['project'] = self._to_dict(project)

            return sale_dict
        except Exception as e:
            self.logger.error(f"Error retrieving sale {sales_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all sales, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing sales
        """
        try:
            sales = self.sales_repository.get_all(filters)

            # Build sales list with basic information
            sales_list = []
            for sale in sales:
                sale_dict = self._to_dict(sale)

                # Get items count and total
                items_count = self.sales_item_repository.count_by_sales(sale.id)
                sale_dict['items_count'] = items_count

                # Add customer name if available
                if sale.customer_id:
                    customer = self.customer_repository.get_by_id(sale.customer_id)
                    if customer:
                        sale_dict['customer_name'] = customer.name

                sales_list.append(sale_dict)

            return sales_list
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
            NotFoundError: If customer not found
        """
        try:
            # Validate sales data
            self._validate_sales_data(sales_data)

            # Extract items data if present
            items_data = sales_data.pop('items', [])

            # Check if customer exists if customer_id provided
            customer_id = sales_data.get('customer_id')
            if customer_id:
                customer = self.customer_repository.get_by_id(customer_id)
                if not customer:
                    raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Set default status if not provided
            if 'status' not in sales_data:
                sales_data['status'] = SaleStatus.QUOTE_REQUEST.value

            # Set default payment status if not provided
            if 'payment_status' not in sales_data:
                sales_data['payment_status'] = PaymentStatus.PENDING.value

            # Set created_at if not provided
            if 'created_at' not in sales_data:
                sales_data['created_at'] = datetime.now()

            # Create sale
            with self.transaction():
                # Create the sale
                sale = self.sales_repository.create(sales_data)

                # Calculate total amount
                total_amount = 0.0

                # Add items if provided
                for item_data in items_data:
                    item_data['sales_id'] = sale.id

                    # Validate product exists if product_id provided
                    product_id = item_data.get('product_id')
                    if product_id:
                        product = self.product_repository.get_by_id(product_id)
                        if not product:
                            raise NotFoundError(f"Product with ID {product_id} not found")

                        # Set price from product if not provided
                        if 'price' not in item_data:
                            item_data['price'] = product.price

                    # Create sales item
                    sales_item = self.sales_item_repository.create(item_data)

                    # Add to total
                    total_amount += sales_item.price * sales_item.quantity

                # Update sale with total amount
                if total_amount > 0:
                    self.sales_repository.update(sale.id, {'total_amount': total_amount})
                    sale.total_amount = total_amount

                # Prepare response
                sale_dict = self._to_dict(sale)
                sale_dict['items'] = []

                for item_data in items_data:
                    item_data['sales_id'] = sale.id
                    sale_dict['items'].append(item_data)

                return sale_dict
        except Exception as e:
            self.logger.error(f"Error creating sale: {str(e)}")
            raise

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
            sale = self.sales_repository.get_by_id(sales_id)
            if not sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Validate sales data
            self._validate_sales_data(sales_data, update=True)

            # Check if customer exists if customer_id provided
            customer_id = sales_data.get('customer_id')
            if customer_id:
                customer = self.customer_repository.get_by_id(customer_id)
                if not customer:
                    raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Update sale
            with self.transaction():
                updated_sale = self.sales_repository.update(sales_id, sales_data)

                # Get sale items
                sale_dict = self._to_dict(updated_sale)
                sale_items = self.sales_item_repository.get_by_sales(sales_id)
                sale_dict['items'] = [self._to_dict(item) for item in sale_items]

                return sale_dict
        except Exception as e:
            self.logger.error(f"Error updating sale {sales_id}: {str(e)}")
            raise

    def delete(self, sales_id: int) -> bool:
        """Delete a sale by ID.

        Args:
            sales_id: ID of the sale to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale not found
            ValidationError: If sale has associated project
        """
        try:
            # Check if sale exists
            sale = self.sales_repository.get_by_id(sales_id)
            if not sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Check if sale has associated project
            project = self.project_repository.get_by_sales(sales_id)
            if project:
                raise ValidationError(f"Cannot delete sale {sales_id} as it has an associated project")

            # Delete sale and related items
            with self.transaction():
                # Delete sales items first
                sales_items = self.sales_item_repository.get_by_sales(sales_id)
                for item in sales_items:
                    self.sales_item_repository.delete(item.id)

                # Delete sale
                self.sales_repository.delete(sales_id)
                return True
        except Exception as e:
            self.logger.error(f"Error deleting sale {sales_id}: {str(e)}")
            raise

    def add_item(self, sales_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add item to sale.

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
            # Check if sale exists
            sale = self.sales_repository.get_by_id(sales_id)
            if not sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Validate product exists if product_id provided
            product_id = item_data.get('product_id')
            if product_id:
                product = self.product_repository.get_by_id(product_id)
                if not product:
                    raise NotFoundError(f"Product with ID {product_id} not found")

                # Set price from product if not provided
                if 'price' not in item_data:
                    item_data['price'] = product.price

            # Validate item data
            self._validate_item_data(item_data)

            # Add item to sale
            with self.transaction():
                # Add sale_id to item data
                item_data['sales_id'] = sales_id

                # Create sales item
                sales_item = self.sales_item_repository.create(item_data)

                # Update sale total amount
                sale_items = self.sales_item_repository.get_by_sales(sales_id)
                total_amount = sum(item.price * item.quantity for item in sale_items)
                self.sales_repository.update(sales_id, {'total_amount': total_amount})

                # Get product details
                sales_item_dict = self._to_dict(sales_item)
                if product_id:
                    sales_item_dict['product'] = self._to_dict(product)

                return sales_item_dict
        except Exception as e:
            self.logger.error(f"Error adding item to sale {sales_id}: {str(e)}")
            raise

    def remove_item(self, sales_id: int, item_id: int) -> bool:
        """Remove item from sale.

        Args:
            sales_id: ID of the sale
            item_id: ID of the item

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale or item not found
        """
        try:
            # Check if sale exists
            sale = self.sales_repository.get_by_id(sales_id)
            if not sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Check if item exists and belongs to this sale
            sales_item = self.sales_item_repository.get_by_id(item_id)
            if not sales_item or sales_item.sales_id != sales_id:
                raise NotFoundError(f"Item {item_id} not found in sale {sales_id}")

            # Remove item from sale
            with self.transaction():
                # Delete sales item
                self.sales_item_repository.delete(item_id)

                # Update sale total amount
                sale_items = self.sales_item_repository.get_by_sales(sales_id)
                total_amount = sum(item.price * item.quantity for item in sale_items)
                self.sales_repository.update(sales_id, {'total_amount': total_amount})

                return True
        except Exception as e:
            self.logger.error(f"Error removing item {item_id} from sale {sales_id}: {str(e)}")
            raise

    def update_status(self, sales_id: int, status: str) -> Dict[str, Any]:
        """Update sale status.

        Args:
            sales_id: ID of the sale
            status: New status

        Returns:
            Dict representing the updated sale

        Raises:
            NotFoundError: If sale not found
            ValidationError: If invalid status
        """
        try:
            # Check if sale exists
            sale = self.sales_repository.get_by_id(sales_id)
            if not sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Validate status
            try:
                SaleStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid sale status: {status}")

            # Update sale status
            with self.transaction():
                updated_sale = self.sales_repository.update(sales_id, {'status': status})

                # Check if we need to update inventory for completed sales
                if status == SaleStatus.COMPLETED.value:
                    self._update_inventory_for_completed_sale(sales_id)

                return self._to_dict(updated_sale)
        except Exception as e:
            self.logger.error(f"Error updating status for sale {sales_id}: {str(e)}")
            raise

    def update_payment_status(self, sales_id: int, payment_status: str) -> Dict[str, Any]:
        """Update sale payment status.

        Args:
            sales_id: ID of the sale
            payment_status: New payment status

        Returns:
            Dict representing the updated sale

        Raises:
            NotFoundError: If sale not found
            ValidationError: If invalid payment status
        """
        try:
            # Check if sale exists
            sale = self.sales_repository.get_by_id(sales_id)
            if not sale:
                raise NotFoundError(f"Sale with ID {sales_id} not found")

            # Validate payment status
            try:
                PaymentStatus(payment_status)
            except ValueError:
                raise ValidationError(f"Invalid payment status: {payment_status}")

            # Update sale payment status
            with self.transaction():
                updated_sale = self.sales_repository.update(sales_id, {'payment_status': payment_status})
                return self._to_dict(updated_sale)
        except Exception as e:
            self.logger.error(f"Error updating payment status for sale {sales_id}: {str(e)}")
            raise

    def get_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get sales by customer ID.

        Args:
            customer_id: ID of the customer

        Returns:
            List of dicts representing sales for the customer

        Raises:
            NotFoundError: If customer not found
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Get sales for customer
            sales = self.sales_repository.get_by_customer(customer_id)

            # Build sales list with basic information
            sales_list = []
            for sale in sales:
                sale_dict = self._to_dict(sale)

                # Get items count
                items_count = self.sales_item_repository.count_by_sales(sale.id)
                sale_dict['items_count'] = items_count

                sales_list.append(sale_dict)

            return sales_list
        except Exception as e:
            self.logger.error(f"Error retrieving sales for customer {customer_id}: {str(e)}")
            raise

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get sales within a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of dicts representing sales in the date range
        """
        try:
            # Validate date range
            if start_date > end_date:
                raise ValidationError(f"Start date must be before end date")

            # Get sales by date range
            sales = self.sales_repository.get_by_date_range(start_date, end_date)

            # Build sales list with basic information
            sales_list = []
            for sale in sales:
                sale_dict = self._to_dict(sale)

                # Get items count
                items_count = self.sales_item_repository.count_by_sales(sale.id)
                sale_dict['items_count'] = items_count

                # Add customer name if available
                if sale.customer_id:
                    customer = self.customer_repository.get_by_id(sale.customer_id)
                    if customer:
                        sale_dict['customer_name'] = customer.name

                sales_list.append(sale_dict)

            return sales_list
        except Exception as e:
            self.logger.error(f"Error retrieving sales in date range: {str(e)}")
            raise

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get sales by status.

        Args:
            status: Sale status

        Returns:
            List of dicts representing sales with the given status

        Raises:
            ValidationError: If invalid status
        """
        try:
            # Validate status
            try:
                SaleStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid sale status: {status}")

            # Get sales by status
            sales = self.sales_repository.get_by_status(status)

            # Build sales list with basic information
            sales_list = []
            for sale in sales:
                sale_dict = self._to_dict(sale)

                # Get items count
                items_count = self.sales_item_repository.count_by_sales(sale.id)
                sale_dict['items_count'] = items_count

                # Add customer name if available
                if sale.customer_id:
                    customer = self.customer_repository.get_by_id(sale.customer_id)
                    if customer:
                        sale_dict['customer_name'] = customer.name

                sales_list.append(sale_dict)

            return sales_list
        except Exception as e:
            self.logger.error(f"Error retrieving sales with status {status}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for sales by query string.

        Args:
            query: Search query string

        Returns:
            List of dicts representing matching sales
        """
        try:
            # Search sales
            sales = self.sales_repository.search(query)

            # Build sales list with basic information
            sales_list = []
            for sale in sales:
                sale_dict = self._to_dict(sale)

                # Get items count
                items_count = self.sales_item_repository.count_by_sales(sale.id)
                sale_dict['items_count'] = items_count

                # Add customer name if available
                if sale.customer_id:
                    customer = self.customer_repository.get_by_id(sale.customer_id)
                    if customer:
                        sale_dict['customer_name'] = customer.name

                sales_list.append(sale_dict)

            return sales_list
        except Exception as e:
            self.logger.error(f"Error searching sales: {str(e)}")
            raise

    # Helper methods

    def _validate_sales_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate sales data.

        Args:
            data: Sales data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Only check customer_id for new sales
        if not update and 'customer_id' not in data:
            raise ValidationError(f"Missing required field: customer_id")

        # Validate status if provided
        if 'status' in data:
            try:
                SaleStatus(data['status'])
            except ValueError:
                raise ValidationError(f"Invalid sale status: {data['status']}")

        # Validate payment status if provided
        if 'payment_status' in data:
            try:
                PaymentStatus(data['payment_status'])
            except ValueError:
                raise ValidationError(f"Invalid payment status: {data['payment_status']}")

        # Validate total_amount if provided
        if 'total_amount' in data:
            total_amount = data['total_amount']
            if not isinstance(total_amount, (int, float)) or total_amount < 0:
                raise ValidationError(f"Invalid total amount: {total_amount}")

    def _validate_item_data(self, data: Dict[str, Any]) -> None:
        """Validate sales item data.

        Args:
            data: Sales item data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        required_fields = ['product_id', 'quantity', 'price']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate quantity
        quantity = data['quantity']
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValidationError(f"Quantity must be a positive integer")

        # Validate price
        price = data['price']
        if not isinstance(price, (int, float)) or price < 0:
            raise ValidationError(f"Price must be a non-negative number")

    def _update_inventory_for_completed_sale(self, sales_id: int) -> None:
        """Update inventory for completed sale.

        Args:
            sales_id: ID of the completed sale

        Raises:
            NotFoundError: If sale or items not found
        """
        # Get sale items
        sale_items = self.sales_item_repository.get_by_sales(sales_id)

        for item in sale_items:
            if not item.product_id:
                continue

            # Get product from inventory
            inventory = self.inventory_repository.get_by_item('product', item.product_id)

            if inventory:
                # Validate there's enough inventory
                if inventory.quantity < item.quantity:
                    raise ValidationError(f"Not enough inventory for product {item.product_id}")

                # Update inventory
                new_quantity = inventory.quantity - item.quantity
                inventory_data = {
                    'quantity': new_quantity,
                    'status': self._determine_inventory_status(new_quantity)
                }

                self.inventory_repository.update(inventory.id, inventory_data)

    def _determine_inventory_status(self, quantity: float) -> str:
        """Determine inventory status based on quantity.

        Args:
            quantity: Current inventory quantity

        Returns:
            Inventory status string
        """
        if quantity <= 0:
            return InventoryStatus.OUT_OF_STOCK.value
        elif quantity < 5:  # This threshold could be configurable
            return InventoryStatus.LOW_STOCK.value
        else:
            return InventoryStatus.IN_STOCK.value