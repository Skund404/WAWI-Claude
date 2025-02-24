

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class LeatherworkingProjectWorkflow:
    """
    Demonstrates a typical workflow for managing a leatherworking project.
    """

    @inject(MaterialService)
        def __init__(self, project_service: ProjectService, hardware_service:
                 HardwareService, supplier_service: SupplierService):
        self.project_service = project_service
        self.hardware_service = hardware_service
        self.supplier_service = supplier_service

        @inject(MaterialService)
            def create_leather_bag_project(self) -> Project:
        """
        Simulate creating a leather bag project with detailed specifications.

        Returns:
            Project: Newly created project
        """
        leather_supplier = self.supplier_service.find_or_create_supplier(
            company_name='Premium Leather Co.', supplier_type=SupplierType.
            LEATHER_SUPPLIER, additional_info={'specialties': [
                'Full-grain leather', 'Vegetable-tanned'],
                'sustainability_rating': 8.5})
        hardware_supplier = self.supplier_service.find_or_create_supplier(
            company_name='Artisan Hardware Solutions', supplier_type=SupplierType.HARDWARE_SUPPLIER, additional_info={'specialties':
                                                                                                                      ['Brass hardware', 'Custom fittings']})
        project_data = {'name': 'Luxury Leather Messenger Bag',
                        'project_type': ProjectType.BAG.name, 'skill_level': SkillLevel
                        .ADVANCED.name, 'description':
                        'Professional messenger bag with multiple compartments',
                        'estimated_hours': 40, 'primary_leather_type':
                        'Full-grain vegetable-tanned leather',
                        'estimated_leather_consumption': 12.5, 'components': [{'name':
                                                                               'Main Body', 'component_type': 'MAIN_BODY', 'material_type':
                                                                               'Full-grain leather', 'length': 16, 'width': 12,
                                                                               'material_thickness': 2.5, 'cutting_instructions':
                                                                               'Precise cut with minimal waste'}, {'name': 'Front Flap',
                                                                                                                   'component_type': 'CLOSURE', 'material_type':
                                                                                                                   'Full-grain leather', 'length': 14, 'width': 10,
                                                                                                                   'material_thickness': 2.0}]}
        project = self.project_service.create_project(project_data)
        hardware_items = [{'name': 'Brass Closure Buckle', 'hardware_type':
                           HardwareType.BUCKLE.name, 'material': HardwareMaterial.BRASS.
                           name, 'width': 35, 'length': 25, 'thickness': 3, 'supplier':
                           hardware_supplier}, {'name': 'Shoulder Strap D-Rings',
                                                'hardware_type': HardwareType.D_RING.name, 'material':
                                                HardwareMaterial.BRASS.name, 'width': 20, 'length': 15,
                                                'supplier': hardware_supplier}]
        for hardware_data in hardware_items:
            hardware = self.hardware_service.create_hardware(hardware_data)
        return project

        @inject(MaterialService)
            def track_project_progress(self, project: Project):
        """
        Simulate tracking and analyzing project progress.

        Args:
            project (Project): Project to track
        """
        material_usage = self.project_service.analyze_project_material_usage(
            project.id)
        print('Material Usage Analysis:')
        print(
            f"Total Estimated Leather: {material_usage.get('total_estimated_leather', 0)} sq ft"
        )
        complexity_report = (self.project_service.
                             generate_project_complexity_report())
        current_project_complexity = next((report for report in
                                           complexity_report if report['project_id'] == project.id), None)
        if current_project_complexity:
            print(
                f"Project Complexity: {current_project_complexity['complexity_score']}"
            )
        complex_projects = self.project_service.get_complex_projects(
            complexity_threshold=7.0)
        print(f'Number of Complex Projects: {len(complex_projects)}')

        @inject(MaterialService)
            def simulate_workflow(self):
        """
        Demonstrate a complete workflow from project creation to tracking.
        """
        leather_bag_project = self.create_leather_bag_project()
        self.track_project_progress(leather_bag_project)


def main():
    project_service = ProjectService(project_repository)
    hardware_service = HardwareService(hardware_repository)
    supplier_service = SupplierService(supplier_repository)
    workflow = LeatherworkingProjectWorkflow(project_service,
                                             hardware_service, supplier_service)
    workflow.simulate_workflow()


if __name__ == '__main__':
    main()
