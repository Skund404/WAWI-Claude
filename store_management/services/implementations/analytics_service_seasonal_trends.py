# services/implementations/analytics_service_seasonal_trends.py
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from sqlalchemy.orm import Session

from database.models.enums import SeasonType, ProductType, LeatherType

from di.core import inject

from services.base_service import BaseService, ValidationError


class SeasonalTrendsAnalytics(BaseService):
    """
    Specialized analytics service for seasonal trends in leatherworking business.

    Provides deep insights into seasonal product performance,
    material usage, and customer behavior across different seasons.
    """

    @inject
    def __init__(
            self,
            session: Session,
            sales_repository,
            product_repository,
            material_repository,
            project_repository
    ):
        super().__init__(session)
        self._logger = logging.getLogger(__name__)
        self._sales_repo = sales_repository
        self._product_repo = product_repository
        self._material_repo = material_repository
        self._project_repo = project_repository

    def analyze_seasonal_product_performance(
            self,
            year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of product performance across seasons.

        Args:
            year: Optional year for analysis (defaults to current year)

        Returns:
            Detailed seasonal product performance insights
        """
        if not year:
            year = datetime.now().year

        try:
            # Fetch sales data for the specified year
            sales = self._sales_repo.get_sales_by_year(year)

            # Seasonal performance metrics
            seasonal_performance = {
                season.name: {
                    'total_revenue': 0,
                    'total_orders': 0,
                    'average_order_value': 0,
                    'product_type_breakdown': defaultdict(float),
                    'top_products': defaultdict(float)
                }
                for season in SeasonType
            }

            # Analyze sales by season
            for sale in sales:
                # Determine season
                season = self._determine_season(sale.created_at)

                # Update seasonal metrics
                seasonal_performance[season]['total_revenue'] += sale.total_amount
                seasonal_performance[season]['total_orders'] += 1

                # Analyze sale items
                for item in sale.items:
                    product = item.product
                    if product:
                        # Product type breakdown
                        if product.type:
                            seasonal_performance[season]['product_type_breakdown'][
                                product.type.name] += item.total_amount

                        # Top products
                        seasonal_performance[season]['top_products'][product.name] += item.total_amount

            # Post-processing of seasonal metrics
            for season, metrics in seasonal_performance.items():
                # Calculate average order value
                metrics['average_order_value'] = (
                    metrics['total_revenue'] / metrics['total_orders']
                    if metrics['total_orders'] > 0 else 0
                )

                # Sort top products
                metrics['top_products'] = dict(
                    sorted(
                        metrics['top_products'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]  # Top 5 products
                )

                # Sort product type breakdown
                metrics['product_type_breakdown'] = dict(
                    sorted(
                        metrics['product_type_breakdown'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                )

            return {
                'year': year,
                'seasonal_performance': seasonal_performance,
                'overall_seasonal_trend': self._analyze_seasonal_trend(seasonal_performance)
            }
        except Exception as e:
            self._logger.error(f"Error analyzing seasonal product performance: {e}")
            raise ValidationError(f"Could not generate seasonal performance report: {e}")

    def analyze_material_seasonal_trends(
            self,
            year: Optional[int] = None,
            material_type: Optional[LeatherType] = None
    ) -> Dict[str, Any]:
        """
        Analyze material usage and performance across seasons.

        Args:
            year: Optional year for analysis
            material_type: Optional specific material type to analyze

        Returns:
            Seasonal material usage insights
        """
        if not year:
            year = datetime.now().year

        try:
            # Fetch material usage data
            material_usage = self._material_repo.get_seasonal_material_usage(
                year=year,
                material_type=material_type
            )

            # Seasonal material metrics
            seasonal_material_metrics = {
                season.name: {
                    'total_quantity_used': 0,
                    'total_cost': 0,
                    'average_cost_per_unit': 0,
                    'project_type_distribution': defaultdict(float),
                    'material_variations': defaultdict(lambda: {
                        'total_quantity': 0,
                        'total_cost': 0
                    })
                }
                for season in SeasonType
            }

            # Analyze material usage
            for material, usage_data in material_usage.items():
                season = self._determine_season(usage_data['date'])

                seasonal_material_metrics[season]['total_quantity_used'] += usage_data['quantity']
                seasonal_material_metrics[season]['total_cost'] += usage_data['cost']

                # Track material variations
                seasonal_material_metrics[season]['material_variations'][material.name]['total_quantity'] += usage_data[
                    'quantity']
                seasonal_material_metrics[season]['material_variations'][material.name]['total_cost'] += usage_data[
                    'cost']

                # Project type distribution
                if usage_data.get('project_type'):
                    seasonal_material_metrics[season]['project_type_distribution'][usage_data['project_type']] += \
                    usage_data['quantity']

            # Post-processing of seasonal material metrics
            for season, metrics in seasonal_material_metrics.items():
                # Calculate average cost per unit
                metrics['average_cost_per_unit'] = (
                    metrics['total_cost'] / metrics['total_quantity_used']
                    if metrics['total_quantity_used'] > 0 else 0
                )

                # Sort material variations and project type distribution
                metrics['material_variations'] = dict(
                    sorted(
                        metrics['material_variations'].items(),
                        key=lambda x: x[1]['total_quantity'],
                        reverse=True
                    )[:5]  # Top 5 material variations
                )

                metrics['project_type_distribution'] = dict(
                    sorted(
                        metrics['project_type_distribution'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                )

            return {
                'year': year,
                'seasonal_material_usage': seasonal_material_metrics,
                'material_type_analyzed': material_type.name if material_type else 'All Materials'
            }
        except Exception as e:
            self._logger.error(f"Error analyzing seasonal material trends: {e}")
            raise ValidationError(f"Could not generate seasonal material usage report: {e}")

    def analyze_hardware_seasonal_trends(
            self,
            year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze hardware usage and performance across seasons.

        Args:
            year: Optional year for analysis

        Returns:
            Seasonal hardware usage insights
        """
        if not year:
            year = datetime.now().year

        try:
            # Fetch hardware usage data
            hardware_usage = self._hardware_repo.get_seasonal_hardware_usage(year)

            # Seasonal hardware metrics
            seasonal_hardware_metrics = {
                season.name: {
                    'total_quantity_used': 0,
                    'total_cost': 0,
                    'average_cost_per_unit': 0,
                    'hardware_type_distribution': defaultdict(float),
                    'top_hardware_types': defaultdict(lambda: {
                        'total_quantity': 0,
                        'total_cost': 0
                    })
                }
                for season in SeasonType
            }

            # Analyze hardware usage
            for hardware, usage_data in hardware_usage.items():
                season = self._determine_season(usage_data['date'])

                seasonal_hardware_metrics[season]['total_quantity_used'] += usage_data['quantity']
                seasonal_hardware_metrics[season]['total_cost'] += usage_data['cost']

                # Track hardware types
                if hardware.type:
                    seasonal_hardware_metrics[season]['hardware_type_distribution'][hardware.type.name] += usage_data[
                        'quantity']

                # Top hardware types
                seasonal_hardware_metrics[season]['top_hardware_types'][hardware.name]['total_quantity'] += usage_data[
                    'quantity']
                seasonal_hardware_metrics[season]['top_hardware_types'][hardware.name]['total_cost'] += usage_data[
                    'cost']

            # Post-processing of seasonal hardware metrics
            for season, metrics in seasonal_hardware_metrics.items():
                # Calculate average cost per unit
                metrics['average_cost_per_unit'] = (
                    metrics['total_cost'] / metrics['total_quantity_used']
                    if metrics['total_quantity_used'] > 0 else 0
                )

                # Sort hardware type distribution
                metrics['hardware_type_distribution'] = dict(
                    sorted(
                        metrics['hardware_type_distribution'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                )

                # Sort top hardware types
                metrics['top_hardware_types'] = dict(
                    sorted(
                        metrics['top_hardware_types'].items(),
                        key=lambda x: x[1]['total_quantity'],
                        reverse=True
                    )[:5]  # Top 5 hardware types
                )

            return {
                'year': year,
                'seasonal_hardware_usage': seasonal_hardware_metrics
            }
        except Exception as e:
            self._logger.error(f"Error analyzing seasonal hardware trends: {e}")
            raise ValidationError(f"Could not generate seasonal hardware usage report: {e}")

    def _determine_season(self, date: datetime) -> str:
        """
        Determine the season for a given date.

        Args:
            date: Date to determine season for

        Returns:
            Season name
        """
        month = date.month

        if month in [12, 1, 2]:
            return SeasonType.WINTER.name
        elif month in [3, 4, 5]:
            return SeasonType.SPRING.name
        elif month in [6, 7, 8]:
            return SeasonType.SUMMER.name
        else:
            return SeasonType.AUTUMN.name

    def _analyze_seasonal_trend(self, seasonal_performance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze overall seasonal trend from performance metrics.

        Args:
            seasonal_performance: Seasonal performance data

        Returns:
            Seasonal trend insights
        """
        try:
            # Compare seasonal revenues
            revenues = [
                seasonal_performance[season]['total_revenue']
                for season in SeasonType.list()
            ]

            # Calculate trend statistics
            trend_analysis = {
                'highest_revenue_season': max(
                    SeasonType.list(),
                    key=lambda s: seasonal_performance[s]['total_revenue']
                ),
                'lowest_revenue_season': min(
                    SeasonType.list(),
                    key=lambda s: seasonal_performance[s]['total_revenue']
                ),
                'revenue_variation': np.std(revenues),
                'revenue_by_season': {
                    season: seasonal_performance[season]['total_revenue']
                    for season in SeasonType.list()
                }
            }

            # Determine overall seasonal trend
            if trend_analysis['revenue_variation'] < 0.1:  # Low variation
                trend_analysis['seasonal_consistency'] = 'Stable'
            elif max(revenues) / min(revenues) > 2:  # High variation
                trend_analysis['seasonal_consistency'] = 'Highly Variable'
            else:
                trend_analysis['seasonal_consistency'] = 'Moderately Variable'

            return trend_analysis
        except Exception as e:
            self._logger.error(f"Error analyzing seasonal trend: {e}")
            return {
                'error': f"Could not generate seasonal trend analysis: {e}"
            }

    def generate_predictive_insights(self) -> Dict[str, Any]:
        """
        Generate predictive business insights based on historical data.

        Returns:
            Predictive analytics insights
        """
        try:
            # Sales prediction
            sales_forecast = self._predict_sales()

            # Inventory prediction
            inventory_forecast = self._predict_inventory_needs()

            # Customer behavior prediction
            customer_prediction = self._predict_customer_trends()

            return {
                'sales_forecast': sales_forecast,
                'inventory_forecast': inventory_forecast,
                'customer_trends': customer_prediction,
                'prediction_timestamp': datetime.now()
            }
        except Exception as e:
            self._logger.error(f"Error generating predictive insights: {e}")
            raise ValidationError(f"Could not generate predictive insights: {e}")

    def _predict_sales(self, prediction_period: int = 3) -> Dict[str, Any]:
        """
        Predict sales for the next few months based on historical data.

        Args:
            prediction_period: Number of months to predict

        Returns:
            Sales prediction insights
        """
        # Get sales data for the past year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        historical_sales = self._sales_repo.get_by_date_range(start_date, end_date)

        # Group sales by month
        monthly_sales = defaultdict(list)
        for sale in historical_sales:
            month_key = sale.created_at.strftime('%Y-%m')
            monthly_sales[month_key].append(sale.total_amount)

        # Calculate monthly averages and standard deviation
        monthly_predictions = []
        for i in range(1, prediction_period + 1):
            # Predict next month based on historical data
            target_month = (end_date + timedelta(days=30 * i)).strftime('%Y-%m')

            # Simple forecasting using average and standard deviation
            if monthly_sales:
                months_data = [sum(sales) for sales in monthly_sales.values()]
                avg_monthly_sales = np.mean(months_data)
                std_monthly_sales = np.std(months_data) if len(months_data) > 1 else 0

                # Prediction with some randomness to account for variability
                prediction = avg_monthly_sales + np.random.normal(0, std_monthly_sales / 2)

                monthly_predictions.append({
                    'month': target_month,
                    'predicted_sales': max(0, prediction),  # Ensure non-negative
                    'confidence_interval': std_monthly_sales
                })
            else:
                monthly_predictions.append({
                    'month': target_month,
                    'predicted_sales': 0,
                    'confidence_interval': 0
                })

        return {
            'monthly_predictions': monthly_predictions,
            'overall_trend': self._calculate_sales_trend(monthly_sales)
        }

    def _predict_inventory_needs(self) -> Dict[str, Any]:
        """
        Predict inventory needs based on historical usage and sales.

        Returns:
            Inventory prediction insights
        """
        # Get material usage over the past year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Analyze material usage
        material_usage = self._material_repo.get_material_usage(start_date, end_date)

        # Predict future inventory needs
        inventory_predictions = {}
        for material, usage_data in material_usage.items():
            # Calculate average monthly usage
            avg_monthly_usage = usage_data.get('total_used', 0) / 12

            # Predict inventory needs for next 3 months
            predicted_needs = avg_monthly_usage * 3

            # Check current inventory levels
            current_inventory = self._inventory_repo.get_material_quantity(material.id)

            inventory_predictions[material.name] = {
                'current_inventory': current_inventory,
                'predicted_usage': predicted_needs,
                'reorder_suggestion': max(0, predicted_needs - current_inventory)
            }

        return {
            'inventory_predictions': inventory_predictions,
            'prediction_date': datetime.now()
        }

    def _predict_customer_trends(self) -> Dict[str, Any]:
        """
        Predict customer behavior and trends.

        Returns:
            Customer trend prediction insights
        """
        # Analyze customer purchase history
        customers = self._customer_repo.get_all()

        customer_predictions = {
            'churn_risk': [],
            'potential_upsell': [],
            'customer_segments': defaultdict(list)
        }

        for customer in customers:
            # Get customer sales history
            sales = self._sales_repo.get_by_customer_id(customer.id)

            if not sales:
                continue

            # Calculate purchase frequency and recency
            sorted_sales = sorted(sales, key=lambda x: x.created_at)
            last_purchase = sorted_sales[-1].created_at
            days_since_last_purchase = (datetime.now() - last_purchase).days

            # Purchase frequency calculation
            purchase_intervals = []
            for i in range(1, len(sorted_sales)):
                purchase_intervals.append((sorted_sales[i].created_at - sorted_sales[i - 1].created_at).days)

            avg_purchase_interval = (
                np.mean(purchase_intervals)
                if purchase_intervals else 0
            )

            # Churn risk assessment
            if days_since_last_purchase > avg_purchase_interval * 2:
                customer_predictions['churn_risk'].append({
                    'customer_id': customer.id,
                    'name': customer.name,
                    'days_since_last_purchase': days_since_last_purchase,
                    'avg_purchase_interval': avg_purchase_interval
                })

            # Potential upsell assessment
            total_sales = sum(sale.total_amount for sale in sales)
            if total_sales > self._calculate_sales_percentile(customers, 75):
                customer_predictions['potential_upsell'].append({
                    'customer_id': customer.id,
                    'name': customer.name,
                    'total_sales': total_sales
                })

            # Customer segmentation
            if customer.tier:
                customer_predictions['customer_segments'][customer.tier.name].append(customer.id)

        return customer_predictions

    def _calculate_sales_percentile(self, customers, percentile: int = 75) -> float:
        """
        Calculate sales percentile across customers.

        Args:
            customers: List of customers
            percentile: Percentile to calculate

        Returns:
            Sales value at specified percentile
        """
        # Get total sales for each customer
        customer_sales = []
        for customer in customers:
            sales = self._sales_repo.get_by_customer_id(customer.id)
            total_sales = sum(sale.total_amount for sale in sales)
            customer_sales.append(total_sales)

        # Calculate percentile
        if not customer_sales:
            return 0

        try:
            return np.percentile(customer_sales, percentile)
        except Exception as e:
            self._logger.warning(f"Error calculating sales percentile: {e}")
            return 0

    def generate_comprehensive_seasonal_report(
            self,
            year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive seasonal report combining multiple analytics.

        Args:
            year: Optional year for analysis (defaults to current year)

        Returns:
            Comprehensive seasonal business insights
        """
        if not year:
            year = datetime.now().year

        try:
            # Collect various seasonal analyses
            seasonal_report = {
                'year': year,
                'product_performance': self.analyze_seasonal_product_performance(year),
                'material_trends': self.analyze_material_seasonal_trends(year),
                'hardware_trends': self.analyze_hardware_seasonal_trends(year),
                'predictive_insights': self.generate_predictive_insights()
            }

            # Additional insights compilation
            seasonal_report['key_insights'] = self._compile_seasonal_key_insights(seasonal_report)

            return seasonal_report
        except Exception as e:
            self._logger.error(f"Error generating comprehensive seasonal report: {e}")
            raise ValidationError(f"Could not generate comprehensive seasonal report: {e}")

    def _compile_seasonal_key_insights(self, seasonal_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile key insights from the comprehensive seasonal report.

        Args:
            seasonal_report: Comprehensive seasonal report data

        Returns:
            Key business insights
        """
        try:
            key_insights = {
                'top_performing_season': None,
                'most_used_material': None,
                'most_popular_hardware': None,
                'revenue_forecast': None,
                'inventory_recommendations': []
            }

            # Identify top performing season
            if 'product_performance' in seasonal_report:
                seasonal_perf = seasonal_report['product_performance']['seasonal_performance']
                top_season = max(
                    seasonal_perf.keys(),
                    key=lambda s: seasonal_perf[s]['total_revenue']
                )
                key_insights['top_performing_season'] = {
                    'name': top_season,
                    'total_revenue': seasonal_perf[top_season]['total_revenue']
                }

            # Most used material
            if 'material_trends' in seasonal_report:
                material_usage = seasonal_report['material_trends']['seasonal_material_usage']
                total_material_usage = defaultdict(float)

                for season, season_data in material_usage.items():
                    for material, usage in season_data.get('material_variations', {}).items():
                        total_material_usage[material] += usage['total_quantity']

                most_used_material = max(
                    total_material_usage.items(),
                    key=lambda x: x[1]
                )[0]
                key_insights['most_used_material'] = {
                    'name': most_used_material,
                    'total_quantity': total_material_usage[most_used_material]
                }

            # Most popular hardware
            if 'hardware_trends' in seasonal_report:
                hardware_usage = seasonal_report['hardware_trends']['seasonal_hardware_usage']
                total_hardware_usage = defaultdict(float)

                for season, season_data in hardware_usage.items():
                    for hardware, usage in season_data.get('top_hardware_types', {}).items():
                        total_hardware_usage[hardware] += usage['total_quantity']

                most_popular_hardware = max(
                    total_hardware_usage.items(),
                    key=lambda x: x[1]
                )[0]
                key_insights['most_popular_hardware'] = {
                    'name': most_popular_hardware,
                    'total_quantity': total_hardware_usage[most_popular_hardware]
                }

            # Revenue forecast
            if 'predictive_insights' in seasonal_report:
                sales_forecast = seasonal_report['predictive_insights']['sales_forecast']
                key_insights['revenue_forecast'] = sales_forecast['monthly_predictions']

            # Inventory recommendations
            if 'predictive_insights' in seasonal_report:
                inventory_predictions = seasonal_report['predictive_insights']['inventory_forecast'][
                    'inventory_predictions']
                key_insights['inventory_recommendations'] = [
                    {
                        'material': material,
                        'current_inventory': data['current_inventory'],
                        'predicted_usage': data['predicted_usage'],
                        'reorder_suggestion': data['reorder_suggestion']
                    }
                    for material, data in inventory_predictions.items()
                    if data['reorder_suggestion'] > 0
                ]

            return key_insights
        except Exception as e:
            self._logger.warning(f"Error compiling seasonal key insights: {e}")
            return {}

    # Optional: Factory function for creating the analytics service
    def create_analytics_service(
            session,
            customer_repo,
            sales_repo,
            project_repo,
            inventory_repo,
            material_repo,
            pattern_repo,
            product_repo,
            hardware_repo
    ) -> AnalyticsService:
        """
        Factory function to create an instance of AnalyticsService.

        Helps with dependency injection and service creation.

        Args:
            All repository dependencies for the analytics service

        Returns:
            Configured AnalyticsService instance
        """
        return AnalyticsService(
            session=session,
            customer_repository=customer_repo,
            sales_repository=sales_repo,
            project_repository=project_repo,
            inventory_repository=inventory_repo,
            material_repository=material_repo,
            pattern_repository=pattern_repo,
            product_repository=product_repo,
            hardware_repository=hardware_repo
        )