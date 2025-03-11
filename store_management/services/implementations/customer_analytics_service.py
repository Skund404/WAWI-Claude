# services/implementations/customer_analytics_service.py
"""
Implementation of customer analytics service.

This module provides analytics functionality for customer data including
segmentation, lifetime value calculation, and purchase patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import sqlalchemy as sa
from di.inject import inject
from sqlalchemy.orm import Session

from database.models.customer import Customer
from database.models.enums import CustomerStatus, CustomerTier
from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.repositories.customer_repository import CustomerRepository
from database.repositories.sales_repository import SalesRepository
from services.base_service import BaseService
from services.dto.analytics_dto import CustomerAnalyticsDTO, CustomerSegmentDTO
from services.exceptions import NotFoundError, ValidationError


@inject
class CustomerAnalyticsService(BaseService):
    """Service for analyzing customer data and generating customer analytics."""

    def __init__(
            self,
            session: Session,
            customer_repository: Optional[CustomerRepository] = None,
            sales_repository: Optional[SalesRepository] = None
    ):
        """
        Initialize the customer analytics service.

        Args:
            session: SQLAlchemy database session
            customer_repository: Repository for customer data access
            sales_repository: Repository for sales data access
        """
        super().__init__(session)
        self.customer_repository = customer_repository or CustomerRepository(session)
        self.sales_repository = sales_repository or SalesRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_customer_analytics(self, customer_id: int) -> CustomerAnalyticsDTO:
        """
        Get comprehensive analytics for a specific customer.

        Args:
            customer_id: The ID of the customer

        Returns:
            CustomerAnalyticsDTO with analytics data

        Raises:
            NotFoundError: If the customer doesn't exist
        """
        # Check if customer exists
        customer = self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer with ID {customer_id} not found")

        # Get customer's sales
        sales = self.sales_repository.get_by_criteria({'customer_id': customer_id})

        if not sales:
            # Return basic analytics for customer with no sales
            return CustomerAnalyticsDTO(
                customer_id=customer_id,
                total_spent=0.0,
                total_orders=0,
                avg_order_value=0.0,
                first_purchase_date=datetime.now(),
                last_purchase_date=None,
                days_since_last_purchase=None,
                purchase_frequency_days=None,
                segment="New",
                lifetime_value=0.0,
                order_trend=[],
                product_preferences=[],
                retention_score=0.0
            )

        # Calculate basic metrics
        total_spent = sum(sale.total_amount for sale in sales)
        total_orders = len(sales)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0

        # Determine first and last purchase dates
        sale_dates = [sale.created_at for sale in sales]
        first_purchase_date = min(sale_dates)
        last_purchase_date = max(sale_dates)
        days_since_last_purchase = (datetime.now() - last_purchase_date).days

        # Calculate purchase frequency
        if total_orders > 1:
            days_between_first_last = (last_purchase_date - first_purchase_date).days
            purchase_frequency_days = days_between_first_last / (total_orders - 1) if days_between_first_last > 0 else 0
        else:
            purchase_frequency_days = None

        # Determine customer segment based on RFM
        segment = self._calculate_customer_segment(
            recency=days_since_last_purchase,
            frequency=total_orders,
            monetary=total_spent
        )

        # Calculate customer lifetime value
        lifetime_value = self._calculate_lifetime_value(customer_id)

        # Get order trend (last 12 months)
        order_trend = self._get_order_trend(customer_id)

        # Get product preferences
        product_preferences = self._get_product_preferences(customer_id)

        # Calculate retention score
        retention_score = self._calculate_retention_score(
            days_since_last_purchase=days_since_last_purchase,
            purchase_frequency=purchase_frequency_days,
            total_orders=total_orders
        )

        return CustomerAnalyticsDTO(
            customer_id=customer_id,
            total_spent=total_spent,
            total_orders=total_orders,
            avg_order_value=avg_order_value,
            first_purchase_date=first_purchase_date,
            last_purchase_date=last_purchase_date,
            days_since_last_purchase=days_since_last_purchase,
            purchase_frequency_days=purchase_frequency_days,
            segment=segment,
            lifetime_value=lifetime_value,
            order_trend=order_trend,
            product_preferences=product_preferences,
            retention_score=retention_score
        )

    def get_all_customers_analytics(
            self,
            time_period: str = "yearly",
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            limit: int = 100,
            offset: int = 0
    ) -> List[CustomerAnalyticsDTO]:
        """
        Get analytics for all customers.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period
            limit: Maximum number of customers to return
            offset: Offset for pagination

        Returns:
            List of CustomerAnalyticsDTO with analytics data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get all customers with pagination
        customers = self.customer_repository.get_all(limit=limit, offset=offset)

        # For each customer, get their analytics
        result = []
        for customer in customers:
            try:
                analytics = self.get_customer_analytics(customer.id)
                result.append(analytics)
            except Exception as e:
                self.logger.error(f"Error calculating analytics for customer {customer.id}: {str(e)}")
                # Continue with next customer

        return result

    def segment_customers(self,
                          segment_by: str = "rfm",
                          time_period: str = "yearly",
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None
                          ) -> List[CustomerSegmentDTO]:
        """
        Segment customers based on specified criteria.

        Args:
            segment_by: Segmentation method (e.g., "rfm", "value", "frequency")
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            List of CustomerSegmentDTO with segmentation data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        if segment_by == "rfm":
            return self._segment_by_rfm(start_date, end_date)
        elif segment_by == "value":
            return self._segment_by_value(start_date, end_date)
        elif segment_by == "frequency":
            return self._segment_by_frequency(start_date, end_date)
        else:
            raise ValidationError(f"Unknown segmentation method: {segment_by}")

    def get_customer_lifetime_value(self, customer_id: int) -> float:
        """
        Calculate customer lifetime value for a specific customer.

        Args:
            customer_id: The ID of the customer

        Returns:
            Customer lifetime value as a float
        """
        return self._calculate_lifetime_value(customer_id)

    def get_retention_analysis(self,
                               time_period: str = "yearly",
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None
                               ) -> Dict[str, Any]:
        """
        Get customer retention analysis.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            Dictionary with retention analysis data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get all customers with sales in the given period
        query = self.session.query(Customer) \
            .join(Sales, Customer.id == Sales.customer_id) \
            .filter(Sales.created_at.between(start_date, end_date)) \
            .distinct()

        customers_with_sales = query.all()

        if not customers_with_sales:
            return {
                "total_customers": 0,
                "retained_customers": 0,
                "retention_rate": 0,
                "churn_rate": 0,
                "avg_days_between_purchases": 0,
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date
            }

        # Calculate retention metrics
        total_customers = len(customers_with_sales)
        active_customers = sum(1 for c in customers_with_sales if c.status == CustomerStatus.ACTIVE)

        # Get average days between purchases
        avg_days_between_purchases = self._calculate_avg_days_between_purchases(
            [c.id for c in customers_with_sales],
            start_date,
            end_date
        )

        # Calculate retention rate
        retention_rate = (active_customers / total_customers) * 100 if total_customers > 0 else 0
        churn_rate = 100 - retention_rate

        return {
            "total_customers": total_customers,
            "retained_customers": active_customers,
            "retention_rate": retention_rate,
            "churn_rate": churn_rate,
            "avg_days_between_purchases": avg_days_between_purchases,
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date
        }

    # Helper methods
    def _calculate_customer_segment(self, recency: int, frequency: int, monetary: float) -> str:
        """
        Calculate customer segment based on RFM (Recency, Frequency, Monetary) analysis.

        Args:
            recency: Days since last purchase
            frequency: Number of orders
            monetary: Total amount spent

        Returns:
            Customer segment name
        """
        # Simple RFM segmentation
        r_score = 1 if recency <= 30 else (2 if recency <= 90 else (3 if recency <= 180 else 4))
        f_score = 4 if frequency >= 10 else (3 if frequency >= 5 else (2 if frequency >= 2 else 1))
        m_score = 4 if monetary >= 1000 else (3 if monetary >= 500 else (2 if monetary >= 100 else 1))

        avg_score = (r_score + f_score + m_score) / 3

        if avg_score >= 3.5:
            return "Champions"
        elif avg_score >= 3:
            return "Loyal Customers"
        elif avg_score >= 2.5:
            return "Potential Loyalists"
        elif avg_score >= 2:
            return "Promising"
        elif avg_score >= 1.5:
            return "Needs Attention"
        else:
            return "At Risk"

    def _calculate_lifetime_value(self, customer_id: int) -> float:
        """
        Calculate customer lifetime value.

        Args:
            customer_id: The ID of the customer

        Returns:
            Customer lifetime value
        """
        # Get all customer's sales
        sales = self.sales_repository.get_by_criteria({'customer_id': customer_id})

        if not sales:
            return 0.0

        # Calculate basic LTV
        total_revenue = sum(sale.total_amount for sale in sales)
        avg_order_value = total_revenue / len(sales)

        # Get customer's first purchase date
        first_purchase_date = min(sale.created_at for sale in sales)
        customer_age_years = (datetime.now() - first_purchase_date).days / 365

        # If customer is very new, use 1 year as minimum for calculation
        customer_age_years = max(customer_age_years, 1)

        # Calculate average yearly value
        yearly_value = total_revenue / customer_age_years

        # Assume 5-year retention for LTV calculation
        ltv = yearly_value * 5

        return ltv

    def _get_order_trend(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        Get order trend for last 12 months.

        Args:
            customer_id: The ID of the customer

        Returns:
            List of dictionaries with month and order data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Get sales in date range
        sales = self.sales_repository.get_by_criteria({
            'customer_id': customer_id,
            'created_at_from': start_date,
            'created_at_to': end_date
        })

        # Group by month
        months_data = {}
        for i in range(12):
            month_date = end_date - timedelta(days=30 * i)
            month_key = month_date.strftime("%Y-%m")
            months_data[month_key] = {
                'month': month_date.strftime("%b %Y"),
                'orders': 0,
                'amount': 0.0
            }

        # Populate with actual data
        for sale in sales:
            month_key = sale.created_at.strftime("%Y-%m")
            if month_key in months_data:
                months_data[month_key]['orders'] += 1
                months_data[month_key]['amount'] += sale.total_amount

        # Convert to list and sort by month
        result = list(months_data.values())
        result.reverse()  # Most recent months first

        return result

    def _get_product_preferences(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        Get product preferences for a customer.

        Args:
            customer_id: The ID of the customer

        Returns:
            List of dictionaries with product preference data
        """
        # Get all customer's sales
        sales = self.sales_repository.get_by_criteria({'customer_id': customer_id})

        if not sales:
            return []

        # Get sales items for each sale
        product_counts = {}

        for sale in sales:
            # In a real implementation, this would likely be a join in the repository
            sale_items = self.session.query(SalesItem).filter(SalesItem.sales_id == sale.id).all()

            for item in sale_items:
                product_id = item.product_id
                if product_id in product_counts:
                    product_counts[product_id]['quantity'] += item.quantity
                    product_counts[product_id]['total_spent'] += (item.price * item.quantity)
                    product_counts[product_id]['orders'] += 1
                else:
                    product_counts[product_id] = {
                        'product_id': product_id,
                        'quantity': item.quantity,
                        'total_spent': item.price * item.quantity,
                        'orders': 1
                    }

        # Convert to list and sort by total spent
        preferences = list(product_counts.values())
        preferences.sort(key=lambda x: x['total_spent'], reverse=True)

        # Get product names
        for pref in preferences:
            # This would normally use a product repository
            product = self.session.query('name').filter_by(id=pref['product_id']).first()
            pref['product_name'] = product.name if product else f"Product {pref['product_id']}"

        return preferences[:5]  # Return top 5 preferences

    def _calculate_retention_score(self, days_since_last_purchase: int,
                                   purchase_frequency: Optional[float],
                                   total_orders: int) -> float:
        """
        Calculate retention score for a customer.

        Args:
            days_since_last_purchase: Days since last purchase
            purchase_frequency: Average days between purchases
            total_orders: Total number of orders

        Returns:
            Retention score (0-100)
        """
        # New or inactive customers
        if total_orders == 0 or purchase_frequency is None:
            return 0.0

        # Recency score (0-40 points)
        if days_since_last_purchase <= 30:
            recency_score = 40
        elif days_since_last_purchase <= 90:
            recency_score = 30
        elif days_since_last_purchase <= 180:
            recency_score = 20
        elif days_since_last_purchase <= 365:
            recency_score = 10
        else:
            recency_score = 0

        # Frequency score (0-30 points)
        frequency_score = min(30, total_orders * 2)

        # Consistency score (0-30 points)
        if purchase_frequency <= 30:  # Monthly shopper
            consistency_score = 30
        elif purchase_frequency <= 90:  # Quarterly shopper
            consistency_score = 20
        elif purchase_frequency <= 180:  # Bi-annual shopper
            consistency_score = 10
        else:
            consistency_score = 5

        return recency_score + frequency_score + consistency_score

    def _segment_by_rfm(self, start_date: datetime, end_date: datetime) -> List[CustomerSegmentDTO]:
        """
        Segment customers by RFM (Recency, Frequency, Monetary).

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            List of CustomerSegmentDTO with segmentation data
        """
        # Get all customers with sales in the period
        customers = self.session.query(Customer) \
            .join(Sales, Customer.id == Sales.customer_id) \
            .filter(Sales.created_at.between(start_date, end_date)) \
            .distinct().all()

        # Calculate RFM scores for each customer
        rfm_data = {}
        segments = {
            "Champions": [],
            "Loyal Customers": [],
            "Potential Loyalists": [],
            "Promising": [],
            "Needs Attention": [],
            "At Risk": []
        }

        for customer in customers:
            analytics = self.get_customer_analytics(customer.id)
            segment = analytics.segment

            if segment not in segments:
                segments[segment] = []

            segments[segment].append(customer.id)

            if segment not in rfm_data:
                rfm_data[segment] = {
                    'total_revenue': 0,
                    'customer_count': 0,
                    'total_orders': 0,
                    'engagement_score': 0,
                    'retention_rate': 0
                }

            rfm_data[segment]['total_revenue'] += analytics.total_spent
            rfm_data[segment]['customer_count'] += 1
            rfm_data[segment]['total_orders'] += analytics.total_orders
            if analytics.retention_score:
                rfm_data[segment]['engagement_score'] += analytics.retention_score

        # Calculate averages and create DTOs
        result = []
        for segment, data in rfm_data.items():
            count = data['customer_count']
            if count > 0:
                avg_order_value = data['total_revenue'] / data['total_orders'] if data['total_orders'] > 0 else 0
                segment_dto = CustomerSegmentDTO(
                    segment_name=segment,
                    customer_count=count,
                    avg_order_value=avg_order_value,
                    total_revenue=data['total_revenue'],
                    engagement_score=data['engagement_score'] / count,
                    retention_rate=75.0,  # Fixed value for example
                    avg_orders_per_year=data['total_orders'] / count,
                    customer_ids=segments[segment]
                )
                result.append(segment_dto)

        return result

    def _segment_by_value(self, start_date: datetime, end_date: datetime) -> List[CustomerSegmentDTO]:
        """
        Segment customers by value (spending).

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            List of CustomerSegmentDTO with segmentation data
        """
        # Get all customers with sales in the period
        customers = self.session.query(Customer) \
            .join(Sales, Customer.id == Sales.customer_id) \
            .filter(Sales.created_at.between(start_date, end_date)) \
            .distinct().all()

        # Default segments
        segments = {
            "High Value": {"threshold": 1000, "ids": []},
            "Medium Value": {"threshold": 500, "ids": []},
            "Low Value": {"threshold": 0, "ids": []}
        }

        segment_data = {
            "High Value": {
                'total_revenue': 0,
                'customer_count': 0,
                'total_orders': 0,
                'engagement_score': 0,
                'retention_rate': 90.0  # Fixed values for example
            },
            "Medium Value": {
                'total_revenue': 0,
                'customer_count': 0,
                'total_orders': 0,
                'engagement_score': 0,
                'retention_rate': 70.0
            },
            "Low Value": {
                'total_revenue': 0,
                'customer_count': 0,
                'total_orders': 0,
                'engagement_score': 0,
                'retention_rate': 50.0
            }
        }

        # Segment customers by total spending
        for customer in customers:
            analytics = self.get_customer_analytics(customer.id)

            if analytics.total_spent >= segments["High Value"]["threshold"]:
                segment = "High Value"
            elif analytics.total_spent >= segments["Medium Value"]["threshold"]:
                segment = "Medium Value"
            else:
                segment = "Low Value"

            segments[segment]["ids"].append(customer.id)
            segment_data[segment]['total_revenue'] += analytics.total_spent
            segment_data[segment]['customer_count'] += 1
            segment_data[segment]['total_orders'] += analytics.total_orders
            if analytics.retention_score:
                segment_data[segment]['engagement_score'] += analytics.retention_score

        # Create DTOs
        result = []
        for segment, data in segment_data.items():
            count = data['customer_count']
            if count > 0:
                avg_order_value = data['total_revenue'] / data['total_orders'] if data['total_orders'] > 0 else 0
                segment_dto = CustomerSegmentDTO(
                    segment_name=segment,
                    customer_count=count,
                    avg_order_value=avg_order_value,
                    total_revenue=data['total_revenue'],
                    engagement_score=data['engagement_score'] / count if data['engagement_score'] > 0 else 0,
                    retention_rate=data['retention_rate'],
                    avg_orders_per_year=data['total_orders'] / count,
                    customer_ids=segments[segment]["ids"]
                )
                result.append(segment_dto)

        return result

    def _segment_by_frequency(self, start_date: datetime, end_date: datetime) -> List[CustomerSegmentDTO]:
        """
        Segment customers by purchase frequency.

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            List of CustomerSegmentDTO with segmentation data
        """
        # Get all customers with sales in the period
        customers = self.session.query(Customer) \
            .join(Sales, Customer.id == Sales.customer_id) \
            .filter(Sales.created_at.between(start_date, end_date)) \
            .distinct().all()

        # Default segments
        segments = {
            "Frequent": {"threshold": 5, "ids": []},
            "Regular": {"threshold": 2, "ids": []},
            "Occasional": {"threshold": 0, "ids": []}
        }

        segment_data = {
            "Frequent": {
                'total_revenue': 0,
                'customer_count': 0,
                'total_orders': 0,
                'engagement_score': 0,
                'retention_rate': 85.0  # Fixed values for example
            },
            "Regular": {
                'total_revenue': 0,
                'customer_count': 0,
                'total_orders': 0,
                'engagement_score': 0,
                'retention_rate': 65.0
            },
            "Occasional": {
                'total_revenue': 0,
                'customer_count': 0,
                'total_orders': 0,
                'engagement_score': 0,
                'retention_rate': 45.0
            }
        }

        # Segment customers by purchase frequency
        for customer in customers:
            # Count orders in period
            orders_count = self.session.query(Sales) \
                .filter(Sales.customer_id == customer.id) \
                .filter(Sales.created_at.between(start_date, end_date)) \
                .count()

            # Get customer analytics
            analytics = self.get_customer_analytics(customer.id)

            if orders_count >= segments["Frequent"]["threshold"]:
                segment = "Frequent"
            elif orders_count >= segments["Regular"]["threshold"]:
                segment = "Regular"
            else:
                segment = "Occasional"

            segments[segment]["ids"].append(customer.id)
            segment_data[segment]['total_revenue'] += analytics.total_spent
            segment_data[segment]['customer_count'] += 1
            segment_data[segment]['total_orders'] += analytics.total_orders
            if analytics.retention_score:
                segment_data[segment]['engagement_score'] += analytics.retention_score

        # Create DTOs
        result = []
        for segment, data in segment_data.items():
            count = data['customer_count']
            if count > 0:
                avg_order_value = data['total_revenue'] / data['total_orders'] if data['total_orders'] > 0 else 0
                segment_dto = CustomerSegmentDTO(
                    segment_name=segment,
                    customer_count=count,
                    avg_order_value=avg_order_value,
                    total_revenue=data['total_revenue'],
                    engagement_score=data['engagement_score'] / count if data['engagement_score'] > 0 else 0,
                    retention_rate=data['retention_rate'],
                    avg_orders_per_year=data['total_orders'] / count,
                    customer_ids=segments[segment]["ids"]
                )
                result.append(segment_dto)

        return result

    def _calculate_avg_days_between_purchases(
            self,
            customer_ids: List[int],
            start_date: datetime,
            end_date: datetime
    ) -> float:
        """
        Calculate average days between purchases for a group of customers.

        Args:
            customer_ids: List of customer IDs
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            Average days between purchases
        """
        if not customer_ids:
            return 0

        # Dictionary to store intervals for each customer
        customer_intervals = {customer_id: [] for customer_id in customer_ids}

        # Get all sales for these customers in date range, ordered by customer and date
        sales = self.session.query(Sales) \
            .filter(Sales.customer_id.in_(customer_ids)) \
            .filter(Sales.created_at.between(start_date, end_date)) \
            .order_by(Sales.customer_id, Sales.created_at) \
            .all()

        # Calculate intervals for each customer
        prev_customer = None
        prev_date = None

        for sale in sales:
            if prev_customer == sale.customer_id and prev_date:
                interval = (sale.created_at - prev_date).days
                customer_intervals[sale.customer_id].append(interval)

            prev_customer = sale.customer_id
            prev_date = sale.created_at

        # Calculate average across all customers
        all_intervals = []
        for intervals in customer_intervals.values():
            all_intervals.extend(intervals)

        return sum(all_intervals) / len(all_intervals) if all_intervals else 0