# database/models/metrics.py
"""
Comprehensive Metrics Models for Leatherworking Management System

This module defines models for tracking, analyzing, and reporting various
business metrics across the leatherworking operations. These models support
data-driven decision making and performance analysis.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text, Boolean, DateTime, JSON, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.base import (
    TimestampMixin,
    ValidationMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    CircularImportResolver
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
)

# Define enums for metrics
import enum


class MetricType(enum.Enum):
    """Enumeration of metric types for categorization."""
    INVENTORY = "inventory"
    SALES = "sales"
    PRODUCTION = "production"
    MATERIAL_USAGE = "material_usage"
    FINANCIAL = "financial"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PROJECT = "project"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"


class TimeFrame(enum.Enum):
    """Enumeration of time frames for metrics aggregation."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Project', 'database.models.project', 'Project')
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Sales', 'database.models.sales', 'Sales')


class MetricSnapshot(Base, TimestampMixin, ValidationMixin):
    """
    Model for storing point-in-time metrics data for historical analysis.

    This model captures a comprehensive snapshot of system metrics at specific
    points in time, enabling trend analysis and historical reporting.
    """
    __tablename__ = 'metric_snapshots'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Metric categorization
    metric_type: Mapped[MetricType] = mapped_column(Enum(MetricType), nullable=False, index=True)
    time_frame: Mapped[TimeFrame] = mapped_column(Enum(TimeFrame), nullable=False)

    # Temporal data
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metric data storage
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Descriptive information
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Related entity references - nullable foreign keys for optional relationships
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), nullable=True)
    material_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('materials.id'), nullable=True)
    leather_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leathers.id'), nullable=True)
    sales_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sales.id'), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="metrics")
    material = relationship("Material")
    leather = relationship("Leather")
    sales = relationship("Sales")

    def __init__(self, **kwargs):
        """
        Initialize a MetricSnapshot instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for metric snapshot attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_metric_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"MetricSnapshot initialization failed: {e}")
            raise ModelValidationError(f"Failed to create MetricSnapshot: {str(e)}") from e

    @classmethod
    def _validate_metric_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of metric data.

        Args:
            data: Metric data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'metric_type', 'Metric type is required')
        validate_not_empty(data, 'time_frame', 'Time frame is required')
        validate_not_empty(data, 'metrics', 'Metrics data is required')

        # Validate metric type
        if 'metric_type' in data:
            ModelValidator.validate_enum(
                data['metric_type'],
                MetricType,
                'metric_type'
            )

        # Validate time frame
        if 'time_frame' in data:
            ModelValidator.validate_enum(
                data['time_frame'],
                TimeFrame,
                'time_frame'
            )

        # Validate metrics data structure
        if 'metrics' in data and not isinstance(data['metrics'], dict):
            raise ValidationError("Metrics must be a dictionary", "metrics")

        # Validate date ranges
        if 'start_date' in data and 'end_date' in data and data['start_date'] and data['end_date']:
            if data['start_date'] > data['end_date']:
                raise ValidationError("Start date cannot be after end date", "date_range")

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Ensure metrics is initialized as a dictionary if not provided
        if not hasattr(self, 'metrics') or self.metrics is None:
            self.metrics = {}

        # Set name if not provided
        if not hasattr(self, 'name') or not self.name:
            self.name = f"{self.metric_type.value.title()} Metrics - {self.snapshot_date.strftime('%Y-%m-%d')}"

    def get_metric_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific metric value from the metrics data.

        Args:
            key: The key of the metric to retrieve
            default: Default value to return if key not found

        Returns:
            The value of the specified metric, or default if not found
        """
        if not self.metrics:
            return default

        return self.metrics.get(key, default)

    def set_metric_value(self, key: str, value: Any) -> None:
        """
        Set a specific metric value in the metrics data.

        Args:
            key: The key of the metric to set
            value: The value to set
        """
        if not hasattr(self, 'metrics') or self.metrics is None:
            self.metrics = {}

        self.metrics[key] = value
        logger.debug(f"Set metric {key} to {value} for snapshot {self.id}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics in this snapshot.

        Returns:
            Dictionary with snapshot metadata and metrics
        """
        return {
            'id': self.id,
            'name': self.name,
            'type': self.metric_type.value if self.metric_type else None,
            'time_frame': self.time_frame.value if self.time_frame else None,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'metrics': self.metrics or {},
            'description': self.description,
            'notes': self.notes
        }

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the model
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        # Special handling for enum values
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)

                # Convert enums to their string values
                if isinstance(value, enum.Enum):
                    result[column.name] = value.value
                else:
                    result[column.name] = value

        return result

    def __repr__(self) -> str:
        """
        String representation of the MetricSnapshot.

        Returns:
            Detailed metric snapshot representation
        """
        return (
            f"<MetricSnapshot(id={self.id}, "
            f"type={self.metric_type.name if self.metric_type else 'None'}, "
            f"date={self.snapshot_date.strftime('%Y-%m-%d') if self.snapshot_date else 'None'})>"
        )


class MaterialUsageLog(Base, TimestampMixin, ValidationMixin):
    """
    Model for tracking detailed material usage efficiency across projects.

    This model records comprehensive data about material utilization,
    enabling analysis of material efficiency and waste reduction.
    """
    __tablename__ = 'material_usage_logs'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Related entity references
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey('materials.id'), nullable=False, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), nullable=True, index=True)
    leather_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leathers.id'), nullable=True)

    # Log date
    date_used: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Usage details
    planned_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    actual_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    wastage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Efficiency metrics
    efficiency_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Quality information
    quality_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    defect_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Optional link to user who logged it

    # Relationships
    material = relationship("Material")
    project = relationship("Project")
    leather = relationship("Leather")

    def __init__(self, **kwargs):
        """
        Initialize a MaterialUsageLog instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for material usage log attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate input data
            self._validate_usage_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"MaterialUsageLog initialization failed: {e}")
            raise ModelValidationError(f"Failed to create MaterialUsageLog: {str(e)}") from e

    @classmethod
    def _validate_usage_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of usage log data.

        Args:
            data: Usage log data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate core required fields
        validate_not_empty(data, 'material_id', 'Material ID is required')
        validate_not_empty(data, 'planned_quantity', 'Planned quantity is required')
        validate_not_empty(data, 'actual_quantity', 'Actual quantity is required')

        # Validate quantities
        for field in ['planned_quantity', 'actual_quantity']:
            if field in data:
                validate_positive_number(
                    data,
                    field,
                    allow_zero=False,
                    message=f"{field.replace('_', ' ').title()} must be positive"
                )

        # Validate wastage
        if 'wastage' in data:
            validate_positive_number(
                data,
                'wastage',
                allow_zero=True,
                message="Wastage cannot be negative"
            )

        # Validate efficiency percentage if provided
        if 'efficiency_percentage' in data and data['efficiency_percentage'] is not None:
            if data['efficiency_percentage'] < 0 or data['efficiency_percentage'] > 100:
                raise ValidationError("Efficiency percentage must be between 0 and 100", "efficiency_percentage")

        # Validate quality rating if provided
        if 'quality_rating' in data and data['quality_rating'] is not None:
            if data['quality_rating'] < 1 or data['quality_rating'] > 5:
                raise ValidationError("Quality rating must be between 1 and 5", "quality_rating")

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Calculate efficiency percentage if not provided
        if not hasattr(self, 'efficiency_percentage') or self.efficiency_percentage is None:
            self.calculate_efficiency()

        # Set wastage if not provided
        if not hasattr(self, 'wastage') or self.wastage is None:
            # Wastage is the difference between planned and actual if actual is less
            if self.actual_quantity <= self.planned_quantity:
                self.wastage = self.planned_quantity - self.actual_quantity
            else:
                self.wastage = 0.0

    def calculate_efficiency(self) -> float:
        """
        Calculate and update the material usage efficiency.

        Returns:
            Calculated efficiency percentage (0-100)
        """
        try:
            if not self.planned_quantity or self.planned_quantity <= 0:
                self.efficiency_percentage = 0.0
                return 0.0

            # Effective usage = actual quantity - wastage
            effective_usage = max(0, self.actual_quantity - self.wastage)

            # Efficiency = (effective usage / planned quantity) * 100
            efficiency = min(100.0, (effective_usage / self.planned_quantity) * 100.0)

            # Update stored efficiency
            self.efficiency_percentage = round(efficiency, 2)

            return self.efficiency_percentage

        except Exception as e:
            logger.error(f"Failed to calculate efficiency: {e}")
            self.efficiency_percentage = None
            return 0.0

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the model
        """
        if exclude_fields is None:
            exclude_fields = []

        # Add standard fields to exclude
        exclude_fields.extend(['_sa_instance_state'])

        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude_fields
        }

    def __repr__(self) -> str:
        """
        String representation of the MaterialUsageLog.

        Returns:
            Detailed material usage log representation
        """
        return (
            f"<MaterialUsageLog(id={self.id}, "
            f"material_id={self.material_id}, "
            f"project_id={self.project_id}, "
            f"efficiency={self.efficiency_percentage}%)>"
        )


class EfficiencyReport(Base, TimestampMixin):
    """
    Model for storing aggregated efficiency reports.

    This model provides a higher-level view of efficiency data,
    aggregating individual usage logs into meaningful reports.
    """
    __tablename__ = 'efficiency_reports'

    # Core attributes
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Report parameters
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Time period
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Optional filtering parameters
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('projects.id'), nullable=True)
    material_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Aggregated metrics
    total_planned: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_actual: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_waste: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_efficiency: Mapped[float] = mapped_column(Float, nullable=True)

    # Report data
    report_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)

    # Metadata
    generated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # User ID
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project = relationship("Project")

    def __init__(self, **kwargs):
        """
        Initialize an EfficiencyReport instance.

        Args:
            **kwargs: Keyword arguments for report attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate dates
            if 'start_date' in kwargs and 'end_date' in kwargs:
                if kwargs['start_date'] > kwargs['end_date']:
                    raise ValidationError("Start date cannot be after end date", "date_range")

            # Initialize base model
            super().__init__(**kwargs)

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"EfficiencyReport initialization failed: {e}")
            raise ModelValidationError(f"Failed to create EfficiencyReport: {str(e)}") from e

    @classmethod
    def generate_from_usage_logs(cls,
                                 start_date: datetime,
                                 end_date: datetime,
                                 name: str,
                                 project_id: Optional[int] = None,
                                 material_type: Optional[str] = None) -> "EfficiencyReport":
        """
        Generate an efficiency report from usage logs within a date range.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            name: Name for the report
            project_id: Optional project ID to filter by
            material_type: Optional material type to filter by

        Returns:
            New EfficiencyReport instance
        """
        from sqlalchemy.orm import Session
        from sqlalchemy import func, and_

        try:
            # This would typically use a database session
            # For demonstration, we'll create a placeholder implementation

            report_data = {
                "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "filters": {
                    "project_id": project_id,
                    "material_type": material_type
                },
                "summary": {
                    "total_logs": 0,
                    "efficiency_trend": [],
                    "waste_percentage": 0
                }
            }

            # Create the report
            report = cls(
                report_name=name,
                report_type="material_efficiency",
                start_date=start_date,
                end_date=end_date,
                project_id=project_id,
                material_type=material_type,
                total_planned=0,
                total_actual=0,
                total_waste=0,
                average_efficiency=0,
                report_data=report_data
            )

            return report

        except Exception as e:
            logger.error(f"Failed to generate efficiency report: {e}")
            raise ModelValidationError(f"Report generation failed: {str(e)}")

    def __repr__(self) -> str:
        """
        String representation of the EfficiencyReport.

        Returns:
            Detailed report representation
        """
        return (
            f"<EfficiencyReport(id={self.id}, "
            f"name='{self.report_name}', "
            f"period={self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')})>"
        )


# Register for lazy import resolution
register_lazy_import('MetricSnapshot', 'database.models.metrics', 'MetricSnapshot')
register_lazy_import('MaterialUsageLog', 'database.models.metrics', 'MaterialUsageLog')
register_lazy_import('EfficiencyReport', 'database.models.metrics', 'EfficiencyReport')