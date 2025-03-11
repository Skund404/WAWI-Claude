# services/implementations/project_metrics_service.py
"""
Implementation of project metrics service.

This module provides analytics functionality for project metrics including
efficiency analysis, bottleneck identification, and resource utilization.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import sqlalchemy as sa
from di.inject import inject
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import func

from database.models.customer import Customer
from database.models.enums import ProjectStatus, ProjectType
from database.models.project import Project
from database.models.project_component import ProjectComponent
from database.models.project_status_history import ProjectStatusHistory
from database.models.sales import Sales
from database.repositories.component_repository import ComponentRepository
from database.repositories.customer_repository import CustomerRepository
from database.repositories.project_repository import ProjectRepository
from database.repositories.sales_repository import SalesRepository
from services.base_service import BaseService
from services.dto.analytics_dto import ProjectMetricsDTO, ProjectPhaseMetricsDTO
from services.exceptions import NotFoundError, ValidationError


@inject
class ProjectMetricsService(BaseService):
    """Service for analyzing project metrics data."""

    def __init__(
            self,
            session: Session,
            project_repository: Optional[ProjectRepository] = None,
            component_repository: Optional[ComponentRepository] = None,
            customer_repository: Optional[CustomerRepository] = None,
            sales_repository: Optional[SalesRepository] = None
    ):
        """
        Initialize the project metrics service.

        Args:
            session: SQLAlchemy database session
            project_repository: Repository for project data access
            component_repository: Repository for component data access
            customer_repository: Repository for customer data access
            sales_repository: Repository for sales data access
        """
        super().__init__(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.customer_repository = customer_repository or CustomerRepository(session)
        self.sales_repository = sales_repository or SalesRepository(session)
        self.logger = logging.getLogger(__name__)

        # Project phase definitions (could come from configuration)
        self.project_phases = [
            {"name": "Design", "statuses": ["INITIAL_CONSULTATION", "DESIGN_PHASE", "PATTERN_DEVELOPMENT"]},
            {"name": "Planning", "statuses": ["CLIENT_APPROVAL", "MATERIAL_SELECTION", "MATERIAL_PURCHASED"]},
            {"name": "Production", "statuses": ["CUTTING", "SKIVING", "PREPARATION", "ASSEMBLY", "STITCHING"]},
            {"name": "Finishing", "statuses": ["EDGE_FINISHING", "HARDWARE_INSTALLATION", "CONDITIONING"]},
            {"name": "Delivery", "statuses": ["QUALITY_CHECK", "FINAL_TOUCHES", "PHOTOGRAPHY", "PACKAGING"]}
        ]

    def get_project_metrics(self, project_id: int) -> ProjectMetricsDTO:
        """
        Get comprehensive metrics for a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            ProjectMetricsDTO with metrics data
        """
        # Check if project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get basic project metrics
        if not hasattr(project, 'start_date') or not project.start_date:
            # Can't calculate metrics without start date
            return ProjectMetricsDTO(
                project_id=project_id,
                project_name=project.name,
                start_date=datetime.now(),
                planned_duration_days=0.0,
                completion_percentage=0.0,
                phase_metrics=[]
            )

        # Get project dates
        start_date = project.start_date
        end_date = project.end_date
        current_date = datetime.now()

        # Calculate duration
        planned_duration = timedelta(days=30)  # Default 30 days if not specified
        if hasattr(project, 'planned_duration_days') and project.planned_duration_days:
            planned_duration = timedelta(days=project.planned_duration_days)
        elif hasattr(project, 'planned_end_date') and project.planned_end_date:
            planned_duration = project.planned_end_date - start_date

        planned_duration_days = planned_duration.days
        actual_duration_days = None

        if end_date:
            actual_duration_days = (end_date - start_date).days

        # Calculate completion percentage
        completion_percentage = 0.0

        if end_date:
            # Project is completed
            completion_percentage = 100.0
        elif hasattr(project, 'completion_percentage') and project.completion_percentage is not None:
            # If project has a completion_percentage attribute, use it
            completion_percentage = project.completion_percentage
        elif hasattr(project, 'status') and project.status:
            # Estimate completion percentage based on status
            status_completion = self._get_status_completion_percentage(project.status.value)
            completion_percentage = status_completion

        # Check if project is on time
        on_time_completion = None

        if end_date:
            planned_end_date = start_date + planned_duration
            on_time_completion = end_date <= planned_end_date

        # Get project status history
        status_history = self._get_project_status_history(project_id)

        # Calculate phase metrics
        phase_metrics = self._calculate_phase_metrics(project, status_history)

        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score(
            project,
            actual_duration_days,
            planned_duration_days,
            phase_metrics
        )

        # Calculate resource utilization
        resource_utilization = self._calculate_resource_utilization(project_id)

        # Calculate customer satisfaction if available
        customer_satisfaction = None
        if hasattr(project, 'customer_rating') and project.customer_rating:
            customer_satisfaction = project.customer_rating
        elif hasattr(project, 'sales_id') and project.sales_id:
            # Try to get from associated sales
            sales = self.sales_repository.get_by_id(project.sales_id)
            if sales and hasattr(sales, 'customer_satisfaction'):
                customer_satisfaction = sales.customer_satisfaction

        # Check if project is within budget
        within_budget = self._check_within_budget(project)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(project, phase_metrics)

        return ProjectMetricsDTO(
            project_id=project_id,
            project_name=project.name,
            start_date=start_date,
            end_date=end_date,
            planned_duration_days=planned_duration_days,
            actual_duration_days=actual_duration_days,
            completion_percentage=completion_percentage,
            efficiency_score=efficiency_score,
            on_time_completion=on_time_completion,
            within_budget=within_budget,
            resource_utilization=resource_utilization,
            customer_satisfaction=customer_satisfaction,
            phase_metrics=phase_metrics,
            bottlenecks=bottlenecks
        )

    def get_all_projects_metrics(self,
                                 time_period: str = "yearly",
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 project_type: Optional[str] = None,
                                 limit: int = 100,
                                 offset: int = 0
                                 ) -> List[ProjectMetricsDTO]:
        """
        Get metrics for all projects.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period
            project_type: Optional project type to filter by
            limit: Maximum number of projects to return
            offset: Offset for pagination

        Returns:
            List of ProjectMetricsDTO with metrics data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get projects active during the period
        query = self.session.query(Project).filter(
            sa.or_(
                sa.and_(Project.start_date <= end_date, Project.end_date >= start_date),
                sa.and_(Project.start_date <= end_date, Project.end_date.is_(None))
            )
        )

        if project_type:
            query = query.filter(Project.type == project_type)

        # Apply pagination
        query = query.order_by(Project.start_date.desc()).limit(limit).offset(offset)

        projects = query.all()

        # Get metrics for each project
        result = []
        for project in projects:
            try:
                metrics = self.get_project_metrics(project.id)
                result.append(metrics)
            except Exception as e:
                self.logger.error(f"Error calculating metrics for project {project.id}: {str(e)}")
                # Continue with next project

        return result

    def get_efficiency_analysis(self,
                                time_period: str = "yearly",
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                project_type: Optional[str] = None
                                ) -> Dict[str, Any]:
        """
        Get efficiency analysis for projects.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period
            project_type: Optional project type to filter by

        Returns:
            Dictionary with efficiency analysis data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get all projects in the period
        query = self.session.query(Project).filter(
            sa.or_(
                sa.and_(Project.start_date <= end_date, Project.end_date >= start_date),
                sa.and_(Project.start_date <= end_date, Project.end_date.is_(None))
            )
        )

        if project_type:
            query = query.filter(Project.type == project_type)

        projects = query.all()

        if not projects:
            return {
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date,
                "project_count": 0,
                "avg_efficiency_score": 0.0,
                "avg_completion_percentage": 0.0,
                "on_time_completion_rate": 0.0,
                "within_budget_rate": 0.0,
                "avg_duration_deviation": 0.0,
                "efficiency_by_type": [],
                "efficiency_by_phase": [],
                "efficiency_trend": []
            }

        # Calculate metrics for all projects
        efficiency_scores = []
        completion_percentages = []
        on_time_completions = []
        within_budget_counts = []
        duration_deviations = []

        # Track efficiency by project type
        efficiency_by_type = {}

        # Track efficiency by phase
        efficiency_by_phase = {
            "Design": {"score_sum": 0.0, "count": 0},
            "Planning": {"score_sum": 0.0, "count": 0},
            "Production": {"score_sum": 0.0, "count": 0},
            "Finishing": {"score_sum": 0.0, "count": 0},
            "Delivery": {"score_sum": 0.0, "count": 0}
        }

        for project in projects:
            try:
                metrics = self.get_project_metrics(project.id)

                if metrics.efficiency_score is not None:
                    efficiency_scores.append(metrics.efficiency_score)

                completion_percentages.append(metrics.completion_percentage)

                if metrics.on_time_completion is not None:
                    on_time_completions.append(1 if metrics.on_time_completion else 0)

                if metrics.within_budget is not None:
                    within_budget_counts.append(1 if metrics.within_budget else 0)

                if metrics.actual_duration_days and metrics.planned_duration_days:
                    deviation = (
                                            metrics.actual_duration_days - metrics.planned_duration_days) / metrics.planned_duration_days
                    duration_deviations.append(deviation)

                # Track by project type
                project_type_str = project.type.value if hasattr(project, 'type') else "unknown"
                if project_type_str not in efficiency_by_type:
                    efficiency_by_type[project_type_str] = {"score_sum": 0.0, "count": 0}

                if metrics.efficiency_score is not None:
                    efficiency_by_type[project_type_str]["score_sum"] += metrics.efficiency_score
                    efficiency_by_type[project_type_str]["count"] += 1

                # Track by phase
                for phase_metric in metrics.phase_metrics:
                    phase_name = phase_metric.phase_name
                    if phase_name in efficiency_by_phase and phase_metric.efficiency_score is not None:
                        efficiency_by_phase[phase_name]["score_sum"] += phase_metric.efficiency_score
                        efficiency_by_phase[phase_name]["count"] += 1

            except Exception as e:
                self.logger.error(f"Error calculating metrics for project {project.id}: {str(e)}")

        # Calculate averages
        avg_efficiency_score = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0.0
        avg_completion_percentage = sum(completion_percentages) / len(
            completion_percentages) if completion_percentages else 0.0
        on_time_completion_rate = sum(on_time_completions) / len(
            on_time_completions) * 100 if on_time_completions else 0.0
        within_budget_rate = sum(within_budget_counts) / len(
            within_budget_counts) * 100 if within_budget_counts else 0.0
        avg_duration_deviation = sum(duration_deviations) / len(
            duration_deviations) * 100 if duration_deviations else 0.0

        # Calculate efficiency by type
        efficiency_by_type_results = []
        for type_name, data in efficiency_by_type.items():
            if data["count"] > 0:
                avg_score = data["score_sum"] / data["count"]
                efficiency_by_type_results.append({
                    "project_type": type_name,
                    "avg_efficiency_score": avg_score,
                    "project_count": data["count"]
                })

        # Calculate efficiency by phase
        efficiency_by_phase_results = []
        for phase_name, data in efficiency_by_phase.items():
            if data["count"] > 0:
                avg_score = data["score_sum"] / data["count"]
                efficiency_by_phase_results.append({
                    "phase_name": phase_name,
                    "avg_efficiency_score": avg_score,
                    "project_count": data["count"]
                })

        # Calculate efficiency trend
        efficiency_trend = self._calculate_efficiency_trend(
            time_period, start_date, end_date, project_type
        )

        return {
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date,
            "project_count": len(projects),
            "avg_efficiency_score": avg_efficiency_score,
            "avg_completion_percentage": avg_completion_percentage,
            "on_time_completion_rate": on_time_completion_rate,
            "within_budget_rate": within_budget_rate,
            "avg_duration_deviation": avg_duration_deviation,
            "efficiency_by_type": efficiency_by_type_results,
            "efficiency_by_phase": efficiency_by_phase_results,
            "efficiency_trend": efficiency_trend
        }

    def get_bottleneck_analysis(self,
                                project_id: Optional[int] = None,
                                time_period: str = "yearly",
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None
                                ) -> Dict[str, Any]:
        """
        Get bottleneck analysis for projects.

        Args:
            project_id: Optional specific project ID
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            Dictionary with bottleneck analysis data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        if project_id:
            # Get bottlenecks for a specific project
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            metrics = self.get_project_metrics(project_id)
            bottlenecks = metrics.bottlenecks or self._identify_bottlenecks(
                project, metrics.phase_metrics
            )

            return {
                "project_id": project_id,
                "project_name": project.name,
                "bottlenecks": bottlenecks,
                "efficiency_score": metrics.efficiency_score,
                "on_time_completion": metrics.on_time_completion,
                "phase_metrics": [
                    {
                        "phase_name": phase.phase_name,
                        "efficiency_score": phase.efficiency_score,
                        "bottleneck_score": phase.bottleneck_score
                    } for phase in metrics.phase_metrics
                ],
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date
            }

        # Get bottlenecks across all projects in the period
        projects = self.session.query(Project).filter(
            sa.or_(
                sa.and_(Project.start_date <= end_date, Project.end_date >= start_date),
                sa.and_(Project.start_date <= end_date, Project.end_date.is_(None))
            )
        ).all()

        if not projects:
            return {
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date,
                "project_count": 0,
                "bottleneck_phases": [],
                "bottleneck_factors": [],
                "bottleneck_by_project_type": []
            }

        # Track bottlenecks by phase
        bottleneck_phases = {
            "Design": {"count": 0, "score_sum": 0.0},
            "Planning": {"count": 0, "score_sum": 0.0},
            "Production": {"count": 0, "score_sum": 0.0},
            "Finishing": {"count": 0, "score_sum": 0.0},
            "Delivery": {"count": 0, "score_sum": 0.0}
        }

        # Track bottleneck factors
        bottleneck_factors = {
            "Material Availability": 0,
            "Resource Constraints": 0,
            "Technical Complexity": 0,
            "Client Feedback Delay": 0,
            "Quality Issues": 0,
            "Skill Gap": 0,
            "Tool Availability": 0,
            "Process Inefficiency": 0,
            "Other": 0
        }

        # Track bottlenecks by project type
        bottleneck_by_project_type = {}

        # Analyze each project
        for project in projects:
            try:
                metrics = self.get_project_metrics(project.id)
                bottlenecks = metrics.bottlenecks or self._identify_bottlenecks(
                    project, metrics.phase_metrics
                )

                if not bottlenecks:
                    continue

                # Track bottleneck phases
                for bottleneck in bottlenecks:
                    phase = bottleneck.get("phase")
                    if phase in bottleneck_phases:
                        bottleneck_phases[phase]["count"] += 1
                        bottleneck_phases[phase]["score_sum"] += bottleneck.get("impact_score", 0)

                    # Track factors
                    factor = bottleneck.get("factor")
                    if factor in bottleneck_factors:
                        bottleneck_factors[factor] += 1
                    else:
                        bottleneck_factors["Other"] += 1

                # Track by project type
                project_type_str = project.type.value if hasattr(project, 'type') else "unknown"
                if project_type_str not in bottleneck_by_project_type:
                    bottleneck_by_project_type[project_type_str] = {
                        "project_count": 0,
                        "bottleneck_count": 0,
                        "phases": {
                            "Design": 0,
                            "Planning": 0,
                            "Production": 0,
                            "Finishing": 0,
                            "Delivery": 0
                        }
                    }

                bottleneck_by_project_type[project_type_str]["project_count"] += 1
                bottleneck_by_project_type[project_type_str]["bottleneck_count"] += len(bottlenecks)

                for bottleneck in bottlenecks:
                    phase = bottleneck.get("phase")
                    if phase in bottleneck_by_project_type[project_type_str]["phases"]:
                        bottleneck_by_project_type[project_type_str]["phases"][phase] += 1

            except Exception as e:
                self.logger.error(f"Error analyzing bottlenecks for project {project.id}: {str(e)}")

        # Prepare results
        bottleneck_phases_result = []
        for phase, data in bottleneck_phases.items():
            if data["count"] > 0:
                bottleneck_phases_result.append({
                    "phase": phase,
                    "count": data["count"],
                    "avg_impact_score": data["score_sum"] / data["count"],
                    "percentage": data["count"] / len(projects) * 100
                })

        bottleneck_factors_result = []
        for factor, count in bottleneck_factors.items():
            if count > 0:
                bottleneck_factors_result.append({
                    "factor": factor,
                    "count": count,
                    "percentage": count / sum(bottleneck_factors.values()) * 100
                })

        bottleneck_by_project_type_result = []
        for project_type, data in bottleneck_by_project_type.items():
            if data["project_count"] > 0:
                bottleneck_by_project_type_result.append({
                    "project_type": project_type,
                    "project_count": data["project_count"],
                    "bottleneck_count": data["bottleneck_count"],
                    "bottleneck_per_project": data["bottleneck_count"] / data["project_count"],
                    "top_bottleneck_phase": max(data["phases"].items(), key=lambda x: x[1])[0]
                })

        # Sort results
        bottleneck_phases_result.sort(key=lambda x: x["count"], reverse=True)
        bottleneck_factors_result.sort(key=lambda x: x["count"], reverse=True)
        bottleneck_by_project_type_result.sort(key=lambda x: x["bottleneck_per_project"], reverse=True)

        return {
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date,
            "project_count": len(projects),
            "bottleneck_phases": bottleneck_phases_result,
            "bottleneck_factors": bottleneck_factors_result,
            "bottleneck_by_project_type": bottleneck_by_project_type_result
        }

    def get_resource_utilization(self,
                                 time_period: str = "yearly",
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 resource_type: Optional[str] = None
                                 ) -> Dict[str, Any]:
        """
        Get resource utilization metrics.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period
            resource_type: Optional resource type to filter by

        Returns:
            Dictionary with resource utilization data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get projects active during the period
        projects = self.session.query(Project).filter(
            sa.or_(
                sa.and_(Project.start_date <= end_date, Project.end_date >= start_date),
                sa.and_(Project.start_date <= end_date, Project.end_date.is_(None))
            )
        ).all()

        if not projects:
            return {
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date,
                "project_count": 0,
                "avg_resource_utilization": 0.0,
                "resource_utilization_by_type": [],
                "resource_utilization_trend": []
            }

        # Calculate resource utilization for each project
        utilization_scores = []
        utilization_by_resource_type = {
            "Labor": {"score_sum": 0.0, "count": 0},
            "Equipment": {"score_sum": 0.0, "count": 0},
            "Materials": {"score_sum": 0.0, "count": 0},
            "Tools": {"score_sum": 0.0, "count": 0}
        }

        for project in projects:
            try:
                # Calculate resource utilization
                utilization = self._calculate_resource_utilization(project.id)
                if utilization:
                    utilization_scores.append(utilization)

                # Calculate utilization by resource type
                resource_types = ["Labor", "Equipment", "Materials", "Tools"]
                for res_type in resource_types:
                    # In a real implementation, we would have specific resource utilization
                    # calculation for each type. For now, we'll use some placeholder logic.
                    if resource_type and res_type != resource_type:
                        continue

                    # Placeholder: generate a utilization score based on project attributes
                    type_utilization = None

                    if res_type == "Labor":
                        # For labor, calculate based on project duration and estimated effort
                        if hasattr(project, 'estimated_labor_hours') and project.estimated_labor_hours:
                            actual_labor_hours = getattr(project, 'actual_labor_hours',
                                                         project.estimated_labor_hours * 0.9)
                            type_utilization = actual_labor_hours / project.estimated_labor_hours
                        else:
                            # Placeholder value
                            type_utilization = 0.85

                    elif res_type == "Equipment":
                        # For equipment, calculate based on equipment usage records
                        # For now, use a placeholder value
                        type_utilization = 0.75

                    elif res_type == "Materials":
                        # For materials, calculate based on material efficiency
                        # For now, use a placeholder value
                        type_utilization = 0.9

                    elif res_type == "Tools":
                        # For tools, calculate based on tool checkout records
                        # For now, use a placeholder value
                        type_utilization = 0.8

                    if type_utilization:
                        utilization_by_resource_type[res_type]["score_sum"] += type_utilization
                        utilization_by_resource_type[res_type]["count"] += 1

            except Exception as e:
                self.logger.error(f"Error calculating resource utilization for project {project.id}: {str(e)}")

        # Calculate average utilization
        avg_utilization = sum(utilization_scores) / len(utilization_scores) if utilization_scores else 0.0

        # Prepare utilization by resource type
        utilization_by_type_result = []
        for res_type, data in utilization_by_resource_type.items():
            if data["count"] > 0:
                avg_type_utilization = data["score_sum"] / data["count"]
                utilization_by_type_result.append({
                    "resource_type": res_type,
                    "avg_utilization": avg_type_utilization,
                    "project_count": data["count"]
                })

        # Calculate utilization trend
        utilization_trend = self._calculate_resource_utilization_trend(
            time_period, start_date, end_date, resource_type
        )

        return {
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date,
            "project_count": len(projects),
            "avg_resource_utilization": avg_utilization,
            "resource_utilization_by_type": utilization_by_type_result,
            "resource_utilization_trend": utilization_trend
        }

    # Helper methods
    def _get_status_completion_percentage(self, status: str) -> float:
        """
        Get estimated completion percentage based on project status.

        Args:
            status: Project status string

        Returns:
            Estimated completion percentage (0-100)
        """
        # Define completion percentages for each status
        # These values should be calibrated based on actual project data
        status_percentages = {
            # Design phase
            "INITIAL_CONSULTATION": 5.0,
            "DESIGN_PHASE": 10.0,
            "PATTERN_DEVELOPMENT": 20.0,

            # Planning phase
            "CLIENT_APPROVAL": 25.0,
            "MATERIAL_SELECTION": 30.0,
            "MATERIAL_PURCHASED": 35.0,

            # Production phase
            "CUTTING": 40.0,
            "SKIVING": 45.0,
            "PREPARATION": 50.0,
            "ASSEMBLY": 60.0,
            "STITCHING": 70.0,

            # Finishing phase
            "EDGE_FINISHING": 75.0,
            "HARDWARE_INSTALLATION": 80.0,
            "CONDITIONING": 85.0,

            # Delivery phase
            "QUALITY_CHECK": 90.0,
            "FINAL_TOUCHES": 95.0,
            "PHOTOGRAPHY": 98.0,
            "PACKAGING": 99.0,

            # Final statuses
            "COMPLETED": 100.0,
            "ON_HOLD": None,  # Can't determine completion for on-hold projects
            "CANCELLED": None  # Can't determine completion for cancelled projects
        }

        # Legacy status mapping
        legacy_status_percentages = {
            "PLANNED": 5.0,
            "MATERIALS_READY": 35.0,
            "IN_PROGRESS": 50.0
        }

        # Combine mappings
        all_percentages = {**status_percentages, **legacy_status_percentages}

        return all_percentages.get(status, 0.0)

    def _get_project_status_history(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get status history for a project.

        Args:
            project_id: ID of the project

        Returns:
            List of dictionaries with status history data
        """
        # In a real implementation, this would come from a ProjectStatusHistory table
        # For now, we'll generate some dummy data based on the project
        project = self.project_repository.get_by_id(project_id)
        if not project or not hasattr(project, 'start_date') or not project.start_date:
            return []

        # Try to get from database if available
        history_records = self.session.query(ProjectStatusHistory).filter(
            ProjectStatusHistory.project_id == project_id
        ).order_by(ProjectStatusHistory.date).all() if hasattr(ProjectStatusHistory, 'project_id') else []

        if history_records:
            return [
                {
                    "status": record.status.value if hasattr(record.status, 'value') else str(record.status),
                    "date": record.date,
                    "duration_days": None  # Will be calculated below
                } for record in history_records
            ]

        # Generate placeholder data if no real history exists
        history = []
        start_date = project.start_date
        end_date = project.end_date or datetime.now()

        # Determine current status
        current_status = project.status.value if hasattr(project, 'status') else "IN_PROGRESS"

        # Generate history based on project duration and current status
        project_duration = (end_date - start_date).days

        if project_duration <= 0:
            return []

        # Define simplified status sequence
        status_sequence = [
            "INITIAL_CONSULTATION",
            "DESIGN_PHASE",
            "PATTERN_DEVELOPMENT",
            "CLIENT_APPROVAL",
            "MATERIAL_SELECTION",
            "MATERIAL_PURCHASED",
            "CUTTING",
            "ASSEMBLY",
            "STITCHING",
            "EDGE_FINISHING",
            "HARDWARE_INSTALLATION",
            "QUALITY_CHECK",
            "FINAL_TOUCHES",
            "COMPLETED"
        ]

        # Find where in the sequence the current status is
        current_index = status_sequence.index(current_status) if current_status in status_sequence else len(
            status_sequence) - 1

        # Generate history entries
        for i, status in enumerate(status_sequence[:current_index + 1]):
            # Calculate date based on position in sequence
            position_ratio = i / len(status_sequence)
            date = start_date + timedelta(days=project_duration * position_ratio)

            history.append({
                "status": status,
                "date": date,
                "duration_days": None  # Will be calculated below
            })

        # Calculate duration for each status
        for i in range(len(history)):
            if i < len(history) - 1:
                duration = (history[i + 1]["date"] - history[i]["date"]).days
            else:
                duration = (end_date - history[i]["date"]).days
            history[i]["duration_days"] = duration

        return history

    def _calculate_phase_metrics(
            self,
            project: Any,
            status_history: List[Dict[str, Any]]
    ) -> List[ProjectPhaseMetricsDTO]:
        """
        Calculate metrics for each project phase.

        Args:
            project: Project model instance
            status_history: List of status history entries

        Returns:
            List of ProjectPhaseMetricsDTO objects
        """
        if not status_history or not hasattr(project, 'start_date') or not project.start_date:
            return []

        # Group status history by phase
        phase_history = {}

        for phase in self.project_phases:
            phase_history[phase["name"]] = {
                "statuses": [],
                "start_date": None,
                "end_date": None,
                "actual_duration_days": 0,
                "planned_duration_days": 0  # Will be calculated based on average for this type of project
            }

        # Assign status history entries to phases
        for status_entry in status_history:
            status = status_entry["status"]

            for phase in self.project_phases:
                if status in phase["statuses"]:
                    phase_history[phase["name"]]["statuses"].append(status_entry)

                    # Update phase start date
                    if (phase_history[phase["name"]]["start_date"] is None or
                            status_entry["date"] < phase_history[phase["name"]]["start_date"]):
                        phase_history[phase["name"]]["start_date"] = status_entry["date"]

                    # Update phase end date
                    if (phase_history[phase["name"]]["end_date"] is None or
                            status_entry["date"] > phase_history[phase["name"]]["end_date"]):
                        phase_history[phase["name"]]["end_date"] = status_entry["date"]

        # Calculate planned duration for each phase
        # In a real implementation, this would be based on historical data
        # For now, we'll use some default values

        # Get total project planned duration
        if hasattr(project, 'planned_duration_days') and project.planned_duration_days:
            planned_duration = project.planned_duration_days
        elif hasattr(project, 'planned_end_date') and project.planned_end_date:
            planned_duration = (project.planned_end_date - project.start_date).days
        else:
            # Default 30 days if not specified
            planned_duration = 30

        # Allocate planned duration to phases
        phase_allocations = {
            "Design": 0.2,  # 20% of total duration
            "Planning": 0.15,  # 15% of total duration
            "Production": 0.4,  # 40% of total duration
            "Finishing": 0.15,  # 15% of total duration
            "Delivery": 0.1  # 10% of total duration
        }

        for phase_name, allocation in phase_allocations.items():
            phase_history[phase_name]["planned_duration_days"] = planned_duration * allocation

        # Calculate actual durations
        end_date = project.end_date or datetime.now()

        for phase_name, phase_data in phase_history.items():
            if phase_data["start_date"] and phase_data["end_date"]:
                phase_data["actual_duration_days"] = (phase_data["end_date"] - phase_data["start_date"]).days

        # Create metrics for each phase
        result = []
        for phase_name, phase_data in phase_history.items():
            if not phase_data["start_date"]:
                continue

            # Calculate efficiency score
            efficiency_score = 0.0

            if phase_data["actual_duration_days"] > 0 and phase_data["planned_duration_days"] > 0:
                # Higher score if completed faster than planned
                efficiency_ratio = phase_data["planned_duration_days"] / phase_data["actual_duration_days"]
                efficiency_score = min(100, efficiency_ratio * 100)

            # Calculate bottleneck score (higher means more likely to be a bottleneck)
            bottleneck_score = None

            if phase_data["actual_duration_days"] > 0 and phase_data["planned_duration_days"] > 0:
                # Higher score if took longer than planned
                deviation = (phase_data["actual_duration_days"] - phase_data["planned_duration_days"]) / phase_data[
                    "planned_duration_days"]
                bottleneck_score = max(0, min(100, deviation * 100))

            # Calculate resource utilization
            resource_utilization = None

            # In a real implementation, this would be calculated based on resource usage data
            # For now, we'll use a placeholder value
            if phase_name == "Production":
                resource_utilization = 0.9  # Production typically has high resource utilization
            elif phase_name == "Design":
                resource_utilization = 0.7  # Design might have lower resource utilization
            else:
                resource_utilization = 0.8  # Default value

            # Create phase metrics DTO
            phase_metrics = ProjectPhaseMetricsDTO(
                phase_name=phase_name,
                planned_duration_days=phase_data["planned_duration_days"],
                actual_duration_days=phase_data["actual_duration_days"],
                efficiency_score=efficiency_score,
                start_date=phase_data["start_date"],
                end_date=phase_data["end_date"],
                bottleneck_score=bottleneck_score,
                resource_utilization=resource_utilization
            )

            result.append(phase_metrics)

        return result

    def _calculate_efficiency_score(
            self,
            project: Any,
            actual_duration_days: Optional[float],
            planned_duration_days: float,
            phase_metrics: List[ProjectPhaseMetricsDTO]
    ) -> Optional[float]:
        """
        Calculate overall efficiency score for a project.

        Args:
            project: Project model instance
            actual_duration_days: Actual project duration in days
            planned_duration_days: Planned project duration in days
            phase_metrics: List of phase metrics

        Returns:
            Efficiency score (0-100) or None if can't be calculated
        """
        if not actual_duration_days:
            # Project not completed yet, calculate based on phase metrics
            completed_phases = [p for p in phase_metrics if p.end_date is not None]
            if not completed_phases:
                return None

            # Average efficiency of completed phases
            return sum(p.efficiency_score for p in completed_phases) / len(completed_phases)

        # Calculate overall efficiency
        # Time efficiency (40%)
        time_efficiency = min(100,
                              (planned_duration_days / actual_duration_days) * 100) if actual_duration_days > 0 else 0

        # Budget efficiency (30%)
        budget_efficiency = 0.0
        if hasattr(project, 'budget') and project.budget:
            actual_cost = getattr(project, 'actual_cost',
                                  project.budget * 0.9)  # Default to 90% of budget if not specified
            budget_efficiency = min(100, (project.budget / actual_cost) * 100) if actual_cost > 0 else 0
        else:
            budget_efficiency = 80.0  # Default value

        # Resource utilization (30%)
        resource_efficiency = 0.0
        if phase_metrics:
            phases_with_utilization = [p for p in phase_metrics if p.resource_utilization is not None]
            if phases_with_utilization:
                resource_efficiency = sum(p.resource_utilization for p in phases_with_utilization) / len(
                    phases_with_utilization) * 100
            else:
                resource_efficiency = 80.0  # Default value
        else:
            resource_efficiency = 80.0  # Default value

        # Calculate weighted score
        efficiency_score = (time_efficiency * 0.4) + (budget_efficiency * 0.3) + (resource_efficiency * 0.3)

        return efficiency_score

    def _calculate_resource_utilization(self, project_id: int) -> Optional[float]:
        """
        Calculate resource utilization for a project.

        Args:
            project_id: ID of the project

        Returns:
            Resource utilization score (0-1) or None if can't be calculated
        """
        # In a real implementation, this would calculate resource utilization
        # based on actual resource allocation and usage data

        # For now, we'll generate a placeholder value
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None

        # Resource utilization varies by project type
        if hasattr(project, 'type'):
            project_type = project.type.value

            if project_type == "CUSTOM":
                # Custom projects might have lower resource utilization
                return 0.75
            elif project_type == "PRODUCTION":
                # Production projects might have higher resource utilization
                return 0.9
            else:
                # Default value
                return 0.85

        # Default value if project type not available
        return 0.85

    def _check_within_budget(self, project: Any) -> Optional[bool]:
        """
        Check if a project is within budget.

        Args:
            project: Project model instance

        Returns:
            True if within budget, False if over budget, None if can't determine
        """
        if not hasattr(project, 'budget') or not project.budget:
            return None

        # Get actual cost
        if hasattr(project, 'actual_cost') and project.actual_cost is not None:
            return project.actual_cost <= project.budget

        # If actual cost not available, try to estimate
        if hasattr(project, 'estimated_cost') and project.estimated_cost is not None:
            # Assume a small buffer (5%)
            return project.estimated_cost <= project.budget * 1.05

        # Can't determine
        return None

    def _identify_bottlenecks(
            self,
            project: Any,
            phase_metrics: List[ProjectPhaseMetricsDTO]
    ) -> List[Dict[str, Any]]:
        """
        Identify bottlenecks in a project.

        Args:
            project: Project model instance
            phase_metrics: List of phase metrics

        Returns:
            List of dictionaries with bottleneck data
        """
        bottlenecks = []

        # Identify phases with high bottleneck scores
        for phase in phase_metrics:
            if phase.bottleneck_score and phase.bottleneck_score > 50:
                # This phase is a potential bottleneck

                # Determine likely factor based on phase and project attributes
                factor = self._determine_bottleneck_factor(project, phase)

                bottlenecks.append({
                    "phase": phase.phase_name,
                    "bottleneck_score": phase.bottleneck_score,
                    "factor": factor,
                    "impact_score": phase.bottleneck_score * 0.8,  # Slightly reduced impact score
                    "description": f"{phase.phase_name} phase took {phase.actual_duration_days:.1f} days vs. planned {phase.planned_duration_days:.1f} days"
                })

        # Sort by bottleneck score
        bottlenecks.sort(key=lambda x: x["bottleneck_score"], reverse=True)

        return bottlenecks[:3]  # Return top 3 bottlenecks

    def _determine_bottleneck_factor(self, project: Any, phase: ProjectPhaseMetricsDTO) -> str:
        """
        Determine the likely factor for a bottleneck.

        Args:
            project: Project model instance
            phase: Phase metrics

        Returns:
            Bottleneck factor description
        """
        # In a real implementation, this would analyze various project data
        # to determine the most likely bottleneck factor

        # For now, we'll use some heuristics based on the phase
        if phase.phase_name == "Design":
            return "Client Feedback Delay"
        elif phase.phase_name == "Planning":
            return "Material Availability"
        elif phase.phase_name == "Production":
            # For production, it could be various factors
            if hasattr(project, 'complexity') and getattr(project, 'complexity', None) == "HIGH":
                return "Technical Complexity"
            else:
                return "Resource Constraints"
        elif phase.phase_name == "Finishing":
            return "Quality Issues"
        elif phase.phase_name == "Delivery":
            return "Process Inefficiency"
        else:
            return "Other"

    def _calculate_efficiency_trend(
            self,
            time_period: str,
            start_date: datetime,
            end_date: datetime,
            project_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate efficiency trend over time.

        Args:
            time_period: Time period granularity
            start_date: Start date for analysis
            end_date: End date for analysis
            project_type: Optional project type to filter by

        Returns:
            List of dictionaries with efficiency trend data
        """
        # Create periods
        periods = []
        if time_period == "monthly":
            # Weekly periods for monthly analysis
            delta = timedelta(days=7)
            format_str = "Week of %b %d"
        elif time_period == "quarterly":
            # Monthly periods for quarterly analysis
            delta = timedelta(days=30)
            format_str = "%b %Y"
        else:  # yearly
            # Monthly periods for yearly analysis
            delta = timedelta(days=30)
            format_str = "%b %Y"

        current_date = start_date
        while current_date < end_date:
            next_date = min(current_date + delta, end_date)
            periods.append((current_date, next_date))
            current_date = next_date

        # Calculate efficiency for each period
        result = []
        for period_start, period_end in periods:
            # Get projects active during this period
            query = self.session.query(Project).filter(
                sa.or_(
                    sa.and_(Project.start_date <= period_end, Project.end_date >= period_start),
                    sa.and_(Project.start_date <= period_end, Project.end_date.is_(None))
                )
            )

            if project_type:
                query = query.filter(Project.type == project_type)

            period_projects = query.all()

            # Calculate efficiency scores
            efficiency_scores = []
            completion_percentages = []
            on_time_counts = []

            for project in period_projects:
                try:
                    metrics = self.get_project_metrics(project.id)

                    if metrics.efficiency_score is not None:
                        efficiency_scores.append(metrics.efficiency_score)

                    completion_percentages.append(metrics.completion_percentage)

                    if metrics.on_time_completion is not None:
                        on_time_counts.append(1 if metrics.on_time_completion else 0)

                except Exception as e:
                    self.logger.error(f"Error calculating metrics for project {project.id}: {str(e)}")

            # Calculate period averages
            avg_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0.0
            avg_completion = sum(completion_percentages) / len(
                completion_percentages) if completion_percentages else 0.0
            on_time_rate = sum(on_time_counts) / len(on_time_counts) * 100 if on_time_counts else 0.0

            # Format period label
            period_label = period_start.strftime(format_str)

            result.append({
                "period": period_label,
                "start_date": period_start,
                "end_date": period_end,
                "project_count": len(period_projects),
                "avg_efficiency_score": avg_efficiency,
                "avg_completion_percentage": avg_completion,
                "on_time_rate": on_time_rate
            })

        return result

    def _calculate_resource_utilization_trend(
            self,
            time_period: str,
            start_date: datetime,
            end_date: datetime,
            resource_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate resource utilization trend over time.

        Args:
            time_period: Time period granularity
            start_date: Start date for analysis
            end_date: End date for analysis
            resource_type: Optional resource type to filter by

        Returns:
            List of dictionaries with resource utilization trend data
        """
        # Create periods
        periods = []
        if time_period == "monthly":
            # Weekly periods for monthly analysis
            delta = timedelta(days=7)
            format_str = "Week of %b %d"
        elif time_period == "quarterly":
            # Monthly periods for quarterly analysis
            delta = timedelta(days=30)
            format_str = "%b %Y"
        else:  # yearly
            # Monthly periods for yearly analysis
            delta = timedelta(days=30)
            format_str = "%b %Y"

        current_date = start_date
        while current_date < end_date:
            next_date = min(current_date + delta, end_date)
            periods.append((current_date, next_date))
            current_date = next_date

        # Calculate utilization for each period
        result = []
        for period_start, period_end in periods:
            # Get projects active during this period
            projects = self.session.query(Project).filter(
                sa.or_(
                    sa.and_(Project.start_date <= period_end, Project.end_date >= period_start),
                    sa.and_(Project.start_date <= period_end, Project.end_date.is_(None))
                )
            ).all()

            # Calculate resource utilization
            utilization_scores = {}

            if resource_type:
                # Only calculate for the requested resource type
                resource_types = [resource_type]
            else:
                # Calculate for all resource types
                resource_types = ["Labor", "Equipment", "Materials", "Tools"]

            for res_type in resource_types:
                utilization_scores[res_type] = []

                for project in projects:
                    try:
                        # In a real implementation, this would use actual resource utilization data
                        # For now, we'll use placeholder values similar to the single project calculation

                        type_utilization = None

                        if res_type == "Labor":
                            # For labor, calculate based on project duration and estimated effort
                            if hasattr(project, 'estimated_labor_hours') and project.estimated_labor_hours:
                                actual_labor_hours = getattr(project, 'actual_labor_hours',
                                                             project.estimated_labor_hours * 0.9)
                                type_utilization = actual_labor_hours / project.estimated_labor_hours
                            else:
                                # Placeholder value
                                type_utilization = 0.85

                        elif res_type == "Equipment":
                            # For equipment, calculate based on equipment usage records
                            # For now, use a placeholder value
                            type_utilization = 0.75

                        elif res_type == "Materials":
                            # For materials, calculate based on material efficiency
                            # For now, use a placeholder value
                            type_utilization = 0.9

                        elif res_type == "Tools":
                            # For tools, calculate based on tool checkout records
                            # For now, use a placeholder value
                            type_utilization = 0.8

                        if type_utilization:
                            utilization_scores[res_type].append(type_utilization)

                    except Exception as e:
                        self.logger.error(f"Error calculating resource utilization for project {project.id}: {str(e)}")

            # Calculate period averages
            utilization_by_type = {}
            for res_type, scores in utilization_scores.items():
                utilization_by_type[res_type] = sum(scores) / len(scores) if scores else 0.0

            # Calculate overall average
            all_scores = [score for scores in utilization_scores.values() for score in scores]
            avg_utilization = sum(all_scores) / len(all_scores) if all_scores else 0.0

            # Format period label
            period_label = period_start.strftime(format_str)

            result.append({
                "period": period_label,
                "start_date": period_start,
                "end_date": period_end,
                "project_count": len(projects),
                "avg_utilization": avg_utilization,
                "utilization_by_type": utilization_by_type
            })

        return result