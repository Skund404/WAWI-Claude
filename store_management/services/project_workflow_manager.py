from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Comprehensive Project Workflow Manager for Leatherworking Project Management

Provides end-to-end project lifecycle management with advanced tracking and optimization.
"""


class ProjectType(Enum):
    """Enumerate different types of leatherworking projects."""
    BAG = auto()
    WALLET = auto()
    BELT = auto()
    ACCESSORY = auto()
    GARMENT = auto()
    CUSTOM = auto()


class SkillLevel(Enum):
    """Enumerate skill levels for projects."""
    BEGINNER = auto()
    INTERMEDIATE = auto()
    ADVANCED = auto()
    PROFESSIONAL = auto()


class ProjectStatus(Enum):
    """Detailed project status tracking."""
    CONCEPT = auto()
    PLANNING = auto()
    DESIGN = auto()
    MATERIAL_SOURCING = auto()
    PROTOTYPE = auto()
    PRODUCTION = auto()
    QUALITY_CHECK = auto()
    REFINEMENT = auto()
    COMPLETED = auto()
    ON_HOLD = auto()
    CANCELLED = auto()


@dataclass
class ProjectMaterial:
    """
    Detailed tracking of materials used in a project.
    """
    material_id: str
    expected_quantity: float
    actual_quantity: float = 0.0
    wastage: float = 0.0
    cost_per_unit: float = 0.0
    procurement_date: Optional[datetime] = None
    supplier: Optional[str] = None


@dataclass
class ProjectTask:
    """
    Comprehensive task tracking for project workflow.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ''
    description: str = ''
    status: str = 'PENDING'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    estimated_duration: Optional[timedelta] = None
    dependencies: List[str] = field(default_factory=list)
    priority: int = 3


class ProjectWorkflowManager:
    """
    Advanced project workflow management for leatherworking projects.
    """

    @inject(MaterialService)
        def __init__(self, material_service: Optional[MaterialManagementService
                                                  ] = None):
        """
        Initialize the Project Workflow Manager.

        Args:
            material_service (Optional[MaterialManagementService]):
                Service for managing material allocations
        """
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.material_service = material_service or MaterialManagementService()
        self.logger = logging.getLogger(__name__)

        @inject(MaterialService)
            def create_project(self, name: str, project_type: ProjectType,
                           skill_level: SkillLevel, description: Optional[str] = None) -> str:
        """
        Create a comprehensive leatherworking project.

        Args:
            name (str): Project name
            project_type (ProjectType): Type of leatherworking project
            skill_level (SkillLevel): Skill level required
            description (Optional[str]): Detailed project description

        Returns:
            str: Generated project ID
        """
        project_id = f'PROJ-{uuid.uuid4().hex[:8].upper()}'
        project = {'id': project_id, 'name': name, 'type': project_type.
                   name, 'skill_level': skill_level.name, 'description':
                   description or '', 'status': ProjectStatus.CONCEPT.name,
                   'created_at': datetime.now(), 'updated_at': datetime.now(),
                   'materials': {}, 'tasks': [], 'progress': 0.0, 'history': [],
                   'metadata': {}}
        self.projects[project_id] = project
        self.logger.info(f'Created new project: {project_id} - {name}')
        return project_id

        @inject(MaterialService)
            def update_project_details(self, project_id: str, **kwargs) -> bool:
        """
        Update project details flexibly.

        Args:
            project_id (str): Project to update
            **kwargs: Flexible keyword arguments for project updates

        Returns:
            bool: Whether update was successful
        """
        if project_id not in self.projects:
            self.logger.error(f'Project {project_id} not found')
            return False
        project = self.projects[project_id]
        for key, value in kwargs.items():
            if key == 'status' and isinstance(value, ProjectStatus):
                value = value.name
            project[key] = value
        project['updated_at'] = datetime.now()
        self.logger.info(f'Updated project {project_id}: {kwargs}')
        return True

        @inject(MaterialService)
            def update_project_status(self, project_id: str, new_status: ProjectStatus
                                  ) -> bool:
        """
        Update the status of a project with comprehensive tracking.

        Args:
            project_id (str): Project to update
            new_status (ProjectStatus): New project status

        Returns:
            bool: Whether status update was successful
        """
        if project_id not in self.projects:
            self.logger.error(f'Project {project_id} not found')
            return False
        project = self.projects[project_id]
        old_status = project.get('status', 'UNKNOWN')
        status_change = {'old_status': old_status, 'new_status': new_status
                         .name, 'timestamp': datetime.now()}
        project['status'] = new_status.name
        project['history'].append(status_change)
        project['updated_at'] = datetime.now()
        self.logger.info(
            f'Project {project_id} status changed from {old_status} to {new_status.name}'
        )
        return True

        @inject(MaterialService)
            def add_project_material(self, project_id: str, material_id: str,
                                 expected_quantity: float, cost_per_unit: float = 0.0, supplier:
                                 Optional[str] = None) -> bool:
        """
        Add a material to the project with comprehensive tracking.

        Args:
            project_id (str): Project to add material to
            material_id (str): Material identifier
            expected_quantity (float): Expected quantity of material
            cost_per_unit (float): Cost per unit of material
            supplier (Optional[str]): Material supplier

        Returns:
            bool: Whether material was successfully added
        """
        if project_id not in self.projects:
            self.logger.error(f'Project {project_id} not found')
            return False
        allocation_success = self.material_service.allocate_material(
            material_id, project_id, expected_quantity)
        if allocation_success:
            project_material = ProjectMaterial(material_id=material_id,
                                               expected_quantity=expected_quantity, cost_per_unit=cost_per_unit, procurement_date=datetime.now(), supplier=supplier)
            self.projects[project_id]['materials'][material_id
                                                   ] = project_material.__dict__
            self.update_project_status(project_id, ProjectStatus.
                                       MATERIAL_SOURCING)
            self.logger.info(
                f'Added material {material_id} to project {project_id}')
        return allocation_success

        @inject(MaterialService)
            def update_material_usage(self, project_id: str, material_id: str,
                                  actual_quantity: float, wastage: float = 0.0) -> bool:
        """
        Update actual material usage for a project.

        Args:
            project_id (str): Project identifier
            material_id (str): Material identifier
            actual_quantity (float): Quantity actually used
            wastage (float): Quantity of material wasted

        Returns:
            bool: Whether update was successful
        """
        if project_id not in self.projects:
            self.logger.error(f'Project {project_id} not found')
            return False
        project = self.projects[project_id]
        if material_id not in project['materials']:
            self.logger.error(
                f'Material {material_id} not found in project {project_id}')
            return False
        material = project['materials'][material_id]
        material['actual_quantity'] = actual_quantity
        material['wastage'] = wastage
        self.material_service.update_material_efficiency(material_id,
                                                         project_id, used=actual_quantity, wasted=wastage)
        self._calculate_project_progress(project_id)
        self.logger.info(
            f'Updated material {material_id} usage in project {project_id}')
        return True

        @inject(MaterialService)
            def add_project_task(self, project_id: str, name: str, description: str
                             = '', dependencies: Optional[List[str]] = None, estimated_duration:
                             Optional[timedelta] = None, priority: int = 3) -> str:
        """
        Add a task to the project workflow.

        Args:
            project_id (str): Project to add task to
            name (str): Task name
            description (str): Task description
            dependencies (Optional[List[str]]): Task dependencies
            estimated_duration (Optional[timedelta]): Estimated task duration
            priority (int): Task priority (1-5)

        Returns:
            str: Generated task ID
        """
        if project_id not in self.projects:
            self.logger.error(f'Project {project_id} not found')
            raise ValueError(f'Project {project_id} not found')
        task = ProjectTask(name=name, description=description, dependencies=dependencies or [], estimated_duration=estimated_duration,
                           priority=priority)
        self.projects[project_id]['tasks'].append(task.__dict__)
        self.logger.info(f'Added task {task.id} to project {project_id}')
        return task.id

        @inject(MaterialService)
            def update_task_status(self, project_id: str, task_id: str, status: str,
                               assigned_to: Optional[str] = None) -> bool:
        """
        Update the status of a specific task.

        Args:
            project_id (str): Project containing the task
            task_id (str): Task to update
            status (str): New task status
            assigned_to (Optional[str]): Person assigned to the task

        Returns:
            bool: Whether task update was successful
        """
        if project_id not in self.projects:
            self.logger.error(f'Project {project_id} not found')
            return False
        project = self.projects[project_id]
        for task in project['tasks']:
            if task['id'] == task_id:
                task['status'] = status
                if assigned_to:
                    task['assigned_to'] = assigned_to
                if status == 'IN_PROGRESS':
                    task['start_date'] = datetime.now()
                elif status in ['COMPLETED', 'CANCELLED']:
                    task['end_date'] = datetime.now()
                self._calculate_project_progress(project_id)
                self.logger.info(f'Updated task {task_id} status to {status}')
                return True
        self.logger.error(f'Task {task_id} not found in project {project_id}')
        return False

        @inject(MaterialService)
            def _calculate_project_progress(self, project_id: str):
        """
        Calculate overall project progress based on tasks and material usage.

        Args:
            project_id (str): Project to calculate progress for
        """
        if project_id not in self.projects:
            return
        project = self.projects[project_id]
        if project['tasks']:
            completed_tasks = sum(1 for task in project['tasks'] if task[
                'status'] == 'COMPLETED')
            task_progress = completed_tasks / len(project['tasks']) * 100
        else:
            task_progress = 0
        material_progress = 0
        if project['materials']:
            material_usage = sum(mat['actual_quantity'] / mat[
                'expected_quantity'] * 100 for mat in project['materials'].
                values()) / len(project['materials'])
            material_progress = material_usage
        project['progress'] = task_progress * 0.6 + material_progress * 0.4
        if project['progress'] > 90:
            self.update_project_status(project_id, ProjectStatus.COMPLETED)
        elif project['progress'] > 0:
            self.update_project_status(project_id, ProjectStatus.PRODUCTION)

        @inject(MaterialService)
            def generate_project_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the project.

        Args:
            project_id (str): Project to summarize

        Returns:
            Dict: Comprehensive project summary
        """
        if project_id not in self.projects:
            self.logger.error(f'Project {project_id} not found')
            return {}
        project = self.projects[project_id]
        return {'id': project['id'], 'name': project['name'], 'type':
                project['type'], 'skill_level': project['skill_level'],
                'status': project['status'], 'description': project.get(
            'description', ''), 'created_at': project['created_at'],
            'updated_at': project['updated_at'], 'progress': project.get(
            'progress', 0.0), 'materials': project.get('materials', {}),
            'tasks': project.get('tasks', [])}

        @inject(MaterialService)
            def get_all_projects(self, status: Optional[ProjectStatus] = None) -> List[
                Dict[str, Any]]:
        """
        Retrieve all projects, optionally filtered by status.

        Args:
            status (Optional[ProjectStatus]): Filter by specific status

        Returns:
            List[Dict]: List of project summaries
        """
        if status:
            return [self.generate_project_summary(proj_id) for proj_id,
                    proj in self.projects.items() if proj['status'] == status.name]
        return [self.generate_project_summary(proj_id) for proj_id in self.
                projects.keys()]


def main():
    """
    Demonstration of Project Workflow Manager functionality.
    """
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    material_service = MaterialManagementService()
    workflow_manager = ProjectWorkflowManager(material_service)
    project_id = workflow_manager.create_project(name='Leather Messenger Bag', project_type=ProjectType.BAG,
                                                 skill_level=SkillLevel.ADVANCED, description='Professional leather messenger bag project')
    workflow_manager.update_project_details(
        project_id, description='High-end leather messenger bag with multiple compartments')
    workflow_manager.add_project_material(project_id, 'LEATHER-BROWN',
                                          expected_quantity=10.5, cost_per_unit=15.0, supplier='Local Tannery')
    summary = workflow_manager.generate_project_summary(project_id)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == '__main__':
    main()
