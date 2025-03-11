# services/dto/analytics_dto.py
"""
Data Transfer Objects for analytics functionality.

These DTOs define the data structures for various analytics results
including customer analytics, profitability analytics, material usage,
and project metrics.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


@dataclass
class CustomerSegmentDTO:
    """Data Transfer Object for customer segment analysis."""
    segment_name: str
    customer_count: int
    avg_order_value: float
    total_revenue: float
    engagement_score: float
    retention_rate: float
    avg_orders_per_year: float
    customer_ids: List[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerSegmentDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing segment data

        Returns:
            CustomerSegmentDTO instance
        """
        return cls(**data)


@dataclass
class CustomerAnalyticsDTO:
    """Data Transfer Object for customer analytics."""
    customer_id: int
    total_spent: float
    total_orders: int
    avg_order_value: float
    first_purchase_date: datetime
    last_purchase_date: Optional[datetime] = None
    days_since_last_purchase: Optional[int] = None
    purchase_frequency_days: Optional[float] = None
    segment: Optional[str] = None
    lifetime_value: Optional[float] = None
    order_trend: Optional[List[Dict[str, Any]]] = None
    product_preferences: Optional[List[Dict[str, Any]]] = None
    retention_score: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerAnalyticsDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing customer analytics data

        Returns:
            CustomerAnalyticsDTO instance
        """
        # Handle date conversions if needed
        if 'first_purchase_date' in data and isinstance(data['first_purchase_date'], str):
            data['first_purchase_date'] = datetime.fromisoformat(data['first_purchase_date'])

        if 'last_purchase_date' in data and isinstance(data['last_purchase_date'], str):
            data['last_purchase_date'] = datetime.fromisoformat(data['last_purchase_date'])

        return cls(**data)


@dataclass
class ProfitMarginDTO:
    """Data Transfer Object for profit margin analysis."""
    item_id: int
    item_type: str  # 'product', 'project', etc.
    name: str
    revenue: float
    cost: float
    profit: float
    margin_percentage: float
    overhead_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    time_period: Optional[str] = None  # 'monthly', 'quarterly', 'yearly'

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfitMarginDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing profit margin data

        Returns:
            ProfitMarginDTO instance
        """
        return cls(**data)


@dataclass
class ProfitabilityAnalyticsDTO:
    """Data Transfer Object for profitability analytics."""
    total_revenue: float
    total_cost: float
    total_profit: float
    overall_margin_percentage: float
    time_period: str  # 'monthly', 'quarterly', 'yearly'
    start_date: datetime
    end_date: datetime
    margin_by_item: List[ProfitMarginDTO] = field(default_factory=list)
    margin_trend: Optional[List[Dict[str, Any]]] = None
    top_performers: Optional[List[ProfitMarginDTO]] = None
    underperformers: Optional[List[ProfitMarginDTO]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfitabilityAnalyticsDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing profitability analytics data

        Returns:
            ProfitabilityAnalyticsDTO instance
        """
        # Handle date conversions
        if 'start_date' in data and isinstance(data['start_date'], str):
            data['start_date'] = datetime.fromisoformat(data['start_date'])

        if 'end_date' in data and isinstance(data['end_date'], str):
            data['end_date'] = datetime.fromisoformat(data['end_date'])

        # Handle nested DTOs
        if 'margin_by_item' in data and isinstance(data['margin_by_item'], list):
            data['margin_by_item'] = [
                ProfitMarginDTO.from_dict(item) if isinstance(item, dict) else item
                for item in data['margin_by_item']
            ]

        if 'top_performers' in data and isinstance(data['top_performers'], list):
            data['top_performers'] = [
                ProfitMarginDTO.from_dict(item) if isinstance(item, dict) else item
                for item in data['top_performers']
            ]

        if 'underperformers' in data and isinstance(data['underperformers'], list):
            data['underperformers'] = [
                ProfitMarginDTO.from_dict(item) if isinstance(item, dict) else item
                for item in data['underperformers']
            ]

        return cls(**data)


@dataclass
class MaterialUsageItemDTO:
    """Data Transfer Object for material usage item."""
    material_id: int
    material_name: str
    material_type: str
    quantity_used: float
    unit: str
    cost: float
    waste_percentage: Optional[float] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    usage_date: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialUsageItemDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing material usage item data

        Returns:
            MaterialUsageItemDTO instance
        """
        # Handle date conversion
        if 'usage_date' in data and isinstance(data['usage_date'], str):
            data['usage_date'] = datetime.fromisoformat(data['usage_date'])

        return cls(**data)


@dataclass
class MaterialUsageAnalyticsDTO:
    """Data Transfer Object for material usage analytics."""
    time_period: str  # 'monthly', 'quarterly', 'yearly'
    start_date: datetime
    end_date: datetime
    total_materials_cost: float
    total_quantity_used: float
    avg_waste_percentage: Optional[float] = None
    usage_by_material: List[MaterialUsageItemDTO] = field(default_factory=list)
    usage_by_project: Optional[List[Dict[str, Any]]] = None
    usage_trend: Optional[List[Dict[str, Any]]] = None
    inventory_turnover: Optional[float] = None
    high_waste_materials: Optional[List[MaterialUsageItemDTO]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialUsageAnalyticsDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing material usage analytics data

        Returns:
            MaterialUsageAnalyticsDTO instance
        """
        # Handle date conversions
        if 'start_date' in data and isinstance(data['start_date'], str):
            data['start_date'] = datetime.fromisoformat(data['start_date'])

        if 'end_date' in data and isinstance(data['end_date'], str):
            data['end_date'] = datetime.fromisoformat(data['end_date'])

        # Handle nested DTOs
        if 'usage_by_material' in data and isinstance(data['usage_by_material'], list):
            data['usage_by_material'] = [
                MaterialUsageItemDTO.from_dict(item) if isinstance(item, dict) else item
                for item in data['usage_by_material']
            ]

        if 'high_waste_materials' in data and isinstance(data['high_waste_materials'], list):
            data['high_waste_materials'] = [
                MaterialUsageItemDTO.from_dict(item) if isinstance(item, dict) else item
                for item in data['high_waste_materials']
            ]

        return cls(**data)


@dataclass
class ProjectPhaseMetricsDTO:
    """Data Transfer Object for project phase metrics."""
    phase_name: str
    planned_duration_days: float
    actual_duration_days: float
    efficiency_score: float
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    bottleneck_score: Optional[float] = None
    resource_utilization: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectPhaseMetricsDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing project phase metrics data

        Returns:
            ProjectPhaseMetricsDTO instance
        """
        # Handle date conversions
        if 'start_date' in data and isinstance(data['start_date'], str):
            data['start_date'] = datetime.fromisoformat(data['start_date'])

        if 'end_date' in data and isinstance(data['end_date'], str):
            data['end_date'] = datetime.fromisoformat(data['end_date'])

        return cls(**data)


@dataclass
class ProjectMetricsDTO:
    """Data Transfer Object for project metrics."""
    project_id: int
    project_name: str
    start_date: datetime
    end_date: Optional[datetime] = None
    planned_duration_days: float
    actual_duration_days: Optional[float] = None
    completion_percentage: float
    efficiency_score: Optional[float] = None
    on_time_completion: Optional[bool] = None
    within_budget: Optional[bool] = None
    resource_utilization: Optional[float] = None
    customer_satisfaction: Optional[float] = None
    phase_metrics: List[ProjectPhaseMetricsDTO] = field(default_factory=list)
    bottlenecks: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetricsDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing project metrics data

        Returns:
            ProjectMetricsDTO instance
        """
        # Handle date conversions
        if 'start_date' in data and isinstance(data['start_date'], str):
            data['start_date'] = datetime.fromisoformat(data['start_date'])

        if 'end_date' in data and isinstance(data['end_date'], str):
            data['end_date'] = datetime.fromisoformat(data['end_date'])

        # Handle nested DTOs
        if 'phase_metrics' in data and isinstance(data['phase_metrics'], list):
            data['phase_metrics'] = [
                ProjectPhaseMetricsDTO.from_dict(item) if isinstance(item, dict) else item
                for item in data['phase_metrics']
            ]

        return cls(**data)


@dataclass
class AnalyticsSummaryDTO:
    """Summary of analytics data for dashboard display."""
    time_period: str
    start_date: datetime
    end_date: datetime
    total_revenue: float
    total_profit: float
    overall_margin_percentage: float
    top_customers: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    material_cost_trend: List[Dict[str, Any]]
    project_completion_rate: float
    avg_customer_satisfaction: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsSummaryDTO':
        """Create DTO from dictionary data.

        Args:
            data: Dictionary containing analytics summary data

        Returns:
            AnalyticsSummaryDTO instance
        """
        # Handle date conversions
        if 'start_date' in data and isinstance(data['start_date'], str):
            data['start_date'] = datetime.fromisoformat(data['start_date'])

        if 'end_date' in data and isinstance(data['end_date'], str):
            data['end_date'] = datetime.fromisoformat(data['end_date'])

        return cls(**data)