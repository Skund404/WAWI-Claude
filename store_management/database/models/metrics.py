# path: database/models/metrics.py
"""
Metrics models for the leatherworking store management application.

This module defines the database models for various metrics and analytics data
collected throughout the leatherworking business operations.
"""

import enum
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship

# Import base classes without causing circular dependencies
from database.models.base import Base, BaseModel


class MetricType(enum.Enum):
    """Enumeration of metric types."""
    INVENTORY = "inventory"
    SALES = "sales"
    PRODUCTION = "production"
    MATERIAL_USAGE = "material_usage"
    FINANCIAL = "financial"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"


class TimeFrame(enum.Enum):
    """Enumeration of time frames for metrics."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class MetricSnapshot(Base, BaseModel):
    """
    Model for storing point-in-time metrics.

    This model captures various metrics as snapshots in time,
    allowing for historical analysis and trend visualization.
    """
    __tablename__ = 'metric_snapshots'

    id = Column(Integer, primary_key=True)

    # Metric categorization
    metric_type = Column(Enum(MetricType), nullable=False)
    time_frame = Column(Enum(TimeFrame), nullable=False)

    # Snapshot details
    snapshot_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Metric data stored as JSON
    metrics = Column(JSON, nullable=False)

    # Description and notes
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """
        Return a string representation of the metric snapshot.

        Returns:
            str: String representation with id, type, and date
        """
        return f"<MetricSnapshot(id={self.id}, type={self.metric_type}, date={self.snapshot_date})>"

    def get_metric_value(self, key: str) -> Any:
        """
        Get a specific metric value from the metrics data.

        Args:
            key: The key of the metric to retrieve

        Returns:
            The value of the specified metric, or None if not found
        """
        if not self.metrics:
            return None

        return self.metrics.get(key)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics in this snapshot.

        Returns:
            Dict[str, Any]: Dictionary of metric keys and values
        """
        return {
            'id': self.id,
            'type': self.metric_type.value if self.metric_type else None,
            'time_frame': self.time_frame.value if self.time_frame else None,
            'date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'metrics': self.metrics or {}
        }


class MaterialUsageLog(Base, BaseModel):
    """
    Model for tracking material usage efficiency.

    This model records detailed information about how efficiently
    materials are being used in leatherworking projects.
    """
    __tablename__ = 'material_usage_logs'

    id = Column(Integer, primary_key=True)

    # Related entities
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)

    # Usage details
    date_used = Column(DateTime, nullable=False, default=datetime.utcnow)
    planned_quantity = Column(Float, nullable=False)
    actual_quantity = Column(Float, nullable=False)
    wastage = Column(Float, default=0.0)

    # Efficiency metrics
    efficiency_percentage = Column(Float, nullable=True)

    # Related entities
    material = relationship("Material")
    project = relationship("Project")

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """
        Return a string representation of the material usage log.

        Returns:
            str: String representation with id, material ID, and project ID
        """
        return f"<MaterialUsageLog(id={self.id}, material_id={self.material_id}, project_id={self.project_id})>"

    def calculate_efficiency(self) -> float:
        """
        Calculate the material usage efficiency.

        Returns:
            float: Efficiency percentage (0-100)
        """
        if not self.planned_quantity or self.planned_quantity <= 0:
            return 0.0

        used = self.actual_quantity - self.wastage
        efficiency = (used / self.planned_quantity) * 100.0

        # Update stored efficiency
        self.efficiency_percentage = efficiency

        return efficiency