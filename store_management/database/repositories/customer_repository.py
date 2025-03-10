# database/repositories/customer_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc

from database.models.customer import Customer
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import CustomerStatus, CustomerTier, CustomerSource


class CustomerRepository(BaseRepository[Customer]):
    """Repository for customer management operations.

    This repository provides methods for managing customer data, including
    searching, filtering, and business logic for customer analytics.
    """

    def _get_model_class(self) -> Type[Customer]:
        """Return the model class this repository manages.

        Returns:
            The Customer model class
        """
        return Customer

    # Basic query methods

    def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address.

        Args:
            email: Email address to search for

        Returns:
            Customer instance or None if not found
        """
        self.logger.debug(f"Getting customer with email '{email}'")
        return self.session.query(Customer).filter(Customer.email == email).first()

    def get_by_status(self, status: CustomerStatus) -> List[Customer]:
        """Get customers by status.

        Args:
            status: Customer status to filter by

        Returns:
            List of customer instances with the specified status
        """
        self.logger.debug(f"Getting customers with status '{status.value}'")
        return self.session.query(Customer).filter(Customer.status == status).all()

    def get_by_tier(self, tier: CustomerTier) -> List[Customer]:
        """Get customers by tier level.

        Args:
            tier: Customer tier to filter by

        Returns:
            List of customer instances with the specified tier
        """
        self.logger.debug(f"Getting customers with tier '{tier.value}'")
        return self.session.query(Customer).filter(Customer.tier == tier).all()

    def get_by_source(self, source: CustomerSource) -> List[Customer]:
        """Get customers by acquisition source.

        Args:
            source: Customer acquisition source to filter by

        Returns:
            List of customer instances with the specified source
        """
        self.logger.debug(f"Getting customers with source '{source.value}'")
        return self.session.query(Customer).filter(Customer.source == source).all()

    def search_customers(self, search_term: str) -> List[Customer]:
        """Search customers by name, email, or notes.

        Args:
            search_term: Term to search for

        Returns:
            List of matching customer instances
        """
        self.logger.debug(f"Searching customers for '{search_term}'")
        search_fields = ['first_name', 'last_name', 'email']
        if hasattr(Customer, 'notes'):
            search_fields.append('notes')

        return self.search(search_term, search_fields)

    # Sales-related methods

    def get_with_sales_history(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Get customer with complete sales history.

        Args:
            customer_id: ID of the customer

        Returns:
            Customer dictionary with sales history, or None if not found
        """
        self.logger.debug(f"Getting sales history for customer {customer_id}")
        from database.models.sales import Sales

        customer = self.get_by_id(customer_id)
        if not customer:
            return None

        # Get customer data
        result = customer.to_dict()

        # Get sales history
        sales = self.session.query(Sales). \
            filter(Sales.customer_id == customer_id). \
            order_by(Sales.created_at.desc()).all()

        result['sales'] = [sale.to_dict() for sale in sales]
        result['total_orders'] = len(sales)
        result['total_spent'] = sum(sale.total_amount for sale in sales) if sales else 0

        return result

    def calculate_customer_lifetime_value(self, customer_id: int) -> Dict[str, Any]:
        """Calculate lifetime value of customer.

        Args:
            customer_id: ID of the customer

        Returns:
            Dictionary with customer lifetime value metrics

        Raises:
            EntityNotFoundError: If customer not found
        """
        self.logger.debug(f"Calculating lifetime value for customer {customer_id}")
        from database.models.sales import Sales

        customer = self.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundError(f"Customer with ID {customer_id} not found")

        # Get all completed sales
        completed_statuses = ['COMPLETED', 'DELIVERED']
        sales = self.session.query(Sales). \
            filter(Sales.customer_id == customer_id). \
            filter(Sales.status.in_(completed_statuses)).all()

        if not sales:
            return {
                'customer_id': customer_id,
                'lifetime_value': 0,
                'average_order_value': 0,
                'first_purchase_date': None,
                'last_purchase_date': None,
                'total_orders': 0,
                'days_as_customer': 0
            }

        # Calculate metrics
        total_spent = sum(sale.total_amount for sale in sales)
        avg_order_value = total_spent / len(sales)
        first_purchase = min(sales, key=lambda s: s.created_at).created_at
        last_purchase = max(sales, key=lambda s: s.created_at).created_at

        return {
            'customer_id': customer_id,
            'lifetime_value': total_spent,
            'average_order_value': avg_order_value,
            'first_purchase_date': first_purchase.isoformat() if first_purchase else None,
            'last_purchase_date': last_purchase.isoformat() if last_purchase else None,
            'total_orders': len(sales),
            'days_as_customer': (datetime.now() - first_purchase).days if first_purchase else 0
        }

    def get_recent_customers(self, limit: int = 10) -> List[Customer]:
        """Get recently created customers.

        Args:
            limit: Maximum number of customers to return

        Returns:
            List of recently created customer instances
        """
        self.logger.debug(f"Getting {limit} most recent customers")
        if hasattr(Customer, 'created_at'):
            return self.session.query(Customer). \
                order_by(Customer.created_at.desc()).limit(limit).all()
        else:
            # If no created_at field, just return most recently added to DB
            return self.session.query(Customer).order_by(Customer.id.desc()).limit(limit).all()

    def get_top_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top customers by total spending.

        Args:
            limit: Maximum number of customers to return

        Returns:
            List of top customer dictionaries with spending information
        """
        self.logger.debug(f"Getting top {limit} customers by spending")
        from database.models.sales import Sales

        # Query for total spending by customer
        query = self.session.query(
            Customer,
            func.sum(Sales.total_amount).label('total_spent'),
            func.count(Sales.id).label('order_count')
        ).join(
            Sales, Sales.customer_id == Customer.id
        ).group_by(
            Customer.id
        ).order_by(
            func.sum(Sales.total_amount).desc()
        ).limit(limit)

        # Format results
        results = []
        for customer, total_spent, order_count in query.all():
            customer_dict = customer.to_dict()
            customer_dict['total_spent'] = total_spent
            customer_dict['order_count'] = order_count
            customer_dict['average_order_value'] = total_spent / order_count if order_count > 0 else 0
            results.append(customer_dict)

        return results

    def get_customer_segments(self) -> Dict[str, List[Dict[str, Any]]]:
        """Segment customers based on spending and order frequency.

        Returns:
            Dictionary with customer segments
        """
        self.logger.debug("Calculating customer segments")
        from database.models.sales import Sales

        # Query for customer metrics
        query = self.session.query(
            Customer,
            func.sum(Sales.total_amount).label('total_spent'),
            func.count(Sales.id).label('order_count'),
            func.max(Sales.created_at).label('last_order_date')
        ).outerjoin(
            Sales, Sales.customer_id == Customer.id
        ).group_by(
            Customer.id
        )

        now = datetime.now()
        customers = []
        for customer, total_spent, order_count, last_order_date in query.all():
            # Skip customers with no orders
            if order_count == 0:
                continue

            days_since_last_order = (now - last_order_date).days if last_order_date else 365

            # Calculate metrics
            customer_data = customer.to_dict()
            customer_data['total_spent'] = total_spent or 0
            customer_data['order_count'] = order_count or 0
            customer_data['days_since_last_order'] = days_since_last_order
            customer_data['average_order_value'] = (total_spent / order_count) if order_count > 0 else 0

            customers.append(customer_data)

        # Define segments
        segments = {
            'high_value': [],
            'regular': [],
            'infrequent': [],
            'at_risk': [],
            'inactive': []
        }

        # Add customers to segments
        avg_spent = sum(c['total_spent'] for c in customers) / len(customers) if customers else 0
        avg_frequency = sum(c['order_count'] for c in customers) / len(customers) if customers else 0

        for customer in customers:
            if customer['days_since_last_order'] > 180:
                segments['inactive'].append(customer)
            elif customer['days_since_last_order'] > 90:
                segments['at_risk'].append(customer)
            elif customer['total_spent'] > avg_spent * 1.5 and customer['order_count'] > avg_frequency:
                segments['high_value'].append(customer)
            elif customer['order_count'] > avg_frequency / 2:
                segments['regular'].append(customer)
            else:
                segments['infrequent'].append(customer)

        return segments

    # GUI-specific functionality

    def get_customer_dashboard_data(self) -> Dict[str, Any]:
        """Get data for customer dashboard in GUI.

        Returns:
            Dictionary with dashboard data
        """
        self.logger.debug("Getting customer dashboard data")

        # Count by status
        status_counts = self.session.query(
            Customer.status,
            func.count().label('count')
        ).group_by(Customer.status).all()

        status_data = {status.value: count for status, count in status_counts}

        # Count by tier
        tier_counts = self.session.query(
            Customer.tier,
            func.count().label('count')
        ).group_by(Customer.tier).all()

        tier_data = {tier.value: count for tier, count in tier_counts}

        # Count by source
        source_counts = self.session.query(
            Customer.source,
            func.count().label('count')
        ).group_by(Customer.source).all()

        source_data = {source.value: count for source, count in source_counts}

        # Get top customers
        top_customers = self.get_top_customers(5)

        # Get recent customers
        recent_customers = [c.to_dict() for c in self.get_recent_customers(5)]

        # Get sales metrics
        from database.models.sales import Sales

        sales_query = self.session.query(
            func.count().label('total_orders'),
            func.sum(Sales.total_amount).label('total_revenue'),
            func.avg(Sales.total_amount).label('average_order_value')
        )

        sales_metrics = sales_query.first()

        total_orders = sales_metrics.total_orders or 0
        total_revenue = sales_metrics.total_revenue or 0
        average_order_value = sales_metrics.average_order_value or 0

        # Combine all data
        return {
            'status_counts': status_data,
            'tier_counts': tier_data,
            'source_counts': source_data,
            'total_customers': self.count(),
            'top_customers': top_customers,
            'recent_customers': recent_customers,
            'sales_metrics': {
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'average_order_value': average_order_value
            }
        }

    def filter_customers_for_gui(self,
                                 search_term: Optional[str] = None,
                                 statuses: Optional[List[CustomerStatus]] = None,
                                 tiers: Optional[List[CustomerTier]] = None,
                                 sources: Optional[List[CustomerSource]] = None,
                                 sort_by: str = 'name',
                                 sort_dir: str = 'asc',
                                 page: int = 1,
                                 page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate customers for GUI display.

        Args:
            search_term: Optional search term
            statuses: Optional list of statuses to filter by
            tiers: Optional list of tiers to filter by
            sources: Optional list of sources to filter by
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            page: Page number
            page_size: Page size

        Returns:
            Dict with paginated results and metadata
        """
        self.logger.debug(
            f"Filtering customers for GUI: search='{search_term}', statuses={statuses}"
        )

        # Build query
        query = self.session.query(Customer)

        # Apply search filter if provided (searching on first_name, last_name, email, and optional notes)
        if search_term:
            query = query.filter(
                or_(
                    Customer.first_name.ilike(f"%{search_term}%"),
                    Customer.last_name.ilike(f"%{search_term}%"),
                    Customer.email.ilike(f"%{search_term}%"),
                    Customer.notes.ilike(f"%{search_term}%") if hasattr(Customer, 'notes') else False
                )
            )

        # Apply status filter if provided
        if statuses:
            query = query.filter(Customer.status.in_(statuses))

        # Apply tier filter if provided
        if tiers:
            query = query.filter(Customer.tier.in_(tiers))

        # Apply source filter if provided
        if sources:
            query = query.filter(Customer.source.in_(sources))

        # Get total count for pagination
        total_count = query.count()

        # Apply sorting
        if sort_by == 'name':
            # Concatenate first_name and last_name for sorting
            from sqlalchemy import func
            full_name = func.concat(Customer.first_name, " ", Customer.last_name)
            if sort_dir.lower() == 'desc':
                query = query.order_by(full_name.desc())
            else:
                query = query.order_by(full_name.asc())
        elif sort_by == 'email':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Customer.email.desc())
            else:
                query = query.order_by(Customer.email.asc())
        elif sort_by == 'status':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Customer.status.desc())
            else:
                query = query.order_by(Customer.status.asc())
        elif sort_by == 'tier':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Customer.tier.desc())
            else:
                query = query.order_by(Customer.tier.asc())
        elif sort_by == 'created_at' and hasattr(Customer, 'created_at'):
            if sort_dir.lower() == 'desc':
                query = query.order_by(Customer.created_at.desc())
            else:
                query = query.order_by(Customer.created_at.asc())
        else:
            # Default to sorting by concatenated name
            from sqlalchemy import func
            full_name = func.concat(Customer.first_name, " ", Customer.last_name)
            query = query.order_by(full_name.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query and format results
        customers = query.all()
        items = [customer.to_dict() for customer in customers]

        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'pages': (total_count + page_size - 1) // page_size,
            'has_next': page < ((total_count + page_size - 1) // page_size),
            'has_prev': page > 1
        }

    def export_customer_data(self, format: str = "csv") -> Dict[str, Any]:
        """Export customer data to specified format.

        Args:
            format: Export format ("csv" or "json")

        Returns:
            Dict with export data and metadata
        """
        self.logger.debug(f"Exporting customer data in {format} format")
        customers = self.get_all(limit=10000)  # Reasonable limit

        # Transform to dictionaries
        data = [c.to_dict() for c in customers]

        # Create metadata
        metadata = {
            'count': len(data),
            'timestamp': datetime.now().isoformat(),
            'format': format,
            'status_counts': {
                status.value: len([c for c in customers if c.status == status])
                for status in CustomerStatus
            }
        }

        return {
            'data': data,
            'metadata': metadata
        }