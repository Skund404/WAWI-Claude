# database/repositories/sales_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc, extract, case

from database.models.sales import Sales
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import SaleStatus, PaymentStatus


class SalesRepository(BaseRepository[Sales]):
    """Repository for sales management operations.

    This repository provides methods for managing sales data, including
    order tracking, reporting, and analytics.
    """

    def _get_model_class(self) -> Type[Sales]:
        """Return the model class this repository manages.

        Returns:
            The Sales model class
        """
        return Sales

    # Basic query methods

    def get_by_customer(self, customer_id: int) -> List[Sales]:
        """Get sales by customer.

        Args:
            customer_id: ID of the customer

        Returns:
            List of sales instances for the specified customer
        """
        self.logger.debug(f"Getting sales for customer {customer_id}")
        return self.session.query(Sales).filter(Sales.customer_id == customer_id).all()

    def get_by_status(self, status: SaleStatus) -> List[Sales]:
        """Get sales by status.

        Args:
            status: Sales status to filter by

        Returns:
            List of sales instances with the specified status
        """
        self.logger.debug(f"Getting sales with status '{status.value}'")
        return self.session.query(Sales).filter(Sales.status == status).all()

    def get_by_payment_status(self, payment_status: PaymentStatus) -> List[Sales]:
        """Get sales by payment status.

        Args:
            payment_status: Payment status to filter by

        Returns:
            List of sales instances with the specified payment status
        """
        self.logger.debug(f"Getting sales with payment status '{payment_status.value}'")
        return self.session.query(Sales).filter(Sales.payment_status == payment_status).all()

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Sales]:
        """Get sales within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of sales instances within the date range
        """
        self.logger.debug(f"Getting sales between {start_date} and {end_date}")
        return self.session.query(Sales). \
            filter(Sales.created_at >= start_date). \
            filter(Sales.created_at <= end_date).all()

    def get_recent_sales(self, limit: int = 10) -> List[Sales]:
        """Get most recent sales.

        Args:
            limit: Maximum number of sales to return

        Returns:
            List of most recent sales instances
        """
        self.logger.debug(f"Getting {limit} most recent sales")
        return self.session.query(Sales).order_by(Sales.created_at.desc()).limit(limit).all()

    # Sales item methods

    def get_sales_with_items(self, sales_id: int) -> Dict[str, Any]:
        """Get sales with all items.

        Args:
            sales_id: ID of the sales record

        Returns:
            Sales dictionary with items and related information

        Raises:
            EntityNotFoundError: If sales record not found
        """
        self.logger.debug(f"Getting sales {sales_id} with items")
        from database.models.sales_item import SalesItem
        from database.models.product import Product
        from database.models.customer import Customer

        sales = self.get_by_id(sales_id)
        if not sales:
            raise EntityNotFoundError(f"Sales with ID {sales_id} not found")

        # Get sales data
        result = sales.to_dict()

        # Get customer data
        customer = self.session.query(Customer).get(sales.customer_id)
        if customer:
            result['customer'] = customer.to_dict()

        # Get sales items with product information
        items_query = self.session.query(SalesItem, Product). \
            outerjoin(Product, SalesItem.product_id == Product.id). \
            filter(SalesItem.sales_id == sales_id)

        items = []
        for item, product in items_query.all():
            item_dict = item.to_dict()
            if product:
                item_dict['product'] = product.to_dict()
            items.append(item_dict)

        result['items'] = items
        result['item_count'] = len(items)

        return result

    def add_item_to_sales(self, sales_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add item to a sales record.

        Args:
            sales_id: ID of the sales record
            item_data: Item data dictionary

        Returns:
            Updated sales with items

        Raises:
            EntityNotFoundError: If sales record not found
            ValidationError: If validation fails
        """
        self.logger.debug(f"Adding item to sales {sales_id}")
        from database.models.sales_item import SalesItem
        from database.models.product import Product

        sales = self.get_by_id(sales_id)
        if not sales:
            raise EntityNotFoundError(f"Sales with ID {sales_id} not found")

        try:
            # Verify product exists
            product_id = item_data.get('product_id')
            if product_id:
                product = self.session.query(Product).get(product_id)
                if not product:
                    raise ValidationError(f"Product with ID {product_id} not found")

            # Create item
            item = SalesItem(sales_id=sales_id, **item_data)
            self.session.add(item)

            # Update sales total
            if 'price' in item_data and 'quantity' in item_data:
                sales.total_amount += item_data['price'] * item_data['quantity']
                self.update(sales)

            self.session.flush()

            # Return updated sales with items
            return self.get_sales_with_items(sales_id)
        except Exception as e:
            self.logger.error(f"Error adding item to sales: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to add item to sales: {str(e)}")

    def remove_item_from_sales(self, sales_id: int, item_id: int) -> Dict[str, Any]:
        """Remove item from a sales record.

        Args:
            sales_id: ID of the sales record
            item_id: ID of the item to remove

        Returns:
            Updated sales with items

        Raises:
            EntityNotFoundError: If sales or item not found
        """
        self.logger.debug(f"Removing item {item_id} from sales {sales_id}")
        from database.models.sales_item import SalesItem

        sales = self.get_by_id(sales_id)
        if not sales:
            raise EntityNotFoundError(f"Sales with ID {sales_id} not found")

        # Find item
        item = self.session.query(SalesItem). \
            filter(SalesItem.id == item_id). \
            filter(SalesItem.sales_id == sales_id).first()

        if not item:
            raise EntityNotFoundError(f"Sales item with ID {item_id} not found in sales {sales_id}")

        try:
            # Update sales total
            sales.total_amount -= item.price * item.quantity
            if sales.total_amount < 0:
                sales.total_amount = 0

            # Remove item
            self.session.delete(item)

            # Update sales
            self.update(sales)

            # Return updated sales with items
            return self.get_sales_with_items(sales_id)
        except Exception as e:
            self.logger.error(f"Error removing item from sales: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to remove item from sales: {str(e)}")

    # Status and payment methods

    def update_sales_status(self, sales_id: int, status: SaleStatus,
                            notes: Optional[str] = None) -> Dict[str, Any]:
        """Update status of a sales record.

        Args:
            sales_id: ID of the sales record
            status: New status
            notes: Optional notes for the status change

        Returns:
            Updated sales data

        Raises:
            EntityNotFoundError: If sales record not found
        """
        self.logger.debug(f"Updating sales {sales_id} status to {status.value}")

        sales = self.get_by_id(sales_id)
        if not sales:
            raise EntityNotFoundError(f"Sales with ID {sales_id} not found")

        try:
            # Store old status for history
            old_status = sales.status

            # Update status
            sales.status = status

            # Add notes if provided
            if notes and hasattr(sales, 'notes'):
                if sales.notes:
                    sales.notes += f"\n[{datetime.now().isoformat()}] Status change {old_status.value} -> {status.value}: {notes}"
                else:
                    sales.notes = f"[{datetime.now().isoformat()}] Status change {old_status.value} -> {status.value}: {notes}"

            # Record status change in history (if implemented)
            # self._record_status_change(sales_id, old_status, status, notes)

            # Update sales
            self.update(sales)

            # Return updated sales
            return sales.to_dict()
        except Exception as e:
            self.logger.error(f"Error updating sales status: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to update sales status: {str(e)}")

    def update_payment_status(self, sales_id: int, payment_status: PaymentStatus,
                              payment_amount: Optional[float] = None,
                              payment_notes: Optional[str] = None) -> Dict[str, Any]:
        """Update payment status of a sales record.

        Args:
            sales_id: ID of the sales record
            payment_status: New payment status
            payment_amount: Optional payment amount
            payment_notes: Optional notes for the payment update

        Returns:
            Updated sales data

        Raises:
            EntityNotFoundError: If sales record not found
        """
        self.logger.debug(f"Updating sales {sales_id} payment status to {payment_status.value}")

        sales = self.get_by_id(sales_id)
        if not sales:
            raise EntityNotFoundError(f"Sales with ID {sales_id} not found")

        try:
            # Store old status for history
            old_payment_status = sales.payment_status

            # Update payment status
            sales.payment_status = payment_status

            # Add payment amount if provided
            if payment_amount is not None:
                # This would typically record the payment in a payment history table
                # For this example, we'll just add it to notes
                payment_record = f"Payment of {payment_amount} recorded on {datetime.now().isoformat()}"
                if payment_notes:
                    payment_record += f": {payment_notes}"

                if hasattr(sales, 'notes'):
                    if sales.notes:
                        sales.notes += f"\n{payment_record}"
                    else:
                        sales.notes = payment_record

            # Update sales
            self.update(sales)

            # Return updated sales
            return sales.to_dict()
        except Exception as e:
            self.logger.error(f"Error updating payment status: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to update payment status: {str(e)}")

    # Analytics and reporting methods

    def get_sales_by_period(self, period: str, start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get sales aggregated by period (day, week, month, year).

        Args:
            period: Aggregation period ('day', 'week', 'month', 'year')
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            List of sales aggregates by period
        """
        self.logger.debug(f"Getting sales by {period} from {start_date} to {end_date}")

        # Build query
        query = self.session.query(Sales)

        # Apply date filters if provided
        if start_date:
            query = query.filter(Sales.created_at >= start_date)
        if end_date:
            query = query.filter(Sales.created_at <= end_date)

        # Define grouping based on period
        if period == 'day':
            # Group by day
            results = self.session.query(
                func.date_trunc('day', Sales.created_at).label('period'),
                func.count().label('order_count'),
                func.sum(Sales.total_amount).label('total_sales')
            ).filter(
                query.whereclause
            ).group_by(
                func.date_trunc('day', Sales.created_at)
            ).order_by(
                func.date_trunc('day', Sales.created_at)
            ).all()

            # Format results
            return [{
                'period': period_date.strftime('%Y-%m-%d'),
                'period_type': 'day',
                'order_count': order_count,
                'total_sales': float(total_sales) if total_sales else 0
            } for period_date, order_count, total_sales in results]

        elif period == 'week':
            # Group by week
            results = self.session.query(
                func.date_trunc('week', Sales.created_at).label('period'),
                func.count().label('order_count'),
                func.sum(Sales.total_amount).label('total_sales')
            ).filter(
                query.whereclause
            ).group_by(
                func.date_trunc('week', Sales.created_at)
            ).order_by(
                func.date_trunc('week', Sales.created_at)
            ).all()

            # Format results
            return [{
                'period': period_date.strftime('%Y-%m-%d'),
                'period_type': 'week',
                'order_count': order_count,
                'total_sales': float(total_sales) if total_sales else 0
            } for period_date, order_count, total_sales in results]

        elif period == 'month':
            # Group by month
            results = self.session.query(
                func.date_trunc('month', Sales.created_at).label('period'),
                func.count().label('order_count'),
                func.sum(Sales.total_amount).label('total_sales')
            ).filter(
                query.whereclause
            ).group_by(
                func.date_trunc('month', Sales.created_at)
            ).order_by(
                func.date_trunc('month', Sales.created_at)
            ).all()

            # Format results
            return [{
                'period': period_date.strftime('%Y-%m'),
                'period_type': 'month',
                'order_count': order_count,
                'total_sales': float(total_sales) if total_sales else 0
            } for period_date, order_count, total_sales in results]

        elif period == 'year':
            # Group by year
            results = self.session.query(
                extract('year', Sales.created_at).label('year'),
                func.count().label('order_count'),
                func.sum(Sales.total_amount).label('total_sales')
            ).filter(
                query.whereclause
            ).group_by(
                extract('year', Sales.created_at)
            ).order_by(
                extract('year', Sales.created_at)
            ).all()

            # Format results
            return [{
                'period': str(int(year)),
                'period_type': 'year',
                'order_count': order_count,
                'total_sales': float(total_sales) if total_sales else 0
            } for year, order_count, total_sales in results]

        else:
            # Invalid period
            raise ValueError(f"Invalid period: {period}. Must be 'day', 'week', 'month', or 'year'")

    def get_product_sales_analysis(self, start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Analyze product sales performance.

        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            List of product sales analytics
        """
        self.logger.debug(f"Analyzing product sales from {start_date} to {end_date}")
        from database.models.sales_item import SalesItem
        from database.models.product import Product

        # Build query
        query = self.session.query(
            Product.id,
            Product.name,
            func.sum(SalesItem.quantity).label('quantity_sold'),
            func.sum(SalesItem.price * SalesItem.quantity).label('total_revenue'),
            func.count(Sales.id.distinct()).label('order_count')
        ).join(
            SalesItem, SalesItem.product_id == Product.id
        ).join(
            Sales, Sales.id == SalesItem.sales_id
        )

        # Apply date filters if provided
        if start_date:
            query = query.filter(Sales.created_at >= start_date)
        if end_date:
            query = query.filter(Sales.created_at <= end_date)

        # Group and order results
        query = query.group_by(
            Product.id, Product.name
        ).order_by(
            func.sum(SalesItem.price * SalesItem.quantity).desc()
        )

        # Execute query
        results = query.all()

        # Format results
        return [{
            'product_id': product_id,
            'product_name': product_name,
            'quantity_sold': quantity_sold,
            'total_revenue': float(total_revenue) if total_revenue else 0,
            'order_count': order_count,
            'average_order_value': float(total_revenue) / order_count if order_count > 0 else 0
        } for product_id, product_name, quantity_sold, total_revenue, order_count in results]

    # GUI-specific functionality

    def get_sales_dashboard_data(self) -> Dict[str, Any]:
        """Get data for sales dashboard in GUI.

        Returns:
            Dictionary with dashboard data
        """
        self.logger.debug("Getting sales dashboard data")

        # Count by status
        status_counts = self.session.query(
            Sales.status,
            func.count().label('count')
        ).group_by(Sales.status).all()

        status_data = {status.value: count for status, count in status_counts}

        # Count by payment status
        payment_status_counts = self.session.query(
            Sales.payment_status,
            func.count().label('count')
        ).group_by(Sales.payment_status).all()

        payment_status_data = {status.value: count for status, count in payment_status_counts}

        # Recent sales
        recent_sales = [s.to_dict() for s in self.get_recent_sales(5)]

        # Sales by period (last 12 months)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        sales_by_month = self.get_sales_by_period('month', start_date, end_date)

        # Total sales metrics
        total_sales_query = self.session.query(
            func.count().label('order_count'),
            func.sum(Sales.total_amount).label('total_revenue'),
            func.avg(Sales.total_amount).label('average_order_value')
        )

        total_sales = total_sales_query.first()

        # Combine all data
        return {
            'status_counts': status_data,
            'payment_status_counts': payment_status_data,
            'recent_sales': recent_sales,
            'sales_by_month': sales_by_month,
            'total_metrics': {
                'order_count': total_sales.order_count or 0,
                'total_revenue': float(total_sales.total_revenue) if total_sales.total_revenue else 0,
                'average_order_value': float(total_sales.average_order_value) if total_sales.average_order_value else 0
            }
        }

    def filter_sales_for_gui(self,
                             search_term: Optional[str] = None,
                             customer_id: Optional[int] = None,
                             statuses: Optional[List[SaleStatus]] = None,
                             payment_statuses: Optional[List[PaymentStatus]] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             sort_by: str = 'created_at',
                             sort_dir: str = 'desc',
                             page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate sales for GUI display.

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
        self.logger.debug(f"Filtering sales for GUI: customer={customer_id}, statuses={statuses}")
        from database.models.customer import Customer

        # Build query
        query = self.session.query(Sales)

        # Apply customer filter if provided
        if customer_id:
            query = query.filter(Sales.customer_id == customer_id)

        # Apply status filter if provided
        if statuses:
            query = query.filter(Sales.status.in_(statuses))

        # Apply payment status filter if provided
        if payment_statuses:
            query = query.filter(Sales.payment_status.in_(payment_statuses))

        # Apply date filters if provided
        if start_date:
            query = query.filter(Sales.created_at >= start_date)
        if end_date:
            query = query.filter(Sales.created_at <= end_date)

        # Apply search filter if provided
        if search_term:
            # Join with customer to search by customer name
            query = query.join(
                Customer, Customer.id == Sales.customer_id
            ).filter(
                or_(
                    Customer.name.ilike(f"%{search_term}%"),
                    Customer.email.ilike(f"%{search_term}%"),
                    Sales.id.cast(String).like(f"%{search_term}%")  # Search by ID as string
                )
            )

        # Get total count for pagination
        total_count = query.count()

        # Apply sorting
        if sort_by == 'created_at':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Sales.created_at.desc())
            else:
                query = query.order_by(Sales.created_at.asc())
        elif sort_by == 'customer':
            # Join with customer for sorting if not already joined
            if not search_term:
                query = query.join(Customer, Customer.id == Sales.customer_id)

            if sort_dir.lower() == 'desc':
                query = query.order_by(Customer.name.desc())
            else:
                query = query.order_by(Customer.name.asc())
        elif sort_by == 'status':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Sales.status.desc())
            else:
                query = query.order_by(Sales.status.asc())
        elif sort_by == 'payment_status':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Sales.payment_status.desc())
            else:
                query = query.order_by(Sales.payment_status.asc())
        elif sort_by == 'total_amount':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Sales.total_amount.desc())
            else:
                query = query.order_by(Sales.total_amount.asc())
        else:
            # Default to created_at desc
            query = query.order_by(Sales.created_at.desc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        sales_list = query.all()

        # Get customer information for each sale
        customer_ids = [s.customer_id for s in sales_list if s.customer_id]

        customers = {}
        if customer_ids:
            customer_query = self.session.query(Customer).filter(Customer.id.in_(customer_ids))
            customers = {c.id: c for c in customer_query.all()}

        # Format results
        items = []
        for sale in sales_list:
            sale_dict = sale.to_dict()

            # Add customer info
            if sale.customer_id and sale.customer_id in customers:
                customer = customers[sale.customer_id]
                sale_dict['customer'] = {
                    'id': customer.id,
                    'name': customer.name,
                    'email': customer.email
                }

            items.append(sale_dict)

        # Return paginated results with metadata
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'pages': (total_count + page_size - 1) // page_size,
            'has_next': page < ((total_count + page_size - 1) // page_size),
            'has_prev': page > 1
        }

    def export_sales_data(self, format: str = "csv",
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
        self.logger.debug(f"Exporting sales data in {format} format from {start_date} to {end_date}")

        # Build query
        query = self.session.query(Sales)

        # Apply date filters if provided
        if start_date:
            query = query.filter(Sales.created_at >= start_date)
        if end_date:
            query = query.filter(Sales.created_at <= end_date)

        # Execute query
        sales_list = query.all()

        # Transform to dictionaries
        data = [s.to_dict() for s in sales_list]

        # Create metadata
        metadata = {
            'count': len(data),
            'timestamp': datetime.now().isoformat(),
            'format': format,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'total_revenue': sum(s.total_amount for s in sales_list)
        }

        return {
            'data': data,
            'metadata': metadata
        }