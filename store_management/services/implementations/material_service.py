# services/implementations/material_service.py
"""
Implementation of Material Service for the leatherworking store management application.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from services.interfaces.material_service import IMaterialService, MaterialType
from database.models.material import Material
from database.repositories.material_repository import MaterialRepository
from utils.error_handler import ValidationError, NotFoundError


class MaterialServiceImpl(IMaterialService):
    """
    Concrete implementation of the Material Service interface.

    Manages CRUD operations and business logic for materials in the leatherworking store.
    """

    def __init__(self, session: Session):
        """
        Initialize the Material Service with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self.session = session
        self.repository = MaterialRepository(session)
        self.logger = logging.getLogger(__name__)

    def _validate_material_data(self, material_data: Dict[str, Any]) -> None:
        """
        Validate material data before creation or update.

        Args:
            material_data (Dict[str, Any]): Material data to validate

        Raises:
            ValidationError: If material data is invalid
        """
        required_fields = ['name', 'material_type', 'quantity']
        for field in required_fields:
            if field not in material_data or not material_data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Validate material type
        try:
            MaterialType(material_data['material_type'])
        except ValueError:
            raise ValidationError(f"Invalid material type: {material_data['material_type']}")

    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new material entry.

        Args:
            material_data (Dict[str, Any]): Data for the new material

        Returns:
            Dict[str, Any]: Created material data

        Raises:
            ValidationError: If material data is invalid
        """
        try:
            # Validate input data
            self._validate_material_data(material_data)

            # Create material
            material = Material(**material_data)

            # Save to database
            with self.session.begin():
                self.repository.create(material)

            self.logger.info(f"Created material: {material.name}")
            return self._material_to_dict(material)

        except ValidationError as ve:
            self.logger.error(f"Validation error creating material: {ve}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating material: {e}")
            raise ValidationError(f"Could not create material: {str(e)}")

    def get_material(self, material_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a material by its identifier.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            Optional[Dict[str, Any]]: Material data or None if not found

        Raises:
            NotFoundError: If material is not found
        """
        try:
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")
            return self._material_to_dict(material)
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving material {material_id}: {e}")
            raise NotFoundError(f"Could not retrieve material: {str(e)}")

    def update_material(self, material_id: int, material_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing material.

        Args:
            material_id (int): Unique identifier for the material
            material_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Dict[str, Any]]: Updated material data

        Raises:
            ValidationError: If update data is invalid
            NotFoundError: If material is not found
        """
        try:
            # Validate material exists
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Validate update data
            if 'material_type' in material_data:
                MaterialType(material_data['material_type'])

            # Update material
            for key, value in material_data.items():
                setattr(material, key, value)

            # Save updates
            with self.session.begin():
                self.repository.update(material)

            self.logger.info(f"Updated material: {material_id}")
            return self._material_to_dict(material)

        except (ValidationError, NotFoundError) as e:
            self.logger.error(f"Error updating material {material_id}: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating material {material_id}: {e}")
            raise ValidationError(f"Could not update material: {str(e)}")

    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material by its identifier.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If material is not found
        """
        try:
            # Validate material exists
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Delete material
            with self.session.begin():
                self.repository.delete(material)

            self.logger.info(f"Deleted material: {material_id}")
            return True

        except (ValidationError, NotFoundError) as e:
            self.logger.error(f"Error deleting material {material_id}: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting material {material_id}: {e}")
            raise ValidationError(f"Could not delete material: {str(e)}")

    def list_materials(
            self,
            material_type: Optional[MaterialType] = None,
            page: int = 1,
            page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List materials with optional filtering and pagination.

        Args:
            material_type: Optional filter by material type
            page: Page number for pagination
            page_size: Number of items per page

        Returns:
            List of material dictionaries
        """
        try:
            # Build query conditions
            conditions = {}
            if material_type:
                conditions['material_type'] = material_type.value

            # Calculate offset
            offset = (page - 1) * page_size

            # Retrieve materials
            materials = self.repository.list_with_filters(
                conditions,
                limit=page_size,
                offset=offset
            )

            self.logger.info(f"Listed materials: type={material_type}, page={page}")
            return [self._material_to_dict(material) for material in materials]

        except SQLAlchemyError as e:
            self.logger.error(f"Error listing materials: {e}")
            raise ValidationError(f"Could not list materials: {str(e)}")

    def get_low_stock_materials(self, include_zero_stock: bool = True) -> List[Dict[str, Any]]:
        """
        Get materials with low stock levels.

        Args:
            include_zero_stock: Whether to include materials with zero stock

        Returns:
            List of dictionaries representing materials with low stock
        """
        try:
            # Define low stock threshold (e.g., less than 10 units)
            low_stock_threshold = 10

            # Retrieve low stock materials
            conditions = {
                'quantity__lt': low_stock_threshold if not include_zero_stock else None
            }

            low_stock_materials = self.repository.list_with_filters(conditions)

            self.logger.info(f"Retrieved low stock materials. Include zero stock: {include_zero_stock}")
            return [self._material_to_dict(material) for material in low_stock_materials]

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving low stock materials: {e}")
            raise ValidationError(f"Could not retrieve low stock materials: {str(e)}")

    def track_material_usage(self, material_id: int, quantity_used: float) -> bool:
        """
        Track usage of a material.

        Args:
            material_id: ID of the material used
            quantity_used: Quantity of material used

        Returns:
            True if the usage was tracked successfully, False otherwise

        Raises:
            NotFoundError: If material is not found
            ValidationError: If usage tracking fails
        """
        try:
            # Retrieve the material
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Validate quantity used
            if quantity_used < 0:
                raise ValidationError("Quantity used must be a non-negative number")

            # Update material quantity
            if material.quantity < quantity_used:
                raise ValidationError("Insufficient material quantity")

            material.quantity -= quantity_used

            # Save updates
            with self.session.begin():
                self.repository.update(material)

            self.logger.info(f"Tracked material usage: {material_id}, Quantity: {quantity_used}")
            return True

        except (NotFoundError, ValidationError) as e:
            self.logger.error(f"Error tracking material usage: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error tracking material usage: {e}")
            raise ValidationError(f"Could not track material usage: {str(e)}")

    def search_materials(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for materials based on parameters.

        Args:
            search_params: Dictionary of search parameters

        Returns:
            List of dictionaries representing matching materials
        """
        try:
            # Validate search parameters
            allowed_params = {'name', 'material_type', 'min_quantity', 'max_quantity'}
            invalid_params = set(search_params.keys()) - allowed_params
            if invalid_params:
                raise ValidationError(f"Invalid search parameters: {invalid_params}")

            # Prepare query conditions
            conditions = {}

            # Name search (case-insensitive partial match)
            if 'name' in search_params:
                conditions['name__ilike'] = f"%{search_params['name']}%"

            # Material type filter
            if 'material_type' in search_params:
                try:
                    conditions['material_type'] = MaterialType(search_params['material_type']).value
                except ValueError:
                    raise ValidationError(f"Invalid material type: {search_params['material_type']}")

            # Quantity range filters
            if 'min_quantity' in search_params:
                conditions['quantity__gte'] = search_params['min_quantity']

            if 'max_quantity' in search_params:
                conditions['quantity__lte'] = search_params['max_quantity']

            # Perform search
            materials = self.repository.list_with_filters(conditions)

            self.logger.info(f"Searched materials with params: {search_params}")
            return [self._material_to_dict(material) for material in materials]

        except (ValidationError, SQLAlchemyError) as e:
            self.logger.error(f"Error searching materials: {e}")
            raise ValidationError(f"Could not search materials: {str(e)}")

    def generate_sustainability_report(self) -> Dict[str, Any]:
        """
        Generate a sustainability report for materials.

        Returns:
            Dictionary containing sustainability metrics
        """
        try:
            # Retrieve all materials
            materials = self.repository.list_with_filters({})

            # Calculate sustainability metrics
            report = {
                'total_materials': len(materials),
                'material_type_breakdown': {},
                'total_quantity': 0,
                'average_quantity_per_type': {},
                'sustainability_score': 0.0
            }

            # Aggregate metrics by material type
            for material in materials:
                material_type = material.material_type

                # Material type breakdown
                if material_type not in report['material_type_breakdown']:
                    report['material_type_breakdown'][material_type] = 0
                report['material_type_breakdown'][material_type] += 1

                # Total quantity
                report['total_quantity'] += material.quantity

            # Calculate average quantity per type
            for material_type, count in report['material_type_breakdown'].items():
                report['average_quantity_per_type'][material_type] = (
                    report['total_quantity'] / count if count > 0 else 0
                )

            # Simple sustainability scoring (placeholder logic)
            # Could be expanded with more complex sustainability metrics
            report['sustainability_score'] = (
                    len(materials) > 0
                    and sum(1 for m in materials if m.quantity > 0) / len(materials)
                    or 0.0
            )

            self.logger.info("Generated sustainability report for materials")
            return report

        except SQLAlchemyError as e:
            self.logger.error(f"Error generating sustainability report: {e}")
            raise ValidationError(f"Could not generate sustainability report: {str(e)}")

    def calculate_material_efficiency(self, material_id: int, period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate efficiency metrics for a material.

        Args:
            material_id: ID of the material
            period_days: Number of days to include in the calculation

        Returns:
            Dictionary containing efficiency metrics

        Raises:
            NotFoundError: If material is not found
        """
        try:
            # Retrieve the material
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Calculate efficiency metrics
            # Note: This is a simplified calculation and would typically
            # involve more complex tracking of material usage
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            # Placeholder for more advanced efficiency calculation
            efficiency_metrics = {
                'material_id': material_id,
                'material_name': material.name,
                'total_quantity': material.quantity,
                'period_days': period_days,
                'usage_rate': 0.0,  # Placeholder for actual usage calculation
                'waste_percentage': 0.0,  # Placeholder for waste calculation
                'efficiency_score': 0.0  # Placeholder for efficiency scoring
            }

            self.logger.info(f"Calculated efficiency metrics for material {material_id}")
            return efficiency_metrics

        except (NotFoundError, SQLAlchemyError) as e:
            self.logger.error(f"Error calculating material efficiency: {e}")
            raise

    def _material_to_dict(self, material: Material) -> Dict[str, Any]:
        """
        Convert a Material model instance to a dictionary.

        Args:
            material (Material): Material model instance

        Returns:
            Dict[str, Any]: Dictionary representation of the material
        """
        return {
            'id': material.id,
            'name': material.name,
            'material_type': material.material_type,
            'quantity': material.quantity,
            # Add other relevant fields from the Material model
            # This method can be expanded to include more fields as needed
        }