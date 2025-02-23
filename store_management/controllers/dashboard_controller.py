# controllers/dashboard_controller.py
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta

from services.dashboard_service import DashboardService
from database.models.metrics import TimeFrame
from dependencies import get_dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(
    dashboard_service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, Any]:
    """
    Get all current dashboard metrics.
    """
    try:
        return dashboard_service.get_dashboard_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/history")
async def get_metrics_history(
    metric_type: str,
    time_frame: TimeFrame,
    days: int = 30,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, Any]:
    """
    Get historical metrics for the specified type and timeframe.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        return dashboard_service.get_metrics_history(metric_type, time_frame, start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics/capture")
async def capture_metrics(
    time_frame: TimeFrame = TimeFrame.DAILY,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
) -> Dict[str, str]:
    """
    Manually trigger metrics capture.
    """
    try:
        dashboard_service.capture_metrics(time_frame)
        return {"message": "Metrics captured successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# scheduler/metrics_scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from database.models.metrics import TimeFrame
from services.dashboard_service import DashboardService

class MetricsScheduler:
    def __init__(self, dashboard_service: DashboardService):
        self.dashboard_service = dashboard_service
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()

    def _setup_jobs(self):
        """Setup all scheduled metric capture jobs"""
        # Daily metrics capture - run at midnight
        self.scheduler.add_job(
            self._capture_daily_metrics,
            CronTrigger(hour=0, minute=0),
            id='daily_metrics',
            replace_existing=True
        )

        # Weekly metrics capture - run on Monday at 1 AM
        self.scheduler.add_job(
            self._capture_weekly_metrics,
            CronTrigger(day_of_week='mon', hour=1, minute=0),
            id='weekly_metrics',
            replace_existing=True
        )

        # Monthly metrics capture - run on 1st of month at 2 AM
        self.scheduler.add_job(
            self._capture_monthly_metrics,
            CronTrigger(day=1, hour=2, minute=0),
            id='monthly_metrics',
            replace_existing=True
        )

        # Cleanup old metrics - run once per month
        self.scheduler.add_job(
            self._cleanup_old_metrics,
            CronTrigger(day=1, hour=3, minute=0),
            id='cleanup_metrics',
            replace_existing=True
        )

    def _capture_daily_metrics(self):
        """Capture daily metrics"""
        try:
            self.dashboard_service.capture_metrics(TimeFrame.DAILY)
            logging.info(f"Daily metrics captured at {datetime.now()}")
        except Exception as e:
            logging.error(f"Error capturing daily metrics: {str(e)}")

    def _capture_weekly_metrics(self):
        """Capture weekly metrics"""
        try:
            self.dashboard_service.capture_metrics(TimeFrame.WEEKLY)
            logging.info(f"Weekly metrics captured at {datetime.now()}")
        except Exception as e:
            logging.error(f"Error capturing weekly metrics: {str(e)}")

    def _capture_monthly_metrics(self):
        """Capture monthly metrics"""
        try:
            self.dashboard_service.capture_metrics(TimeFrame.MONTHLY)
            logging.info(f"Monthly metrics captured at {datetime.now()}")
        except Exception as e:
            logging.error(f"Error capturing monthly metrics: {str(e)}")

    def _cleanup_old_metrics(self):
        """Clean up old metrics"""
        try:
            deleted_count = self.dashboard_service.metrics_repository.cleanup_old_metrics()
            logging.info(f"Cleaned up {deleted_count} old metrics at {datetime.now()}")
        except Exception as e:
            logging.error(f"Error cleaning up old metrics: {str(e)}")

    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logging.info("Metrics scheduler started successfully")
        except Exception as e:
            logging.error(f"Error starting metrics scheduler: {str(e)}")
            raise

    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            self.scheduler.shutdown()
            logging.info("Metrics scheduler shut down successfully")
        except Exception as e:
            logging.error(f"Error shutting down metrics scheduler: {str(e)}")
            raise

# config/dependencies.py
from fastapi import Depends
from typing import Generator

from services.dashboard_service import DashboardService
from database.repositories.metrics_repository import MetricsRepository
from config.container import get_container

def get_dashboard_service() -> Generator[DashboardService, None, None]:
    """Dependency to get dashboard service instance"""
    container = get_container()
    try:
        service = container.get_service('DashboardService')
        yield service
    finally:
        pass  # Add any cleanup if needed