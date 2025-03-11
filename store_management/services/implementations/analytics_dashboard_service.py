# services/implementations/analytics_dashboard_service.py
"""
Implementation of analytics dashboard service.

This module provides integrated analytics data for dashboard display,
combining metrics from various analytics services.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from di.inject import inject
from sqlalchemy.orm import Session

from services.base_service import BaseService
from services.dto.analytics_dto import AnalyticsSummaryDTO
from services.exceptions import NotFoundError, ValidationError
from services.implementations.customer_analytics_service import CustomerAnalyticsService
from services.implementations.material_usage_analytics_service import MaterialUsageAnalyticsService
from services.implementations.profitability_analytics_service import ProfitabilityAnalyticsService
from services.implementations.project_metrics_service import ProjectMetricsService


@inject
class AnalyticsDashboardService(BaseService):
    """Service for providing integrated analytics data for dashboard display."""

    def __init__(
            self,
            session: Session,
            customer_analytics_service: Optional[CustomerAnalyticsService] = None,
            profitability_analytics_service: Optional[ProfitabilityAnalyticsService] = None,
            material_usage_analytics_service: Optional[MaterialUsageAnalyticsService] = None,
            project_metrics_service: Optional[ProjectMetricsService] = None
    ):
        """
        Initialize the analytics dashboard service.

        Args:
            session: SQLAlchemy database session
            customer_analytics_service: Service for customer analytics
            profitability_analytics_service: Service for profitability analytics
            material_usage_analytics_service: Service for material usage analytics
            project_metrics_service: Service for project metrics
        """
        super().__init__(session)
        self.customer_analytics_service = customer_analytics_service or CustomerAnalyticsService(session)
        self.profitability_analytics_service = profitability_analytics_service or ProfitabilityAnalyticsService(session)
        self.material_usage_analytics_service = material_usage_analytics_service or MaterialUsageAnalyticsService(
            session)
        self.project_metrics_service = project_metrics_service or ProjectMetricsService(session)
        self.logger = logging.getLogger(__name__)

    def get_analytics_summary(self,
                              time_period: str = "yearly",
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None
                              ) -> AnalyticsSummaryDTO:
        """
        Get summary analytics for dashboard.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            AnalyticsSummaryDTO with summary analytics data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get profitability data
        try:
            profitability_data = self.profitability_analytics_service.get_profitability_analytics(
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )

            total_revenue = profitability_data.total_revenue
            total_profit = profitability_data.total_profit
            overall_margin_percentage = profitability_data.overall_margin_percentage

            # Get top products
            top_products = self.profitability_analytics_service.get_top_performers(
                item_type="product",
                limit=5,
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            self.logger.error(f"Error getting profitability data: {str(e)}")
            total_revenue = 0.0
            total_profit = 0.0
            overall_margin_percentage = 0.0
            top_products = []

        # Get top customers
        try:
            # Segment customers
            customer_segments = self.customer_analytics_service.segment_customers(
                segment_by="value",
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )

            # Sort by total revenue
            customer_segments.sort(key=lambda x: x.total_revenue, reverse=True)

            # Get top customers from highest value segment
            high_value_segment = next((s for s in customer_segments if s.segment_name == "High Value"), None)

            if high_value_segment and high_value_segment.customer_ids:
                top_customers = []
                for customer_id in high_value_segment.customer_ids[:5]:  # Top 5
                    try:
                        analytics = self.customer_analytics_service.get_customer_analytics(customer_id)
                        top_customers.append({
                            "customer_id": customer_id,
                            "total_spent": analytics.total_spent,
                            "total_orders": analytics.total_orders,
                            "avg_order_value": analytics.avg_order_value,
                            "last_purchase_date": analytics.last_purchase_date
                        })
                    except Exception as e:
                        self.logger.error(f"Error getting analytics for customer {customer_id}: {str(e)}")
            else:
                top_customers = []
        except Exception as e:
            self.logger.error(f"Error getting customer segments: {str(e)}")
            top_customers = []

        # Get material cost trend
        try:
            material_usage = self.material_usage_analytics_service.get_material_usage_analytics(
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )

            # Convert usage trend to material cost trend
            material_cost_trend = []
            if material_usage.usage_trend:
                material_cost_trend = [
                    {
                        "period": item["period"],
                        "cost": item["total_cost"]
                    } for item in material_usage.usage_trend
                ]
        except Exception as e:
            self.logger.error(f"Error getting material usage: {str(e)}")
            material_cost_trend = []

        # Get project completion rate
        try:
            efficiency_analysis = self.project_metrics_service.get_efficiency_analysis(
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )

            project_completion_rate = efficiency_analysis.get("avg_completion_percentage", 0.0)
            avg_customer_satisfaction = None

            # If customer satisfaction data is available in the analysis
            if "avg_customer_satisfaction" in efficiency_analysis:
                avg_customer_satisfaction = efficiency_analysis["avg_customer_satisfaction"]
        except Exception as e:
            self.logger.error(f"Error getting project efficiency analysis: {str(e)}")
            project_completion_rate = 0.0
            avg_customer_satisfaction = None

        return AnalyticsSummaryDTO(
            time_period=time_period,
            start_date=start_date,
            end_date=end_date,
            total_revenue=total_revenue,
            total_profit=total_profit,
            overall_margin_percentage=overall_margin_percentage,
            top_customers=top_customers,
            top_products=top_products,
            material_cost_trend=material_cost_trend,
            project_completion_rate=project_completion_rate,
            avg_customer_satisfaction=avg_customer_satisfaction
        )

    def get_key_performance_indicators(self,
                                       time_period: str = "yearly",
                                       start_date: Optional[datetime] = None,
                                       end_date: Optional[datetime] = None
                                       ) -> Dict[str, Any]:
        """
        Get key performance indicators.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            Dictionary with KPI data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get previous period for comparison
        period_duration = (end_date - start_date).days
        prev_end_date = start_date
        prev_start_date = prev_end_date - timedelta(days=period_duration)

        # Get current period profitability
        try:
            profitability_data = self.profitability_analytics_service.get_profitability_analytics(
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )

            current_revenue = profitability_data.total_revenue
            current_profit = profitability_data.total_profit
            current_margin = profitability_data.overall_margin_percentage
        except Exception as e:
            self.logger.error(f"Error getting current profitability: {str(e)}")
            current_revenue = 0.0
            current_profit = 0.0
            current_margin = 0.0

        # Get previous period profitability
        try:
            prev_profitability_data = self.profitability_analytics_service.get_profitability_analytics(
                time_period=time_period,
                start_date=prev_start_date,
                end_date=prev_end_date
            )

            prev_revenue = prev_profitability_data.total_revenue
            prev_profit = prev_profitability_data.total_profit
            prev_margin = prev_profitability_data.overall_margin_percentage
        except Exception as e:
            self.logger.error(f"Error getting previous profitability: {str(e)}")
            prev_revenue = 0.0
            prev_profit = 0.0
            prev_margin = 0.0

        # Calculate changes
        revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else None
        profit_change = ((current_profit - prev_profit) / prev_profit * 100) if prev_profit > 0 else None
        margin_change = current_margin - prev_margin

        # Get customer metrics
        try:
            retention_analysis = self.customer_analytics_service.get_retention_analysis(
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )

            current_retention_rate = retention_analysis.get("retention_rate", 0.0)

            # Get previous period retention
            prev_retention_analysis = self.customer_analytics_service.get_retention_analysis(
                time_period=time_period,
                start_date=prev_start_date,
                end_date=prev_end_date
            )

            prev_retention_rate = prev_retention_analysis.get("retention_rate", 0.0)
            retention_change = current_retention_rate - prev_retention_rate
        except Exception as e:
            self.logger.error(f"Error getting retention analysis: {str(e)}")
            current_retention_rate = 0.0
            retention_change = None

        # Get project metrics
        try:
            efficiency_analysis = self.project_metrics_service.get_efficiency_analysis(
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )

            current_project_efficiency = efficiency_analysis.get("avg_efficiency_score", 0.0)
            on_time_rate = efficiency_analysis.get("on_time_completion_rate", 0.0)

            # Get previous period project metrics
            prev_efficiency_analysis = self.project_metrics_service.get_efficiency_analysis(
                time_period=time_period,
                start_date=prev_start_date,
                end_date=prev_end_date
            )

            prev_project_efficiency = prev_efficiency_analysis.get("avg_efficiency_score", 0.0)
            prev_on_time_rate = prev_efficiency_analysis.get("on_time_completion_rate", 0.0)

            efficiency_change = current_project_efficiency - prev_project_efficiency
            on_time_change = on_time_rate - prev_on_time_rate
        except Exception as e:
            self.logger.error(f"Error getting project efficiency: {str(e)}")
            current_project_efficiency = 0.0
            on_time_rate = 0.0
            efficiency_change = None
            on_time_change = None

        # Get material usage metrics
        try:
            material_usage = self.material_usage_analytics_service.get_material_usage_analytics(
                time_period=time_period,
                start_date=start_date,
                end_date=end_date
            )

            current_material_cost = material_usage.total_materials_cost
            current_waste_pct = material_usage.avg_waste_percentage or 0.0

            # Get previous period material metrics
            prev_material_usage = self.material_usage_analytics_service.get_material_usage_analytics(
                time_period=time_period,
                start_date=prev_start_date,
                end_date=prev_end_date
            )

            prev_material_cost = prev_material_usage.total_materials_cost
            prev_waste_pct = prev_material_usage.avg_waste_percentage or 0.0

            material_cost_change = ((
                                                current_material_cost - prev_material_cost) / prev_material_cost * 100) if prev_material_cost > 0 else None
            waste_pct_change = current_waste_pct - prev_waste_pct
        except Exception as e:
            self.logger.error(f"Error getting material usage: {str(e)}")
            current_material_cost = 0.0
            current_waste_pct = 0.0
            material_cost_change = None
            waste_pct_change = None

        # Return KPI data
        return {
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date,
            "financial_kpis": {
                "revenue": {
                    "value": current_revenue,
                    "change": revenue_change,
                    "change_type": "percentage"
                },
                "profit": {
                    "value": current_profit,
                    "change": profit_change,
                    "change_type": "percentage"
                },
                "margin": {
                    "value": current_margin,
                    "change": margin_change,
                    "change_type": "absolute"
                }
            },
            "customer_kpis": {
                "retention_rate": {
                    "value": current_retention_rate,
                    "change": retention_change,
                    "change_type": "absolute"
                }
            },
            "operations_kpis": {
                "project_efficiency": {
                    "value": current_project_efficiency,
                    "change": efficiency_change,
                    "change_type": "absolute"
                },
                "on_time_completion": {
                    "value": on_time_rate,
                    "change": on_time_change,
                    "change_type": "absolute"
                },
                "material_cost": {
                    "value": current_material_cost,
                    "change": material_cost_change,
                    "change_type": "percentage"
                },
                "waste_percentage": {
                    "value": current_waste_pct,
                    "change": waste_pct_change,
                    "change_type": "absolute"
                }
            }
        }

    def get_trend_data(self,
                       metric_type: str,
                       time_period: str = "monthly",
                       months: int = 12
                       ) -> List[Dict[str, Any]]:
        """
        Get trend data for specified metric.

        Args:
            metric_type: Type of metric to get trend for
            time_period: Analysis period granularity ("monthly", "quarterly", "yearly")
            months: Number of months to include in trend

        Returns:
            List of dictionaries with trend data
        """
        # Calculate date range
        end_date = datetime.now()

        if time_period == "monthly":
            start_date = end_date - timedelta(days=30 * months)
        elif time_period == "quarterly":
            start_date = end_date - timedelta(days=90 * (months // 3))
        else:  # yearly
            start_date = end_date - timedelta(days=365 * (months // 12))

        # Get trend data based on metric type
        if metric_type == "revenue":
            # Get revenue trend
            try:
                margin_trend = self.profitability_analytics_service.get_margin_trend(
                    time_period=time_period,
                    months=months
                )

                return [
                    {
                        "period": item["period"],
                        "value": item["revenue"]
                    } for item in margin_trend
                ]
            except Exception as e:
                self.logger.error(f"Error getting revenue trend: {str(e)}")
                return []

        elif metric_type == "profit":
            # Get profit trend
            try:
                margin_trend = self.profitability_analytics_service.get_margin_trend(
                    time_period=time_period,
                    months=months
                )

                return [
                    {
                        "period": item["period"],
                        "value": item["profit"]
                    } for item in margin_trend
                ]
            except Exception as e:
                self.logger.error(f"Error getting profit trend: {str(e)}")
                return []

        elif metric_type == "margin":
            # Get margin trend
            try:
                margin_trend = self.profitability_analytics_service.get_margin_trend(
                    time_period=time_period,
                    months=months
                )

                return [
                    {
                        "period": item["period"],
                        "value": item["margin_percentage"]
                    } for item in margin_trend
                ]
            except Exception as e:
                self.logger.error(f"Error getting margin trend: {str(e)}")
                return []

        elif metric_type == "material_cost":
            # Get material cost trend
            try:
                material_trend = self.material_usage_analytics_service.get_material_usage_trend(
                    time_period=time_period,
                    months=months
                )

                return [
                    {
                        "period": item["period"],
                        "value": item.get("total_cost", 0.0)
                    } for item in material_trend
                ]
            except Exception as e:
                self.logger.error(f"Error getting material cost trend: {str(e)}")
                return []

        elif metric_type == "project_efficiency":
            # Get project efficiency trend
            try:
                efficiency_trend = self.project_metrics_service._calculate_efficiency_trend(
                    time_period=time_period,
                    start_date=start_date,
                    end_date=end_date
                )

                return [
                    {
                        "period": item["period"],
                        "value": item["avg_efficiency_score"]
                    } for item in efficiency_trend
                ]
            except Exception as e:
                self.logger.error(f"Error getting project efficiency trend: {str(e)}")
                return []

        elif metric_type == "customer_retention":
            # For customer retention, we need to calculate it for each period
            # This would typically come from actual historical data
            # For now, we'll generate placeholder data

            periods = []
            if time_period == "monthly":
                # Weekly periods for monthly analysis
                delta = timedelta(days=7)
                format_str = "Week of %b %d"
            elif time_period == "quarterly":
                # Monthly periods for quarterly analysis
                delta = timedelta(days=30)
                format_str = "%b %Y"
            else:  # yearly
                # Monthly periods for yearly analysis
                delta = timedelta(days=30)
                format_str = "%b %Y"

            current_date = start_date
            while current_date < end_date:
                next_date = min(current_date + delta, end_date)
                periods.append((current_date, next_date))
                current_date = next_date

            result = []
            for period_start, period_end in periods:
                try:
                    # Get retention for this period
                    retention_analysis = self.customer_analytics_service.get_retention_analysis(
                        time_period="custom",  # Use custom time period
                        start_date=period_start,
                        end_date=period_end
                    )

                    retention_rate = retention_analysis.get("retention_rate", 0.0)
                    period_label = period_start.strftime(format_str)

                    result.append({
                        "period": period_label,
                        "value": retention_rate
                    })
                except Exception as e:
                    self.logger.error(f"Error getting retention for period {period_start} to {period_end}: {str(e)}")

            return result

        # Default: return empty list for unknown metric type
        return []