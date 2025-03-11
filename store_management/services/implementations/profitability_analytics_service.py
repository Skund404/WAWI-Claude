# services/implementations/profitability_analytics_service.py
"""
Implementation of profitability analytics service.

This module provides analytics functionality for profitability data including
margin analysis, cost breakdowns, and profitability trends.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import sqlalchemy as sa
from di.inject import inject
from sqlalchemy.orm import Session

from database.models.enums import ProjectType
from database.models.material import Material
from database.models.product import Product
from database.models.project import Project
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem
from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.repositories.product_repository import ProductRepository
from database.repositories.project_repository import ProjectRepository
from database.repositories.sales_repository import SalesRepository
from database.repositories.purchase_repository import PurchaseRepository
from services.base_service import BaseService
from services.dto.analytics_dto import ProfitMarginDTO, ProfitabilityAnalyticsDTO
from services.exceptions import NotFoundError, ValidationError


@inject
class ProfitabilityAnalyticsService(BaseService):
    """Service for analyzing profitability data."""

    def __init__(
            self,
            session: Session,
            product_repository: Optional[ProductRepository] = None,
            project_repository: Optional[ProjectRepository] = None,
            sales_repository: Optional[SalesRepository] = None,
            purchase_repository: Optional[PurchaseRepository] = None
    ):
        """
        Initialize the profitability analytics service.

        Args:
            session: SQLAlchemy database session
            product_repository: Repository for product data access
            project_repository: Repository for project data access
            sales_repository: Repository for sales data access
            purchase_repository: Repository for purchase data access
        """
        super().__init__(session)
        self.product_repository = product_repository or ProductRepository(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.sales_repository = sales_repository or SalesRepository(session)
        self.purchase_repository = purchase_repository or PurchaseRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_profitability_analytics(self,
                                    time_period: str = "yearly",
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None,
                                    item_type: Optional[str] = None
                                    ) -> ProfitabilityAnalyticsDTO:
        """
        Get profitability analytics for products, projects, or all items.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period
            item_type: Type of items to analyze ("product", "project", or None for all)

        Returns:
            ProfitabilityAnalyticsDTO with profitability data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get margin by item type
        margin_by_item = []
        total_revenue = 0.0
        total_cost = 0.0

        if item_type == "product" or item_type is None:
            product_margins = self._get_product_margins(start_date, end_date)
            margin_by_item.extend(product_margins)

            # Add to totals
            for margin in product_margins:
                total_revenue += margin.revenue
                total_cost += margin.cost

        if item_type == "project" or item_type is None:
            project_margins = self._get_project_margins(start_date, end_date)
            margin_by_item.extend(project_margins)

            # Add to totals
            for margin in project_margins:
                total_revenue += margin.revenue
                total_cost += margin.cost

        # Calculate overall metrics
        total_profit = total_revenue - total_cost
        overall_margin_percentage = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0

        # Get top performers (top 5 by margin)
        margin_by_item.sort(key=lambda x: x.margin_percentage, reverse=True)
        top_performers = margin_by_item[:5] if margin_by_item else []

        # Get underperformers (bottom 5 by margin)
        underperformers = margin_by_item[-5:] if len(margin_by_item) >= 5 else []
        underperformers.reverse()  # Lowest margin first

        # Get margin trend
        margin_trend = self._get_margin_trend(time_period, start_date, end_date, item_type)

        return ProfitabilityAnalyticsDTO(
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_profit=total_profit,
            overall_margin_percentage=overall_margin_percentage,
            time_period=time_period,
            start_date=start_date,
            end_date=end_date,
            margin_by_item=margin_by_item,
            margin_trend=margin_trend,
            top_performers=top_performers,
            underperformers=underperformers
        )

    def get_product_profitability(self,
                                  product_id: int,
                                  time_period: str = "yearly",
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None
                                  ) -> Dict[str, Any]:
        """
        Get profitability analysis for a specific product.

        Args:
            product_id: The ID of the product
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            Dictionary with product profitability data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Check if product exists
        product = self.product_repository.get_by_id(product_id)
        if not product:
            raise NotFoundError(f"Product with ID {product_id} not found")

        # Get sales data for this product in the time period
        sales_items = self.session.query(SalesItem) \
            .join(Sales, SalesItem.sales_id == Sales.id) \
            .filter(SalesItem.product_id == product_id) \
            .filter(Sales.created_at.between(start_date, end_date)) \
            .all()

        if not sales_items:
            return {
                "product_id": product_id,
                "product_name": product.name,
                "revenue": 0.0,
                "cost": 0.0,
                "profit": 0.0,
                "margin_percentage": 0.0,
                "units_sold": 0,
                "average_price": 0.0,
                "cost_breakdown": {
                    "material": 0.0,
                    "labor": 0.0,
                    "overhead": 0.0
                },
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date
            }

        # Calculate revenue, cost, and profit
        revenue = sum(item.price * item.quantity for item in sales_items)
        units_sold = sum(item.quantity for item in sales_items)

        # Get base product cost
        base_cost_per_unit = product.cost_price if hasattr(product, 'cost_price') else 0.0

        # Estimate cost breakdown
        material_cost_percentage = 0.60  # Example: 60% of cost is material
        labor_cost_percentage = 0.25  # Example: 25% of cost is labor
        overhead_cost_percentage = 0.15  # Example: 15% of cost is overhead

        cost_per_unit = base_cost_per_unit
        total_cost = cost_per_unit * units_sold

        # If total cost is 0 or very low, estimate based on price
        if total_cost < revenue * 0.1:  # Unrealistically low cost
            cost_per_unit = revenue * 0.6 / units_sold  # Assume 60% cost
            total_cost = cost_per_unit * units_sold

        material_cost = total_cost * material_cost_percentage
        labor_cost = total_cost * labor_cost_percentage
        overhead_cost = total_cost * overhead_cost_percentage

        profit = revenue - total_cost
        margin_percentage = (profit / revenue * 100) if revenue > 0 else 0.0

        return {
            "product_id": product_id,
            "product_name": product.name,
            "revenue": revenue,
            "cost": total_cost,
            "profit": profit,
            "margin_percentage": margin_percentage,
            "units_sold": units_sold,
            "average_price": revenue / units_sold if units_sold > 0 else 0.0,
            "cost_breakdown": {
                "material": material_cost,
                "labor": labor_cost,
                "overhead": overhead_cost
            },
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date
        }

    def get_project_profitability(self,
                                  project_id: int,
                                  include_breakdown: bool = False
                                  ) -> Dict[str, Any]:
        """
        Get profitability analysis for a specific project.

        Args:
            project_id: The ID of the project
            include_breakdown: Whether to include detailed cost breakdown

        Returns:
            Dictionary with project profitability data
        """
        # Check if project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get associated sales if any
        sales = None
        if hasattr(project, 'sales_id') and project.sales_id:
            sales = self.sales_repository.get_by_id(project.sales_id)

        # Calculate revenue
        revenue = 0.0
        if sales:
            revenue = sales.total_amount

        # Calculate project costs
        # In a real implementation, this would include material costs, labor costs, etc.

        # For simplicity, we'll estimate costs based on the project
        estimated_material_cost = 0.0
        estimated_labor_cost = 0.0
        estimated_overhead_cost = 0.0

        # If the project has components, calculate materials cost
        if hasattr(project, 'components') and project.components:
            for component in project.components:
                # In a real implementation, this would calculate the actual material costs
                # based on the component's materials and quantities
                estimated_material_cost += 50.0  # Placeholder
        else:
            # Estimate material costs as a percentage of revenue
            estimated_material_cost = revenue * 0.3  # Example: 30% of revenue

        # Estimate labor costs
        if hasattr(project, 'start_date') and hasattr(project, 'end_date') and project.start_date and project.end_date:
            # Calculate duration in days
            duration = (project.end_date - project.start_date).days
            estimated_labor_cost = duration * 100.0  # Example: $100 per day
        else:
            # Estimate labor costs as a percentage of revenue
            estimated_labor_cost = revenue * 0.4  # Example: 40% of revenue

        # Estimate overhead costs
        estimated_overhead_cost = (estimated_material_cost + estimated_labor_cost) * 0.15  # Example: 15% overhead

        # Total cost
        total_cost = estimated_material_cost + estimated_labor_cost + estimated_overhead_cost

        # Profit and margin
        profit = revenue - total_cost
        margin_percentage = (profit / revenue * 100) if revenue > 0 else 0.0

        result = {
            "project_id": project_id,
            "project_name": project.name,
            "revenue": revenue,
            "cost": total_cost,
            "profit": profit,
            "margin_percentage": margin_percentage,
            "status": project.status.value if hasattr(project, 'status') else "Unknown",
        }

        if include_breakdown:
            result["cost_breakdown"] = {
                "material": estimated_material_cost,
                "labor": estimated_labor_cost,
                "overhead": estimated_overhead_cost
            }

            # If there's a start and end date, include duration
            if hasattr(project, 'start_date') and hasattr(project, 'end_date') and project.start_date:
                if project.end_date:
                    duration = (project.end_date - project.start_date).days
                else:
                    duration = (datetime.now() - project.start_date).days
                result["duration_days"] = duration

        return result

    def get_margin_trend(self,
                         item_type: Optional[str] = None,
                         item_id: Optional[int] = None,
                         time_period: str = "monthly",
                         months: int = 12
                         ) -> List[Dict[str, Any]]:
        """
        Get margin trend over time.

        Args:
            item_type: Type of item to analyze ("product", "project", or None for all)
            item_id: Optional specific item ID
            time_period: Analysis period granularity ("monthly", "quarterly", "yearly")
            months: Number of months to include in trend

        Returns:
            List of dictionaries with margin trend data
        """
        # Set date range
        end_date = datetime.now()

        if time_period == "monthly":
            start_date = end_date - timedelta(days=30 * months)
            periods = months
            delta = timedelta(days=30)
        elif time_period == "quarterly":
            start_date = end_date - timedelta(days=90 * (months // 3))
            periods = months // 3
            delta = timedelta(days=90)
        else:  # yearly
            start_date = end_date - timedelta(days=365 * (months // 12))
            periods = months // 12
            delta = timedelta(days=365)

        # If looking at a specific item
        if item_id and item_type:
            return self._get_specific_item_margin_trend(
                item_type, item_id, start_date, end_date, periods, delta, time_period
            )

        # Otherwise, get overall margin trend
        return self._get_margin_trend(time_period, start_date, end_date, item_type)

    def get_top_performers(self,
                           item_type: Optional[str] = None,
                           limit: int = 10,
                           time_period: str = "yearly",
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None
                           ) -> List[Dict[str, Any]]:
        """
        Get top performing products or projects by profitability.

        Args:
            item_type: Type of items to analyze ("product", "project", or None for all)
            limit: Maximum number of items to return
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            List of dictionaries with top performer data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get margins for all items
        margin_by_item = []

        if item_type == "product" or item_type is None:
            product_margins = self._get_product_margins(start_date, end_date)
            margin_by_item.extend(product_margins)

        if item_type == "project" or item_type is None:
            project_margins = self._get_project_margins(start_date, end_date)
            margin_by_item.extend(project_margins)

        # Sort by profit and get top performers
        margin_by_item.sort(key=lambda x: x.profit, reverse=True)
        top_performers = margin_by_item[:limit] if margin_by_item else []

        # Convert to dictionaries for easier JSON serialization
        result = []
        for item in top_performers:
            result.append({
                "item_id": item.item_id,
                "item_type": item.item_type,
                "name": item.name,
                "revenue": item.revenue,
                "cost": item.cost,
                "profit": item.profit,
                "margin_percentage": item.margin_percentage
            })

        return result

    # Helper methods
    def _get_product_margins(self, start_date: datetime, end_date: datetime) -> List[ProfitMarginDTO]:
        """
        Get profit margins for all products in the given time period.

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            List of ProfitMarginDTO objects
        """
        # Get all products with sales in the time period
        products = self.session.query(Product) \
            .join(SalesItem, Product.id == SalesItem.product_id) \
            .join(Sales, SalesItem.sales_id == Sales.id) \
            .filter(Sales.created_at.between(start_date, end_date)) \
            .distinct() \
            .all()

        result = []
        for product in products:
            # Calculate revenue and cost for this product
            sales_items = self.session.query(SalesItem) \
                .join(Sales, SalesItem.sales_id == Sales.id) \
                .filter(SalesItem.product_id == product.id) \
                .filter(Sales.created_at.between(start_date, end_date)) \
                .all()

            revenue = sum(item.price * item.quantity for item in sales_items)

            # Get product cost
            cost_per_unit = product.cost_price if hasattr(product, 'cost_price') else 0.0
            units_sold = sum(item.quantity for item in sales_items)

            # If cost is suspiciously low, estimate it
            if cost_per_unit <= 0:
                cost_per_unit = revenue * 0.6 / units_sold if units_sold > 0 else 0  # Example: 60% cost

            total_cost = cost_per_unit * units_sold
            profit = revenue - total_cost
            margin_percentage = (profit / revenue * 100) if revenue > 0 else 0.0

            # Create margins DTO
            margin = ProfitMarginDTO(
                item_id=product.id,
                item_type="product",
                name=product.name,
                revenue=revenue,
                cost=total_cost,
                profit=profit,
                margin_percentage=margin_percentage,
                overhead_cost=total_cost * 0.15,  # Example: 15% overhead
                labor_cost=total_cost * 0.25,  # Example: 25% labor
                material_cost=total_cost * 0.60  # Example: 60% material
            )

            result.append(margin)

        return result

    def _get_project_margins(self, start_date: datetime, end_date: datetime) -> List[ProfitMarginDTO]:
        """
        Get profit margins for all projects in the given time period.

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            List of ProfitMarginDTO objects
        """
        # Get all projects that were active in the time period
        projects = self.session.query(Project) \
            .filter(
            sa.or_(
                sa.and_(Project.start_date <= end_date, Project.end_date >= start_date),
                sa.and_(Project.start_date <= end_date, Project.end_date.is_(None))
            )
        ) \
            .all()

        result = []
        for project in projects:
            # Get profitability data for this project
            profitability = self.get_project_profitability(project.id, include_breakdown=True)

            # Create margins DTO
            margin = ProfitMarginDTO(
                item_id=project.id,
                item_type="project",
                name=project.name,
                revenue=profitability["revenue"],
                cost=profitability["cost"],
                profit=profitability["profit"],
                margin_percentage=profitability["margin_percentage"],
                overhead_cost=profitability.get("cost_breakdown", {}).get("overhead", 0.0),
                labor_cost=profitability.get("cost_breakdown", {}).get("labor", 0.0),
                material_cost=profitability.get("cost_breakdown", {}).get("material", 0.0)
            )

            result.append(margin)

        return result

    def _get_margin_trend(self,
                          time_period: str,
                          start_date: datetime,
                          end_date: datetime,
                          item_type: Optional[str] = None
                          ) -> List[Dict[str, Any]]:
        """
        Get margin trend over the specified time period.

        Args:
            time_period: Analysis period granularity ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period
            item_type: Type of items to analyze ("product", "project", or None for all)

        Returns:
            List of dictionaries with margin trend data
        """
        # Calculate the number of periods
        if time_period == "monthly":
            delta = timedelta(days=30)
            format_str = "%b %Y"  # Aug 2023
        elif time_period == "quarterly":
            delta = timedelta(days=90)
            format_str = "Q%q %Y"  # Q3 2023
        else:  # yearly
            delta = timedelta(days=365)
            format_str = "%Y"  # 2023

        # Create periods
        periods = []
        current_start = start_date
        while current_start < end_date:
            current_end = min(current_start + delta, end_date)
            periods.append((current_start, current_end))
            current_start = current_end

        # Calculate margins for each period
        result = []
        for period_start, period_end in periods:
            # Get revenue and cost for this period
            revenue = 0.0
            cost = 0.0

            # Product sales in this period
            if item_type == "product" or item_type is None:
                sales_items = self.session.query(SalesItem) \
                    .join(Sales, SalesItem.sales_id == Sales.id) \
                    .filter(Sales.created_at.between(period_start, period_end)) \
                    .all()

                for item in sales_items:
                    revenue += item.price * item.quantity

                    # Get product cost (simplified)
                    product = self.product_repository.get_by_id(item.product_id)
                    cost_per_unit = product.cost_price if hasattr(product, 'cost_price') and product.cost_price else 0.0

                    # If cost is suspiciously low, estimate it
                    if cost_per_unit <= 0:
                        cost_per_unit = item.price * 0.6  # Example: 60% cost

                    cost += cost_per_unit * item.quantity

            # Project costs in this period
            if item_type == "project" or item_type is None:
                projects = self.session.query(Project) \
                    .filter(
                    sa.or_(
                        sa.and_(Project.start_date <= period_end, Project.end_date >= period_start),
                        sa.and_(Project.start_date <= period_end, Project.end_date.is_(None))
                    )
                ) \
                    .all()

                for project in projects:
                    # Get associated sales if any
                    if hasattr(project, 'sales_id') and project.sales_id:
                        sales = self.sales_repository.get_by_id(project.sales_id)
                        if sales and sales.created_at.between(period_start, period_end):
                            revenue += sales.total_amount

                    # Estimate project costs for this period
                    # This is simplified - a real implementation would consider actual material usage,
                    # labor tracking, etc. during the specific period
                    profitability = self.get_project_profitability(project.id, include_breakdown=True)
                    project_cost = profitability["cost"]

                    # Apportion cost to this period based on duration overlap
                    if hasattr(project, 'start_date') and hasattr(project, 'end_date') and project.start_date:
                        project_end = project.end_date or end_date
                        project_duration = (project_end - project.start_date).days

                        if project_duration > 0:
                            overlap_start = max(period_start, project.start_date)
                            overlap_end = min(period_end, project_end)
                            overlap_days = (overlap_end - overlap_start).days

                            # Apportion cost based on overlap period
                            period_cost = project_cost * (overlap_days / project_duration)
                            cost += period_cost
                        else:
                            # Project with zero or negative duration - allocate all cost
                            cost += project_cost
                    else:
                        # Project without proper dates - allocate all cost
                        cost += project_cost

            # Calculate profit and margin
            profit = revenue - cost
            margin_percentage = (profit / revenue * 100) if revenue > 0 else 0.0

            # Format period label
            if time_period == "quarterly":
                # Custom handling for quarters - extract quarter number
                quarter = ((period_start.month - 1) // 3) + 1
                period_label = f"Q{quarter} {period_start.year}"
            else:
                period_label = period_start.strftime(format_str)

            result.append({
                "period": period_label,
                "start_date": period_start,
                "end_date": period_end,
                "revenue": revenue,
                "cost": cost,
                "profit": profit,
                "margin_percentage": margin_percentage
            })

        return result

    def _get_specific_item_margin_trend(self,
                                        item_type: str,
                                        item_id: int,
                                        start_date: datetime,
                                        end_date: datetime,
                                        periods: int,
                                        delta: timedelta,
                                        time_period: str
                                        ) -> List[Dict[str, Any]]:
        """
        Get margin trend for a specific item over time.

        Args:
            item_type: Type of item ("product" or "project")
            item_id: ID of the item
            start_date: Start date for analysis
            end_date: End date for analysis
            periods: Number of periods in the trend
            delta: Time delta for each period
            time_period: Period type ("monthly", "quarterly", "yearly")

        Returns:
            List of dictionaries with margin trend data
        """
        # Check if item exists
        if item_type == "product":
            item = self.product_repository.get_by_id(item_id)
            if not item:
                raise NotFoundError(f"Product with ID {item_id} not found")
        elif item_type == "project":
            item = self.project_repository.get_by_id(item_id)
            if not item:
                raise NotFoundError(f"Project with ID {item_id} not found")
        else:
            raise ValidationError(f"Invalid item type: {item_type}")

        # Create periods
        period_data = []
        current_start = start_date

        for _ in range(periods):
            current_end = min(current_start + delta, end_date)
            period_data.append({
                "start_date": current_start,
                "end_date": current_end,
                "revenue": 0.0,
                "cost": 0.0,
                "profit": 0.0,
                "margin_percentage": 0.0
            })
            current_start = current_end

        # Get data for each period
        if item_type == "product":
            self._get_product_period_data(item_id, period_data)
        else:  # project
            self._get_project_period_data(item_id, period_data)

        # Format result
        result = []
        for i, period in enumerate(period_data):
            # Format period label
            if time_period == "monthly":
                period_label = period["start_date"].strftime("%b %Y")
            elif time_period == "quarterly":
                quarter = ((period["start_date"].month - 1) // 3) + 1
                period_label = f"Q{quarter} {period['start_date'].year}"
            else:  # yearly
                period_label = period["start_date"].strftime("%Y")

            result.append({
                "period": period_label,
                "start_date": period["start_date"],
                "end_date": period["end_date"],
                "revenue": period["revenue"],
                "cost": period["cost"],
                "profit": period["profit"],
                "margin_percentage": period["margin_percentage"]
            })

        return result

    def _get_product_period_data(self, product_id: int, period_data: List[Dict[str, Any]]) -> None:
        """
        Get profit data for a product over multiple periods.

        Args:
            product_id: The ID of the product
            period_data: List of period dictionaries to update with data

        Returns:
            None (updates period_data in place)
        """
        for period in period_data:
            # Get sales for this product in this period
            sales_items = self.session.query(SalesItem) \
                .join(Sales, SalesItem.sales_id == Sales.id) \
                .filter(SalesItem.product_id == product_id) \
                .filter(Sales.created_at.between(period["start_date"], period["end_date"])) \
                .all()

            if not sales_items:
                continue

            # Calculate revenue
            period["revenue"] = sum(item.price * item.quantity for item in sales_items)

            # Get product cost
            product = self.product_repository.get_by_id(product_id)
            cost_per_unit = product.cost_price if hasattr(product, 'cost_price') and product.cost_price else 0.0
            units_sold = sum(item.quantity for item in sales_items)

            # If cost is suspiciously low, estimate it
            if cost_per_unit <= 0:
                cost_per_unit = period["revenue"] * 0.6 / units_sold if units_sold > 0 else 0  # Example: 60% cost

            period["cost"] = cost_per_unit * units_sold
            period["profit"] = period["revenue"] - period["cost"]
            period["margin_percentage"] = (period["profit"] / period["revenue"] * 100) if period["revenue"] > 0 else 0.0

    def _get_project_period_data(self, project_id: int, period_data: List[Dict[str, Any]]) -> None:
        """
        Get profit data for a project over multiple periods.

        Args:
            project_id: The ID of the project
            period_data: List of period dictionaries to update with data

        Returns:
            None (updates period_data in place)
        """
        # Get project data
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return

        # Get project profitability data
        profitability = self.get_project_profitability(project_id, include_breakdown=True)

        # Get project duration
        if not hasattr(project, 'start_date') or not project.start_date:
            return

        project_end = project.end_date or datetime.now()
        project_start = project.start_date
        project_duration = (project_end - project_start).days

        if project_duration <= 0:
            return

        # Get associated sales
        sales = None
        if hasattr(project, 'sales_id') and project.sales_id:
            sales = self.sales_repository.get_by_id(project.sales_id)

        total_revenue = profitability["revenue"]
        total_cost = profitability["cost"]

        # For each period, calculate overlap with project duration
        for period in period_data:
            period_start = period["start_date"]
            period_end = period["end_date"]

            # Check if period overlaps with project
            if period_end < project_start or period_start > project_end:
                continue

            # Calculate overlap duration
            overlap_start = max(period_start, project_start)
            overlap_end = min(period_end, project_end)
            overlap_days = max(0, (overlap_end - overlap_start).days)

            # Skip periods with no overlap
            if overlap_days <= 0:
                continue

            # Calculate proportion of project in this period
            period_proportion = overlap_days / project_duration

            # Allocate cost proportionally
            period["cost"] = total_cost * period_proportion

            # Allocate revenue (all to period with sales date if available)
            if sales and sales.created_at.between(period_start, period_end):
                period["revenue"] = total_revenue
            else:
                # Or distribute proportionally if no sales record
                period["revenue"] = total_revenue * period_proportion

            period["profit"] = period["revenue"] - period["cost"]
            period["margin_percentage"] = (period["profit"] / period["revenue"] * 100) if period["revenue"] > 0 else 0.0