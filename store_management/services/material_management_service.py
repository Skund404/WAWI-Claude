# services/material_management_service.py
"""
Material Management Service for tracking and allocating materials in leatherworking projects.
"""

import json
import logging
from typing import Dict, Optional, Union, List, Any

from database.models.enums import MaterialType, MaterialQualityGrade


class MaterialManagementService:
    """
    Service for managing material allocations, tracking, and efficiency.
    """

    def __init__(self):
        """
        Initialize the Material Management Service.
        """
        self.logger = logging.getLogger(__name__)
        self._material_allocations: Dict[str, Dict[str, float]] = {}

    def allocate_material(self, material_id: str, project_id: str, quantity: float) -> bool:
        """
        Allocate material to a specific project.

        Args:
            material_id (str): Unique identifier for the material
            project_id (str): Project the material is allocated to
            quantity (float): Quantity of material to allocate

        Returns:
            bool: Whether material allocation was successful
        """
        try:
            # Track material allocations
            if material_id not in self._material_allocations:
                self._material_allocations[material_id] = {}

            self._material_allocations[material_id][project_id] = quantity

            self.logger.info(f"Allocated {quantity} of material {material_id} to project {project_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error allocating material: {e}")
            return False

    def update_material_efficiency(self, material_id: str, project_id: str,
                                   used: float = 0.0, wasted: float = 0.0) -> bool:
        """
        Update material usage efficiency for a project.

        Args:
            material_id (str): Unique identifier for the material
            project_id (str): Project the material was used in
            used (float): Quantity of material actually used
            wasted (float): Quantity of material wasted

        Returns:
            bool: Whether material efficiency update was successful
        """
        try:
            # Validate and log material usage
            allocated = self._material_allocations.get(material_id, {}).get(project_id, 0.0)

            if used + wasted > allocated:
                self.logger.warning(f"Material usage exceeds allocation for {material_id}")
                return False

            efficiency = (used / allocated) * 100 if allocated > 0 else 0.0

            self.logger.info(
                f"Material {material_id} in project {project_id}: "
                f"Allocated: {allocated}, Used: {used}, Wasted: {wasted}, "
                f"Efficiency: {efficiency:.2f}%"
            )

            return True
        except Exception as e:
            self.logger.error(f"Error updating material efficiency: {e}")
            return False

    def get_material_allocation(self, material_id: str, project_id: Optional[str] = None) -> Union[
        float, Dict[str, float]]:
        """
        Retrieve material allocation details.

        Args:
            material_id (str): Unique identifier for the material
            project_id (Optional[str]): Specific project to get allocation for

        Returns:
            Union[float, Dict[str, float]]: Allocation details
        """
        if project_id:
            return self._material_allocations.get(material_id, {}).get(project_id, 0.0)

        return self._material_allocations.get(material_id, {})

    def find_available_materials(self, material_type: Optional[MaterialType] = None,
                                 quality_grade: Optional[MaterialQualityGrade] = None) -> List[Dict[str, Any]]:
        """
        Find available materials based on type and quality.

        Args:
            material_type (Optional[MaterialType]): Type of material to find
            quality_grade (Optional[MaterialQualityGrade]): Quality grade of material

        Returns:
            List[Dict[str, Any]]: List of available materials
        """
        # This is a mock implementation. In a real-world scenario, this would interact
        # with a material repository or database to find actual available materials.
        available_materials = [
            {
                'id': 'LEATHER-001',
                'type': MaterialType.LEATHER,
                'quality': MaterialQualityGrade.PREMIUM,
                'color': 'Brown',
                'thickness': 3.0,
                'available_quantity': 25.5
            },
            {
                'id': 'SUPPLIES-001',
                'type': MaterialType.SUPPLIES,
                'quality': MaterialQualityGrade.STANDARD,
                'color': 'Black',
                'material': 'Polyester',
                'available_quantity': 500
            }
        ]

        # Filter materials based on type and quality if specified
        filtered_materials = available_materials
        if material_type:
            filtered_materials = [
                mat for mat in filtered_materials
                if mat['type'] == material_type
            ]

        if quality_grade:
            filtered_materials = [
                mat for mat in filtered_materials
                if mat['quality'] == quality_grade
            ]

        return filtered_materials

    def create_material_transaction(self, material_id: str, quantity: float,
                                    transaction_type: str, project_id: Optional[str] = None) -> bool:
        """
        Create a material transaction record.

        Args:
            material_id (str): Unique identifier for the material
            quantity (float): Quantity of material involved in transaction
            transaction_type (str): Type of transaction (e.g., 'PURCHASE', 'USE', 'RETURN')
            project_id (Optional[str]): Project associated with the transaction

        Returns:
            bool: Whether transaction was successfully recorded
        """
        try:
            # In a real implementation, this would create a MaterialTransaction record
            self.logger.info(
                f"Material Transaction: {material_id}, Quantity: {quantity}, "
                f"Type: {transaction_type}, Project: {project_id}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error creating material transaction: {e}")
            return False


def main():
    """
    Demonstration of Material Management Service functionality.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    material_service = MaterialManagementService()

    # Example usage
    project_id = "PROJ-12345"
    material_id = "LEATHER-BLACK"

    # Allocate material
    material_service.allocate_material(material_id, project_id, 10.5)

    # Update material usage
    material_service.update_material_efficiency(material_id, project_id, used=8.0, wasted=0.5)

    # Find available materials
    print("Available Leather Materials:")
    leather_materials = material_service.find_available_materials(
        material_type=MaterialType.LEATHER,
        quality_grade=MaterialQualityGrade.PREMIUM
    )
    for material in leather_materials:
        print(json.dumps(material, indent=2))

    # Create a material transaction
    material_service.create_material_transaction(
        material_id,
        quantity=10.5,
        transaction_type='PURCHASE',
        project_id=project_id
    )

    # Get material allocation details
    allocation = material_service.get_material_allocation(material_id, project_id)
    print(f"Material allocation: {allocation}")


if __name__ == '__main__':
    main()