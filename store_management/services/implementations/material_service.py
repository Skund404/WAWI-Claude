# Path: services/implementations/material_service.py

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import get_db
from database.models.material import Material, MaterialTransaction, MaterialType, MaterialQualityGrade
from database.models.supplier import Supplier
from services.interfaces.material_service import IMaterialService
from di.service import Service
from utils.exceptions import ResourceNotFoundError, ValidationError


class MaterialService(Service, IMaterialService):
    """
    Implementation of the Material Service.

    Provides methods for managing material-related operations.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the Material Service.

        Args:
            session (Optional[Session]): SQLAlchemy database session
        """
        super().__init__(None)  # Placeholder for dependency container
        self._session = session or get_db()
        self._logger = logging.getLogger(__name__)

    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new material.

        Args:
            material_data (Dict[str, Any]): Data for creating a new material

        Returns:
            Dict[str, Any]: Created material details

        Raises:
            ValidationError: If material data is invalid
            ResourceNotFoundError: If supplier is not found
        """
        try:
            # Validate required fields
            required_fields = ['name', 'material_type', 'unit_price']
            for field in required_fields:
                if field not in material_data:
                    raise ValidationError(f"Missing required field: {field}")

            # Validate material type
            material_type = MaterialType(material_data['material_type'])

            # Optional: Validate supplier if provided
            supplier = None
            if 'supplier_id' in material_data:
                supplier = self._session.query(Supplier).get(material_data['supplier_id'])
                if not supplier:
                    raise ResourceNotFoundError("Supplier", str(material_data['supplier_id']))

            # Create material
            material = Material(
                name=material_data['name'],
                material_type=material_type,
                supplier_id=material_data.get('supplier_id'),
                quality_grade=MaterialQualityGrade(material_data.get('quality_grade', 'STANDARD')),
                unit_price=material_data['unit_price'],
                current_stock=material_data.get('current_stock', 0.0),
                minimum_stock=material_data.get('minimum_stock', 0.0)
            )

            # Add to session and commit
            self._session.add(material)
            self._session.commit()

            return material.to_dict()
        except (SQLAlchemyError, ValueError) as e:
            self._session.rollback()
            self._logger.error(f"Error creating material: {e}")
            raise

    def get_material(self, material_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific material by ID.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            Optional[Dict[str, Any]]: Material details

        Raises:
            ResourceNotFoundError: If material is not found
        """
        try:
            material = self._session.query(Material).get(material_id)
            if not material:
                raise ResourceNotFoundError("Material", str(material_id))

            return material.to_dict(include_transactions=True)
        except SQLAlchemyError as e:
            self._logger.error(f"Error retrieving material {material_id}: {e}")
            raise

    def update_material(self, material_id: int, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing material.

        Args:
            material_id (int): Unique identifier for the material
            material_data (Dict[str, Any]): Updated material information

        Returns:
            Dict[str, Any]: Updated material details

        Raises:
            ResourceNotFoundError: If material is not found
        """
        try:
            material = self._session.query(Material).get(material_id)
            if not material:
                raise ResourceNotFoundError("Material", str(material_id))

            # Update basic material fields
            if 'name' in material_data:
                material.name = material_data['name']

            if 'material_type' in material_data:
                material.material_type = MaterialType(material_data['material_type'])

            if 'quality_grade' in material_data:
                material.quality_grade = MaterialQualityGrade(material_data['quality_grade'])

            if 'unit_price' in material_data:
                material.unit_price = material_data['unit_price']

            if 'minimum_stock' in material_data:
                material.minimum_stock = material_data['minimum_stock']

            if 'is_active' in material_data:
                material.is_active = material_data['is_active']

            # Optional: Update supplier
            if 'supplier_id' in material_data:
                supplier = self._session.query(Supplier).get(material_data['supplier_id'])
                if not supplier:
                    raise ResourceNotFoundError("Supplier", str(material_data['supplier_id']))
                material.supplier_id = material_data['supplier_id']

            # Commit changes
            self._session.commit()

            return material.to_dict()
        except (SQLAlchemyError, ValueError) as e:
            self._session.rollback()
            self._logger.error(f"Error updating material {material_id}: {e}")
            raise

    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            bool: True if deletion was successful

        Raises:
            ResourceNotFoundError: If material is not found
        """
        try:
            material = self._session.query(Material).get(material_id)
            if not material:
                raise ResourceNotFoundError("Material", str(material_id))

            self._session.delete(material)
            self._session.commit()
            return True
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Error deleting material {material_id}: {e}")
            raise

    def update_stock(self, material_id: int, quantity_change: float,
                     transaction_type: str = 'ADJUSTMENT',
                     notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Update the stock of a material.

        Args:
            material_id (int): Unique identifier for the material
            quantity_change (float): Amount to change stock by
            transaction_type (str): Type of stock transaction
            notes (Optional[str]): Additional notes for the transaction

        Returns:
            Dict[str, Any]: Updated material details

        Raises:
            ResourceNotFoundError: If material is not found
            ValueError: If stock update would result in negative stock
        """
        try:
            material = self._session.query(Material).get(material_id)
            if not material:
                raise ResourceNotFoundError("Material", str(material_id))

            # Update stock
            material.update_stock(quantity_change)

            # Create transaction record
            transaction = MaterialTransaction(
                material_id=material_id,
                quantity_change=quantity_change,
                transaction_type=transaction_type,
                notes=notes
            )
            self._session.add(transaction)

            # Commit changes
            self._session.commit()

            return material.to_dict(include_transactions=True)
        except (SQLAlchemyError, ValueError) as e:
            self._session.rollback()
            self._logger.error(f"Error updating stock for material {material_id}: {e}")
            raise

    def get_low_stock_materials(self, include_zero_stock: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve materials with low stock.

        Args:
            include_zero_stock (bool): Whether to include materials with zero stock

        Returns:
            List[Dict[str, Any]]: List of materials with low stock
        """
        try:
            # Build query to find low stock materials
            query = self._session.query(Material)

            if not include_zero_stock:
                query = query.filter(Material.current_stock > 0)

            low_stock_materials = query.filter(
                Material.current_stock <= Material.minimum_stock
            ).all()

            return [material.to_dict() for material in low_stock_materials]
        except SQLAlchemyError as e:
            self._logger.error(f"Error retrieving low stock materials: {e}")
            raise

    def search_materials(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for materials based on various parameters.

        Args:
            search_params (Dict[str, Any]): Search criteria

        Returns:
            List[Dict[str, Any]]: List of matching materials
        """
        try:
            query = self._session.query(Material)

            # Filter by material type
            if 'material_type' in search_params:
                query = query.filter(
                    Material.material_type == MaterialType(search_params['material_type'])
                )

            # Filter by quality grade
            if 'quality_grade' in search_params:
                query = query.filter(
                    Material.quality_grade == MaterialQualityGrade(search_params['quality_grade'])
                )

            # Filter by name (partial match)
            if 'name' in search_params:
                query = query.filter(
                    Material.name.ilike(f"%{search_params['name']}%")
                )

            # Filter by supplier
            if 'supplier_id' in search_params:
                query = query.filter(
                    Material.supplier_id == search_params['supplier_id']
                )

            # Filter by stock range
            if 'min_stock' in search_params:
                query = query.filter(Material.current_stock >= search_params['min_stock'])

            if 'max_stock' in search_params:
                query = query.filter(Material.current_stock <= search_params['max_stock'])

            # Filter by active status
            if 'is_active' in search_params:
                query = query.filter(Material.is_active == search_params['is_active'])

            # Execute query and convert results
            materials = query.all()
            return [material.to_dict() for material in materials]
        except (SQLAlchemyError, ValueError) as e:
            self._logger.error(f"Error searching materials: {e}")
            raise

    def generate_material_usage_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate a comprehensive material usage report.

        Args:
            start_date (datetime): Start of the reporting period
            end_date (datetime): End of the reporting period

        Returns:
            Dict[str, Any]: Detailed material usage report
        """
        try:
            # Retrieve material transactions within the date range
            transactions = (
                self._session.query(MaterialTransaction)
                .filter(
                    MaterialTransaction.transaction_date.between(start_date, end_date)
                )
                .all()
            )

            # Aggregate report metrics
            report = {
                'total_transactions': len(transactions),
                'total_quantity_change': 0.0,
                'transactions_by_type': {},
                'materials_usage': {}
            }

            # Calculate transaction statistics
            for transaction in transactions:
                # Total quantity change
                report['total_quantity_change'] += transaction.quantity_change

                # Transactions by type
                transaction_type = transaction.transaction_type
                report['transactions_by_type'][transaction_type] = (
                    report['transactions_by_type'].get(transaction_type, 0) + 1
                )

                # Material-specific usage
                material_id = transaction.material_id
                if material_id not in report['materials_usage']:
                    report['materials_usage'][material_id] = {
                        'name': transaction.material.name,
                        'total_quantity_change': 0.0,
                        'transactions': []
                    }

                material_usage = report['materials_usage'][material_id]
                material_usage['total_quantity_change'] += transaction.quantity_change
                material_usage['transactions'].append(transaction.to_dict())

            return report
        except SQLAlchemyError as e:
            self._logger.error(f"Error generating material usage report: {e}")
            raise
