# Path: examples/material_management_workflow.py
"""
Example workflow demonstrating material management in the leatherworking system.
"""

from typing import Dict, Any, List
from services.implementations.material_service import MaterialService
from services.implementations.supplier_service import SupplierService
from database.repositories.material_repository import MaterialRepository
from database.repositories.supplier_repository import SupplierRepository
from database.sqlalchemy.session import get_db_session
from utils.logger import get_logger


class MaterialManagementWorkflow:
    """
    Demonstrates a typical workflow for managing materials in leatherworking.
    """

    def __init__(
            self,
            material_service: MaterialService,
            supplier_service: SupplierService
    ):
        """
        Initialize the workflow with necessary services.

        Args:
            material_service (MaterialService): Service for material management
            supplier_service (SupplierService): Service for supplier management
        """
        self.material_service = material_service
        self.supplier_service = supplier_service
        self.logger = get_logger(__name__)

    def onboard_leather_material(self, supplier_id: int) -> Dict[str, Any]:
        """
        Onboard a new leather material from a specific supplier.

        Args:
            supplier_id (int): ID of the supplier providing the material

        Returns:
            Dict[str, Any]: Details of the created material
        """
        try:
            # Get supplier details
            supplier = self.supplier_service.get_supplier(supplier_id)

            # Define material data
            material_data = {
                'name': 'Full Grain Vegetable Tanned Leather',
                'type': 'leather',
                'supplier_id': supplier_id,
                'current_stock': 50.5,  # square feet
                'unit': 'sq_ft',
                'quality_grade': 'premium',
                'thickness': 2.5,  # mm
                'color': 'natural',
                'tanning_method': 'vegetable',
                'reorder_point': 20.0,
                'minimum_order': 10.0
            }

            # Create the material
            material = self.material_service.create_material(material_data)

            self.logger.info(f"Onboarded material: {material.name}")
            return material.to_dict()

        except Exception as e:
            self.logger.error(f"Error onboarding material from supplier {supplier_id}: {e}")
            raise

    def manage_material_inventory(self, material_id: int) -> Dict[str, Any]:
        """
        Manage inventory for a specific material.

        Args:
            material_id (int): ID of the material to manage

        Returns:
            Dict[str, Any]: Material inventory management details
        """
        try:
            # Get material details
            material = self.material_service.get_material(material_id)

            # Track material usage
            usage_log = self.material_service.track_material_usage(material_id, 5.5)

            # Check if material needs reordering
            if material.current_stock <= material.reorder_point:
                self.logger.warning(f"Material {material.name} needs reordering")

            # Calculate material efficiency
            efficiency_metrics = self.material_service.calculate_material_efficiency(material_id)

            return {
                'material': material.to_dict(),
                'usage_log': usage_log,
                'efficiency_metrics': efficiency_metrics
            }

        except Exception as e:
            self.logger.error(f"Error managing material inventory for material {material_id}: {e}")
            raise

    def generate_material_reports(self) -> Dict[str, Any]:
        """
        Generate comprehensive material reports.

        Returns:
            Dict[str, Any]: Generated material reports
        """
        try:
            # Generate sustainability report
            sustainability_report = self.material_service.generate_sustainability_report()

            # Get low stock materials
            low_stock_materials = self.material_service.get_low_stock_materials(include_zero_stock=False)

            return {
                'sustainability_report': sustainability_report,
                'low_stock_materials': [mat.to_dict() for mat in low_stock_materials]
            }

        except Exception as e:
            self.logger.error(f"Error generating material reports: {e}")
            raise

    def simulate_workflow(self):
        """
        Simulate a complete material management workflow.
        """
        try:
            # Assume we know a supplier ID
            supplier_id = 1  # This would typically come from a database or user input

            # Onboard a new material
            onboarded_material = self.onboard_leather_material(supplier_id)
            material_id = onboarded_material['id']

            # Manage material inventory
            inventory_details = self.manage_material_inventory(material_id)

            # Generate reports
            reports = self.generate_material_reports()

            return {
                'onboarded_material': onboarded_material,
                'inventory_details': inventory_details,
                'reports': reports
            }

        except Exception as e:
            self.logger.error(f"Workflow simulation failed: {e}")
            raise


def main():
    """
    Demonstrate the material management workflow.
    """
    # Get database session
    session = get_db_session()

    try:
        # Initialize repositories
        material_repo = MaterialRepository(session)
        supplier_repo = SupplierRepository(session)

        # Initialize services
        material_service = MaterialService(material_repo)
        supplier_service = SupplierService(supplier_repo)

        # Create workflow
        workflow = MaterialManagementWorkflow(
            material_service,
            supplier_service
        )

        # Run workflow simulation
        result = workflow.simulate_workflow()
        print("Material Management Workflow Result:")
        for key, value in result.items():
            print(f"\n{key.replace('_', ' ').title()}:")
            print(value)

    except Exception as e:
        print(f"Workflow execution failed: {e}")
    finally:
        # Close database session
        session.close()

if __name__ == '__main__':
    main()