

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class MetricsRepository:

        @inject(MaterialService)
        def __init__(self, session: Session):
        self.session = session

        @inject(MaterialService)
        def create_metric_snapshot(self, snapshot_data: Dict) ->MetricSnapshot:
        """Create a new metric snapshot"""
        snapshot = MetricSnapshot(**snapshot_data)
        self.session.add(snapshot)
        self.session.commit()
        return snapshot

        @inject(MaterialService)
        def get_latest_metrics(self, metric_type: MetricType) ->Optional[
        MetricSnapshot]:
        """Get the most recent metrics for a given type"""
        return self.session.query(MetricSnapshot).filter(MetricSnapshot.
            metric_type == metric_type).order_by(MetricSnapshot.timestamp.
            desc()).first()

        @inject(MaterialService)
        def get_metrics_history(self, metric_type: MetricType, time_frame:
        TimeFrame, start_date: datetime, end_date: datetime=None) ->List[
        MetricSnapshot]:
        """Get historical metrics for a given type and timeframe"""
        if end_date is None:
            end_date = datetime.utcnow()
        return self.session.query(MetricSnapshot).filter(and_(
            MetricSnapshot.metric_type == metric_type, MetricSnapshot.
            time_frame == time_frame, MetricSnapshot.timestamp.between(
            start_date, end_date))).order_by(MetricSnapshot.timestamp.asc()
            ).all()

        @inject(MaterialService)
        def log_material_usage(self, usage_data: Dict) ->MaterialUsageLog:
        """Log material usage data"""
        usage_log = MaterialUsageLog(**usage_data)
        usage_log.efficiency = usage_log.calculate_efficiency()
        self.session.add(usage_log)
        self.session.commit()
        return usage_log

        @inject(MaterialService)
        def get_material_usage_history(self, material_id: Optional[int]=None,
        start_date: datetime=None, end_date: datetime=None) ->List[
        MaterialUsageLog]:
        """Get material usage history with optional filtering"""
        query = self.session.query(MaterialUsageLog)
        if material_id:
            query = query.filter(MaterialUsageLog.material_id == material_id)
        if start_date:
            query = query.filter(MaterialUsageLog.timestamp >= start_date)
        if end_date:
            query = query.filter(MaterialUsageLog.timestamp <= end_date)
        return query.order_by(MaterialUsageLog.timestamp.asc()).all()

        @inject(MaterialService)
        def get_material_efficiency_stats(self, material_id: Optional[int]=None,
        days: int=30) ->Dict:
        """Calculate material efficiency statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        query = self.session.query(func.avg(MaterialUsageLog.efficiency).
            label('avg_efficiency'), func.sum(MaterialUsageLog.waste_amount
            ).label('total_waste'), func.sum(MaterialUsageLog.quantity_used
            ).label('total_used')).filter(MaterialUsageLog.timestamp >=
            start_date)
        if material_id:
            query = query.filter(MaterialUsageLog.material_id == material_id)
        result = query.first()
        return {'average_efficiency': float(result.avg_efficiency) if
            result.avg_efficiency else 0.0, 'total_waste': float(result.
            total_waste) if result.total_waste else 0.0, 'total_used': 
            float(result.total_used) if result.total_used else 0.0}

        @inject(MaterialService)
        def cleanup_old_metrics(self, days_to_keep: int=365) ->int:
        """Clean up old metric snapshots"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted = self.session.query(MetricSnapshot).filter(MetricSnapshot.
            timestamp < cutoff_date).delete()
        self.session.commit()
        return deleted
