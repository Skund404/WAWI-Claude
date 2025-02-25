# store_management/database/repositories/material_repository.py
"""
SQLAlchemy implementation of the Material Repository.

Provides comprehensive data access and manipulation methods 
for materials with advanced querying capabilities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
import logging

from di.core import inject
from services.interfaces import MaterialService
from models.material import (
    Material,
    MaterialType,
    MaterialQualityGrade
)
from database.repositories.base_repository import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)


class MaterialRepository(BaseRepository[Material]):
    """
    Repository for Material model operations.

    Provides advanced methods for material data management,
    including stock updates, searching, and reporting.
    """

    def __init__(self, session):
        """
        Initialize the Material Repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session, Material)
        self._session = session

    def update_stock(
            self,
            material_id: Any,
            quantity_change: float,
            transaction_type: str,
            notes: Optional[str] = None
    ) -> Material:
        """
        Update the stock of a material.

        Args:
            material_id (Any): ID of the material
            quantity_change (float): Quantity to add or subtract
            transaction_type (str): Type of stock transaction
            notes (Optional[str], optional): Additional notes for the transaction

        Returns:
            Material: Updated material

        Raises:
            ValueError: If stock update would be invalid
        """
        try:
            # Retrieve material
            material = self.get_by_id(material_id)

            # Calculate new stock
            new_stock = material.stock + quantity_change

            # Validate stock level
            if new_stock < 0:
                raise ValueError('Insufficient stock', {
                    'current_stock': material.stock,
                    'quantity_change': quantity_change
                })

            # Update stock
            material.stock = new_stock

            # Commit changes
            self._session.commit()

            logger.info(f'Updated stock for material {material_id}: {quantity_change}')
            return material
        except ValueError:
            self._session.rollback()
            raise
        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error(f'Failed to update material stock: {e}')
            raise

    def get_low_stock_materials(
            self,
            include_zero_stock: bool = False
    ) -> List[Material]:
        """
        Retrieve materials with low stock.

        Args:
            include_zero_stock (bool, optional): Whether to include materials
                with zero stock. Defaults to False.

        Returns:
            List[Material]: List of low stock materials
        """
        try:
            query = self._session.query(Material)

            if include_zero_stock:
                query = query.filter(Material.stock <= Material.minimum_stock)
            else:
                query = query.filter(
                    (Material.stock <= Material.minimum_stock) &
                    (Material.stock > 0)
                )

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Failed to retrieve low stock materials: {e}')
            raise

    def search_materials(self, search_params: Dict[str, Any]) -> List[Material]:
        """
        Search materials based on multiple criteria.

        Args:
            search_params (Dict[str, Any]): Search criteria

        Returns:
            List[Material]: List of matching materials
        """
        try:
            query = self._session.query(Material)

            for key, value in search_params.items():
                if key == 'material_type':
                    query = query.filter(Material.material_type == MaterialType(value))
                elif key == 'quality_grade':
                    query = query.filter(Material.quality_grade == MaterialQualityGrade(value))
                elif key == 'name':
                    query = query.filter(Material.name.ilike(f'%{value}%'))
                else:
                    query = query.filter(getattr(Material, key) == value)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Failed to search materials: {e}')
            raise

    def generate_material_usage_report(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive material usage report.

        Args:
            start_date (Optional[str], optional): Start date for the report
        end_date (Optional[str], optional): End date for the report

        Returns:
            Dict[str, Any]: Material usage report
        """
        try:
            # Retrieve all materials
            materials = self._session.query(Material).all()

            # Initialize report structure
            report = {
                'total_materials': len(materials),
                'low_stock_materials': 0,
                'materials': []
            }

            # Process each material
            for material in materials:
                material_data = {
                    'id': material.id,
                    'name': material.name,
                    'material_type': material.material_type.value,
                    'quality_grade': material.quality_grade.value,
                    'current_stock': material.stock,
                    'minimum_stock': material.minimum_stock,
                    'is_low_stock': material.stock <= material.minimum_stock
                }

                # Count low stock materials
                if material_data['is_low_stock']:
                    report['low_stock_materials'] += 1

                report['materials'].append(material_data)

            return report
        except SQLAlchemyError as e:
            logger.error(f'Failed to generate material usage report: {e}')
            raise

    def validate_material_substitution(
            self,
            original_material_id: Any,
            substitute_material_id: Any
    ) -> bool:
        """
        Check if one material can be substituted for another.

        Args:
            original_material_id (Any): ID of the original material
            substitute_material_id (Any): ID of the potential substitute material

        Returns:
            bool: True if substitution is possible, False otherwise
        """
        try:
            # Retrieve both materials
            original_material = self.get_by_id(original_material_id)
            substitute_material = self.get_by_id(substitute_material_id)

            # Define substitution criteria
            criteria = [
                original_material.material_type == substitute_material.material_type,
                substitute_material.stock > 0,
                substitute_material.quality_grade.value >= original_material.quality_grade.value
            ]

            # Check all criteria
            return all(criteria)
        except SQLAlchemyError as e:
            logger.error(f'Failed to validate material substitution: {e}')
            raise

    def get_material_statistics(self) -> Dict[str, Any]:
        """
        Generate comprehensive material statistics.

        Returns:
            Dict[str, Any]: Detailed material statistics
        """
        try:
            # Total materials
            total_materials = self._session.query(Material).count()

            # Materials by type
            materials_by_type = (
                self._session.query(Material.material_type, func.count(Material.material_type))
                .group_by(Material.material_type)
                .all()
            )

            # Total stock value
            total_stock_value = (
                self._session.query(func.sum(Material.stock * Material.unit_price))
                .scalar() or 0
            )

            # Average stock level
            avg_stock = (
                self._session.query(func.avg(Material.stock))
                .scalar() or 0
            )

            return {
                'total_materials': total_materials,
                'materials_by_type': dict(materials_by_type),
                'total_stock_value': float(total_stock_value),
                'average_stock_level': float(avg_stock)
            }
        except SQLAlchemyError as e:
            logger.error(f'Failed to generate material statistics: {e}')
            raise