

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class TestProjectWorkflowManager(unittest.TestCase):

        @inject(MaterialService)
        def setUp(self):
        self.mock_material_service = Mock()
        self.workflow_manager = ProjectWorkflowManager(self.
            mock_material_service)

        @inject(MaterialService)
        def test_create_project(self):
        project_id = self.workflow_manager.create_project(name=
            'Test Project', project_type=ProjectType.BAG, skill_level=
            SkillLevel.INTERMEDIATE, description='Test description')
        self.assertIn(project_id, self.workflow_manager.projects)
        project = self.workflow_manager.projects[project_id]
        self.assertEqual(project['name'], 'Test Project')
        self.assertEqual(project['type'], ProjectType.BAG.name)
        self.assertEqual(project['skill_level'], SkillLevel.INTERMEDIATE.name)
        self.assertEqual(project['description'], 'Test description')
        self.assertEqual(project['status'], ProjectStatus.CONCEPT.name)

        @inject(MaterialService)
        def test_update_project_details(self):
        project_id = self.workflow_manager.create_project(name=
            'Original Project', project_type=ProjectType.WALLET,
            skill_level=SkillLevel.BEGINNER)
        success = self.workflow_manager.update_project_details(project_id,
            name='Updated Project', description='New description')
        self.assertTrue(success)
        project = self.workflow_manager.projects[project_id]
        self.assertEqual(project['name'], 'Updated Project')
        self.assertEqual(project['description'], 'New description')

        @inject(MaterialService)
        def test_update_project_status(self):
        project_id = self.workflow_manager.create_project(name=
            'Status Test Project', project_type=ProjectType.BELT,
            skill_level=SkillLevel.ADVANCED)
        success = self.workflow_manager.update_project_status(project_id,
            ProjectStatus.DESIGN)
        self.assertTrue(success)
        project = self.workflow_manager.projects[project_id]
        self.assertEqual(project['status'], ProjectStatus.DESIGN.name)
        self.assertEqual(len(project['history']), 1)

        @inject(MaterialService)
        def test_add_project_material(self):
        project_id = self.workflow_manager.create_project(name=
            'Material Test Project', project_type=ProjectType.ACCESSORY,
            skill_level=SkillLevel.PROFESSIONAL)
        self.mock_material_service.allocate_material.return_value = True
        success = self.workflow_manager.add_project_material(project_id,
            'LEATHER-001', expected_quantity=5.0, cost_per_unit=10.0,
            supplier='Test Supplier')
        self.assertTrue(success)
        project = self.workflow_manager.projects[project_id]
        self.assertIn('LEATHER-001', project['materials'])
        material = project['materials']['LEATHER-001']
        self.assertEqual(material['expected_quantity'], 5.0)
        self.assertEqual(material['cost_per_unit'], 10.0)
        self.assertEqual(material['supplier'], 'Test Supplier')

        @inject(MaterialService)
        def test_update_material_usage(self):
        project_id = self.workflow_manager.create_project(name=
            'Usage Test Project', project_type=ProjectType.GARMENT,
            skill_level=SkillLevel.INTERMEDIATE)
        self.workflow_manager.add_project_material(project_id, 'FABRIC-001',
            expected_quantity=10.0)
        success = self.workflow_manager.update_material_usage(project_id,
            'FABRIC-001', actual_quantity=9.5, wastage=0.5)
        self.assertTrue(success)
        project = self.workflow_manager.projects[project_id]
        material = project['materials']['FABRIC-001']
        self.assertEqual(material['actual_quantity'], 9.5)
        self.assertEqual(material['wastage'], 0.5)

        @inject(MaterialService)
        def test_add_project_task(self):
        project_id = self.workflow_manager.create_project(name=
            'Task Test Project', project_type=ProjectType.CUSTOM,
            skill_level=SkillLevel.ADVANCED)
        task_id = self.workflow_manager.add_project_task(project_id, name=
            'Test Task', description='Task description', estimated_duration
            =timedelta(hours=2), priority=2)
        project = self.workflow_manager.projects[project_id]
        self.assertIn(task_id, [task['id'] for task in project['tasks']])
        task = next(task for task in project['tasks'] if task['id'] == task_id)
        self.assertEqual(task['name'], 'Test Task')
        self.assertEqual(task['description'], 'Task description')
        self.assertEqual(task['estimated_duration'], timedelta(hours=2))
        self.assertEqual(task['priority'], 2)

        @inject(MaterialService)
        def test_update_task_status(self):
        project_id = self.workflow_manager.create_project(name=
            'Task Status Test Project', project_type=ProjectType.BAG,
            skill_level=SkillLevel.BEGINNER)
        task_id = self.workflow_manager.add_project_task(project_id, name=
            'Status Test Task')
        success = self.workflow_manager.update_task_status(project_id,
            task_id, status='IN_PROGRESS', assigned_to='John Doe')
        self.assertTrue(success)
        project = self.workflow_manager.projects[project_id]
        task = next(task for task in project['tasks'] if task['id'] == task_id)
        self.assertEqual(task['status'], 'IN_PROGRESS')
        self.assertEqual(task['assigned_to'], 'John Doe')

        @inject(MaterialService)
        def test_generate_project_summary(self):
        project_id = self.workflow_manager.create_project(name=
            'Summary Test Project', project_type=ProjectType.WALLET,
            skill_level=SkillLevel.INTERMEDIATE, description=
            'Test summary generation')
        self.workflow_manager.add_project_material(project_id,
            'LEATHER-002', expected_quantity=3.0)
        self.workflow_manager.add_project_task(project_id, name='Summary Task')
        summary = self.workflow_manager.generate_project_summary(project_id)
        self.assertEqual(summary['name'], 'Summary Test Project')
        self.assertEqual(summary['type'], ProjectType.WALLET.name)
        self.assertEqual(summary['skill_level'], SkillLevel.INTERMEDIATE.name)
        self.assertEqual(summary['description'], 'Test summary generation')
        self.assertIn('LEATHER-002', summary['materials'])
        self.assertEqual(len(summary['tasks']), 1)


if __name__ == '__main__':
    unittest.main()
