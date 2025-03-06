# services/implementations/sale_service.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select

from database.models.enums import SaleStatus, PaymentStatus
from database.models.sale import Sale, SaleItem
from database.models.product import Product
from database.models.base import ModelValidationError
from database.exceptions import ModelNotFoundError, RepositoryError
from database.repositories.sale_repository import SaleRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError, ServiceError
from services.interfaces.sale_service import ISaleService
from utils.logger import get_logger

logger = get_logger(__name__)


class SaleService(BaseService, ISaleService):
    """
    Enhanced Sale Service implementation with comprehensive validation,
    error handling, and logging.
    """

    def __init__(self, sale_repository: Optional[SaleRepository] = None):
        """
        Initialize the Sale Service with a repository.

        Args:
            sale_repository: Repository for sale data access.
                If not provided, a new one will be created.
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.info("Initializing SaleService")

        # Create repository if not provided
        if sale_repository is None:
            session = get_db_session()
            self.sale_repository = SaleRepository(session)
        else:
            self.sale_repository = sale_repository

    def get_all_sales(
            self,
            status: Optional[SaleStatus] = None,
            payment_status: Optional[PaymentStatus] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            include_deleted: bool = False,
            page: int = 1,
            page_size: int = 50,
            sort_by: str = "sale_date",
            sort_desc: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all sales with optional filtering, pagination, and sorting.

        Args:
            status: Filter by sale status
            payment_status: Filter by payment status
            start_date: Filter by sales on or after this date
            end_date: Filter by Sales on or before this date
            include_deleted: Whether to include soft-deleted sales
            page: Page number for pagination
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending sale

        Returns:
            Tuple containing:
                - List of Sales as dictionaries
                - Total count of sales matching the filters

        Raises:
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Getting all sales with filters: status={status}, payment_status={payment_status}, "
                              f"start_date={start_date}, end_date={end_date}, include_deleted={include_deleted}")

            # Set up filter conditions
            filters = []

            if not include_deleted:
                filters.append(Sale.is_deleted == False)

            if status is not None:
                filters.append(Sale.status == status)

            if payment_status is not None:
                filters.append(Sale.payment_status == payment_status)

            if start_date is not None:
                filters.append(Sale.sale_date >= start_date)

            if end_date is not None:
                filters.append(Sale.sale_date <= end_date)

            # Get sales and total count
            sales, total_count = self.sale_repository.get_all_with_pagination(
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_desc=sort_desc
            )

            # Convert to dictionaries using the model's to_dict method
            result = []
            for sale in sales:
                # Add item count
                sale_dict = sale.to_dict()
                sale_dict['item_count'] = len(sale.items)
                result.append(sale_dict)

            self.logger.info(f"Retrieved {len(result)} sales (total: {total_count})")
            return result, total_count

        except RepositoryError as e:
            self.logger.error(f"Repository error getting sales: {str(e)}")
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting sales: {str(e)}")
            raise ServiceError(f"Error retrieving sales: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting sales: {str(e)}")
            raise ServiceError(f"Unexpected error retrieving sales: {str(e)}")

    def get_sale_by_id(self, sale_id: int, include_items: bool = True) -> Dict[str, Any]:
        """
        Get sale by ID.

        Args:
            sale_id: ID of the sale to retrieve
            include_items: Whether to include sale items

        Returns:
            Sale data as a dictionary

        Raises:
            NotFoundError: If sale doesn't exist
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Getting sale by ID: {sale_id}, include_items={include_items}")

            # Get sale with or without items
            sale = self.sale_repository.get_by_id(
                sale_id,
                include_related=['items'] if include_items else [] # Removed 'supplier' as it's not relevant here
            )

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if sale.is_deleted:
                self.logger.warning(f"Sale with ID {sale_id} has been deleted")
                raise NotFoundError(f"Sale with ID {sale_id} has been deleted")

            # Convert to dictionary using the model's to_dict method
            result = sale.to_dict()

            # Add items if requested
            if include_items:
                result['items'] = [item.to_dict() for item in sale.items]

            self.logger.info(f"Retrieved sale with ID {sale_id}")
            return result

        except NotFoundError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error getting sale {sale_id}: {str(e)}")
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting sale {sale_id}: {str(e)}")
            raise ServiceError(f"Error retrieving sale: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting sale {sale_id}: {str(e)}")
            raise ServiceError(f"Unexpected error retrieving sale: {str(e)}")

    def get_sale_by_number(self, sale_number: str) -> Dict[str, Any]:
        """
        Get sale by sale number.

        Args:
            sale_number: Sale number to retrieve

        Returns:
            Sale data as a dictionary

        Raises:
            NotFoundError: If sale doesn't exist
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Getting sale by number: {sale_number}")

            # Find the sale
            sale = self.sale_repository.find_one_by(
                filters=[Sale.sale_number == sale_number, Sale.is_deleted == False],
                include_related=['items'] # Removed 'supplier' as it's not relevant here
            )

            if sale is None:
                self.logger.warning(f"Sale with number '{sale_number}' not found")
                raise NotFoundError(f"Sale with number '{sale_number}' not found")

            # Convert to dictionary using the model's to_dict method
            result = sale.to_dict()
            result['items'] = [item.to_dict() for item in sale.items]

            self.logger.info(f"Retrieved sale with number '{sale_number}'")
            return result

        except NotFoundError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error getting sale '{sale_number}': {str(e)}")
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting sale '{sale_number}': {str(e)}")
            raise ServiceError(f"Error retrieving sale: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting sale '{sale_number}': {str(e)}")
            raise ServiceError(f"Unexpected error retrieving sale: {str(e)}")

    def create_sale(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new sale.

        Args:
            sale_data: Sale data

        Returns:
            Created sale data

        Raises:
            ValidationError: If validation fails
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Creating new sale with data: {sale_data}")

            # Ensure sale number is unique
            if 'sale_number' in sale_data:
                existing = self.sale_repository.find_one_by(
                    filters=[Sale.sale_number == sale_data['sale_number'], Sale.is_deleted == False]
                )
                if existing:
                    self.logger.warning(f"Sale with number '{sale_data['sale_number']}' already exists")
                    raise ValidationError(f"Sale with number '{sale_data['sale_number']}' already exists")

            # Extract items if present
            items_data = sale_data.pop('items', [])

            # Create sale using the model's constructor which handles validation
            try:
                sale = Sale(**sale_data)
                self.sale_repository.add(sale)
                self.sale_repository.commit()
            except ModelValidationError as e:
                raise ValidationError(str(e))

            # Add items if provided
            for item_data in items_data:
                if 'product_id' in item_data and 'quantity' in item_data and 'unit_price' in item_data:
                    try:
                        # Use the model's add_item method
                        item = SaleItem(
                            sale_id=sale.id,
                            product_id=item_data['product_id'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price']
                        )
                        sale.items.append(item)
                    except ModelValidationError as e:
                        raise ValidationError(f"Item validation error: {str(e)}")

            # Update sale total and save
            if items_data:
                sale.calculate_total()
                self.sale_repository.commit()

            # Return the created sale
            self.logger.info(f"Created new sale with ID {sale.id}")
            result = sale.to_dict()
            result['items'] = [item.to_dict() for item in sale.items]
            return result

        except ValidationError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error creating sale: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating sale: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error creating sale: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating sale: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Unexpected error creating sale: {str(e)}")

    def update_sale(self, sale_id: int, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing sale.

        Args:
            sale_id: ID of the sale to update
            sale_data: Updated sale data

        Returns:
            Updated sale data

        Raises:
            NotFoundError: If sale doesn't exist
            ValidationError: If validation fails
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Updating sale {sale_id} with data: {sale_data}")

            # Get the sale
            sale = self.sale_repository.get_by_id(sale_id, include_related=['items'])

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if sale.is_deleted:
                self.logger.warning(f"Sale with ID {sale_id} has been deleted")
                raise NotFoundError(f"Sale with ID {sale_id} has been deleted")

            # Ensure sale number is unique if changed
            if 'sale_number' in sale_data and sale_data['sale_number'] != sale.sale_number:
                existing = self.sale_repository.find_one_by(
                    filters=[
                        Sale.sale_number == sale_data['sale_number'],
                        Sale.id != sale_id,
                        Sale.is_deleted == False
                    ]
                )
                if existing:
                    self.logger.warning(f"Sale with number '{sale_data['sale_number']}' already exists")
                    raise ValidationError(f"Sale with number '{sale_data['sale_number']}' already exists")

            # Extract items if present
            items_data = sale_data.pop('items', None)

            # Update sale using the model's update method which handles validation
            try:
                sale.update(**sale_data)
            except ModelValidationError as e:
                raise ValidationError(str(e))

            # Update items if provided
            if items_data is not None:
                # Remove existing items
                for item in list(sale.items):
                    self.sale_repository.session.delete(item)
                sale.items.clear()

                # Add new items
                for item_data in items_data:
                    if 'product_id' in item_data and 'quantity' in item_data and 'unit_price' in item_data:
                        try:
                            item = SaleItem(
                                sale_id=sale.id,
                                product_id=item_data['product_id'],
                                quantity=item_data['quantity'],
                                unit_price=item_data['unit_price']
                            )
                            sale.items.append(item)
                        except ModelValidationError as e:
                            raise ValidationError(f"Item validation error: {str(e)}")

            # Recalculate total
            sale.calculate_total()

            # Commit changes
            self.sale_repository.commit()

            # Return the updated sale
            self.logger.info(f"Updated sale with ID {sale_id}")
            result = sale.to_dict()
            result['items'] = [item.to_dict() for item in sale.items]
            return result

        except NotFoundError:
            raise
        except ValidationError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error updating sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error updating sale: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Unexpected error updating sale: {str(e)}")

    def delete_sale(self, sale_id: int, permanent: bool = False) -> bool:
        """
        Delete an sale.

        Args:
            sale_id: ID of the sale to delete
            permanent: Whether to permanently delete the sale

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale doesn't exist
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Deleting sale {sale_id} (permanent={permanent})")

            # Get the sale
            sale = self.sale_repository.get_by_id(sale_id)

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if sale.is_deleted and not permanent:
                self.logger.warning(f"Sale with ID {sale_id} already deleted")
                return True

            # Delete the sale
            if permanent:
                self.sale_repository.delete(sale)
                self.logger.info(f"Permanently deleted sale with ID {sale_id}")
            else:
                # Use model's soft_delete method
                sale.soft_delete()
                self.logger.info(f"Soft deleted sale with ID {sale_id}")

            # Commit changes
            self.sale_repository.commit()
            return True

        except NotFoundError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error deleting sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error deleting sale: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Unexpected error deleting sale: {str(e)}")

    def restore_sale(self, sale_id: int) -> Dict[str, Any]:
        """
        Restore a soft-deleted sale.

        Args:
            sale_id: ID of the sale to restore

        Returns:
            Restored sale data

        Raises:
            NotFoundError: If sale doesn't exist
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Restoring sale {sale_id}")

            # Get the sale
            sale = self.sale_repository.get_by_id(sale_id, include_deleted=True)

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if not sale.is_deleted:
                self.logger.warning(f"Sale with ID {sale_id} is not deleted")
                result = sale.to_dict()
                result['items'] = [item.to_dict() for item in sale.items]
                return result

            # Restore the sale using model's restore method
            sale.restore()

            # Commit changes
            self.sale_repository.commit()

            # Return the restored sale
            self.logger.info(f"Restored sale with ID {sale_id}")
            result = sale.to_dict()
            result['items'] = [item.to_dict() for item in sale.items]
            return result

        except NotFoundError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error restoring sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error restoring sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error restoring sale: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error restoring sale {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error restoring sale: {str(e)}")

    def update_sale_status(self, sale_id: int, status: SaleStatus) -> Dict[str, Any]:
        """
        Update the status of an sale.

        Args:
            sale_id: ID of the sale to update
            status: New status

        Returns:
            Updated sale data

        Raises:
            NotFoundError: If sale doesn't exist
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Updating status of sale {sale_id} to {status}")

            # Get the sale
            sale = self.sale_repository.get_by_id(sale_id)

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if sale.is_deleted:
                self.logger.warning(f"Sale with ID {sale_id} has been deleted")
                raise NotFoundError(f"Sale with ID {sale_id} has been deleted")

            # Update status using model's update_status method which handles validation
            old_status = sale.status
            sale.update_status(status)

            # Commit changes
            self.sale_repository.commit()

            # Return the updated sale
            self.logger.info(f"Updated status of sale {sale_id} from {old_status} to {status}")
            result = sale.to_dict()
            result['items'] = [item.to_dict() for item in sale.items]
            return result

        except NotFoundError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error updating sale status {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except ModelValidationError as e:
            self.logger.error(f"Validation error updating sale status {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ValidationError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating sale status {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error updating sale status: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating sale status {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Unexpected error updating sale status: {str(e)}")

    def update_payment_status(self, sale_id: int, payment_status: PaymentStatus) -> Dict[str, Any]:
        """
        Update the payment status of an sale.

        Args:
            sale_id: ID of the sale to update
            payment_status: New payment status

        Returns:
            Updated sale data

        Raises:
            NotFoundError: If sale doesn't exist
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Updating payment status of sale {sale_id} to {payment_status}")

            # Get the sale
            sale = self.sale_repository.get_by_id(sale_id)

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if sale.is_deleted:
                self.logger.warning(f"Sale with ID {sale_id} has been deleted")
                raise NotFoundError(f"Sale with ID {sale_id} has been deleted")

            # Update payment status
            old_payment_status = sale.payment_status
            sale.update(payment_status=payment_status)

            # Commit changes
            self.sale_repository.commit()

            # Return the updated sale
            self.logger.info(
                f"Updated payment status of sale {sale_id} from {old_payment_status} to {payment_status}")
            result = sale.to_dict()
            result['items'] = [item.to_dict() for item in sale.items]
            return result

        except NotFoundError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error updating sale payment status {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except ModelValidationError as e:
            self.logger.error(f"Validation error updating sale payment status {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ValidationError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating sale payment status {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error updating sale payment status: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating sale payment status {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Unexpected error updating sale payment status: {str(e)}")

    def add_sale_item(self, sale_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an item to an sale.

        Args:
            sale_id: ID of the sale
            item_data: Item data including product_id, quantity, and unit_price

        Returns:
            Added sale item data

        Raises:
            NotFoundError: If sale doesn't exist
            ValidationError: If validation fails
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Adding item to sale {sale_id}: {item_data}")

            # Validate required fields
            required_fields = ['product_id', 'quantity', 'unit_price']
            for field in required_fields:
                if field not in item_data:
                    self.logger.warning(f"Missing required field '{field}' for sale item")
                    raise ValidationError(f"Missing required field '{field}' for sale item")

            # Get the sale
            sale = self.sale_repository.get_by_id(sale_id)

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if sale.is_deleted:
                self.logger.warning(f"Sale with ID {sale_id} has been deleted")
                raise NotFoundError(f"Sale with ID {sale_id} has been deleted")

            # Add the item
            try:
                # Create a new SaleItem
                item_data['sale_id'] = sale_id
                item = SaleItem(**item_data)

                # Add to sale
                sale.items.append(item)

                # Update sale totals
                sale.calculate_total()

                # Commit changes
                self.sale_repository.commit()
            except ModelValidationError as e:
                raise ValidationError(str(e))

            # Return the added item
            self.logger.info(f"Added item to sale {sale_id}")
            return item.to_dict()

        except NotFoundError:
            raise
        except ValidationError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error adding sale item to {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error adding sale item to {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error adding sale item: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error adding sale item to {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Unexpected error adding sale item: {str(e)}")

    def update_sale_item(self, sale_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an sale item.

        Args:
            sale_id: ID of the sale
            item_id: ID of the item to update
            item_data: Updated item data

        Returns:
            Updated sale item data

        Raises:
            NotFoundError: If sale or item doesn't exist
            ValidationError: If validation fails
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Updating item {item_id} in sale {sale_id}: {item_data}")

            # Get the sale
            sale = self.sale_repository.get_by_id(sale_id, include_related=['items'])

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if sale.is_deleted:
                self.logger.warning(f"Sale with ID {sale_id} has been deleted")
                raise NotFoundError(f"Sale with ID {sale_id} has been deleted")

            # Find the item
            item = None
            for i in sale.items:
                if i.id == item_id:
                    item = i
                    break

            if item is None:
                self.logger.warning(f"Item with ID {item_id} not found in sale {sale_id}")
                raise NotFoundError(f"Item with ID {item_id} not found in sale {sale_id}")

            # Update the item using model's update method
            try:
                item.update(**item_data)

                # Update sale totals
                sale.calculate_total()

                # Commit changes
                self.sale_repository.commit()
            except ModelValidationError as e:
                raise ValidationError(str(e))

            # Return the updated item
            self.logger.info(f"Updated item {item_id} in sale {sale_id}")
            return item.to_dict()

        except NotFoundError:
            raise
        except ValidationError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error updating sale item {item_id} in {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating sale item {item_id} in {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error updating sale item: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating sale item {item_id} in {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Unexpected error updating sale item: {str(e)}")

    def remove_sale_item(self, sale_id: int, item_id: int) -> bool:
        """
        Remove an item from a sale.

        Args:
            sale_id: ID of the sale
            item_id: ID of the item to remove

        Returns:
            True if successful

        Raises:
            NotFoundError: If sale or item doesn't exist
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Removing item {item_id} from sale {sale_id}")

            # Get the sale
            sale = self.sale_repository.get_by_id(sale_id, include_related=['items'])

            if sale is None:
                self.logger.warning(f"Sale with ID {sale_id} not found")
                raise NotFoundError(f"Sale with ID {sale_id} not found")

            if sale.is_deleted:
                self.logger.warning(f"Sale with ID {sale_id} has been deleted")
                raise NotFoundError(f"Sale with ID {sale_id} has been deleted")

            # Find the item
            item_found = False
            item_to_remove = None
            for item in sale.items:
                if item.id == item_id:
                    item_found = True
                    item_to_remove = item
                    break

            if not item_found:
                self.logger.warning(f"Item with ID {item_id} not found in sale {sale_id}")
                raise NotFoundError(f"Item with ID {item_id} not found in sale {sale_id}")

            # Remove the item
            sale.items.remove(item_to_remove)
            self.sale_repository.session.delete(item_to_remove)

            # Update sale totals
            sale.calculate_total()

            # Commit changes
            self.sale_repository.commit()

            # Return success
            self.logger.info(f"Removed item {item_id} from sale {sale_id}")
            return True

        except NotFoundError:
            raise
        except RepositoryError as e:
            self.logger.error(f"Repository error removing sale item {item_id} from {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error removing sale item {item_id} from {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Error removing sale item: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error removing sale item {item_id} from {sale_id}: {str(e)}")
            self.sale_repository.rollback()
            raise ServiceError(f"Unexpected error removing sale item: {str(e)}")

    def get_sale_statistics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[
        str, Any]:
        """
        Get sale statistics for a given period.

        Args:
            start_date: Start date for the period
            end_date: End date for the period

        Returns:
            Dictionary with sale statistics

        Raises:
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Getting sale statistics for period: {start_date} to {end_date}")

            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=30)

            # Build filters
            filters = [
                Sale.is_deleted == False,
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date
            ]

            # Get all sales for the period
            sales = self.sale_repository.find_by(filters)

            # Calculate statistics
            total_sales = len(sales)
            total_revenue = sum(sale.total for sale in sales)

            # Count by status
            status_counts = {}
            for status in SaleStatus:
                status_counts[status.name] = len([o for o in sales if o.status == status])

            # Count by payment status
            payment_status_counts = {}
            for status in PaymentStatus:
                payment_status_counts[status.name] = len([o for o in sales if o.payment_status == status])

            # Get top products (requires joining with SaleItem and Product)
            top_products = self.sale_repository.get_top_products(start_date, end_date, limit=5)

            # Compile results
            result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'average_sale_value': total_revenue / total_sales if total_sales > 0 else 0,
                'status_counts': status_counts,
                'payment_status_counts': payment_status_counts,
                'top_products': top_products
            }

            self.logger.info(f"Retrieved sale statistics for period: {start_date} to {end_date}")
            return result

        except RepositoryError as e:
            self.logger.error(f"Repository error getting sale statistics: {str(e)}")
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting sale statistics: {str(e)}")
            raise ServiceError(f"Error retrieving sale statistics: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting sale statistics: {str(e)}")
            raise ServiceError(f"Unexpected error retrieving sale statistics: {str(e)}")

    def search_sales(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for sales by various criteria.

        Args:
            query: Search query string

        Returns:
            List of matching sales

        Raises:
            ServiceError: If a service error occurs
        """
        try:
            self.logger.debug(f"Searching sales with query: {query}")

            # Build search filters
            filters = [
                Sale.is_deleted == False,
                or_(
                    Sale.sale_number.ilike(f"%{query}%"),
                    Sale.customer_name.ilike(f"%{query}%"),
                    Sale.customer_email.ilike(f"%{query}%"),
                    Sale.shipping_address.ilike(f"%{query}%"),
                    Sale.notes.ilike(f"%{query}%")
                )
            ]

            # Search sales
            sales = self.sale_repository.find_by(filters, include_related=['items'])

            # Convert to dictionaries using the model's to_dict method
            result = []
            for sale in sales:
                sale_dict = sale.to_dict()
                sale_dict['item_count'] = len(sale.items)
                result.append(sale_dict)

            self.logger.info(f"Found {len(result)} sales matching query: {query}")
            return result

        except RepositoryError as e:
            self.logger.error(f"Repository error searching sales: {str(e)}")
            raise ServiceError(str(e))
        except SQLAlchemyError as e:
            self.logger.error(f"Database error searching sales: {str(e)}")
            raise ServiceError(f"Error searching sales: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error searching sales: {str(e)}")
            raise ServiceError(f"Unexpected error searching sales: {str(e)}")

