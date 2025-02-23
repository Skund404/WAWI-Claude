# Path: services/implementations/material_service.py
"""
Concrete implementation of the Material Service for leatherworking materials.
"""

from typing import Dict, Any, List
from services.interfaces.material_service import IMaterialService, MaterialType
from database.repositories.material_repository import MaterialRepository
from database.models.material import Material
from database.models.enums import MaterialQualityGrade
from utils.error_handler import ApplicationError, ValidationError
from utils.logger import get_logger
from datetime import datetime, timedelta


class MaterialService(IMaterialService):
    """
    Concrete implementation of material management services.

    Provides business logic and validation for material-related operations.
    """

    def __init__(self, material_repository: MaterialRepository):
        """
        Initialize the material service with a material repository.

        Args:
            material_repository (MaterialRepository): Repository for material data access
        """
        self.material_repository = material_repository
        self.logger = get_logger(__name__)

    def _validate_material_data(self, material_data: Dict[str, Any]) -> None:
        """
        Validate material data before creation or update.

        Args:
            material_data (Dict[str, Any]): Material data to validate

        Raises:
            ValidationError: If material data is invalid
        """
        # Validate required fields
        required_fields = ['name', 'type', 'supplier_id', 'current_stock', 'unit']
        for field in required_fields:
            if field not in material_data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate material type
        if material_data['type'] not in [t.value for t in MaterialType]:
            raise ValidationError(f"Invalid material type: {material_data['type']}")

        # Validate stock levels
        if not isinstance(material_data['current_stock'], (int, float)) or \
                material_data['current_stock'] < 0:
            raise ValidationError("Current stock must be a non-negative number")

        # Optional quality grade validation
        if 'quality_grade' in material_data:
            if material_data['quality_grade'] not in [q.value for q in MaterialQualityGrade]:
                raise ValidationError(f"Invalid quality grade: {material_data['quality_grade']}")

    def create_material(self, material_data: Dict[str, Any]) -> Material:
        """
        Create a new material entry.

        Args:
            material_data (Dict[str, Any]): Detailed information about the material

        Returns:
            Material: Created material object

        Raises:
            ValidationError: If material data is invalid
        """
        try:
            # Validate input data
            self._validate_material_data(material_data)

            # Create material
            material = Material(**material_data)
            created_material = self.material_repository.create(material)

            self.logger.info(f"Created material: {created_material.name}")
            return created_material

        except Exception as e:
            self.logger.error(f"Error creating material: {str(e)}")
            raise ApplicationError("Failed to create material", details=str(e))

    def get_material(self, material_id: int) -> Material:
        """
        Retrieve a specific material by its ID.

        Args:
            material_id (int): Unique identifier for the material

        Returns:
            Material: Material object

        Raises:
            ApplicationError: If material retrieval fails
        """
        try:
            material = self.material_repository.get(material_id)

            if not material:
                raise ApplicationError(f"Material with ID {material_id} not found")

            return material

        except Exception as e:
            self.logger.error(f"Error retrieving material {material_id}: {str(e)}")
            raise ApplicationError(f"Failed to retrieve material {material_id}", details=str(e))

    def update_material(self, material_id: int, material_data: Dict[str, Any]) -> Material:
        """
        Update an existing material's details.

        Args:
            material_id (int): Unique identifier for the material
            material_data (Dict[str, Any]): Updated material information

        Returns:
            Material: Updated material object

        Raises:
            ValidationError: If update data is invalid
            ApplicationError: If material update fails
        """
        try:
            # Validate input data
            self._validate_material_data(material_data)

            # Update material
            updated_material = self.material_repository.update(material_id, material_data)

            self.logger.info(f"Updated material: {updated_material.name}")
            return updated_material

        except Exception as e:
            self.logger.error(f"Error updating material {material_id}: {str(e)}")
            raise ApplicationError(f"Failed to update material {material_id}", details=str(e))

    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material from the system.

        Args:
            material_id (int): Unique identifier for the material to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            ApplicationError: If material deletion fails
        """
        try:
            self.material_repository.delete(material_id)
            self.logger.info(f"Deleted material with ID: {material_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting material {material_id}: {str(e)}")
            raise ApplicationError(f"Failed to delete material {material_id}", details=str(e))

    def get_low_stock_materials(self, include_zero_stock: bool = False) -> List[Material]:
        """
        Retrieve materials with low stock levels.

        Args:
            include_zero_stock (bool, optional): Whether to include materials
            with zero stock. Defaults to False.

        Returns:
            List[Material]: Materials with low stock
        """
        try:
            low_stock_materials = self.material_repository.get_low_stock_materials(include_zero_stock)
            return low_stock_materials

        except Exception as e:
            self.logger.error(f"Error retrieving low stock materials: {str(e)}")
            raise ApplicationError("Failed to retrieve low stock materials", details=str(e))

    def track_material_usage(self, material_id: int, quantity_used: float) -> Dict[str, Any]:
        """
        Track the usage of a specific material.

        Args:
            material_id (int): Unique identifier for the material
            quantity_used (float): Amount of material used

        Returns:
            Dict with material usage tracking details
        """
        try:
            # Retrieve the material
            material = self.get_material(material_id)

            # Update material stock
            material.update_stock(-quantity_used)

            # Create a usage log entry
            usage_log = {
                'material_id': material_id,
                'quantity_used': quantity_used,
                'timestamp': datetime.now(),
                'remaining_stock': material.current_stock
            }

            # Log the usage
            self.logger.info(f"Material usage tracked: {usage_log}")

            return usage_log

        except Exception as e:
            self.logger.error(f"Error tracking material usage for material {material_id}: {str(e)}")
            raise ApplicationError(f"Failed to track material usage for material {material_id}", details=str(e))

    def search_materials(self, search_params: Dict[str, Any]) -> List[Material]:
        """
        Search for materials based on various parameters.

        Args:
            search_params (Dict[str, Any]): Search criteria

        Returns:
            List[Material]: Materials matching the search criteria
        """
        try:
            materials = self.material_repository.search_materials(search_params)
            return materials

        except Exception as e:
            self.logger.error(f"Error searching materials: {str(e)}")
            raise ApplicationError("Failed to search materials", details=str(e))

    def generate_sustainability_report(self) -> List[Dict[str, Any]]:
        """
        Generate a sustainability report for materials.

        Returns:
            List[Dict[str, Any]]: List of dictionaries with material sustainability metrics
        """
        try:
            sustainability_report = self.material_repository.generate_sustainability_report()
            return sustainability_report

        except Exception as e:
            self.logger.error(f"Error generating sustainability report: {str(e)}")
            raise ApplicationError("Failed to generate sustainability report", details=str(e))

    def calculate_material_efficiency(self, material_id: int, period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate efficiency metrics for a specific material.

        Args:
            material_id (int): Unique identifier for the material
            period_days (int, optional): Number of days to analyze. Defaults to 30.

        Returns:
            Dict containing material efficiency metrics
        """
        try:
            # Set the date range for analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            # Calculate efficiency metrics
            efficiency_metrics = self.material_repository.calculate_material_efficiency(
                material_id,
                start_date,
                end_date
            )

            return efficiency_metrics

        except Exception as e:
            self.logger.error(f"Error calculating material efficiency for material {material_id}: {str(e)}")
            raise ApplicationError(
                f"Failed to calculate material efficiency for material {material_id}",
                details=str(e)
            )