# services/implementations/material_usage_analytics_service.py
"""
Implementation of material usage analytics service.

This module provides analytics functionality for material usage data including
consumption patterns, waste analysis, and inventory turnover metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import sqlalchemy as sa
from di.inject import inject
from sqlalchemy.orm import Session, aliased

from database.models.component import Component
from database.models.component_material import ComponentMaterial
from database.models.enums import InventoryStatus, MaterialType, TransactionType
from database.models.inventory import Inventory
from database.models.inventory_transaction import InventoryTransaction
from database.models.material import Material, Leather, Hardware, Supplies
from database.models.picking_list import PickingList
from database.models.picking_list_item import PickingListItem
from database.models.project import Project
from database.models.project_component import ProjectComponent
from database.repositories.component_repository import ComponentRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.project_repository import ProjectRepository
from services.base_service import BaseService
from services.dto.analytics_dto import MaterialUsageAnalyticsDTO, MaterialUsageItemDTO
from services.exceptions import NotFoundError, ValidationError


@inject
class MaterialUsageAnalyticsService(BaseService):
    """Service for analyzing material usage data."""

    def __init__(
            self,
            session: Session,
            inventory_repository: Optional[InventoryRepository] = None,
            material_repository: Optional[MaterialRepository] = None,
            component_repository: Optional[ComponentRepository] = None,
            project_repository: Optional[ProjectRepository] = None
    ):
        """
        Initialize the material usage analytics service.

        Args:
            session: SQLAlchemy database session
            inventory_repository: Repository for inventory data access
            material_repository: Repository for material data access
            component_repository: Repository for component data access
            project_repository: Repository for project data access
        """
        super().__init__(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_material_usage_analytics(self,
                                     time_period: str = "yearly",
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None,
                                     material_type: Optional[str] = None
                                     ) -> MaterialUsageAnalyticsDTO:
        """
        Get material usage analytics.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period
            material_type: Optional material type to filter by

        Returns:
            MaterialUsageAnalyticsDTO with usage data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get material usage data from inventory transactions
        usage_by_material = self._get_material_usage_by_material(
            start_date, end_date, material_type
        )

        # Calculate total materials cost and quantity
        total_materials_cost = sum(item.cost for item in usage_by_material)
        total_quantity_used = sum(item.quantity_used for item in usage_by_material)

        # Calculate average waste percentage
        high_waste_materials = []
        total_waste_pct = 0.0
        waste_count = 0

        for item in usage_by_material:
            if item.waste_percentage:
                total_waste_pct += item.waste_percentage
                waste_count += 1

                # Identify high waste materials (over 10%)
                if item.waste_percentage > 10.0:
                    high_waste_materials.append(item)

        avg_waste_percentage = total_waste_pct / waste_count if waste_count > 0 else None

        # Get usage by project
        usage_by_project = self._get_material_usage_by_project(
            start_date, end_date, material_type
        )

        # Get usage trend
        usage_trend = self._get_material_usage_trend(
            time_period, start_date, end_date, material_type
        )

        # Calculate inventory turnover
        inventory_turnover = self._calculate_inventory_turnover(
            start_date, end_date, material_type
        )

        return MaterialUsageAnalyticsDTO(
            time_period=time_period,
            start_date=start_date,
            end_date=end_date,
            total_materials_cost=total_materials_cost,
            total_quantity_used=total_quantity_used,
            avg_waste_percentage=avg_waste_percentage,
            usage_by_material=usage_by_material,
            usage_by_project=usage_by_project,
            usage_trend=usage_trend,
            inventory_turnover=inventory_turnover,
            high_waste_materials=high_waste_materials
        )

    def get_material_usage_by_project(self,
                                      project_id: int
                                      ) -> Dict[str, Any]:
        """
        Get material usage for a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            Dictionary with material usage data
        """
        # Check if project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get project start and end dates
        if not hasattr(project, 'start_date') or not project.start_date:
            return {
                "project_id": project_id,
                "project_name": project.name,
                "total_materials_cost": 0.0,
                "total_quantity_used": 0.0,
                "materials": []
            }

        start_date = project.start_date
        end_date = project.end_date or datetime.now()

        # Get materials used in this project
        materials_used = []

        # Method 1: Get from project components if available
        if hasattr(project, 'components') and project.components:
            for project_component in project.components:
                component = self.component_repository.get_by_id(project_component.component_id)
                if component and hasattr(component, 'materials') and component.materials:
                    for comp_material in component.materials:
                        material = self.material_repository.get_by_id(comp_material.material_id)
                        if material:
                            quantity = comp_material.quantity * project_component.quantity
                            cost = self._get_material_cost(material.id) * quantity

                            materials_used.append({
                                "material_id": material.id,
                                "material_name": material.name,
                                "material_type": material.material_type.value if hasattr(material,
                                                                                         'material_type') else "unknown",
                                "quantity_used": quantity,
                                "unit": material.unit.value if hasattr(material, 'unit') else "piece",
                                "cost": cost
                            })

        # Method 2: Get from picking lists
        picking_lists = self.session.query(PickingList).filter(
            PickingList.project_id == project_id
        ).all() if hasattr(PickingList, 'project_id') else []

        for picking_list in picking_lists:
            picking_items = self.session.query(PickingListItem).filter(
                PickingListItem.picking_list_id == picking_list.id
            ).all()

            for item in picking_items:
                if item.material_id:
                    material = self.material_repository.get_by_id(item.material_id)
                    if material:
                        cost = self._get_material_cost(material.id) * item.quantity_picked

                        materials_used.append({
                            "material_id": material.id,
                            "material_name": material.name,
                            "material_type": material.material_type.value if hasattr(material,
                                                                                     'material_type') else "unknown",
                            "quantity_used": item.quantity_picked,
                            "unit": material.unit.value if hasattr(material, 'unit') else "piece",
                            "cost": cost
                        })

        # Method 3: Get from inventory transactions
        # This requires inventory transactions to be linked to projects
        transactions = self.session.query(InventoryTransaction).filter(
            InventoryTransaction.project_id == project_id,
            InventoryTransaction.transaction_type == TransactionType.USAGE
        ).all() if hasattr(InventoryTransaction, 'project_id') else []

        for transaction in transactions:
            inventory = self.inventory_repository.get_by_id(transaction.inventory_id)
            if inventory and inventory.item_type == "material":
                material = self.material_repository.get_by_id(inventory.item_id)
                if material:
                    cost = transaction.amount * transaction.quantity

                    materials_used.append({
                        "material_id": material.id,
                        "material_name": material.name,
                        "material_type": material.material_type.value if hasattr(material,
                                                                                 'material_type') else "unknown",
                        "quantity_used": transaction.quantity,
                        "unit": material.unit.value if hasattr(material, 'unit') else "piece",
                        "cost": cost
                    })

        # Combine and consolidate materials used
        consolidated = {}
        for material in materials_used:
            material_id = material["material_id"]
            if material_id in consolidated:
                consolidated[material_id]["quantity_used"] += material["quantity_used"]
                consolidated[material_id]["cost"] += material["cost"]
            else:
                consolidated[material_id] = material

        # Calculate totals
        total_materials_cost = sum(item["cost"] for item in consolidated.values())
        total_quantity_used = sum(item["quantity_used"] for item in consolidated.values())

        # Sort materials by cost
        materials_list = list(consolidated.values())
        materials_list.sort(key=lambda x: x["cost"], reverse=True)

        return {
            "project_id": project_id,
            "project_name": project.name,
            "total_materials_cost": total_materials_cost,
            "total_quantity_used": total_quantity_used,
            "materials": materials_list
        }

    def get_material_usage_trend(self,
                                 material_id: Optional[int] = None,
                                 material_type: Optional[str] = None,
                                 time_period: str = "monthly",
                                 months: int = 12
                                 ) -> List[Dict[str, Any]]:
        """
        Get material usage trend over time.

        Args:
            material_id: Optional specific material ID
            material_type: Optional material type to filter by
            time_period: Analysis period granularity ("monthly", "quarterly", "yearly")
            months: Number of months to include in trend

        Returns:
            List of dictionaries with usage trend data
        """
        # Set date range
        end_date = datetime.now()

        if time_period == "monthly":
            start_date = end_date - timedelta(days=30 * months)
        elif time_period == "quarterly":
            start_date = end_date - timedelta(days=90 * (months // 3))
        else:  # yearly
            start_date = end_date - timedelta(days=365 * (months // 12))

        # If looking at a specific material
        if material_id:
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            return self._get_specific_material_usage_trend(
                material_id, time_period, start_date, end_date
            )

        # Otherwise, get overall usage trend
        return self._get_material_usage_trend(
            time_period, start_date, end_date, material_type
        )

    def get_waste_analysis(self,
                           time_period: str = "yearly",
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           material_type: Optional[str] = None
                           ) -> Dict[str, Any]:
        """
        Get waste analysis for materials.

        Args:
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period
            material_type: Optional material type to filter by

        Returns:
            Dictionary with waste analysis data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get material usage with waste percentages
        usage_by_material = self._get_material_usage_by_material(
            start_date, end_date, material_type
        )

        # Calculate waste metrics
        total_materials_cost = sum(item.cost for item in usage_by_material)
        total_waste_pct = 0.0
        waste_count = 0
        waste_materials = []

        for item in usage_by_material:
            if item.waste_percentage:
                total_waste_pct += item.waste_percentage
                waste_count += 1

                # Add to waste materials list with estimated waste cost
                waste_cost = item.cost * (item.waste_percentage / 100)
                waste_materials.append({
                    "material_id": item.material_id,
                    "material_name": item.material_name,
                    "material_type": item.material_type,
                    "waste_percentage": item.waste_percentage,
                    "waste_cost": waste_cost,
                    "total_cost": item.cost,
                    "quantity_used": item.quantity_used,
                    "unit": item.unit
                })

        avg_waste_percentage = total_waste_pct / waste_count if waste_count > 0 else 0.0

        # Sort waste materials by waste cost
        waste_materials.sort(key=lambda x: x["waste_cost"], reverse=True)

        # Get waste trend
        waste_trend = []
        if time_period == "monthly":
            # For monthly, get weekly trend
            for i in range(4):  # 4 weeks
                week_start = start_date + timedelta(days=i * 7)
                week_end = min(week_start + timedelta(days=7), end_date)

                week_materials = self._get_material_usage_by_material(
                    week_start, week_end, material_type
                )

                week_waste_pct = 0.0
                week_waste_count = 0

                for item in week_materials:
                    if item.waste_percentage:
                        week_waste_pct += item.waste_percentage
                        week_waste_count += 1

                week_avg_waste = week_waste_pct / week_waste_count if week_waste_count > 0 else 0.0

                waste_trend.append({
                    "period": f"Week {i + 1}",
                    "start_date": week_start,
                    "end_date": week_end,
                    "avg_waste_percentage": week_avg_waste
                })
        else:
            # For quarterly or yearly, get monthly trend
            months = 3 if time_period == "quarterly" else 12
            for i in range(months):
                month_start = start_date + timedelta(days=i * 30)
                month_end = min(month_start + timedelta(days=30), end_date)

                month_materials = self._get_material_usage_by_material(
                    month_start, month_end, material_type
                )

                month_waste_pct = 0.0
                month_waste_count = 0

                for item in month_materials:
                    if item.waste_percentage:
                        month_waste_pct += item.waste_percentage
                        month_waste_count += 1

                month_avg_waste = month_waste_pct / month_waste_count if month_waste_count > 0 else 0.0

                waste_trend.append({
                    "period": month_start.strftime("%b %Y"),
                    "start_date": month_start,
                    "end_date": month_end,
                    "avg_waste_percentage": month_avg_waste
                })

        # Get total waste cost
        total_waste_cost = sum(item["waste_cost"] for item in waste_materials)
        waste_cost_percentage = (total_waste_cost / total_materials_cost * 100) if total_materials_cost > 0 else 0.0

        return {
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date,
            "total_materials_cost": total_materials_cost,
            "total_waste_cost": total_waste_cost,
            "waste_cost_percentage": waste_cost_percentage,
            "avg_waste_percentage": avg_waste_percentage,
            "waste_materials": waste_materials[:10],  # Top 10 waste materials
            "waste_trend": waste_trend
        }

    def get_inventory_turnover(self,
                               material_id: Optional[int] = None,
                               material_type: Optional[str] = None,
                               time_period: str = "yearly",
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None
                               ) -> Dict[str, Any]:
        """
        Get inventory turnover metrics.

        Args:
            material_id: Optional specific material ID
            material_type: Optional material type to filter by
            time_period: Analysis period ("monthly", "quarterly", "yearly")
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            Dictionary with inventory turnover data
        """
        # Set default date range if not provided
        end_date = end_date or datetime.now()

        if time_period == "monthly":
            start_date = start_date or (end_date - timedelta(days=30))
        elif time_period == "quarterly":
            start_date = start_date or (end_date - timedelta(days=90))
        else:  # yearly
            start_date = start_date or (end_date - timedelta(days=365))

        # Get turnover ratio
        turnover_ratio = self._calculate_inventory_turnover(
            start_date, end_date, material_type, material_id
        )

        # Get days inventory outstanding (DIO)
        days_in_period = (end_date - start_date).days
        dio = days_in_period / turnover_ratio if turnover_ratio > 0 else 0

        # Get inventory levels
        current_inventory = self._get_current_inventory_levels(material_type, material_id)

        # For a specific material
        if material_id:
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Get usage data
            usage_data = self._get_specific_material_usage_data(
                material_id, start_date, end_date
            )

            # Get inventory transactions
            transactions = self._get_material_inventory_transactions(
                material_id, start_date, end_date
            )

            return {
                "material_id": material_id,
                "material_name": material.name,
                "material_type": material.material_type.value if hasattr(material, 'material_type') else "unknown",
                "turnover_ratio": turnover_ratio,
                "days_inventory_outstanding": dio,
                "current_inventory_level": self._get_material_inventory_level(material_id),
                "current_inventory_value": self._get_material_inventory_value(material_id),
                "usage_data": usage_data,
                "transactions": transactions,
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date
            }

        # For all materials or a material type
        # Get top and bottom turnover materials
        materials_turnover = self._get_materials_turnover(
            start_date, end_date, material_type
        )

        # Sort by turnover ratio
        materials_turnover.sort(key=lambda x: x["turnover_ratio"], reverse=True)

        # Get top and bottom 5
        top_turnover = materials_turnover[:5] if materials_turnover else []
        bottom_turnover = materials_turnover[-5:] if len(materials_turnover) >= 5 else []
        bottom_turnover.reverse()  # Lowest turnover first

        # Calculate average turnover by material type
        turnover_by_type = {}
        for material in materials_turnover:
            mat_type = material["material_type"]
            if mat_type in turnover_by_type:
                turnover_by_type[mat_type]["total_ratio"] += material["turnover_ratio"]
                turnover_by_type[mat_type]["count"] += 1
            else:
                turnover_by_type[mat_type] = {
                    "material_type": mat_type,
                    "total_ratio": material["turnover_ratio"],
                    "count": 1
                }

        # Calculate averages
        avg_turnover_by_type = []
        for mat_type, data in turnover_by_type.items():
            avg_turnover = data["total_ratio"] / data["count"]
            avg_turnover_by_type.append({
                "material_type": mat_type,
                "avg_turnover_ratio": avg_turnover,
                "avg_days_inventory_outstanding": days_in_period / avg_turnover if avg_turnover > 0 else 0
            })

        return {
            "overall_turnover_ratio": turnover_ratio,
            "overall_days_inventory_outstanding": dio,
            "current_inventory_levels": current_inventory,
            "top_turnover_materials": top_turnover,
            "bottom_turnover_materials": bottom_turnover,
            "turnover_by_material_type": avg_turnover_by_type,
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date
        }

    # Helper methods
    def _get_material_usage_by_material(
            self,
            start_date: datetime,
            end_date: datetime,
            material_type: Optional[str] = None
    ) -> List[MaterialUsageItemDTO]:
        """
        Get material usage data grouped by material.

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period
            material_type: Optional material type to filter by

        Returns:
            List of MaterialUsageItemDTO objects
        """
        # Get all materials of the specified type (or all)
        query = self.session.query(Material)
        if material_type:
            query = query.filter(Material.material_type == material_type)

        materials = query.all()

        result = []
        for material in materials:
            # Get usage quantity from inventory transactions
            transactions = self.session.query(InventoryTransaction).join(
                Inventory, InventoryTransaction.inventory_id == Inventory.id
            ).filter(
                Inventory.item_type == "material",
                Inventory.item_id == material.id,
                InventoryTransaction.transaction_type == TransactionType.USAGE,
                InventoryTransaction.created_at.between(start_date, end_date)
            ).all()

            quantity_used = sum(tx.quantity for tx in transactions)

            # If no usage, skip this material
            if quantity_used <= 0:
                continue

            # Get material cost
            cost_per_unit = self._get_material_cost(material.id)
            total_cost = cost_per_unit * quantity_used

            # Estimate waste percentage based on waste transactions
            waste_transactions = self.session.query(InventoryTransaction).join(
                Inventory, InventoryTransaction.inventory_id == Inventory.id
            ).filter(
                Inventory.item_type == "material",
                Inventory.item_id == material.id,
                InventoryTransaction.transaction_type == TransactionType.WASTE,
                InventoryTransaction.created_at.between(start_date, end_date)
            ).all()

            waste_quantity = sum(tx.quantity for tx in waste_transactions)
            waste_percentage = (waste_quantity / quantity_used * 100) if quantity_used > 0 else 0

            # Create DTO
            usage_item = MaterialUsageItemDTO(
                material_id=material.id,
                material_name=material.name,
                material_type=material.material_type.value if hasattr(material, 'material_type') else "unknown",
                quantity_used=quantity_used,
                unit=material.unit.value if hasattr(material, 'unit') else "piece",
                cost=total_cost,
                waste_percentage=waste_percentage if waste_percentage > 0 else None,
                usage_date=max(tx.created_at for tx in transactions) if transactions else None
            )

            result.append(usage_item)

        return result

    def _get_material_usage_by_project(
            self,
            start_date: datetime,
            end_date: datetime,
            material_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get material usage data grouped by project.

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period
            material_type: Optional material type to filter by

        Returns:
            List of dictionaries with project usage data
        """
        # Get all projects active in the period
        projects = self.session.query(Project).filter(
            sa.or_(
                sa.and_(Project.start_date <= end_date, Project.end_date >= start_date),
                sa.and_(Project.start_date <= end_date, Project.end_date.is_(None))
            )
        ).all()

        result = []
        for project in projects:
            # Get project materials data
            project_data = self.get_material_usage_by_project(project.id)

            # If no materials or empty, skip
            if not project_data.get("materials"):
                continue

            # Filter by material type if needed
            if material_type:
                project_data["materials"] = [
                    m for m in project_data["materials"]
                    if m.get("material_type") == material_type
                ]

                # Recalculate totals
                project_data["total_materials_cost"] = sum(m["cost"] for m in project_data["materials"])
                project_data["total_quantity_used"] = sum(m["quantity_used"] for m in project_data["materials"])

                # If no materials left after filtering, skip
                if not project_data["materials"]:
                    continue

            result.append({
                "project_id": project.id,
                "project_name": project.name,
                "project_type": project.type.value if hasattr(project, 'type') else "unknown",
                "status": project.status.value if hasattr(project, 'status') else "unknown",
                "start_date": project.start_date,
                "end_date": project.end_date,
                "total_materials_cost": project_data["total_materials_cost"],
                "material_count": len(project_data["materials"]),
                "top_materials": project_data["materials"][:3]  # Top 3 materials by cost
            })

        # Sort by total materials cost
        result.sort(key=lambda x: x["total_materials_cost"], reverse=True)

        return result

    def _get_material_usage_trend(
            self,
            time_period: str,
            start_date: datetime,
            end_date: datetime,
            material_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get material usage trend over time.

        Args:
            time_period: Time period granularity
            start_date: Start date for analysis
            end_date: End date for analysis
            material_type: Optional material type filter

        Returns:
            List of dictionaries with usage trend data
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

        # Get usage data for each period
        result = []
        for period_start, period_end in periods:
            # Get material usage for this period
            usage_items = self._get_material_usage_by_material(
                period_start, period_end, material_type
            )

            # Calculate totals
            total_cost = sum(item.cost for item in usage_items)
            total_quantity = sum(item.quantity_used for item in usage_items)
            material_count = len(usage_items)

            # Get top 3 materials by cost
            top_materials = sorted(usage_items, key=lambda x: x.cost, reverse=True)[:3]
            top_materials_data = [
                {
                    "material_id": m.material_id,
                    "material_name": m.material_name,
                    "cost": m.cost,
                    "quantity_used": m.quantity_used
                } for m in top_materials
            ]

            # Format period label
            period_label = period_start.strftime(format_str)

            result.append({
                "period": period_label,
                "start_date": period_start,
                "end_date": period_end,
                "total_cost": total_cost,
                "total_quantity": total_quantity,
                "material_count": material_count,
                "top_materials": top_materials_data
            })

        return result

    def _get_specific_material_usage_trend(
            self,
            material_id: int,
            time_period: str,
            start_date: datetime,
            end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get usage trend for a specific material.

        Args:
            material_id: ID of the material
            time_period: Time period granularity
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            List of dictionaries with material usage trend data
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

        # Get material info
        material = self.material_repository.get_by_id(material_id)
        if not material:
            return []

        # Get usage data for each period
        result = []
        for period_start, period_end in periods:
            # Get usage transactions for this period
            transactions = self.session.query(InventoryTransaction).join(
                Inventory, InventoryTransaction.inventory_id == Inventory.id
            ).filter(
                Inventory.item_type == "material",
                Inventory.item_id == material_id,
                InventoryTransaction.transaction_type == TransactionType.USAGE,
                InventoryTransaction.created_at.between(period_start, period_end)
            ).all()

            quantity_used = sum(tx.quantity for tx in transactions)

            # Get waste transactions
            waste_transactions = self.session.query(InventoryTransaction).join(
                Inventory, InventoryTransaction.inventory_id == Inventory.id
            ).filter(
                Inventory.item_type == "material",
                Inventory.item_id == material_id,
                InventoryTransaction.transaction_type == TransactionType.WASTE,
                InventoryTransaction.created_at.between(period_start, period_end)
            ).all()

            waste_quantity = sum(tx.quantity for tx in waste_transactions)
            waste_percentage = (waste_quantity / quantity_used * 100) if quantity_used > 0 else 0

            # Get cost
            cost_per_unit = self._get_material_cost(material_id)
            total_cost = cost_per_unit * quantity_used

            # Format period label
            period_label = period_start.strftime(format_str)

            result.append({
                "period": period_label,
                "start_date": period_start,
                "end_date": period_end,
                "quantity_used": quantity_used,
                "total_cost": total_cost,
                "waste_quantity": waste_quantity,
                "waste_percentage": waste_percentage if waste_percentage > 0 else None
            })

        return result

    def _get_material_cost(self, material_id: int) -> float:
        """
        Get the cost per unit of a material.

        Args:
            material_id: ID of the material

        Returns:
            Cost per unit of the material
        """
        # Get material
        material = self.material_repository.get_by_id(material_id)
        if not material:
            return 0.0

        # Try to get cost from material
        if hasattr(material, 'cost_price') and material.cost_price:
            return material.cost_price

        # If not available, estimate from latest purchase
        inventory = self.session.query(Inventory).filter(
            Inventory.item_type == "material",
            Inventory.item_id == material_id
        ).first()

        if inventory:
            # Get latest purchase transaction
            transaction = self.session.query(InventoryTransaction).filter(
                InventoryTransaction.inventory_id == inventory.id,
                InventoryTransaction.transaction_type == TransactionType.PURCHASE
            ).order_by(InventoryTransaction.created_at.desc()).first()

            if transaction and transaction.quantity > 0:
                return transaction.amount / transaction.quantity

        # Default estimated cost
        return 10.0  # Default placeholder cost

    def _calculate_inventory_turnover(
            self,
            start_date: datetime,
            end_date: datetime,
            material_type: Optional[str] = None,
            material_id: Optional[int] = None
    ) -> float:
        """
        Calculate inventory turnover ratio.

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period
            material_type: Optional material type to filter by
            material_id: Optional specific material ID

        Returns:
            Inventory turnover ratio
        """
        # Get cost of goods sold (COGS)
        cogs = 0.0

        # Get average inventory value
        avg_inventory = 0.0

        if material_id:
            # For a specific material
            # Get usage transactions
            transactions = self.session.query(InventoryTransaction).join(
                Inventory, InventoryTransaction.inventory_id == Inventory.id
            ).filter(
                Inventory.item_type == "material",
                Inventory.item_id == material_id,
                InventoryTransaction.transaction_type == TransactionType.USAGE,
                InventoryTransaction.created_at.between(start_date, end_date)
            ).all()

            quantity_used = sum(tx.quantity for tx in transactions)
            cost_per_unit = self._get_material_cost(material_id)
            cogs = quantity_used * cost_per_unit

            # Get inventory levels at start and end
            start_inventory = self._get_material_inventory_value_at_date(material_id, start_date)
            end_inventory = self._get_material_inventory_value_at_date(material_id, end_date)
            avg_inventory = (start_inventory + end_inventory) / 2
        else:
            # For all materials or material type
            # Get usage data
            usage_items = self._get_material_usage_by_material(
                start_date, end_date, material_type
            )

            cogs = sum(item.cost for item in usage_items)

            # Get average inventory value
            start_inventory = self._get_total_inventory_value_at_date(start_date, material_type)
            end_inventory = self._get_total_inventory_value_at_date(end_date, material_type)
            avg_inventory = (start_inventory + end_inventory) / 2

        # Calculate turnover
        if avg_inventory <= 0:
            return 0.0

        return cogs / avg_inventory

    def _get_material_inventory_level(self, material_id: int) -> float:
        """
        Get current inventory level for a material.

        Args:
            material_id: ID of the material

        Returns:
            Current inventory quantity
        """
        inventory = self.session.query(Inventory).filter(
            Inventory.item_type == "material",
            Inventory.item_id == material_id
        ).first()

        if inventory:
            return inventory.quantity

        return 0.0

    def _get_material_inventory_value(self, material_id: int) -> float:
        """
        Get current inventory value for a material.

        Args:
            material_id: ID of the material

        Returns:
            Current inventory value
        """
        quantity = self._get_material_inventory_level(material_id)
        cost_per_unit = self._get_material_cost(material_id)

        return quantity * cost_per_unit

    def _get_material_inventory_value_at_date(self, material_id: int, date: datetime) -> float:
        """
        Get inventory value for a material at a specific date.

        Args:
            material_id: ID of the material
            date: Date to get inventory value at

        Returns:
            Inventory value at the specified date
        """
        # Get current inventory
        current_quantity = self._get_material_inventory_level(material_id)

        # Get transactions after the date
        transactions = self.session.query(InventoryTransaction).join(
            Inventory, InventoryTransaction.inventory_id == Inventory.id
        ).filter(
            Inventory.item_type == "material",
            Inventory.item_id == material_id,
            InventoryTransaction.created_at > date
        ).all()

        # Calculate quantity at date by reversing transactions
        quantity_at_date = current_quantity

        for tx in transactions:
            if tx.transaction_type == TransactionType.PURCHASE:
                quantity_at_date -= tx.quantity
            elif tx.transaction_type in [TransactionType.USAGE, TransactionType.WASTE]:
                quantity_at_date += tx.quantity

        # Get cost per unit
        cost_per_unit = self._get_material_cost(material_id)

        return max(0, quantity_at_date) * cost_per_unit

    def _get_total_inventory_value_at_date(
            self,
            date: datetime,
            material_type: Optional[str] = None
    ) -> float:
        """
        Get total inventory value for all materials at a specific date.

        Args:
            date: Date to get inventory value at
            material_type: Optional material type to filter by

        Returns:
            Total inventory value at the specified date
        """
        # Get all materials
        query = self.session.query(Material)
        if material_type:
            query = query.filter(Material.material_type == material_type)

        materials = query.all()

        # Sum inventory values
        total_value = 0.0
        for material in materials:
            value = self._get_material_inventory_value_at_date(material.id, date)
            total_value += value

        return total_value

    def _get_current_inventory_levels(
            self,
            material_type: Optional[str] = None,
            material_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get current inventory levels.

        Args:
            material_type: Optional material type to filter by
            material_id: Optional specific material ID

        Returns:
            List of dictionaries with inventory level data
        """
        # Query inventory records
        query = self.session.query(
            Inventory, Material
        ).join(
            Material,
            sa.and_(
                Inventory.item_type == "material",
                Inventory.item_id == Material.id
            )
        )

        if material_type:
            query = query.filter(Material.material_type == material_type)

        if material_id:
            query = query.filter(Material.id == material_id)

        inventory_items = query.all()

        result = []
        for inventory, material in inventory_items:
            cost_per_unit = self._get_material_cost(material.id)
            inventory_value = inventory.quantity * cost_per_unit

            result.append({
                "material_id": material.id,
                "material_name": material.name,
                "material_type": material.material_type.value if hasattr(material, 'material_type') else "unknown",
                "quantity": inventory.quantity,
                "unit": material.unit.value if hasattr(material, 'unit') else "piece",
                "inventory_value": inventory_value,
                "status": inventory.status.value if hasattr(inventory, 'status') else "unknown",
                "location": inventory.storage_location if hasattr(inventory, 'storage_location') else None
            })

        return result

    def _get_specific_material_usage_data(
            self,
            material_id: int,
            start_date: datetime,
            end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get detailed usage data for a specific material.

        Args:
            material_id: ID of the material
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            Dictionary with detailed usage data
        """
        # Get material
        material = self.material_repository.get_by_id(material_id)
        if not material:
            return {}

        # Get usage transactions
        transactions = self.session.query(InventoryTransaction).join(
            Inventory, InventoryTransaction.inventory_id == Inventory.id
        ).filter(
            Inventory.item_type == "material",
            Inventory.item_id == material_id,
            InventoryTransaction.transaction_type == TransactionType.USAGE,
            InventoryTransaction.created_at.between(start_date, end_date)
        ).all()

        quantity_used = sum(tx.quantity for tx in transactions)

        # Get waste transactions
        waste_transactions = self.session.query(InventoryTransaction).join(
            Inventory, InventoryTransaction.inventory_id == Inventory.id
        ).filter(
            Inventory.item_type == "material",
            Inventory.item_id == material_id,
            InventoryTransaction.transaction_type == TransactionType.WASTE,
            InventoryTransaction.created_at.between(start_date, end_date)
        ).all()

        waste_quantity = sum(tx.quantity for tx in waste_transactions)
        waste_percentage = (waste_quantity / quantity_used * 100) if quantity_used > 0 else 0

        # Get components using this material
        components = self.session.query(Component).join(
            ComponentMaterial, Component.id == ComponentMaterial.component_id
        ).filter(
            ComponentMaterial.material_id == material_id
        ).all()

        components_data = [
            {
                "component_id": component.id,
                "component_name": component.name,
                "component_type": component.component_type.value if hasattr(component, 'component_type') else "unknown"
            } for component in components
        ]

        # Get projects using this material
        projects = self.session.query(Project).join(
            ProjectComponent, Project.id == ProjectComponent.project_id
        ).join(
            Component, ProjectComponent.component_id == Component.id
        ).join(
            ComponentMaterial, Component.id == ComponentMaterial.component_id
        ).filter(
            ComponentMaterial.material_id == material_id,
            sa.or_(
                sa.and_(Project.start_date <= end_date, Project.end_date >= start_date),
                sa.and_(Project.start_date <= end_date, Project.end_date.is_(None))
            )
        ).distinct().all()

        projects_data = [
            {
                "project_id": project.id,
                "project_name": project.name,
                "project_type": project.type.value if hasattr(project, 'type') else "unknown",
                "status": project.status.value if hasattr(project, 'status') else "unknown"
            } for project in projects
        ]

        return {
            "quantity_used": quantity_used,
            "cost_per_unit": self._get_material_cost(material_id),
            "total_cost": quantity_used * self._get_material_cost(material_id),
            "waste_quantity": waste_quantity,
            "waste_percentage": waste_percentage if waste_percentage > 0 else None,
            "components_using": components_data,
            "projects_using": projects_data
        }

    def _get_material_inventory_transactions(
            self,
            material_id: int,
            start_date: datetime,
            end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get inventory transactions for a material.

        Args:
            material_id: ID of the material
            start_date: Start date for analysis period
            end_date: End date for analysis period

        Returns:
            List of dictionaries with transaction data
        """
        transactions = self.session.query(InventoryTransaction).join(
            Inventory, InventoryTransaction.inventory_id == Inventory.id
        ).filter(
            Inventory.item_type == "material",
            Inventory.item_id == material_id,
            InventoryTransaction.created_at.between(start_date, end_date)
        ).order_by(InventoryTransaction.created_at).all()

        result = []
        for tx in transactions:
            result.append({
                "transaction_id": tx.id,
                "transaction_type": tx.transaction_type.value,
                "quantity": tx.quantity,
                "amount": tx.amount,
                "date": tx.created_at,
                "reference": tx.reference if hasattr(tx, 'reference') else None,
                "project_id": tx.project_id if hasattr(tx, 'project_id') else None
            })

        return result

    def _get_materials_turnover(
            self,
            start_date: datetime,
            end_date: datetime,
            material_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get turnover data for all materials.

        Args:
            start_date: Start date for analysis period
            end_date: End date for analysis period
            material_type: Optional material type to filter by

        Returns:
            List of dictionaries with turnover data
        """
        # Get all materials
        query = self.session.query(Material)
        if material_type:
            query = query.filter(Material.material_type == material_type)

        materials = query.all()

        result = []
        for material in materials:
            # Get usage data
            usage_transactions = self.session.query(InventoryTransaction).join(
                Inventory, InventoryTransaction.inventory_id == Inventory.id
            ).filter(
                Inventory.item_type == "material",
                Inventory.item_id == material.id,
                InventoryTransaction.transaction_type == TransactionType.USAGE,
                InventoryTransaction.created_at.between(start_date, end_date)
            ).all()

            quantity_used = sum(tx.quantity for tx in usage_transactions)

            # Skip if no usage
            if quantity_used <= 0:
                continue

            # Calculate COGS
            cost_per_unit = self._get_material_cost(material.id)
            cogs = quantity_used * cost_per_unit

            # Get average inventory value
            start_inventory = self._get_material_inventory_value_at_date(material.id, start_date)
            end_inventory = self._get_material_inventory_value_at_date(material.id, end_date)
            avg_inventory = (start_inventory + end_inventory) / 2

            # Calculate turnover
            turnover_ratio = cogs / avg_inventory if avg_inventory > 0 else 0

            # Get days inventory outstanding
            days_in_period = (end_date - start_date).days
            dio = days_in_period / turnover_ratio if turnover_ratio > 0 else 0

            result.append({
                "material_id": material.id,
                "material_name": material.name,
                "material_type": material.material_type.value if hasattr(material, 'material_type') else "unknown",
                "cogs": cogs,
                "avg_inventory_value": avg_inventory,
                "turnover_ratio": turnover_ratio,
                "days_inventory_outstanding": dio,
                "current_inventory_level": self._get_material_inventory_level(material.id),
                "current_inventory_value": self._get_material_inventory_value(material.id)
            })

        return result