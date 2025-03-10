# services/interfaces/analytics_service.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple
from database.models.enums import (
    ProjectType,
    ComponentType,
    MaterialType,
    LeatherType,
    SkillLevel
)


class IAnalyticsService(Protocol):
    """Comprehensive analytics service for leatherworking business intelligence."""

    def get_dashboard_metrics(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Generate key metrics for the dashboard.

        Returns condensed, high-level business performance indicators.
        """
        ...

    def get_sales_performance(self,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Comprehensive sales performance analysis.

        Includes total revenue, order count, average order value,
        sales by product category, and trend analysis.
        """
        ...

    def get_material_efficiency_report(self,
                                       material_type: Optional[MaterialType] = None,
                                       start_date: Optional[datetime] = None,
                                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Detailed material usage and efficiency report.

        Tracks material consumption, waste, cost-effectiveness,
        and utilization across different material types.
        """
        ...

    def get_project_complexity_analysis(self,
                                        project_type: Optional[ProjectType] = None,
                                        skill_level: Optional[SkillLevel] = None) -> Dict[str, Any]:
        """Analyze project complexity and resource allocation.

        Provides insights into project types, skill requirements,
        and resource utilization.
        """
        ...

    def get_inventory_health_report(self) -> Dict[str, Any]:
        """Comprehensive inventory health and status report.

        Includes stock levels, low stock alerts,
        material type distribution, and value analysis.
        """
        ...

    def get_pattern_performance_analytics(self,
                                          start_date: Optional[datetime] = None,
                                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Pattern utilization and performance tracking.

        Analyzes pattern usage, profitability, and skill level distribution.
        """
        ...

    def get_customer_lifetime_value_analysis(self,
                                             customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Comprehensive customer value and purchase behavior analysis.

        Provides deep insights into customer purchasing patterns,
        total revenue, and customer segmentation.
        """
        ...

    def get_production_efficiency_report(self,
                                         start_date: Optional[datetime] = None,
                                         end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Production efficiency and bottleneck identification.

        Tracks production times, resource utilization,
        and identifies potential improvement areas.
        """
        ...

    def generate_predictive_insights(self) -> Dict[str, Any]:
        """Generate predictive business insights.

        Uses historical data to provide forecasts on sales,
        inventory needs, and potential business opportunities.
        """
        ...