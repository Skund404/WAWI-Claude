# store_management/database/repositories/metrics_repository.py
"""
Repository for managing metrics and performance tracking in the application.

This module provides advanced querying and management of metric snapshots,
material usage logs, and related performance metrics.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces import MaterialService
from models.metrics import MetricSnapshot, MaterialUsageLog, MetricType, TimeFrame

# Configure logging
logger = logging.getLogger(__name__)


class MetricsRepository:
    """
    Repository for managing metrics and performance tracking.

    Provides methods for creating, retrieving, and analyzing 
    metric snapshots and material usage logs.
    """

    @inject(MaterialService)
    def __init__(self, session: Session):
        """
        Initialize the MetricsRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self.session = session

    def create_metric_snapshot(self, snapshot_data: Dict[str, Any]) -> MetricSnapshot:
        """
        Create a new metric snapshot.

        Args:
            snapshot_data (Dict[str, Any]): Data for the metric snapshot

        Returns:
            MetricSnapshot: Created metric snapshot

        Raises:
            ValueError: If required snapshot data is missing
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate required fields
            if not all(key in snapshot_data for key in ['metric_type', 'time_frame', 'value']):
                raise ValueError("Missing required fields for metric snapshot")

            # Create and save snapshot
            snapshot = MetricSnapshot(**snapshot_data)
            snapshot.timestamp = datetime.utcnow()

            self.session.add(snapshot)
            self.session.commit()

            return snapshot
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating metric snapshot: {e}")
            raise
        except ValueError as e:
            logger.error(f"Validation error creating metric snapshot: {e}")
            raise

    def get_latest_metrics(self, metric_type: MetricType) -> Optional[MetricSnapshot]:
        """
        Retrieve the most recent metrics for a given type.

        Args:
            metric_type (MetricType): Type of metric to retrieve

        Returns:
            Optional[MetricSnapshot]: Most recent metric snapshot or None
        """
        try:
            return (
                self.session.query(MetricSnapshot)
                .filter(MetricSnapshot.metric_type == metric_type)
                .order_by(MetricSnapshot.timestamp.desc())
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving latest metrics for {metric_type}: {e}")
            raise

    def get_metrics_history(
            self,
            metric_type: MetricType,
            time_frame: TimeFrame,
            start_date: datetime,
            end_date: Optional[datetime] = None
    ) -> List[MetricSnapshot]:
        """
        Retrieve historical metrics within a specified timeframe.

        Args:
            metric_type (MetricType): Type of metric to retrieve
            time_frame (TimeFrame): Granularity of metrics
            start_date (datetime): Start of the date range
            end_date (Optional[datetime], optional): End of the date range. Defaults to current time.

        Returns:
            List[MetricSnapshot]: List of metric snapshots in the specified range
        """
        try:
            # Use current time if no end date provided
            if end_date is None:
                end_date = datetime.utcnow()

            return (
                self.session.query(MetricSnapshot)
                .filter(
                    and_(
                        MetricSnapshot.metric_type == metric_type,
                        MetricSnapshot.time_frame == time_frame,
                        MetricSnapshot.timestamp.between(start_date, end_date)
                    )
                )
                .order_by(MetricSnapshot.timestamp.asc())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving metrics history: {e}")
            raise

    def log_material_usage(self, usage_data: Dict[str, Any]) -> MaterialUsageLog:
        """
        Log material usage data.

        Args:
            usage_data (Dict[str, Any]): Data for material usage log

        Returns:
            MaterialUsageLog: Created material usage log

        Raises:
            ValueError: If required usage data is missing
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate required fields
            if not all(key in usage_data for key in ['material_id', 'quantity_used']):
                raise ValueError("Missing required fields for material usage log")

            # Create usage log with efficiency calculation
            usage_log = MaterialUsageLog(**usage_data)
            usage_log.timestamp = datetime.utcnow()
            usage_log.efficiency = usage_log.calculate_efficiency()

            self.session.add(usage_log)
            self.session.commit()

            return usage_log
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error logging material usage: {e}")
            raise
        except ValueError as e:
            logger.error(f"Validation error logging material usage: {e}")
            raise

    def get_material_usage_history(
            self,
            material_id: Optional[int] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[MaterialUsageLog]:
        """
        Retrieve material usage history with optional filtering.

        Args:
            material_id (Optional[int], optional): Specific material ID to filter
            start_date (Optional[datetime], optional): Start of date range
            end_date (Optional[datetime], optional): End of date range

        Returns:
            List[MaterialUsageLog]: List of material usage logs
        """
        try:
            query = self.session.query(MaterialUsageLog)

            if material_id:
                query = query.filter(MaterialUsageLog.material_id == material_id)

            if start_date:
                query = query.filter(MaterialUsageLog.timestamp >= start_date)

            if end_date:
                query = query.filter(MaterialUsageLog.timestamp <= end_date)

            return query.order_by(MaterialUsageLog.timestamp.asc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving material usage history: {e}")
            raise

    def get_material_efficiency_stats(
            self,
            material_id: Optional[int] = None,
            days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate material efficiency statistics.

        Args:
            material_id (Optional[int], optional): Specific material ID to analyze
            days (int, optional): Number of days to look back. Defaults to 30.

        Returns:
            Dict[str, float]: Efficiency statistics including average efficiency, total waste, and total used
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = (
                self.session.query(
                    self.session.query(MaterialUsageLog)
                    .filter(MaterialUsageLog.timestamp >= start_date)
                )
            )

            if material_id:
                query = query.filter(MaterialUsageLog.material_id == material_id)

            # Aggregate calculations
            avg_efficiency = query.with_entities(
                self.session.func.avg(MaterialUsageLog.efficiency).label('avg_efficiency')
            ).scalar() or 0.0

            total_waste = query.with_entities(
                self.session.func.sum(MaterialUsageLog.waste_amount).label('total_waste')
            ).scalar() or 0.0

            total_used = query.with_entities(
                self.session.func.sum(MaterialUsageLog.quantity_used).label('total_used')
            ).scalar() or 0.0

            return {
                'average_efficiency': float(avg_efficiency),
                'total_waste': float(total_waste),
                'total_used': float(total_used)
            }
        except SQLAlchemyError as e:
            logger.error(f"Error calculating material efficiency stats: {e}")
            raise

    def cleanup_old_metrics(self, days_to_keep: int = 365) -> int:
        """
        Clean up old metric snapshots.

        Args:
            days_to_keep (int, optional): Number of days to retain metrics. Defaults to 365.

        Returns:
            int: Number of deleted metric snapshots
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            deleted = (
                self.session.query(MetricSnapshot)
                .filter(MetricSnapshot.timestamp < cutoff_date)
                .delete(synchronize_session=False)
            )

            self.session.commit()

            logger.info(f"Cleaned up {deleted} old metric snapshots")
            return deleted
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error cleaning up old metrics: {e}")
            raise