# services/implementations/analytics_service.py
from __future__ import annotations

import logging
import statistics
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject

# Use lazy imports to prevent circular dependencies
from utils.lazy_imports import lazy_import_enum, lazy_import_repository

class AnalyticsService(BaseService, IAnalyticsService):
    """
    Comprehensive analytics service for leatherworking business intelligence.

    This service provides deep insights across multiple business dimensions:
    - Product Profitability
    - Custom Order Analysis
    - Seasonal Trends
    - Material Utilization
    - Customer Behavior
    """

    @inject
    def __init__(
            self,
            session: Session,
            customer_repository=None,
            sales_repository=None,
            project_repository=None,
            inventory_repository=None,
            material_repository=None,
            pattern_repository=None,
            product_repository=None,
            hardware_repository=None
    ):
        """
        Initialize the analytics service with required repositories.

        Args:
            session: Database session
            customer_repository: Repository for customer data
            sales_repository: Repository for sales data
            project_repository: Repository for project data
            inventory_repository: Repository for inventory data
            material_repository: Repository for material data
            pattern_repository: Repository for pattern data
            product_repository: Repository for product data
            hardware_repository: Repository for hardware data
        """
        super().__init__(session)
        self._logger = logging.getLogger(__name__)

        # Lazy load repositories
        self._customer_repo = (
            customer_repository or
            lazy_import_repository('Customer')(session)
        )
        self._sales_repo = (
            sales_repository or
            lazy_import_repository('Sales')(session)
        )
        self._project_repo = (
            project_repository or
            lazy_import_repository('Project')(session)
        )
        self._inventory_repo = (
            inventory_repository or
            lazy_import_repository('Inventory')(session)
        )
        self._material_repo = (
            material_repository or
            lazy_import_repository('Material')(session)
        )
        self._pattern_repo = (
            pattern_repository or
            lazy_import_repository('Pattern')(session)
        )
        self._product_repo = (
            product_repository or
            lazy_import_repository('Product')(session)
        )
        self._hardware_repo = (
            hardware_repository or
            lazy_import_repository('Hardware')(session)
        )

        # Lazy load enums
        self.ProjectType = lazy_import_enum('ProjectType')
        self.ComponentType = lazy_import_enum('ComponentType')
        self.MaterialType = lazy_import_enum('MaterialType')
        self.LeatherType = lazy_import_enum('LeatherType')
        self.SkillLevel = lazy_import_enum('SkillLevel')
        self.CustomerTier = lazy_import_enum('CustomerTier')
        self.SeasonType = lazy_import_enum('SeasonType')
        self.ProductType = lazy_import_enum('ProductType')

    def get_dashboard_metrics(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard metrics for business overview.

        Args:
            date_range: Optional date range for metrics (start_date, end_date)

        Returns:
            Dictionary of key business metrics
        """
        try:
            # Set default date range to last 30 days if not provided
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            # Aggregate metrics from various analytical methods
            return {
                'sales_metrics': self._get_sales_dashboard_metrics(date_range),
                'product_metrics': self._get_product_dashboard_metrics(date_range),
                'project_metrics': self._get_project_dashboard_metrics(date_range),
                'inventory_metrics': self._get_inventory_dashboard_metrics(),
                'customer_metrics': self._get_customer_dashboard_metrics(date_range)
            }
        except Exception as e:
            self._logger.error(f"Error generating dashboard metrics: {e}")
            raise ValidationError(f"Could not generate dashboard metrics: {e}")

    def _get_sales_dashboard_metrics(self, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Generate sales-related dashboard metrics.

        Args:
            date_range: Tuple of start and end dates

        Returns:
            Dictionary of sales metrics
        """
        sales = self._sales_repo.get_by_date_range(*date_range)

        # Calculate key sales metrics
        total_revenue = sum(sale.total_amount for sale in sales)
        total_orders = len(sales)
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        # Top-selling products
        product_sales = defaultdict(float)
        for sale in sales:
            for item in sale.items:
                product_sales[item.product.name] += item.total_amount

        top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'total_revenue': round(total_revenue, 2),
            'total_orders': total_orders,
            'average_order_value': round(avg_order_value, 2),
            'top_products': dict(top_products)
        }

    def _get_product_dashboard_metrics(self, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Generate product-related dashboard metrics.

        Args:
            date_range: Tuple of start and end dates

        Returns:
            Dictionary of product metrics
        """
        # Fetch product data
        products = self._product_repo.get_by_date_range(*date_range)

        # Analyze product types
        product_type_breakdown = defaultdict(int)
        for product in products:
            if product.type:
                product_type_breakdown[product.type.name] += 1

        # Profitability analysis
        product_profitability = self.get_product_profitability_deep_dive(date_range[0], date_range[1])

        return {
            'total_products': len(products),
            'product_type_distribution': dict(product_type_breakdown),
            'most_profitable_products': product_profitability['most_profitable_products'],
            'overall_profit_margin': product_profitability['overall_profit_margin']
        }

    def _get_project_dashboard_metrics(self, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Generate project-related dashboard metrics.

        Args:
            date_range: Tuple of start and end dates

        Returns:
            Dictionary of project metrics
        """
        projects = self._project_repo.get_by_date_range(*date_range)

        # Project status breakdown
        status_breakdown = defaultdict(int)
        project_types = defaultdict(int)

        for project in projects:
            if project.status:
                status_breakdown[project.status.name] += 1
            if project.type:
                project_types[project.type.name] += 1

        # Project complexity analysis
        complexity_analysis = self.get_project_complexity_analysis()

        return {
            'total_projects': len(projects),
            'status_breakdown': dict(status_breakdown),
            'project_types': dict(project_types),
            'average_project_complexity': complexity_analysis.get('average_complexity', 0)
        }

    def _get_inventory_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Generate inventory-related dashboard metrics.

        Returns:
            Dictionary of inventory metrics
        """
        # Inventory health report
        inventory_health = self.get_inventory_health_report()

        return {
            'total_inventory_items': inventory_health.get('total_inventory_items', 0),
            'total_inventory_value': inventory_health.get('total_inventory_value', 0),
            'low_stock_items': inventory_health.get('low_stock_items', []),
            'material_type_distribution': inventory_health.get('material_type_distribution', {})
        }

    def _get_customer_dashboard_metrics(self, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Generate customer-related dashboard metrics.

        Args:
            date_range: Tuple of start and end dates

        Returns:
            Dictionary of customer metrics
        """
        # Customer lifetime value analysis
        customer_metrics = self.get_customer_lifetime_value_analysis()

        # Recent custom order insights
        custom_order_insights = self.analyze_custom_order_insights(*date_range)

        return {
            'total_customers': customer_metrics.get('total_customers', 0),
            'total_customer_lifetime_value': customer_metrics.get('total_customer_lifetime_value', 0),
            'tier_distribution': customer_metrics.get('tier_distribution', {}),
            'custom_order_rate': custom_order_insights.get('custom_order_rate', 0)
        }

    def get_product_profitability_deep_dive(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive product profitability analysis.

        Args:
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis

        Returns:
            Detailed product profitability insights
        """
        # Implementation details would be similar to the previous draft
        # This is a placeholder - you'd replace with full implementation
        try:
            # Fetch product sales data
            sales = self._sales_repo.get_by_date_range(
                start_date or datetime.now() - timedelta(days=365),
                end_date or datetime.now()
            )

            # Analyze product profitability
            product_profitability = defaultdict(lambda: {
                'total_revenue': 0,
                'total_cost': 0,
                'quantity_sold': 0
            })

            for sale in sales:
                for item in sale.items:
                    product = item.product
                    if product:
                        product_profitability[product.name]['total_revenue'] += item.total_amount
                        product_profitability[product.name]['quantity_sold'] += item.quantity
                        # Note: You'd calculate actual cost here

            # Calculate profit margins
            profitability_summary = []
            for product_name, metrics in product_profitability.items():
                profit_margin = (
                    (metrics['total_revenue'] - metrics['total_cost']) / metrics['total_revenue'] * 100
                    if metrics['total_revenue'] > 0 else 0
                )

                profitability_summary.append({
                    'product_name': product_name,
                    'total_revenue': metrics['total_revenue'],
                    'quantity_sold': metrics['quantity_sold'],
                    'profit_margin': round(profit_margin, 2)
                })

            # Sort by profit margin
            profitability_summary.sort(key=lambda x: x['profit_margin'], reverse=True)

            return {
                'most_profitable_products': profitability_summary[:5],
                'least_profitable_products': profitability_summary[-5:],
                'overall_profit_margin': round(
                    sum(item['profit_margin'] for item in profitability_summary) / len(profitability_summary),
                    2
                )
            }
        except Exception as e:
            self._logger.error(f"Error in product profitability analysis: {e}")
            raise ValidationError(f"Could not generate product profitability report: {e}")

    def get_project_complexity_analysis(
            self,
            project_type: Optional[ProjectType] = None,
            skill_level: Optional[SkillLevel] = None
    ) -> Dict[str, Any]:
        """
        Analyze project complexity and resource allocation.

        Args:
            project_type: Optional filter for project type
            skill_level: Optional filter for skill level

        Returns:
            Project complexity insights
        """
        try:
            # Fetch projects with optional filtering
            projects = self._project_repo.get_projects(
                project_type=project_type,
                skill_level=skill_level
            )

            # Complexity metrics
            complexity_metrics = {
                'total_projects': len(projects),
                'complexity_by_type': defaultdict(list),
                'complexity_by_skill_level': defaultdict(list)
            }

            for project in projects:
                # Calculate project complexity
                complexity_score = self._calculate_project_complexity(project)

                # Categorize by project type
                if project.type:
                    complexity_metrics['complexity_by_type'][project.type.name].append(complexity_score)

                # Categorize by skill level
                if project.skill_level:
                    complexity_metrics['complexity_by_skill_level'][project.skill_level.name].append(complexity_score)

            # Calculate average complexities
            complexity_metrics['complexity_by_type'] = {
                type_name: np.mean(scores)
                for type_name, scores in complexity_metrics['complexity_by_type'].items()
            }

            complexity_metrics['complexity_by_skill_level'] = {
                skill_name: np.mean(scores)
                for skill_name, scores in complexity_metrics['complexity_by_skill_level'].items()
            }

            complexity_metrics['average_complexity'] = np.mean([
                score for type_scores in complexity_metrics['complexity_by_type'].values()
                for score in type_scores
            ])

            return complexity_metrics
        except Exception as e:
            self._logger.error(f"Error in project complexity analysis: {e}")
            raise ValidationError(f"Could not generate project complexity report: {e}")

    def _calculate_project_complexity(self, project):
        """
        Calculate a complexity score for a project.

        Args:
            project: Project model instance

        Returns:
            Complexity score (float between 0 and 1)
        """
        # Complexity factors
        complexity_factors = []

        # Number of components
        components = self._project_repo.get_project_components(project.id)
        complexity_factors.append(min(len(components) / 10, 1))  # Cap at 10 components

        # Skill level impact
        skill_level_map = {
            SkillLevel.BEGINNER: 0.2,
            SkillLevel.INTERMEDIATE: 0.5,
            SkillLevel.ADVANCED: 0.7,
            SkillLevel.MASTER: 1.0
        }
        complexity_factors.append(skill_level_map.get(project.skill_level, 0.5))

        # Project duration complexity
        if project.start_date and project.end_date:
            project_duration = (project.end_date - project.start_date).days
            complexity_factors.append(min(project_duration / 30, 1))  # Cap at 30 days

        # Calculate final complexity score
        return np.mean(complexity_factors)

    def get_inventory_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive inventory health report.

        Returns:
            Detailed inventory health insights
        """
        try:
            # Fetch all inventory items
            inventory_items = self._inventory_repo.get_all()

            # Inventory metrics
            inventory_metrics = {
                'total_inventory_items': len(inventory_items),
                'total_inventory_value': 0,
                'material_type_distribution': defaultdict(float),
                'status_breakdown': defaultdict(int),
                'low_stock_items': [],
                'critical_stock_items': []
            }

            # Analyze inventory items
            for item in inventory_items:
                # Calculate item value
                item_value = self._calculate_item_value(item)
                inventory_metrics['total_inventory_value'] += item_value

                # Track material type distribution
                if item.item_type:
                    inventory_metrics['material_type_distribution'][item.item_type] += item_value

                # Status breakdown
                if item.status:
                    inventory_metrics['status_breakdown'][item.status.name] += 1

                # Low and critical stock tracking
                if item.quantity <= 10:
                    inventory_metrics['low_stock_items'].append({
                        'id': item.id,
                        'name': self._get_item_name(item),
                        'quantity': item.quantity,
                        'type': item.item_type
                    })

                if item.quantity <= 5:
                    inventory_metrics['critical_stock_items'].append({
                        'id': item.id,
                        'name': self._get_item_name(item),
                        'quantity': item.quantity,
                        'type': item.item_type
                    })

            return inventory_metrics
        except Exception as e:
            self._logger.error(f"Error generating inventory health report: {e}")
            raise ValidationError(f"Could not generate inventory health report: {e}")

    def _calculate_item_value(self, inventory_item) -> float:
        """
        Calculate the value of an inventory item.

        Args:
            inventory_item: Inventory item model instance

        Returns:
            Estimated item value
        """
        try:
            if inventory_item.item_type == 'material':
                material = self._material_repo.get_by_id(inventory_item.item_id)
                return material.cost_per_unit * inventory_item.quantity if material else 0
            elif inventory_item.item_type == 'product':
                product = self._product_repo.get_by_id(inventory_item.item_id)
                return product.price * inventory_item.quantity if product else 0
            elif inventory_item.item_type == 'tool':
                tool = self._hardware_repo.get_by_id(inventory_item.item_id)
                return tool.cost * inventory_item.quantity if tool else 0
            return 0
        except Exception as e:
            self._logger.warning(f"Could not calculate item value: {e}")
            return 0

    def _get_item_name(self, inventory_item) -> str:
        """
        Get the name of an inventory item.

        Args:
            inventory_item: Inventory item model instance

        Returns:
            Item name or 'Unknown'
        """
        try:
            if inventory_item.item_type == 'material':
                material = self._material_repo.get_by_id(inventory_item.item_id)
                return material.name if material else 'Unknown Material'
            elif inventory_item.item_type == 'product':
                product = self._product_repo.get_by_id(inventory_item.item_id)
                return product.name if product else 'Unknown Product'
            elif inventory_item.item_type == 'tool':
                tool = self._hardware_repo.get_by_id(inventory_item.item_id)
                return tool.name if tool else 'Unknown Tool'
            return 'Unknown Item'
        except Exception as e:
            self._logger.warning(f"Could not retrieve item name: {e}")
            return 'Unknown Item'

    def get_customer_lifetime_value_analysis(
            self,
            customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive customer lifetime value analysis.

        Args:
            customer_id: Optional specific customer ID

        Returns:
            Customer lifetime value insights
        """
        try:
            # Fetch customers
            if customer_id:
                customers = [self._customer_repo.get_by_id(customer_id)]
            else:
                customers = self._customer_repo.get_all()

            # Customer metrics
            customer_metrics = {
                'total_customers': len(customers),
                'total_customer_lifetime_value': 0,
                'tier_distribution': defaultdict(int),
                'customer_details': []
            }

            for customer in customers:
                # Get customer sales history
                sales = self._sales_repo.get_by_customer_id(customer.id)

                # Calculate customer-specific metrics
                total_sales = sum(sale.total_amount for sale in sales)
                avg_order_value = total_sales / len(sales) if sales else 0

                # Purchase frequency
                if sales:
                    sorted_sales = sorted(sales, key=lambda x: x.created_at)
                    purchase_intervals = [
                        (sorted_sales[i + 1].created_at - sorted_sales[i].created_at).days
                        for i in range(len(sorted_sales) - 1)
                    ]
                    avg_purchase_frequency = np.mean(purchase_intervals) if purchase_intervals else 0
                else:
                    avg_purchase_frequency = 0

                # Customer lifetime value estimation
                customer_lifetime_value = total_sales * (1 / (avg_purchase_frequency + 1))

                # Track tier distribution
                if customer.tier:
                    customer_metrics['tier_distribution'][customer.tier.name] += 1

                # Add customer details
                customer_details = {
                    'id': customer.id,
                    'name': customer.name,
                    'total_sales': total_sales,
                    'avg_order_value': avg_order_value,
                    'total_orders': len(sales),
                    'avg_purchase_frequency': avg_purchase_frequency,
                    'customer_lifetime_value': customer_lifetime_value,
                    'tier': customer.tier.name if customer.tier else 'Unclassified'
                }
                customer_metrics['customer_details'].append(customer_details)

                # Add to total lifetime value
                customer_metrics['total_customer_lifetime_value'] += customer_lifetime_value

            # Sort customers by lifetime value
            customer_metrics['customer_details'].sort(
                key=lambda x: x['customer_lifetime_value'],
                reverse=True
            )

            return customer_metrics
        except Exception as e:
            self._logger.error(f"Error generating customer lifetime value analysis: {e}")
            raise ValidationError(f"Could not generate customer lifetime value analysis: {e}")

    def analyze_custom_order_insights(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze custom order behavior and characteristics.

        Args:
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis

        Returns:
            Custom order insights
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        try:
            # Fetch custom orders
            custom_orders = self._sales_repo.get_custom_orders(start_date, end_date)
            standard_orders = self._sales_repo.get_standard_orders(start_date, end_date)

            # Custom order analysis
            custom_order_insights = {
                'total_custom_orders': len(custom_orders),
                'total_custom_revenue': sum(order.total_amount for order in custom_orders),
                'average_custom_order_value': sum(order.total_amount for order in custom_orders) / len(
                    custom_orders) if custom_orders else 0,

                'total_standard_orders': len(standard_orders),
                'total_standard_revenue': sum(order.total_amount for order in standard_orders),
                'average_standard_order_value': sum(order.total_amount for order in standard_orders) / len(
                    standard_orders) if standard_orders else 0,

                'custom_order_rate': len(custom_orders) / (len(custom_orders) + len(standard_orders)) * 100 if (
                            custom_orders or standard_orders) else 0
            }

            # Skill level impact analysis
            custom_order_by_skill = defaultdict(list)
            for order in custom_orders:
                if order.project and order.project.skill_level:
                    skill_level = order.project.skill_level.name
                    custom_order_by_skill[skill_level].append(order.total_amount)

            # Skill level pricing insights
            skill_level_pricing = {
                skill_level: {
                    'average_order_value': np.mean(orders),
                    'order_count': len(orders)
                }
                for skill_level, orders in custom_order_by_skill.items()
            }

            custom_order_insights['skill_level_pricing'] = skill_level_pricing

            return custom_order_insights
        except Exception as e:
            self._logger.error(f"Error analyzing custom order insights: {e}")
            raise ValidationError(f"Could not generate custom order insights: {e}")