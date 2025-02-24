from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
router = APIRouter(prefix='/api/dashboard', tags=['dashboard'])


@router.get('/metrics')
async def get_dashboard_metrics(dashboard_service: DashboardService = Depends
(get_dashboard_service)) -> Dict[str, Any]:
"""
Get all current dashboard metrics.
"""
try:
    pass
return dashboard_service.get_dashboard_metrics()
except Exception as e:
    pass
raise HTTPException(status_code=500, detail=str(e))


@router.get('/metrics/history')
async def get_metrics_history(metric_type: str, time_frame: TimeFrame, days:
int = 30, dashboard_service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, Any]:
"""
Get historical metrics for the specified type and timeframe.
"""
try:
    pass
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=days)
return dashboard_service.get_metrics_history(metric_type,
time_frame, start_date, end_date)
except Exception as e:
    pass
raise HTTPException(status_code=500, detail=str(e))


@router.post('/metrics/capture')
async def capture_metrics(time_frame: TimeFrame = TimeFrame.DAILY,
dashboard_service: DashboardService = Depends(get_dashboard_service)) -> Dict[
str, str]:
"""
Manually trigger metrics capture.
"""
try:
    pass
dashboard_service.capture_metrics(time_frame)
return {'message': 'Metrics captured successfully'}
except Exception as e:
    pass
raise HTTPException(status_code=500, detail=str(e))


class MetricsScheduler:

    pass
@inject(MaterialService)
def __init__(self, dashboard_service: DashboardService):
    pass
self.dashboard_service = dashboard_service
self.scheduler = BackgroundScheduler()
self._setup_jobs()

@inject(MaterialService)
def _setup_jobs(self):
    pass
"""Setup all scheduled metric capture jobs"""
self.scheduler.add_job(self._capture_daily_metrics, CronTrigger(
hour=0, minute=0), id='daily_metrics', replace_existing=True)
self.scheduler.add_job(self._capture_weekly_metrics, CronTrigger(
day_of_week='mon', hour=1, minute=0), id='weekly_metrics',
replace_existing=True)
self.scheduler.add_job(self._capture_monthly_metrics, CronTrigger(
day=1, hour=2, minute=0), id='monthly_metrics',
replace_existing=True)
self.scheduler.add_job(self._cleanup_old_metrics, CronTrigger(day=1,
hour=3, minute=0), id='cleanup_metrics', replace_existing=True)

@inject(MaterialService)
def _capture_daily_metrics(self):
    pass
"""Capture daily metrics"""
try:
    pass
self.dashboard_service.capture_metrics(TimeFrame.DAILY)
logging.info(f'Daily metrics captured at {datetime.now()}')
except Exception as e:
    pass
logging.error(f'Error capturing daily metrics: {str(e)}')

@inject(MaterialService)
def _capture_weekly_metrics(self):
    pass
"""Capture weekly metrics"""
try:
    pass
self.dashboard_service.capture_metrics(TimeFrame.WEEKLY)
logging.info(f'Weekly metrics captured at {datetime.now()}')
except Exception as e:
    pass
logging.error(f'Error capturing weekly metrics: {str(e)}')

@inject(MaterialService)
def _capture_monthly_metrics(self):
    pass
"""Capture monthly metrics"""
try:
    pass
self.dashboard_service.capture_metrics(TimeFrame.MONTHLY)
logging.info(f'Monthly metrics captured at {datetime.now()}')
except Exception as e:
    pass
logging.error(f'Error capturing monthly metrics: {str(e)}')

@inject(MaterialService)
def _cleanup_old_metrics(self):
    pass
"""Clean up old metrics"""
try:
    pass
deleted_count = (self.dashboard_service.metrics_repository.
cleanup_old_metrics())
logging.info(
f'Cleaned up {deleted_count} old metrics at {datetime.now()}')
except Exception as e:
    pass
logging.error(f'Error cleaning up old metrics: {str(e)}')

@inject(MaterialService)
def start(self):
    pass
"""Start the scheduler"""
try:
    pass
self.scheduler.start()
logging.info('Metrics scheduler started successfully')
except Exception as e:
    pass
logging.error(f'Error starting metrics scheduler: {str(e)}')
raise

@inject(MaterialService)
def shutdown(self):
    pass
"""Shutdown the scheduler"""
try:
    pass
self.scheduler.shutdown()
logging.info('Metrics scheduler shut down successfully')
except Exception as e:
    pass
logging.error(f'Error shutting down metrics scheduler: {str(e)}')
raise


def get_dashboard_service() -> Generator[DashboardService, None, None]:
"""Dependency to get dashboard service instance"""
container = get_container()
try:
    pass
except Exception:
    pass
service = container.get_service('DashboardService')
yield service
finally:
pass
