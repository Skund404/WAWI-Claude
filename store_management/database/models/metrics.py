from di.core import inject
from services.interfaces import MaterialService, ProjectService, \
    InventoryService, OrderService


class MetricType(enum.Enum):
    """ """
    INVENTORY = 'inventory'
    PROJECT = 'project'
    MATERIAL = 'material'
    SUPPLIER = 'supplier'


class TimeFrame(enum.Enum):
    """ """
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'


class MetricSnapshot(BaseModel):
    """Stores point-in-time snapshots of various system metrics"""
    __tablename__ = 'metric_snapshots'
    id = Column(Integer, primary_key=True)
    metric_type = Column(SQLAEnum(MetricType), nullable=False)
    time_frame = Column(SQLAEnum(TimeFrame), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    leather_stock_level = Column(Float)
    hardware_stock_level = Column(Float)
    low_stock_count = Column(Integer)
    pending_orders = Column(Integer)
    active_projects = Column(Integer)
    completed_projects = Column(Integer)
    completion_rate = Column(Float)
    delayed_projects = Column(Integer)
    material_usage = Column(Float)
    material_waste = Column(Float)
    material_efficiency = Column(Float)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'),
                        nullable=True)
    quality_score = Column(Float)
    delivery_score = Column(Float)
    price_score = Column(Float)
    response_score = Column(Float)
    supplier = relationship('Supplier', back_populates='metrics')

    @inject(MaterialService)
    def __repr__(self):
        return (
            f'<MetricSnapshot(type={self.metric_type}, '
            f'time={self.timestamp})>'
        )


class MaterialUsageLog(BaseModel):
    """Detailed logging of material usage"""
    __tablename__ = 'material_usage_logs'
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey('materials.id'),
                        nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    quantity_used = Column(Float, nullable=False)
    waste_amount = Column(Float, default=0.0)
    efficiency = Column(Float)
    notes = Column(String(500))
    material = relationship('Material', back_populates='usage_logs')
    project = relationship('Project', back_populates='material_logs')

    @inject(MaterialService)
    def calculate_efficiency(self) -> float:
        if self.quantity_used == 0:
            return 0.0
        return (self.quantity_used - self.waste_amount) / \
            self.quantity_used


class MetricsRepository:
    """ """

    @inject(MaterialService)
    def __init__(self, session: Session):
        self.session = session

    @inject(MaterialService)
    def create_metric_snapshot(self, snapshot_data: Dict) -> MetricSnapshot:
        """Create a new metric snapshot"""
        snapshot = MetricSnapshot(**snapshot_data)
        self.session.add(snapshot)
        self.session.commit()
        return snapshot

    @inject(MaterialService)
    def get_latest_metrics(self, metric_type: MetricType) -> Optional[
        MetricSnapshot]:
        """Get the most recent metrics for a given type"""
        return self.session.query(MetricSnapshot).filter(
            MetricSnapshot.metric_type == metric_type
        ).order_by(MetricSnapshot.timestamp.desc()).first()

    @inject(MaterialService)
    def get_metrics_history(self, metric_type: MetricType, time_frame:
                             TimeFrame, start_date: datetime, end_date: datetime = None
                             ) -> List[MetricSnapshot]:
        """Get historical metrics for a given type and timeframe"""
        if end_date is None:
            end_date = datetime.utcnow()
        return self.session.query(MetricSnapshot).filter(and_(
            MetricSnapshot.metric_type == metric_type,
            MetricSnapshot.time_frame == time_frame,
            MetricSnapshot.timestamp.between(
                start_date, end_date))).order_by(
            MetricSnapshot.timestamp.asc()).all()

    @inject(MaterialService)
    def log_material_usage(self, usage_data: Dict) -> MaterialUsageLog:
        """Log material usage data"""
        usage_log = MaterialUsageLog(**usage_data)
        usage_log.efficiency = usage_log.calculate_efficiency()
        self.session.add(usage_log)
        self.session.commit()
        return usage_log

    @inject(MaterialService)
    def get_material_usage_history(
            self, material_id: Optional[int] = None,
            start_date: datetime = None, end_date: datetime = None
    ) -> List[MaterialUsageLog]:
        """Get material usage history with optional filtering"""
        query = self.session.query(MaterialUsageLog)
        if material_id:
            query = query.filter(
                MaterialUsageLog.material_id == material_id)
        if start_date:
            query = query.filter(MaterialUsageLog.timestamp >= start_date)
        if end_date:
            query = query.filter(MaterialUsageLog.timestamp <= end_date)
        return query.order_by(MaterialUsageLog.timestamp.asc()).all()

    @inject(MaterialService)
    def get_material_efficiency_stats(
            self, material_id: Optional[int] = None,
            days: int = 30) -> Dict:
        """Calculate material efficiency statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        query = self.session.query(
            func.avg(MaterialUsageLog.efficiency).label('avg_efficiency'),
            func.sum(MaterialUsageLog.waste_amount).label('total_waste'),
            func.sum(MaterialUsageLog.quantity_used).label('total_used')
        ).filter(MaterialUsageLog.timestamp >= start_date)
        if material_id:
            query = query.filter(
                MaterialUsageLog.material_id == material_id)
        result = query.first()
        return {
            'average_efficiency': float(result.avg_efficiency)
            if result.avg_efficiency else 0.0,
            'total_waste': float(result.total_waste)
            if result.total_waste else 0.0,
            'total_used': float(result.total_used)
            if result.total_used else 0.0
        }

    @inject(MaterialService)
    def cleanup_old_metrics(self, days_to_keep: int = 365) -> int:
        """Clean up old metric snapshots"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted = self.session.query(MetricSnapshot).filter(
            MetricSnapshot.timestamp < cutoff_date).delete()
        self.session.commit()
        return deleted


class DashboardService(IBaseService):
    """ """

    @inject(MaterialService)
    def __init__(self, container):
        super().__init__(container)
        self.metrics_repository = container.get_service('MetricsRepository')
        self.inventory_service = container.get_service('IInventoryService')
        self.project_service = container.get_service('IProjectService')
        self.supplier_service = container.get_service('ISupplierService')

    @inject(MaterialService)
    def get_dashboard_metrics(self) -> Dict:
        """
        Retrieves all metrics needed for the dashboard.
        """
        try:
            return {
                'inventory_metrics': self._get_inventory_metrics(),
                'project_metrics': self._get_project_metrics(),
                'material_usage': self._get_material_usage(),
                'supplier_metrics': self._get_supplier_metrics()
            }
        except Exception as e:
            logging.error(f'Error fetching dashboard metrics: {str(e)}')
            raise

    @inject(MaterialService)
    def capture_metrics(self, time_frame: TimeFrame = TimeFrame.DAILY):
        """
        Captures current metrics and stores them in the database.
        """
        try:
            inventory_metrics = self._get_inventory_metrics()
            self.metrics_repository.create_metric_snapshot({
                'metric_type': MetricType.INVENTORY,
                'time_frame': time_frame, **inventory_metrics
            })
            project_metrics = self._get_project_metrics()
            self.metrics_repository.create_metric_snapshot({
                'metric_type': MetricType.PROJECT,
                'time_frame': time_frame, **project_metrics
            })
            material_metrics = self._get_material_usage()
            self.metrics_repository.create_metric_snapshot({
                'metric_type': MetricType.MATERIAL,
                'time_frame': time_frame, **material_metrics
            })
            supplier_metrics = self._get_supplier_metrics()
            for supplier_metric in supplier_metrics:
                self.metrics_repository.create_metric_snapshot({
                    'metric_type': MetricType.SUPPLIER,
                    'time_frame': time_frame, **supplier_metric
                })
        except Exception as e:
            logging.error(f'Error capturing metrics: {str(e)}')
            raise

    @inject(MaterialService)
    def _get_inventory_metrics(self) -> Dict:
        """Gets current inventory status and alerts."""
        try:
            low_stock_parts = self.inventory_service.get_low_stock_parts(
                include_out_of_stock=True)
            low_stock_leather = self.inventory_service.get_low_stock_leather(
                include_out_of_stock=True)
            return {
                'leather_stock_level': self._calculate_stock_percentage
                (low_stock_leather),
                'hardware_stock_level': self._calculate_stock_percentage
                (low_stock_parts),
                'low_stock_count': len(low_stock_parts) + len(
                    low_stock_leather),
                'pending_orders': len(self._get_pending_orders())
            }
        except Exception as e:
            logging.error(f'Error in inventory metrics: {str(e)}')
            return self._get_default_inventory_metrics()

    @inject(MaterialService)
    def _get_project_metrics(self) -> Dict:
        """Retrieves project-related metrics."""
        try:
            current_month = datetime.now().replace(day=1)
            completed_projects = self.project_service.\
                get_completed_projects(start_date=current_month)
            active_projects = self.project_service.get_active_projects()
            return {
                'active_projects': len(active_projects),
                'completed_projects': len(completed_projects),
                'completion_rate': self._calculate_completion_rate(
                    active_projects),
                'delayed_projects': self._count_delayed_projects(
                    active_projects)
            }
        except Exception as e:
            logging.error(f'Error in project metrics: {str(e)}')
            return self._get_default_project_metrics()

    @inject(MaterialService)
    def _get_material_usage(self) -> Dict:
        """Calculates material usage trends."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            usage_stats = (self.metrics_repository.
                get_material_efficiency_stats(days=30))
            usage_history = self.metrics_repository.\
                get_material_usage_history(start_date=start_date,
                                            end_date=end_date)
            return {
                'material_usage': usage_stats['total_used'],
                'material_waste': usage_stats['total_waste'],
                'material_efficiency': usage_stats['average_efficiency']
            }
        except Exception as e:
            logging.error(f'Error in material usage: {str(e)}')
            return self._get_default_material_metrics()

    @inject(MaterialService)
    def _get_supplier_metrics(self) -> List[Dict]:
        """Gets supplier performance metrics."""
        try:
            suppliers = self.supplier_service.get_all_suppliers()
            metrics = []
            for supplier in suppliers:
                performance = self.supplier_service.\
                    get_supplier_performance(supplier.id)
                metrics.append({
                    'supplier_id': supplier.id,
                    'quality_score': performance.quality_score,
                    'delivery_score': performance.delivery_score,
                    'price_score': performance.price_score,
                    'response_score': performance.response_score
                })
            return metrics
        except Exception as e:
            logging.error(f'Error in supplier metrics: {str(e)}')
            return self._get_default_supplier_metrics()

    @inject(MaterialService)
    def _calculate_stock_percentage(self, items: List) -> float:
        if not items:
            return 100.0
        optimal_items = sum(
            1 for item in items if not item.needs_reorder())
        return optimal_items / len(items) * 100

    @inject(MaterialService)
    def _calculate_completion_rate(self, projects: List) -> float:
        if not projects:
            return 100.0
        completed_tasks = sum(
            project.completed_tasks for project in projects)
        total_tasks = sum(project.total_tasks for project in projects)
        return completed_tasks / total_tasks * 100 if total_tasks > \
                                                        0 else 0.0

    @inject(MaterialService)
    def _get_default_inventory_metrics(self) -> Dict:
        return {
            'leather_stock_level': 0, 'hardware_stock_level': 0,
            'low_stock_count': 0, 'pending_orders': 0
        }

    @inject(MaterialService)
    def _get_default_project_metrics(self) -> Dict:
        return {
            'active_projects': 0, 'completed_projects': 0,
            'completion_rate': 0.0, 'delayed_projects': 0
        }

    @inject(MaterialService)
    def _get_default_material_metrics(self) -> Dict:
        return {
            'material_usage': 0.0, 'material_waste': 0.0,
            'material_efficiency': 0.0
        }

    @inject(MaterialService)
    def _get_default_supplier_metrics(self) -> List[Dict]:
        return []