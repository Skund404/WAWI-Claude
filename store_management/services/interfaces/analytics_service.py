# services/interfaces/analytics_service.py
"""
Interface definitions for analytics services.

This module defines Protocol classes for the various analytics services,
providing a clear contract for implementations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union

from services.dto.analytics_dto import (
    AnalyticsSummaryDTO,
    CustomerAnalyticsDTO,
    CustomerSegmentDTO,
    MaterialUsageAnalyticsDTO,
    ProfitabilityAnalyticsDTO,
    ProjectMetricsDTO,
)


class ICustomerAnalyticsService(Protocol):
    """Interface for the customer analytics service."""

    def get_customer_analytics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> CustomerAnalyticsDTO:
        """
        Get customer analytics data for the specified date range.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            CustomerAnalyticsDTO with analytics data
        """
        ...

    def get_customer_segments(
        self, segment_count: int = 3, min_orders: int = 1
    ) -> List[CustomerSegmentDTO]:
        """
        Get customer segments based on RFM (Recency, Frequency, Monetary) analysis.

        Args:
            segment_count: Number of segments to create
            min_orders: Minimum number of orders for inclusion

        Returns:
            List of CustomerSegmentDTO objects
        """
        ...

    def get_retention_data(
        self, period_count: int = 6, period_unit: str = "month"
    ) -> Dict[str, List[float]]:
        """
        Get customer retention data by cohort.

        Args:
            period_count: Number of periods to analyze
            period_unit: Period unit ('day', 'week', 'month', 'quarter', 'year')

        Returns:
            Dictionary with cohort labels and retention percentages
        """
        ...

    def get_customer_lifetime_value(
        self, segment: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get customer lifetime value metrics.

        Args:
            segment: Optional customer segment to filter by

        Returns:
            Dictionary with CLV metrics
        """
        ...


class IProfitabilityAnalyticsService(Protocol):
    """Interface for the profitability analytics service."""

    def get_profitability_analytics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> ProfitabilityAnalyticsDTO:
        """
        Get profitability analytics data for the specified date range.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            ProfitabilityAnalyticsDTO with analytics data
        """
        ...

    def get_profit_margins_by_product_type(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Get profit margins by product type.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary mapping product types to profit margins
        """
        ...

    def get_profit_margins_by_project_type(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Get profit margins by project type.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary mapping project types to profit margins
        """
        ...

    def get_cost_breakdown(
        self, project_type: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get cost breakdown by category.

        Args:
            project_type: Optional project type to filter by

        Returns:
            Dictionary mapping cost categories to percentages
        """
        ...


class IMaterialUsageAnalyticsService(Protocol):
    """Interface for the material usage analytics service."""

    def get_material_usage_analytics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> MaterialUsageAnalyticsDTO:
        """
        Get material usage analytics data for the specified date range.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            MaterialUsageAnalyticsDTO with analytics data
        """
        ...

    def get_material_consumption_by_type(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Get material consumption by material type.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary mapping material types to consumption amounts
        """
        ...

    def get_waste_analysis(
        self, material_type: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get waste analysis by material.

        Args:
            material_type: Optional material type to filter by

        Returns:
            Dictionary with waste metrics
        """
        ...

    def get_inventory_turnover(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Get inventory turnover metrics.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary with inventory turnover metrics
        """
        ...


class IProjectMetricsService(Protocol):
    """Interface for the project metrics service."""

    def get_project_metrics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> ProjectMetricsDTO:
        """
        Get project metrics data for the specified date range.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            ProjectMetricsDTO with metrics data
        """
        ...

    def get_project_completion_time(
        self, project_type: Optional[str] = None
    ) -> Dict[str, Union[float, int]]:
        """
        Get project completion time metrics.

        Args:
            project_type: Optional project type to filter by

        Returns:
            Dictionary with completion time metrics
        """
        ...

    def get_project_phase_metrics(
        self, project_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Union[float, int]]]:
        """
        Get metrics for each project phase.

        Args:
            project_type: Optional project type to filter by

        Returns:
            Dictionary mapping phases to metrics
        """
        ...

    def get_bottleneck_analysis(self) -> Dict[str, Any]:
        """
        Get bottleneck analysis for projects.

        Returns:
            Dictionary with bottleneck analysis
        """
        ...


class IAnalyticsDashboardService(Protocol):
    """Interface for the analytics dashboard service."""

    def get_analytics_summary(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> AnalyticsSummaryDTO:
        """
        Get a summary of key analytics metrics for the dashboard.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            AnalyticsSummaryDTO with summary metrics
        """
        ...

    def get_dashboard_kpis(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get KPIs for the analytics dashboard.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary with KPI metrics
        """
        ...

    def get_trend_data(
        self,
        metric: str,
        period: str = "month",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, List[Any]]:
        """
        Get trend data for a specific metric.

        Args:
            metric: Metric to get trend data for
            period: Period unit ('day', 'week', 'month', 'quarter', 'year')
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary with trend data
        """
        ...