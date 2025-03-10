from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, func, select, desc, distinct
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from database.models.enums import (
    LeatherType,
    LeatherFinish,
    MaterialType,
    InventoryStatus,
    QualityGrade,
    TransactionType
)
from database.models.material import Leather, Material
from database.models.inventory import Inventory
from database.models.component import Component
from database.models.component_material import ComponentMaterial
from database.models.project import Project
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem
from database.models.supplier import Supplier

from database.repositories.base_repository import BaseRepository
from database.repositories.material_repository import MaterialRepository
from database.exceptions import (
    DatabaseError,
    ModelNotFoundError,
    RepositoryError,

)


class LeatherRepository(BaseRepository[Leather]):
    """
    Advanced repository for leather material data access with comprehensive ERP capabilities.

    Provides sophisticated querying, tracking, and analysis for leather materials 
    across the leatherworking workflow.
    """

    def __init__(self, session: Session):
        """
        Initialize the Leather Repository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Leather)
        self.logger = logging.getLogger(self.__class__.__name__)

    def find_leather_by_criteria(
            self,
            criteria: Dict[str, Any]
    ) -> List[Leather]:
        """
        Advanced search for leather materials with multiple filtering options.

        Args:
            criteria: Dictionary of search parameters
                - leather_type: Optional[LeatherType]
                - min_thickness: Optional[float]
                - max_thickness: Optional[float]
                - min_area: Optional[float]
                - max_area: Optional[float]
                - finish: Optional[LeatherFinish]
                - quality_grade: Optional[QualityGrade]
                - supplier_id: Optional[int]
                - inventory_status: Optional[InventoryStatus]
                - is_full_hide: Optional[bool]

        Returns:
            List of leather materials matching the criteria
        """
        try:
            query = select(Leather).where(
                Leather.material_type == MaterialType.LEATHER
            )
            conditions = []

            # Leather Type Filter
            if leather_type := criteria.get('leather_type'):
                conditions.append(Leather.leather_type == leather_type)

            # Thickness Range Filter
            if min_thickness := criteria.get('min_thickness'):
                conditions.append(Leather.thickness >= min_thickness)
            if max_thickness := criteria.get('max_thickness'):
                conditions.append(Leather.thickness <= max_thickness)

            # Area Range Filter
            if min_area := criteria.get('min_area'):
                conditions.append(Leather.area >= min_area)
            if max_area := criteria.get('max_area'):
                conditions.append(Leather.area <= max_area)

            # Finish Filter
            if finish := criteria.get('finish'):
                conditions.append(Leather.finish == finish)

            # Quality Grade Filter
            if quality_grade := criteria.get('quality_grade'):
                conditions.append(Leather.quality_grade == quality_grade)

            # Supplier Filter
            if supplier_id := criteria.get('supplier_id'):
                conditions.append(Leather.supplier_id == supplier_id)

            # Full Hide Filter
            if is_full_hide := criteria.get('is_full_hide'):
                conditions.append(Leather.is_full_hide == is_full_hide)

            # Inventory Status Filter
            if inventory_status := criteria.get('inventory_status'):
                query = query.join(
                    Inventory,
                    and_(
                        Inventory.item_id == Leather.id,
                        Inventory.item_type == 'material'
                    )
                )
                conditions.append(Inventory.status == inventory_status)

            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Include inventory and supplier details
            query = query.options(
                joinedload(Leather.inventory),
                joinedload(Leather.supplier)
            )

            # Execute query
            results = self.session.execute(query).unique().scalars().all()

            self.logger.info(f"Advanced leather search returned {len(results)} results")
            return results

        except SQLAlchemyError as e:
            self.logger.error(f"Advanced leather search error: {e}")
            raise RepositoryError(f"Leather search failed: {e}")

    def find_with_sufficient_area(
            self,
            required_area: float,
            filters: Optional[Dict[str, Any]] = None
    ) -> List[Leather]:
        """
        Find leather materials with sufficient area for a specific requirement.

        Args:
            required_area: Minimum area needed
            filters: Optional additional filtering criteria

        Returns:
            List of leather materials with sufficient area
        """
        try:
            query = select(Leather).join(
                Inventory,
                and_(
                    Inventory.item_id == Leather.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Leather.material_type == MaterialType.LEATHER,
                    Inventory.quantity >= required_area
                )
            )

            # Apply additional filters
            if filters:
                if leather_type := filters.get('leather_type'):
                    query = query.where(Leather.leather_type == leather_type)

                if min_thickness := filters.get('min_thickness'):
                    query = query.where(Leather.thickness >= min_thickness)

                if finish := filters.get('finish'):
                    query = query.where(Leather.finish == finish)

            # Include inventory details
            query = query.options(joinedload(Leather.inventory))

            # Execute query
            results = self.session.execute(query).unique().scalars().all()

            self.logger.info(f"Found {len(results)} leather materials with sufficient area")
            return results

        except SQLAlchemyError as e:
            self.logger.error(f"Error finding leather with sufficient area: {e}")
            raise RepositoryError(f"Failed to find leather with sufficient area: {e}")

    def calculate_leather_usage_analytics(
            self,
            leather_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive usage analytics for a specific leather material.

        Args:
            leather_id: ID of the leather material
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis

        Returns:
            Detailed usage analytics dictionary
        """
        try:
            # Set default date range
            end_date = end_date or datetime.now()
            start_date = start_date or (end_date - timedelta(days=365))

            # Retrieve leather
            leather = self.get_by_id(leather_id)

            # Get current inventory
            inventory_query = select(Inventory).where(
                and_(
                    Inventory.item_id == leather_id,
                    Inventory.item_type == 'material'
                )
            )
            current_inventory = self.session.execute(inventory_query).scalar_one_or_none()

            # Analyze component usage
            component_usage_query = select(
                Component.id,
                Component.name,
                func.sum(ComponentMaterial.quantity).label('total_quantity')
            ).join(ComponentMaterial).where(
                and_(
                    ComponentMaterial.material_id == leather_id,
                    ComponentMaterial.created_at.between(start_date, end_date)
                )
            ).group_by(Component.id, Component.name)

            component_usage = self.session.execute(component_usage_query).all()

            # Analyze project usage
            project_usage_query = select(
                Project.id,
                Project.name,
                func.count(distinct(Component.id)).label('component_count')
            ).join(Component).join(ComponentMaterial).where(
                and_(
                    ComponentMaterial.material_id == leather_id,
                    Project.created_at.between(start_date, end_date)
                )
            ).group_by(Project.id, Project.name)

            project_usage = self.session.execute(project_usage_query).all()

            # Prepare analytics
            analytics = {
                "leather_id": leather_id,
                "leather_name": leather.name,
                "leather_type": leather.leather_type,
                "current_inventory": {
                    "quantity": current_inventory.quantity if current_inventory else 0,
                    "status": current_inventory.status if current_inventory else None
                },
                "usage_period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_component_usage": sum(usage[2] for usage in component_usage),
                "unique_components_used": len(component_usage),
                "projects_used_in": len(project_usage),
                "component_usage_details": [
                    {
                        "component_id": usage[0],
                        "component_name": usage[1],
                        "total_quantity": usage[2]
                    } for usage in component_usage
                ],
                "project_usage_details": [
                    {
                        "project_id": proj[0],
                        "project_name": proj[1],
                        "component_count": proj[2]
                    } for proj in project_usage
                ]
            }

            self.logger.info(f"Generated usage analytics for leather {leather_id}")
            return analytics

        except SQLAlchemyError as e:
            self.logger.error(f"Leather usage analytics error: {e}")
            raise RepositoryError(f"Failed to generate leather usage analytics: {e}")

    def get_leather_usage_history(
            self,
            leather_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve usage history for a specific leather material.

        Args:
            leather_id: ID of the leather material
            start_date: Optional start date for history
            end_date: Optional end date for history

        Returns:
            List of usage records detailing leather usage across components and projects
        """
        try:
            # Validate leather existence
            leather = self.get_by_id(leather_id)

            # Prepare query for component material usage
            query = select(
                ComponentMaterial,
                Component,
                Project
            ).join(Component
                   ).outerjoin(Project
                               ).where(
                and_(
                    ComponentMaterial.material_id == leather_id,
                    ComponentMaterial.material_type == MaterialType.LEATHER
                )
            )

            # Apply date range filter
            if start_date:
                query = query.where(ComponentMaterial.created_at >= start_date)
            if end_date:
                query = query.where(ComponentMaterial.created_at <= end_date)

            # Order by date (most recent first)
            query = query.order_by(ComponentMaterial.created_at.desc())

            # Execute query
            results = self.session.execute(query).all()

            # Process usage history
            usage_history = []
            for component_material, component, project in results:
                record = {
                    "quantity_used": component_material.quantity,
                    "created_at": component_material.created_at,
                    "component_id": component.id,
                    "component_name": component.name,
                    "project_id": project.id if project else None,
                    "project_name": project.name if project else None
                }
                usage_history.append(record)

            self.logger.info(f"Retrieved {len(usage_history)} usage records for leather {leather_id}")
            return usage_history

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving leather usage history: {e}")
            raise RepositoryError(f"Failed to retrieve leather usage history: {e}")

    def analyze_leather_efficiency(
            self,
            leather_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze the efficiency of a specific leather material.

        Args:
            leather_id: ID of the leather material
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis

        Returns:
            Comprehensive efficiency analysis of the leather material
        """
        try:
            # Set default date range (last 12 months)
            end_date = end_date or datetime.now()
            start_date = start_date or (end_date - timedelta(days=365))

            # Retrieve leather
            leather = self.get_by_id(leather_id)

            # Get current inventory
            inventory_query = select(Inventory).where(
                and_(
                    Inventory.item_id == leather_id,
                    Inventory.item_type == 'material'
                )
            )
            current_inventory = self.session.execute(inventory_query).scalar_one_or_none()

            # Analyze total usage
            usage_query = select(
                func.sum(ComponentMaterial.quantity).label('total_used_area'),
                func.count(distinct(Component.id)).label('unique_components'),
                func.count(distinct(Project.id)).label('unique_projects')
            ).join(Component
                   ).outerjoin(Project
                               ).where(
                and_(
                    ComponentMaterial.material_id == leather_id,
                    ComponentMaterial.material_type == MaterialType.LEATHER,
                    ComponentMaterial.created_at.between(start_date, end_date)
                )
            )

            usage_result = self.session.execute(usage_query).first()

            # Calculate efficiency metrics
            total_area = leather.area if hasattr(leather, 'area') else 0
            used_area = usage_result.total_used_area or 0

            # Determine efficiency rating
            efficiency_ratio = used_area / total_area if total_area > 0 else 0

            if efficiency_ratio > 0.9:
                efficiency_rating = "EXCELLENT"
            elif efficiency_ratio > 0.7:
                efficiency_rating = "GOOD"
            elif efficiency_ratio > 0.5:
                efficiency_rating = "AVERAGE"
            elif efficiency_ratio > 0.3:
                efficiency_rating = "POOR"
            else:
                efficiency_rating = "CRITICAL"

            # Prepare efficiency analysis
            efficiency_analysis = {
                "leather_id": leather_id,
                "leather_type": leather.leather_type,
                "total_area": total_area,
                "used_area": used_area,
                "remaining_area": total_area - used_area,
                "efficiency_ratio": efficiency_ratio,
                "efficiency_rating": efficiency_rating,
                "unique_components": usage_result.unique_components or 0,
                "unique_projects": usage_result.unique_projects or 0,
                "current_inventory": {
                    "quantity": current_inventory.quantity if current_inventory else 0,
                    "status": current_inventory.status if current_inventory else 0}
            }

            self.logger.info(f"Generated efficiency analysis for leather {leather_id}")
            return efficiency_analysis

        except SQLAlchemyError as e:
            self.logger.error(f"Error analyzing leather efficiency: {e}")
            raise RepositoryError(f"Failed to analyze leather efficiency: {e}")

    def recommend_leather_replacements(
        self,
        leather_id: int,
        required_area: float
    ) -> List[Dict[str, Any]]:
        """
        Recommend alternative leather materials based on specific requirements.

        Args:
            leather_id: ID of the original leather material
            required_area: Area needed for replacement

        Returns:
            List of recommended leather alternatives
        """
        try:
            # Retrieve original leather
            original_leather = self.get_by_id(leather_id)

            # Prepare recommendation query
            query = select(Leather).join(
                Inventory,
                and_(
                    Inventory.item_id == Leather.id,
                    Inventory.item_type == 'material'
                )
            ).where(
                and_(
                    Leather.material_type == MaterialType.LEATHER,
                    Inventory.quantity >= required_area,
                    # Exclude the original leather
                    Leather.id != leather_id
                )
            )

            # Add similarity filters based on original leather characteristics
            conditions = []

            # Similar leather type
            if original_leather.leather_type:
                conditions.append(
                    or_(
                        Leather.leather_type == original_leather.leather_type,
                        # Allow some flexibility with related types
                        Leather.leather_type.in_([
                            LeatherType.FULL_GRAIN if original_leather.leather_type == LeatherType.TOP_GRAIN else None,
                            LeatherType.TOP_GRAIN if original_leather.leather_type == LeatherType.FULL_GRAIN else None
                        ])
                    )
                )

            # Similar thickness range (within 20% tolerance)
            if original_leather.thickness:
                min_thickness = original_leather.thickness * 0.8
                max_thickness = original_leather.thickness * 1.2
                conditions.append(
                    and_(
                        Leather.thickness >= min_thickness,
                        Leather.thickness <= max_thickness
                    )
                )

            # Similar finish if specified
            if original_leather.finish:
                conditions.append(Leather.finish == original_leather.finish)

            # Apply additional conditions
            if conditions:
                query = query.where(and_(*conditions))

            # Order by closest match (inventory quantity close to required area)
            query = query.order_by(
                func.abs(Inventory.quantity - required_area)
            ).options(
                joinedload(Leather.inventory),
                joinedload(Leather.supplier)
            )

            # Limit recommendations
            query = query.limit(5)

            # Execute query
            alternatives = self.session.execute(query).unique().scalars().all()

            # Prepare recommendation details
            recommendations = []
            for leather in alternatives:
                recommendation = {
                    "leather_id": leather.id,
                    "name": leather.name,
                    "leather_type": leather.leather_type,
                    "thickness": leather.thickness,
                    "available_area": leather.inventory.quantity if leather.inventory else 0,
                    "finish": leather.finish,
                    "supplier_id": leather.supplier_id,
                    "supplier_name": leather.supplier.name if leather.supplier else None
                }
                recommendations.append(recommendation)

            self.logger.info(f"Generated {len(recommendations)} leather replacement recommendations")
            return recommendations

        except SQLAlchemyError as e:
            self.logger.error(f"Error recommending leather replacements: {e}")
            raise RepositoryError(f"Failed to recommend leather replacements: {e}")

    def generate_comprehensive_leather_report(
        self,
        leather_id: int,
        report_type: str = 'full'
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a specific leather material.

        Args:
            leather_id: ID of the leather material
            report_type: Type of report to generate ('full', 'usage', 'efficiency')

        Returns:
            Comprehensive leather material report
        """
        try:
            # Retrieve leather details
            leather = self.get_by_id(leather_id)

            # Prepare comprehensive report
            report = {
                "leather_id": leather_id,
                "name": leather.name,
                "material_type": leather.material_type,
                "leather_type": leather.leather_type,
                "report_type": report_type
            }

            # Add report sections based on type
            if report_type in ['full', 'usage']:
                report['usage_analytics'] = self.calculate_leather_usage_analytics(leather_id)
                report['usage_history'] = self.get_leather_usage_history(leather_id)

            if report_type in ['full', 'efficiency']:
                report['efficiency_analysis'] = self.analyze_leather_efficiency(leather_id)

            if report_type == 'full':
                # Additional comprehensive details
                report['inventory_details'] = self._get_leather_inventory_details(leather_id)
                report['supplier_details'] = self._get_leather_supplier_details(leather_id)

            self.logger.info(f"Generated {report_type} report for leather {leather_id}")
            return report

        except SQLAlchemyError as e:
            self.logger.error(f"Error generating comprehensive leather report: {e}")
            raise RepositoryError(f"Failed to generate comprehensive leather report: {e}")

    def _get_leather_inventory_details(self, leather_id: int) -> Dict[str, Any]:
        """
        Helper method to retrieve detailed inventory information.

        Args:
            leather_id: ID of the leather material

        Returns:
            Detailed inventory information
        """
        try:
            inventory_query = select(Inventory).where(
                and_(
                    Inventory.item_id == leather_id,
                    Inventory.item_type == 'material'
                )
            )
            inventory = self.session.execute(inventory_query).scalar_one_or_none()

            if not inventory:
                return {}

            return {
                "quantity": inventory.quantity,
                "status": inventory.status,
                "min_stock_level": inventory.min_stock_level,
                "storage_location": inventory.storage_location
            }

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving leather inventory details: {e}")
            raise RepositoryError(f"Failed to retrieve leather inventory details: {e}")

    def _get_leather_supplier_details(self, leather_id: int) -> Dict[str, Any]:
        """
        Helper method to retrieve detailed supplier information.

        Args:
            leather_id: ID of the leather material

        Returns:
            Detailed supplier information
        """
        try:
            leather_query = select(Leather).where(
                Leather.id == leather_id
            ).options(joinedload(Leather.supplier))

            leather = self.session.execute(leather_query).scalar_one_or_none()

            if not leather or not leather.supplier:
                return {}

            supplier = leather.supplier
            return {
                "supplier_id": supplier.id,
                "name": supplier.name,
                "contact_email": supplier.contact_email,
                "status": supplier.status
            }

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving leather supplier details: {e}")
            raise RepositoryError(f"Failed to retrieve leather supplier details: {e}")