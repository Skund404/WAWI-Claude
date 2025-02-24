from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Example workflow demonstrating project management in the leatherworking system.
"""


class LeatherworkingProjectWorkflow:
    """
    Demonstrates a typical workflow for managing leatherworking projects.
    """

        @inject(MaterialService)
        def __init__(self, project_service: ProjectService, material_service:
        MaterialService, inventory_service: InventoryService):
        """
        Initialize the workflow with necessary services.

        Args:
            project_service (ProjectService): Service for project management
            material_service (MaterialService): Service for material management
            inventory_service (InventoryService): Service for inventory tracking
        """
        self.project_service = project_service
        self.material_service = material_service
        self.inventory_service = inventory_service
        self.logger = get_logger(__name__)

        @inject(MaterialService)
        def create_leather_bag_project(self) ->Dict[str, Any]:
        """
        Create a sample leather bag project with predefined characteristics.

        Returns:
            Dict[str, Any]: Created project details
        """
        try:
            project_data = {'name': 'Classic Leather Messenger Bag', 'type':
                'bag', 'skill_level': 'intermediate', 'complexity_level': 7,
                'estimated_time': 120, 'collection': 'Urban Essentials',
                'version': '1.0'}
            project = self.project_service.create_project(project_data)
            self.logger.info(f'Created project: {project.name}')
            return project.to_dict()
        except Exception as e:
            self.logger.error(f'Error creating leather bag project: {e}')
            raise

        @inject(MaterialService)
        def track_project_progress(self, project_id: int):
        """
        Track and log project progress and material usage.

        Args:
            project_id (int): ID of the project to track
        """
        try:
            project = self.project_service.get_project(project_id,
                include_components=True)
            material_usage = (self.project_service.
                analyze_project_material_usage(project_id))
            self.logger.info(f'Project Progress: {project.name}')
            self.logger.info(f'Material Usage: {material_usage}')
            return {'project': project.to_dict(), 'material_usage':
                material_usage}
        except Exception as e:
            self.logger.error(f'Error tracking project progress: {e}')
            raise

        @inject(MaterialService)
        def simulate_workflow(self):
        """
        Simulate a complete project workflow from creation to tracking.
        """
        try:
            created_project = self.create_leather_bag_project()
            project_id = created_project['id']
            progress_details = self.track_project_progress(project_id)
            self.project_service.update_project_status(project_id,
                'in_progress')
            return progress_details
        except Exception as e:
            self.logger.error(f'Workflow simulation failed: {e}')
            raise


def main():
    """
    Demonstrate the project workflow.
    """
    session = get_db_session()
    try:
        project_repo = ProjectRepository(session)
        material_repo = MaterialRepository(session)
        inventory_repo = InventoryRepository(session)
        project_service = ProjectService(project_repo)
        material_service = MaterialService(material_repo)
        inventory_service = InventoryService(inventory_repo)
        workflow = LeatherworkingProjectWorkflow(project_service,
            material_service, inventory_service)
        result = workflow.simulate_workflow()
        print('Workflow Simulation Result:', result)
    except Exception as e:
        print(f'Workflow execution failed: {e}')
    finally:
        session.close()


if __name__ == '__main__':
    main()
