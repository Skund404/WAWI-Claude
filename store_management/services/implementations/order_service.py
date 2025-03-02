# services/implementations/order_service.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select

from database.models.enums import OrderStatus, PaymentStatus
from database.models.order import Order, OrderItem
from database.models.product import Product
from database.repositories.order_repository import OrderRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.order_service import IOrderService
from utils.logger import get_logger

logger = get_logger(__name__)

class OrderService(BaseService, IOrderService):
    """
    Enhanced Order Service implementation with comprehensive validation,
    error handling, and logging.
    """
    
    def __init__(self, order_repository: Optional[OrderRepository] = None):
        """
        Initialize the Order Service with a repository.
        
        Args:
            order_repository: Repository for order data access.
                If not provided, a new one will be created.
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.info("Initializing OrderService")
        
        # Create repository if not provided
        if order_repository is None:
            session = get_db_session()
            self.order_repository = OrderRepository(session)
        else:
            self.order_repository = order_repository
    
    def get_all_orders(
        self, 
        status: Optional[OrderStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "order_date",
        sort_desc: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all orders with optional filtering, pagination, and sorting.
        
        Args:
            status: Filter by order status
            payment_status: Filter by payment status
            start_date: Filter by orders on or after this date
            end_date: Filter by orders on or before this date
            include_deleted: Whether to include soft-deleted orders
            page: Page number for pagination
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_desc: Whether to sort in descending order
            
        Returns:
            Tuple containing:
                - List of orders as dictionaries
                - Total count of orders matching the filters
        """
        try:
            self.logger.debug(f"Getting all orders with filters: status={status}, payment_status={payment_status}, "
                             f"start_date={start_date}, end_date={end_date}, include_deleted={include_deleted}")
            
            # Set up filter conditions
            filters = []
            
            if not include_deleted:
                filters.append(Order.deleted == False)
                
            if status is not None:
                filters.append(Order.status == status)
                
            if payment_status is not None:
                filters.append(Order.payment_status == payment_status)
                
            if start_date is not None:
                filters.append(Order.order_date >= start_date)
                
            if end_date is not None:
                filters.append(Order.order_date <= end_date)
            
            # Get orders and total count
            orders, total_count = self.order_repository.get_all_with_pagination(
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_desc=sort_desc
            )
            
            # Convert to dictionaries
            result = []
            for order in orders:
                # Add item count
                order_dict = order.to_dict()
                order_dict['item_count'] = len(order.items)
                result.append(order_dict)
                
            self.logger.info(f"Retrieved {len(result)} orders (total: {total_count})")
            return result, total_count
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting orders: {str(e)}")
            raise ValidationError(f"Error retrieving orders: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting orders: {str(e)}")
            raise ValidationError(f"Unexpected error retrieving orders: {str(e)}")

    def get_order_by_id(self, order_id: int, include_items: bool = True) -> Dict[str, Any]:
        """
        Get order by ID.
        
        Args:
            order_id: ID of the order to retrieve
            include_items: Whether to include order items
            
        Returns:
            Order data as a dictionary
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        try:
            self.logger.debug(f"Getting order by ID: {order_id}, include_items={include_items}")
            
            # Get order with or without items
            order = self.order_repository.get_by_id(
                order_id, 
                include_related=['items', 'supplier'] if include_items else ['supplier']
            )
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if order.deleted:
                self.logger.warning(f"Order with ID {order_id} has been deleted")
                raise NotFoundError(f"Order with ID {order_id} has been deleted")
            
            # Convert to dictionary
            result = order.to_dict()
            
            # Add items if requested
            if include_items:
                result['items'] = [item.to_dict() for item in order.items]
            
            self.logger.info(f"Retrieved order with ID {order_id}")
            return result
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting order {order_id}: {str(e)}")
            raise ValidationError(f"Error retrieving order: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting order {order_id}: {str(e)}")
            raise ValidationError(f"Unexpected error retrieving order: {str(e)}")

    def get_order_by_number(self, order_number: str) -> Dict[str, Any]:
        """
        Get order by order number.
        
        Args:
            order_number: Order number to retrieve
            
        Returns:
            Order data as a dictionary
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        try:
            self.logger.debug(f"Getting order by number: {order_number}")
            
            # Find the order
            order = self.order_repository.find_one_by(
                filters=[Order.order_number == order_number, Order.deleted == False],
                include_related=['items', 'supplier']
            )
            
            if order is None:
                self.logger.warning(f"Order with number '{order_number}' not found")
                raise NotFoundError(f"Order with number '{order_number}' not found")
            
            # Convert to dictionary
            result = order.to_dict()
            result['items'] = [item.to_dict() for item in order.items]
            
            self.logger.info(f"Retrieved order with number '{order_number}'")
            return result
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting order '{order_number}': {str(e)}")
            raise ValidationError(f"Error retrieving order: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting order '{order_number}': {str(e)}")
            raise ValidationError(f"Unexpected error retrieving order: {str(e)}")

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            order_data: Order data
            
        Returns:
            Created order data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            self.logger.debug(f"Creating new order with data: {order_data}")
            
            # Ensure order number is unique
            if 'order_number' in order_data:
                existing = self.order_repository.find_one_by(
                    filters=[Order.order_number == order_data['order_number'], Order.deleted == False]
                )
                if existing:
                    self.logger.warning(f"Order with number '{order_data['order_number']}' already exists")
                    raise ValidationError(f"Order with number '{order_data['order_number']}' already exists")
            
            # Extract items if present
            items_data = order_data.pop('items', [])
            
            # Create order
            order = Order(**order_data)
            self.order_repository.add(order)
            self.order_repository.commit()
            
            # Add items if provided
            for item_data in items_data:
                if 'product_id' in item_data and 'quantity' in item_data and 'unit_price' in item_data:
                    order.add_item(
                        product_id=item_data['product_id'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price']
                    )
            
            # Update order total and save
            if items_data:
                order.calculate_total()
                self.order_repository.commit()
            
            # Return the created order
            self.logger.info(f"Created new order with ID {order.id}")
            result = order.to_dict()
            result['items'] = [item.to_dict() for item in order.items]
            return result
            
        except ValidationError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating order: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error creating order: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating order: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error creating order: {str(e)}")

    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing order.
        
        Args:
            order_id: ID of the order to update
            order_data: Updated order data
            
        Returns:
            Updated order data
            
        Raises:
            NotFoundError: If order doesn't exist
            ValidationError: If validation fails
        """
        try:
            self.logger.debug(f"Updating order {order_id} with data: {order_data}")
            
            # Get the order
            order = self.order_repository.get_by_id(order_id, include_related=['items'])
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if order.deleted:
                self.logger.warning(f"Order with ID {order_id} has been deleted")
                raise NotFoundError(f"Order with ID {order_id} has been deleted")
            
            # Ensure order number is unique if changed
            if 'order_number' in order_data and order_data['order_number'] != order.order_number:
                existing = self.order_repository.find_one_by(
                    filters=[
                        Order.order_number == order_data['order_number'],
                        Order.id != order_id,
                        Order.deleted == False
                    ]
                )
                if existing:
                    self.logger.warning(f"Order with number '{order_data['order_number']}' already exists")
                    raise ValidationError(f"Order with number '{order_data['order_number']}' already exists")
            
            # Extract items if present
            items_data = order_data.pop('items', None)
            
            # Update order
            order.update(**order_data)
            
            # Update items if provided
            if items_data is not None:
                # Remove existing items
                for item in list(order.items):
                    order.remove_item(item.id)
                
                # Add new items
                for item_data in items_data:
                    if 'product_id' in item_data and 'quantity' in item_data and 'unit_price' in item_data:
                        order.add_item(
                            product_id=item_data['product_id'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price']
                        )
            
            # Commit changes
            self.order_repository.commit()
            
            # Return the updated order
            self.logger.info(f"Updated order with ID {order_id}")
            result = order.to_dict()
            result['items'] = [item.to_dict() for item in order.items]
            return result
            
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating order {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error updating order: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating order {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error updating order: {str(e)}")

    def delete_order(self, order_id: int, permanent: bool = False) -> bool:
        """
        Delete an order.
        
        Args:
            order_id: ID of the order to delete
            permanent: Whether to permanently delete the order
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        try:
            self.logger.debug(f"Deleting order {order_id} (permanent={permanent})")
            
            # Get the order
            order = self.order_repository.get_by_id(order_id)
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if order.deleted and not permanent:
                self.logger.warning(f"Order with ID {order_id} already deleted")
                return True
            
            # Delete the order
            if permanent:
                self.order_repository.delete(order)
                self.logger.info(f"Permanently deleted order with ID {order_id}")
            else:
                order.soft_delete()
                self.logger.info(f"Soft deleted order with ID {order_id}")
            
            # Commit changes
            self.order_repository.commit()
            return True
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting order {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error deleting order: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error deleting order {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error deleting order: {str(e)}")

    def restore_order(self, order_id: int) -> Dict[str, Any]:
        """
        Restore a soft-deleted order.
        
        Args:
            order_id: ID of the order to restore
            
        Returns:
            Restored order data
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        try:
            self.logger.debug(f"Restoring order {order_id}")
            
            # Get the order
            order = self.order_repository.get_by_id(order_id, include_deleted=True)
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if not order.deleted:
                self.logger.warning(f"Order with ID {order_id} is not deleted")
                result = order.to_dict()
                result['items'] = [item.to_dict() for item in order.items]
                return result
            
            # Restore the order
            order.restore()
            
            # Commit changes
            self.order_repository.commit()
            
            # Return the restored order
            self.logger.info(f"Restored order with ID {order_id}")
            result = order.to_dict()
            result['items'] = [item.to_dict() for item in order.items]
            return result
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error restoring order {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error restoring order: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error restoring order {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error restoring order: {str(e)}")
            
    def update_order_status(self, order_id: int, status: OrderStatus) -> Dict[str, Any]:
        """
        Update the status of an order.
        
        Args:
            order_id: ID of the order to update
            status: New status
            
        Returns:
            Updated order data
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        try:
            self.logger.debug(f"Updating status of order {order_id} to {status}")
            
            # Get the order
            order = self.order_repository.get_by_id(order_id)
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if order.deleted:
                self.logger.warning(f"Order with ID {order_id} has been deleted")
                raise NotFoundError(f"Order with ID {order_id} has been deleted")
            
            # Update status
            old_status = order.status
            order.update(status=status)
            
            # Commit changes
            self.order_repository.commit()
            
            # Return the updated order
            self.logger.info(f"Updated status of order {order_id} from {old_status} to {status}")
            result = order.to_dict()
            result['items'] = [item.to_dict() for item in order.items]
            return result
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating order status {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error updating order status: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating order status {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error updating order status: {str(e)}")
            
    def update_payment_status(self, order_id: int, payment_status: PaymentStatus) -> Dict[str, Any]:
        """
        Update the payment status of an order.
        
        Args:
            order_id: ID of the order to update
            payment_status: New payment status
            
        Returns:
            Updated order data
            
        Raises:
            NotFoundError: If order doesn't exist
        """
        try:
            self.logger.debug(f"Updating payment status of order {order_id} to {payment_status}")
            
            # Get the order
            order = self.order_repository.get_by_id(order_id)
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if order.deleted:
                self.logger.warning(f"Order with ID {order_id} has been deleted")
                raise NotFoundError(f"Order with ID {order_id} has been deleted")
            
            # Update payment status
            old_payment_status = order.payment_status
            order.update(payment_status=payment_status)
            
            # Commit changes
            self.order_repository.commit()
            
            # Return the updated order
            self.logger.info(f"Updated payment status of order {order_id} from {old_payment_status} to {payment_status}")
            result = order.to_dict()
            result['items'] = [item.to_dict() for item in order.items]
            return result
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating order payment status {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error updating order payment status: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating order payment status {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error updating order payment status: {str(e)}")
    
    def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an item to an order.
        
        Args:
            order_id: ID of the order
            item_data: Item data including product_id, quantity, and unit_price
            
        Returns:
            Added order item data
            
        Raises:
            NotFoundError: If order doesn't exist
            ValidationError: If validation fails
        """
        try:
            self.logger.debug(f"Adding item to order {order_id}: {item_data}")
            
            # Validate required fields
            required_fields = ['product_id', 'quantity', 'unit_price']
            for field in required_fields:
                if field not in item_data:
                    self.logger.warning(f"Missing required field '{field}' for order item")
                    raise ValidationError(f"Missing required field '{field}' for order item")
            
            # Get the order
            order = self.order_repository.get_by_id(order_id)
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if order.deleted:
                self.logger.warning(f"Order with ID {order_id} has been deleted")
                raise NotFoundError(f"Order with ID {order_id} has been deleted")
            
            # Add the item
            item = order.add_item(
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price']
            )
            
            # Add notes if provided
            if 'notes' in item_data:
                item.update(notes=item_data['notes'])
            
            # Commit changes
            self.order_repository.commit()
            
            # Return the added item
            self.logger.info(f"Added item to order {order_id}: {item}")
            return item.to_dict()
            
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error adding order item to {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error adding order item: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error adding order item to {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error adding order item: {str(e)}")
    
    def update_order_item(self, order_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an order item.
        
        Args:
            order_id: ID of the order
            item_id: ID of the item to update
            item_data: Updated item data
            
        Returns:
            Updated order item data
            
        Raises:
            NotFoundError: If order or item doesn't exist
            ValidationError: If validation fails
        """
        try:
            self.logger.debug(f"Updating item {item_id} in order {order_id}: {item_data}")
            
            # Get the order
            order = self.order_repository.get_by_id(order_id, include_related=['items'])
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if order.deleted:
                self.logger.warning(f"Order with ID {order_id} has been deleted")
                raise NotFoundError(f"Order with ID {order_id} has been deleted")
            
            # Find the item
            item = None
            for i in order.items:
                if i.id == item_id:
                    item = i
                    break
            
            if item is None:
                self.logger.warning(f"Item with ID {item_id} not found in order {order_id}")
                raise NotFoundError(f"Item with ID {item_id} not found in order {order_id}")
            
            # Update the item
            item.update(**item_data)
            
            # Commit changes
            self.order_repository.commit()
            
            # Return the updated item
            self.logger.info(f"Updated item {item_id} in order {order_id}")
            return item.to_dict()
            
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating order item {item_id} in {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error updating order item: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating order item {item_id} in {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error updating order item: {str(e)}")
    
    def remove_order_item(self, order_id: int, item_id: int) -> bool:
        """
        Remove an item from an order.
        
        Args:
            order_id: ID of the order
            item_id: ID of the item to remove
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If order or item doesn't exist
        """
        try:
            self.logger.debug(f"Removing item {item_id} from order {order_id}")
            
            # Get the order
            order = self.order_repository.get_by_id(order_id, include_related=['items'])
            
            if order is None:
                self.logger.warning(f"Order with ID {order_id} not found")
                raise NotFoundError(f"Order with ID {order_id} not found")
                
            if order.deleted:
                self.logger.warning(f"Order with ID {order_id} has been deleted")
                raise NotFoundError(f"Order with ID {order_id} has been deleted")
            
            # Find the item
            item_found = False
            for item in order.items:
                if item.id == item_id:
                    item_found = True
                    break
            
            if not item_found:
                self.logger.warning(f"Item with ID {item_id} not found in order {order_id}")
                raise NotFoundError(f"Item with ID {item_id} not found in order {order_id}")
            
            # Remove the item
            order.remove_item(item_id)
            
            # Commit changes
            self.order_repository.commit()
            
            # Return success
            self.logger.info(f"Removed item {item_id} from order {order_id}")
            return True
            
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error removing order item {item_id} from {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Error removing order item: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error removing order item {item_id} from {order_id}: {str(e)}")
            self.order_repository.rollback()
            raise ValidationError(f"Unexpected error removing order item: {str(e)}")
    
    def get_order_statistics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get order statistics for a given period.
        
        Args:
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            Dictionary with order statistics
        """
        try:
            self.logger.debug(f"Getting order statistics for period: {start_date} to {end_date}")
            
            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=30)
            
            # Build filters
            filters = [
                Order.deleted == False,
                Order.order_date >= start_date,
                Order.order_date <= end_date
            ]
            
            # Get all orders for the period
            orders = self.order_repository.find_by(filters)
            
            # Calculate statistics
            total_orders = len(orders)
            total_revenue = sum(order.total_amount for order in orders)
            
            # Count by status
            status_counts = {}
            for status in OrderStatus:
                status_counts[status.name] = len([o for o in orders if o.status == status])
            
            # Count by payment status
            payment_status_counts = {}
            for status in PaymentStatus:
                payment_status_counts[status.name] = len([o for o in orders if o.payment_status == status])
            
            # Get top products (requires joining with OrderItem and Product)
            top_products = self.order_repository.get_top_products(start_date, end_date, limit=5)
            
            # Compile results
            result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'average_order_value': total_revenue / total_orders if total_orders > 0 else 0,
                'status_counts': status_counts,
                'payment_status_counts': payment_status_counts,
                'top_products': top_products
            }
            
            self.logger.info(f"Retrieved order statistics for period: {start_date} to {end_date}")
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting order statistics: {str(e)}")
            raise ValidationError(f"Error retrieving order statistics: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting order statistics: {str(e)}")
            raise ValidationError(f"Unexpected error retrieving order statistics: {str(e)}")
    
    def search_orders(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for orders by various criteria.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching orders
        """
        try:
            self.logger.debug(f"Searching orders with query: {query}")
            
            # Build search filters
            filters = [
                Order.deleted == False,
                or_(
                    Order.order_number.ilike(f"%{query}%"),
                    Order.customer_name.ilike(f"%{query}%"),
                    Order.customer_email.ilike(f"%{query}%"),
                    Order.shipping_address.ilike(f"%{query}%"),
                    Order.notes.ilike(f"%{query}%")
                )
            ]
            
            # Search orders
            orders = self.order_repository.find_by(filters, include_related=['items'])
            
            # Convert to dictionaries
            result = []
            for order in orders:
                order_dict = order.to_dict()
                order_dict['item_count'] = len(order.items)
                result.append(order_dict)
            
            self.logger.info(f"Found {len(result)} orders matching query: {query}")
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error searching orders: {str(e)}")
            raise ValidationError(f"Error searching orders: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error searching orders: {str(e)}")
            raise ValidationError(f"Unexpected error searching orders: {str(e)}")