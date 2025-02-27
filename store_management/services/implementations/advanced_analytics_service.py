#!/usr/bin/env python3
# Path: dashboard_service.py
"""
Dashboard Service Implementation

Provides functionality for retrieving and aggregating metrics for the dashboard interface.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from services.base_service import BaseService, NotFoundError, ValidationError
logger = logging.getLogger(__name__)


class DashboardService(BaseService):
    """
    Service for managing and retrieving dashboard metrics and analytics.
    Handles data aggregation and metric calculations for the dashboard view.
    """

    def __init__(self, container) -> None:
        """
        Initialize the dashboard service.

        Args:
            container: Dependency injection container
        """
        super().__init__(container)
        self.metrics_repository = self.get_dependency('MetricsRepository')
        self.inventory_service = self.get_dependency('InventoryService')
        self.project_service = self.get_dependency('ProjectService')
        self.supplier_service = self.get_dependency('SupplierService')

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get all dashboard metrics including inventory, projects, and supplier data.

        Returns:
            Dict[str, Any]: Combined dashboard metrics
        """
        try:
            return {
                'inventory': self._get_inventory_metrics(),
                'projects': self._get_project_metrics(),
                'material_usage': self._get_material_usage(),
                'supplier_metrics': self._get_supplier_metrics()
            }
        except Exception as e:
            logger.error(f'Error getting dashboard metrics: {str(e)}')
            return self._get_default_metrics()

    def _get_inventory_metrics(self) -> Dict[str, Any]:
        """
        Get inventory-related metrics.

        Returns:
            Dict[str, Any]: Inventory metrics including stock levels and alerts
        """
        try:
            inventory_data = {
                'low_stock_parts': self.inventory_service.get_low_stock_parts(True),
                'low_stock_leather': self.inventory_service.get_low_stock_leather(True)
            }
            inventory_data['stock_status'] = self._calculate_stock_percentage(
                inventory_data['low_stock_parts'] + inventory_data['low_stock_leather']
            )
            return inventory_data
        except Exception as e:
            logger.error(f'Error calculating inventory metrics: {str(e)}')
            return self._get_default_inventory_metrics()

    def _get_project_metrics(self) -> Dict[str, Any]:
        """
        Get project-related metrics and statistics.

        Returns:
            Dict[str, Any]: Project metrics including completion rates and status
        """
        try:
            projects = self.project_service.search_projects({})
            return {
                'total_projects': len(projects),
                'completion_rate': self._calculate_completion_rate(projects),
                'projects_by_status': self._group_projects_by_status(projects)
            }
        except Exception as e:
            logger.error(f'Error calculating project metrics: {str(e)}')
            return self._get_default_project_metrics()

    def _get_material_usage(self) -> Dict[str, Any]:
        """
        Get material usage statistics and trends.

        Returns:
            Dict[str, Any]: Material usage metrics and efficiency data
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            return {
                'usage_trends': self.metrics_repository.get_material_usage_history(
                    None, start_date, end_date
                ),
                'efficiency_stats': self._calculate_material_efficiency()
            }
        except Exception as e:
            logger.error(f'Error calculating material usage: {str(e)}')
            return self._get_default_material_usage()

    def _get_supplier_metrics(self) -> Dict[str, Any]:
        """
        Get supplier performance metrics.

        Returns:
            Dict[str, Any]: Supplier metrics including reliability and delivery stats
        """
        try:
            return {
                'performance': self.supplier_service.generate_supplier_report(),
                'active_orders': self._get_active_supplier_orders()
            }
        except Exception as e:
            logger.error(f'Error calculating supplier metrics: {str(e)}')
            return self._get_default_supplier_metrics()

    def _calculate_stock_percentage(self, items: List[Any]) -> Dict[str, float]:
        """
        Calculate percentage of items at different stock levels.

        Args:
            items: List of inventory items

        Returns:
            Dict[str, float]: Percentages for different stock levels
        """
        total = len(items)
        if not total:
            return {'healthy': 0, 'warning': 0, 'critical': 0}

        return {
            'healthy': len([i for i in items if i.quantity > i.reorder_point]) / total * 100,
            'warning': len([i for i in items if i.quantity <= i.reorder_point and i.quantity > 0]) / total * 100,
            'critical': len([i for i in items if i.quantity == 0]) / total * 100
        }

    def _calculate_completion_rate(self, projects: List[Any]) -> float:
        """
        Calculate project completion rate.

        Args:
            projects: List of projects

        Returns:
            float: Completion rate as percentage
        """
        if not projects:
            return 0.0

        completed = len([p for p in projects if p.status == 'completed'])
        return completed / len(projects) * 100

    def _group_projects_by_status(self, projects: List[Any]) -> Dict[str, int]:
        """
        Group projects by their status.

        Args:
            projects: List of projects

        Returns:
            Dict[str, int]: Count of projects by status
        """
        status_counts = {}
        for project in projects:
            status_counts[project.status] = status_counts.get(project.status, 0) + 1
        return status_counts

    def _calculate_material_efficiency(self) -> Dict[str, float]:
        """
        Calculate material usage efficiency metrics.

        Returns:
            Dict[str, float]: Efficiency metrics
        """
        try:
            return {
                'last_week': self.metrics_repository.get_material_efficiency_stats(None, 7),
                'last_month': self.metrics_repository.get_material_efficiency_stats(None, 30),
                'last_quarter': self.metrics_repository.get_material_efficiency_stats(None, 90)
            }
        except Exception as e:
            logger.error(f'Error calculating material efficiency: {str(e)}')
            return {'last_week': 0, 'last_month': 0, 'last_quarter': 0}

    def _get_active_supplier_orders(self) -> List[Dict[str, Any]]:
        """
        Get list of active supplier orders.

        Returns:
            List[Dict[str, Any]]: Active orders with supplier info
        """
        try:
            return self.supplier_service.get_active_orders()
        except Exception as e:
            logger.error(f'Error getting active supplier orders: {str(e)}')
            return []

    def _get_default_metrics(self) -> Dict[str, Any]:
        """
        Get default metrics when normal calculation fails.

        Returns:
            Dict[str, Any]: Default metrics structure
        """
        return {
            'inventory': self._get_default_inventory_metrics(),
            'projects': self._get_default_project_metrics(),
            'material_usage': self._get_default_material_usage(),
            'supplier_metrics': self._get_default_supplier_metrics()
        }

    def _get_default_inventory_metrics(self) -> Dict[str, Any]:
        """
        Get default inventory metrics.

        Returns:
            Dict[str, Any]: Default inventory metrics
        """
        return {
            'low_stock_parts': [],
            'low_stock_leather': [],
            'stock_status': {'healthy': 0, 'warning': 0, 'critical': 0}
        }

    def _get_default_project_metrics(self) -> Dict[str, Any]:
        """
        Get default project metrics.

        Returns:
            Dict[str, Any]: Default project metrics
        """
        return {
            'total_projects': 0,
            'completion_rate': 0,
            'projects_by_status': {}
        }

    def _get_default_material_usage(self) -> Dict[str, Any]:
        """
        Get default material usage metrics.

        Returns:
            Dict[str, Any]: Default material usage metrics
        """
        return {
            'usage_trends': [],
            'efficiency_stats': {'last_week': 0, 'last_month': 0, 'last_quarter': 0}
        }

    def _get_default_supplier_metrics(self) -> Dict[str, Any]:
        """
        Get default supplier metrics.

        Returns:
            Dict[str, Any]: Default supplier metrics
        """
        return {'performance': {}, 'active_orders': []}