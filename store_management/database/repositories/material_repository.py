from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta

from sqlalchemy import (
    and_, or_, func, select, desc,
    distinct
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import (
    Session, joinedload, selectinload,
    contains_eager
)

from database.models.enums import (
    MaterialType,
    InventoryStatus,
    TransactionType,
    QualityGrade,
    SupplierStatus
)
from database.models.material import Material
from database.models.inventory import Inventory
from database.models.supplier import Supplier
from database.models.component import Component
from database.models.component_material import ComponentMaterial
from database.models.project import Project
from database.models.purchase_item import PurchaseItem
from database.models.purchase import Purchase
from database.models.base import ModelValidationError

from database.repositories.base_repository import BaseRepository
from database.exceptions import (
    DatabaseError,
    ModelNotFoundError,
    RepositoryError
)
from services.base_service import ValidationError


class MaterialRepository(BaseRepository[Material]):
    """
    Advanced repository for material data access with comprehensive ERP capabilities.

    Provides sophisticated querying, tracking, and analysis for materials 
    across the leatherworking workflow.
    """

    def __init__(self, session: Session):
        """
        Initialize the Material Repository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Material)
        self.logger = logging.getLogger(self.__class__.__name__)

    def advanced_material_search(
            self,
            search_params: Dict[str, Any]
    ) -> List[Material]:
        """
        Comprehensive material search with multiple filtering options.

        Args:
            search_params: Dictionary of search and filter parameters
                - material_type: Optional[MaterialType]
                - min_quantity: Optional[float]
                - max_quantity: Optional[float]
                - supplier_id: Optional[int]
                - quality_grade: Optional[QualityGrade]
                - inventory_status: Optional[InventoryStatus]
                - used_in_project: Optional[int]
                - used_in_component: Optional[int]

        Returns:
            List of materials matching search criteria
        """
        try:
            query = select(Material)
            conditions = []

            # Material Type Filter
            if material_type := search_params.get('material_type'):
                conditions.append(Material.material_type == material_type)

            # Inventory Quantity Range
            if min_qty := search_params.get('min_quantity'):
                query = query.join(Inventory,
                                   and_(
                                       Inventory.item_id == Material.id,
                                       Inventory.item_type == 'material'
                                   )
                                   )
                conditions.append(Inventory.quantity >= min_qty)

            if max_qty := search_params.get('max_quantity'):
                conditions.append(Inventory.quantity <= max_qty)

            # Supplier Filter
            if supplier_id := search_params.get('supplier_id'):
                conditions.append(Material.supplier_id == supplier_id)

            # Quality Grade Filter
            if quality_grade := search_params.get('quality_grade'):
                conditions.append(Material.quality_grade == quality_grade)

            # Inventory Status Filter
            if status := search_params.get('inventory_status'):
                query = query.join(Inventory,
                                   and_(
                                       Inventory.item_id == Material.id,
                                       Inventory.item_type == 'material'
                                   )
                                   )
                conditions.append(Inventory.status == status)

            # Project Usage Filter
            if project_id := search_params.get('used_in_project'):
                query = query.join(ComponentMaterial).join(Component).join(Project)
                conditions.append(Project.id == project_id)

            # Component Usage Filter
            if component_id := search_params.get('used_in_component'):
                query = query.join(ComponentMaterial)
                conditions.append(ComponentMaterial.component_id == component_id)

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Include inventory and supplier details
            query = query.options(
                joinedload(Material.inventory),
                joinedload(Material.supplier)
            )

            # Execute query
            results = self.session.execute(query).unique().scalars().all()

            self.logger.info(f"Advanced material search returned {len(results)} results")
            return results

        except SQLAlchemyError as e:
            self.logger.error(f"Advanced material search error: {e}")
            raise RepositoryError(f"Material search failed: {e}")

    def get_low_stock_critical_materials(
            self,
            threshold_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Identify critical low-stock materials based on usage history.

        Args:
            threshold_days: Number of days to analyze past usage

        Returns:
            List of critical low-stock materials with detailed information
        """
        try:
            # Calculate usage in the past threshold period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=threshold_days)

            # Complex query to find materials with low stock relative to recent usage
            query = select(
                Material,
                Inventory,
                func.sum(ComponentMaterial.quantity).label('total_recent_usage')
            ).join(Inventory,
                   and_(
                       Inventory.item_id == Material.id,
                       Inventory.item_type == 'material'
                   )
                   ).outerjoin(ComponentMaterial,
                               and_(
                                   ComponentMaterial.material_id == Material.id,
                                   ComponentMaterial.created_at.between(start_date, end_date)
                               )
                               ).where(
                and_(
                    Material.is_deleted == False,
                    or_(
                        Inventory.status == InventoryStatus.LOW_STOCK,
                        Inventory.quantity <= func.coalesce(func.sum(ComponentMaterial.quantity), 0) * 1.5
                    )
                )
            ).group_by(Material.id, Inventory.id)

            results = self.session.execute(query).all()

            # Process and enrich results
            critical_materials = []
            for material, inventory, recent_usage in results:
                critical_info = {
                    "material_id": material.id,
                    "material_name": material.name,
                    "material_type": material.material_type,
                    "current_quantity": inventory.quantity,
                    "recent_usage": recent_usage or 0,
                    "inventory_status": inventory.status,
                    "supplier_id": material.supplier_id
                }
                critical_materials.append(critical_info)

            self.logger.warning(f"Found {len(critical_materials)} critical low-stock materials")
            return critical_materials

        except SQLAlchemyError as e:
            self.logger.error(f"Error identifying critical low-stock materials: {e}")
            raise RepositoryError(f"Failed to identify critical low-stock materials: {e}")

    def generate_material_utilization_report(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive material utilization report.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            Detailed material utilization report
        """
        try:
            # Default to last 90 days if no dates provided
            start_date = start_date or (datetime.now() - timedelta(days=90))
            end_date = end_date or datetime.now()

            # Aggregate usage across different domains
            usage_query = select(
                Material.id,
                Material.name,
                Material.material_type,
                func.sum(ComponentMaterial.quantity).label('total_component_usage'),
                func.count(distinct(Component.id)).label('unique_components'),
                func.count(distinct(Project.id)).label('unique_projects')
            ).join(ComponentMaterial, isouter=True
                   ).join(Component, isouter=True
                          ).join(Project, isouter=True
                                 ).where(
                and_(
                    Material.is_deleted == False,
                    ComponentMaterial.created_at.between(start_date, end_date)
                )
            ).group_by(Material.id, Material.name, Material.material_type)

            results = self.session.execute(usage_query).all()

            # Prepare comprehensive report
            utilization_report = {
                "report_period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_materials_analyzed": len(results),
                "material_utilization": [],
                "summary": {
                    "total_component_usage": 0,
                    "total_unique_components": 0,
                    "total_unique_projects": 0
                }
            }

            # Process and aggregate results
            for material_id, name, material_type, component_usage, unique_components, unique_projects in results:
                material_data = {
                    "material_id": material_id,
                    "name": name,
                    "material_type": material_type,
                    "total_component_usage": component_usage or 0,
                    "unique_components": unique_components or 0,
                    "unique_projects": unique_projects or 0
                }

                utilization_report["material_utilization"].append(material_data)

                # Update summary
                utilization_report["summary"]["total_component_usage"] += component_usage or 0
                utilization_report["summary"]["total_unique_components"] += unique_components or 0
                utilization_report["summary"]["total_unique_projects"] += unique_projects or 0

            self.logger.info("Generated comprehensive material utilization report")
            return utilization_report

        except SQLAlchemyError as e:
            self.logger.error(f"Error generating material utilization report: {e}")
            raise RepositoryError(f"Failed to generate material utilization report: {e}")

    def forecast_material_needs(
            self,
            look_ahead_days: int = 90
    ) -> Dict[str, Any]:
        """
        Forecast future material needs based on historical usage and current projects.

        Args:
            look_ahead_days: Number of days to forecast

        Returns:
            Forecasted material needs and recommendations
        """
        try:
            # Calculate historical average usage
            end_date = datetime.now()
            historical_start = end_date - timedelta(days=180)  # 6-month historical data

            # Query to calculate average daily usage per material
            usage_query = select(
                Material.id,
                Material.name,
                Material.material_type,
                func.avg(ComponentMaterial.quantity /
                         func.nullif(func.date_part('day', end_date - ComponentMaterial.created_at), 0)
                         ).label('avg_daily_usage')
            ).join(ComponentMaterial
                   ).where(
                ComponentMaterial.created_at.between(historical_start, end_date)
            ).group_by(Material.id, Material.name, Material.material_type)

            usage_results = self.session.execute(usage_query).all()

            # Prepare forecast report
            forecast_report = {
                "forecast_period": {
                    "start_date": end_date,
                    "end_date": end_date + timedelta(days=look_ahead_days)
                },
                "material_forecasts": []
            }

            # Process each material's forecast
            for material_id, name, material_type, avg_daily_usage in usage_results:
                # Get current inventory
                inventory_query = select(Inventory).where(
                    and_(
                        Inventory.item_id == material_id,
                        Inventory.item_type == 'material'
                    )
                )
                current_inventory = self.session.execute(inventory_query).scalar_one_or_none()

                # Forecast calculation
                forecast = {
                    "material_id": material_id,
                    "name": name,
                    "material_type": material_type,
                    "current_inventory": current_inventory.quantity if current_inventory else 0,
                    "avg_daily_usage": avg_daily_usage or 0,
                    "forecasted_usage": (avg_daily_usage or 0) * look_ahead_days,
                    "recommendation": "MONITOR"
                }

                # Determine recommendation
                days_of_stock = (current_inventory.quantity / avg_daily_usage) if avg_daily_usage else float('inf')
                if days_of_stock < look_ahead_days / 2:
                    forecast["recommendation"] = "URGENT_RESTOCK"
                elif days_of_stock < look_ahead_days:
                    forecast["recommendation"] = "CONSIDER_RESTOCK"

                forecast_report["material_forecasts"].append(forecast)

            self.logger.info("Generated material needs forecast")
            return forecast_report

        except SQLAlchemyError as e:
            self.logger.error(f"Error forecasting material needs: {e}")
            raise RepositoryError(f"Failed to forecast material needs: {e}")

    def batch_update_materials(
            self,
            updates: List[Dict[str, Any]]
    ) -> List[Material]:
        """
        Perform batch updates on multiple materials.

        Args:
            updates: List of dictionaries containing material update information
                Each dictionary should have:
                - 'id': Material ID (required)
                - Other material fields to update
                - Optional 'inventory' sub-dictionary for inventory updates

        Returns:
            List of updated material objects

        Raises:
            ModelValidationError: If update data is invalid
            ModelNotFoundError: If any material is not found
        """
        try:
            updated_materials = []

            # Start a transaction
            with self.session.begin():
                for update_data in updates:
                    # Extract material ID and remove from update data
                    material_id = update_data.pop('id', None)
                    if not material_id:
                        raise ModelValidationError("Material ID is required for batch update")

                    # Extract inventory data if present
                    inventory_data = update_data.pop('inventory', {})

                    # Retrieve the existing material
                    material = self.get_by_id(material_id)
                    if not material:
                        raise ModelNotFoundError(f"Material with ID {material_id} not found")

                    # Update material attributes
                    for key, value in update_data.items():
                        setattr(material, key, value)

                    # Update inventory if data provided
                    if material.inventory and inventory_data:
                        for key, value in inventory_data.items():
                            setattr(material.inventory, key, value)

                        # Trigger any inventory-specific validations
                        material.inventory.validate()

                    # Validate the updated material
                    material.validate()

                    updated_materials.append(material)

            # Log the batch update
            self.logger.info(f"Batch updated {len(updated_materials)} materials")
            return updated_materials

        except (ModelValidationError, ModelNotFoundError) as e:
            self.logger.error(f"Validation error in batch material update: {e}")
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in batch material update: {e}")
            self.session.rollback()
            raise RepositoryError(f"Failed to batch update materials: {e}")

    def analyze_material_cost_efficiency(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze material cost efficiency across different usage contexts.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            Comprehensive material cost efficiency report
        """
        try:
            # Default to last 12 months if no dates provided
            end_date = end_date or datetime.now()
            start_date = start_date or (end_date - timedelta(days=365))

            # Aggregate material usage and cost information
            cost_analysis_query = select(
                Material.id,
                Material.name,
                Material.material_type,
                func.sum(PurchaseItem.quantity).label('total_purchased_quantity'),
                func.sum(PurchaseItem.price).label('total_purchase_cost'),
                func.sum(ComponentMaterial.quantity).label('total_used_quantity'),
                func.count(distinct(Project.id)).label('unique_projects')
            ).join(PurchaseItem, isouter=True
            ).join(ComponentMaterial, isouter=True
            ).join(Component, isouter=True
            ).join(Project, isouter=True
            ).where(
                and_(
                    Material.is_deleted == False,
                    or_(
                        PurchaseItem.created_at.between(start_date, end_date),
                        ComponentMaterial.created_at.between(start_date, end_date)
                    )
                )
            ).group_by(Material.id, Material.name, Material.material_type)

            results = self.session.execute(cost_analysis_query).all()

            # Prepare cost efficiency report
            cost_efficiency_report = {
                "analysis_period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "materials": [],
                "summary": {
                    "total_materials_analyzed": 0,
                    "total_purchase_cost": 0,
                    "total_used_quantity": 0
                }
            }

            # Process and analyze results
            for (
                material_id, name, material_type,
                purchased_qty, purchase_cost,
                used_qty, unique_projects
            ) in results:
                # Calculate key metrics
                avg_unit_cost = (purchase_cost / purchased_qty) if purchased_qty else 0
                utilization_ratio = (used_qty / purchased_qty) if purchased_qty else 0

                # Determine efficiency rating
                if utilization_ratio > 0.9:
                    efficiency_rating = "EXCELLENT"
                elif utilization_ratio > 0.7:
                    efficiency_rating = "GOOD"
                elif utilization_ratio > 0.5:
                    efficiency_rating = "AVERAGE"
                elif utilization_ratio > 0.3:
                    efficiency_rating = "POOR"
                else:
                    efficiency_rating = "CRITICAL"

                # Prepare material efficiency data
                material_efficiency = {
                    "material_id": material_id,
                    "name": name,
                    "material_type": material_type,
                    "total_purchased_quantity": purchased_qty or 0,
                    "total_purchase_cost": purchase_cost or 0,
                    "total_used_quantity": used_qty or 0,
                    "unique_projects": unique_projects or 0,
                    "avg_unit_cost": avg_unit_cost,
                    "utilization_ratio": utilization_ratio,
                    "efficiency_rating": efficiency_rating
                }

                cost_efficiency_report["materials"].append(material_efficiency)

                # Update summary
                cost_efficiency_report["summary"]["total_materials_analyzed"] += 1
                cost_efficiency_report["summary"]["total_purchase_cost"] += purchase_cost or 0
                cost_efficiency_report["summary"]["total_used_quantity"] += used_qty or 0

            self.logger.info("Generated material cost efficiency analysis")
            return cost_efficiency_report

        except SQLAlchemyError as e:
            self.logger.error(f"Error analyzing material cost efficiency: {e}")
            raise RepositoryError(f"Failed to analyze material cost efficiency: {e}")

    def get_material_sourcing_recommendations(
        self,
        material_type: Optional[MaterialType] = None
    ) -> Dict[str, Any]:
        """
        Generate material sourcing recommendations based on current inventory and usage.

        Args:
            material_type: Optional filter for specific material type

        Returns:
            Sourcing recommendations report
        """
        try:
            # Base query for low stock and usage analysis
            query = select(
                Material,
                Inventory,
                func.sum(ComponentMaterial.quantity).label('total_usage'),
                func.avg(PurchaseItem.price).label('avg_purchase_price')
            ).join(Inventory,
                and_(
                    Inventory.item_id == Material.id,
                    Inventory.item_type == 'material'
                )
            ).outerjoin(ComponentMaterial,
                ComponentMaterial.material_id == Material.id
            ).outerjoin(PurchaseItem,
                PurchaseItem.material_id == Material.id
            ).where(
                and_(
                    Material.is_deleted == False,
                    Inventory.status.in_([
                        InventoryStatus.LOW_STOCK,
                        InventoryStatus.OUT_OF_STOCK
                    ])
                )
            )

            # Apply material type filter if provided
            if material_type:
                query = query.where(Material.material_type == material_type)

            # Group and prepare results
            query = query.group_by(Material, Inventory)

            results = self.session.execute(query).all()

            # Prepare sourcing recommendations
            sourcing_recommendations = {
                "total_recommendations": 0,
                "recommendations": []
            }

            for material, inventory, total_usage, avg_price in results:
                recommendation = {
                    "material_id": material.id,
                    "name": material.name,
                    "material_type": material.material_type,
                    "current_quantity": inventory.quantity,
                    "inventory_status": inventory.status,
                    "total_usage": total_usage or 0,
                    "avg_purchase_price": avg_price or 0,
                    "recommended_order_quantity": max(
                        (total_usage or 0) * 1.5 - inventory.quantity,
                        0
                    ),
                    "supplier_id": material.supplier_id
                }

                sourcing_recommendations["recommendations"].append(recommendation)
                sourcing_recommendations["total_recommendations"] += 1

            self.logger.info(f"Generated {sourcing_recommendations['total_recommendations']} material sourcing recommendations")
            return sourcing_recommendations

        except SQLAlchemyError as e:
            self.logger.error(f"Error generating material sourcing recommendations: {e}")
            raise RepositoryError(f"Failed to generate material sourcing recommendations: {e}")

    def generate_comprehensive_material_report(
        self,
        report_type: str = 'full',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report covering multiple aspects of materials.

        Args:
            report_type: Type of report ('full', 'inventory', 'usage', 'cost')
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            Comprehensive material report
        """
        try:
            # Set default date range (last 12 months)
            end_date = end_date or datetime.now()
            start_date = start_date or (end_date - timedelta(days=365))

            # Prepare comprehensive report
            comprehensive_report = {
                "report_period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "report_type": report_type
            }

            # Additional report sections based on report type
            if report_type in ['full', 'inventory']:
                comprehensive_report['inventory_analysis'] = self.get_low_stock_critical_materials()

            if report_type in ['full', 'usage']:
                comprehensive_report['utilization_report'] = self.generate_material_utilization_report(
                    start_date, end_date
                )

            if report_type in ['full', 'cost']:
                comprehensive_report['cost_efficiency_analysis'] = self.analyze_material_cost_efficiency(
                    start_date, end_date
                )

            if report_type == 'full':
                comprehensive_report['sourcing_recommendations'] = self.get_material_sourcing_recommendations()
                comprehensive_report['forecast'] = self.forecast_material_needs()

            self.logger.info(f"Generated comprehensive {report_type} material report")
            return comprehensive_report

        except Exception as e:
            self.logger.error(f"Error generating comprehensive material report: {e}")
            raise RepositoryError(f"Failed to generate comprehensive material report: {e}")

    def validate_material_data(
        self,
        material_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Validate material data before creation or update.

        Args:
            material_data: Dictionary of material attributes to validate

        Returns:
            Validated and potentially modified material data
        """
        try:
            # Validate required fields
            required_fields = ['name', 'material_type']
            for field in required_fields:
                if field not in material_data:
                    raise ValidationError(f"Missing required field: {field}")

            # Validate material type
            if material_data['material_type'] not in MaterialType:
                raise ValidationError(f"Invalid material type: {material_data['material_type']}")

            # Additional type-specific validations could be added here
            # For example, specific validations for leather, hardware, etc.

            # Sanitize and validate optional fields
            if 'supplier_id' in material_data:
                # Optionally validate supplier existence
                supplier_query = select(Supplier).where(Supplier.id == material_data['supplier_id'])
                supplier = self.session.execute(supplier_query).scalar_one_or_none()
                if not supplier:
                    raise ValidationError(f"Invalid supplier ID: {material_data['supplier_id']}")

            # Clean up and standardize data
            cleaned_data = {
                k: v for k, v in material_data.items()
                if v is not None and k in [
                    'name', 'description', 'material_type',
                    'supplier_id', 'quality_grade'
                ]
            }

            self.logger.info("Material data validated successfully")
            return cleaned_data

        except (ValidationError, SQLAlchemyError) as e:
            self.logger.error(f"Material data validation error: {e}")
            raise RepositoryError(f"Failed to validate material data: {e}")