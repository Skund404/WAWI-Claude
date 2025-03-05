# services/implementations/project_service.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import uuid

from services.interfaces.project_service import IProjectService, ProjectType, SkillLevel, ProjectStatus
from database.models.project import Project  # Ensure this import is correct
from database.models.components import ProjectComponent
from database.repositories.project_repository import ProjectRepository
from services.base_service import BaseService, NotFoundError, ValidationError
from utils.logger import log_info, log_error, log_debug


class ProjectService(BaseService, IProjectService):
    """
    Comprehensive implementation of Project Service for managing leatherworking projects.

    Supports advanced project management features including:
    - Project creation and management
    - Component tracking
    - Material requirement analysis
    - Project complexity reporting
    - Advanced querying and filtering
    """

    def __init__(self, project_repository: Optional[ProjectRepository] = None):
        """
        Initialize the project service.

        Args:
            project_repository: Optional repository for project data access
        """
        super().__init__()
        self._repository = project_repository or ProjectRepository()
        self.logger = logging.getLogger(__name__)

    def create_project(self, project_data: Dict[str, Any]) -> Project:
        """
        Create a new project with comprehensive validation.

        Args:
            project_data (Dict[str, Any]): Project creation data

        Returns:
            Project: Created project instance

        Raises:
            ValidationError: If project data is invalid
        """
        try:
            # Validate required fields
            required_fields = ['name', 'project_type']
            for field in required_fields:
                if field not in project_data:
                    raise ValidationError(f"Missing required field: {field}")

            # Validate project type and skill level
            if 'project_type' in project_data:
                if not isinstance(project_data['project_type'], ProjectType):
                    raise ValidationError(f"Invalid project type: {project_data['project_type']}")

            if 'skill_level' in project_data:
                if not isinstance(project_data['skill_level'], SkillLevel):
                    raise ValidationError(f"Invalid skill level: {project_data['skill_level']}")

            # Set default values
            project_data.setdefault('status', ProjectStatus.INITIAL_CONSULTATION)
            project_data.setdefault('start_date', datetime.utcnow())

            # Create project using repository method
            project = self._repository.create(project_data)

            # Handle components if provided
            if 'components' in project_data and project_data['components']:
                for component_data in project_data['components']:
                    self.add_component_to_project(project.id, component_data)

            log_info(f"Created project: {project.name}")
            return project

        except Exception as e:
            log_error(f"Project creation failed: {str(e)}")
            raise ValidationError(f"Failed to create project: {str(e)}")

    def get_project(self, project_id: str) -> Project:
        """
        Retrieve a project by its ID.

        Args:
            project_id (str): Unique project identifier

        Returns:
            Project: Retrieved project instance

        Raises:
            NotFoundError: If project is not found
        """
        try:
            project = self._repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")
            return project
        except Exception as e:
            log_error(f"Failed to retrieve project {project_id}: {str(e)}")
            raise

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Project:
        """
        Update an existing project with comprehensive validation.

        Args:
            project_id (str): Unique project identifier
            updates (Dict[str, Any]): Project update data

        Returns:
            Project: Updated project instance

        Raises:
            NotFoundError: If project is not found
            ValidationError: If update data is invalid
        """
        try:
            # Validate project type if present
            if 'project_type' in updates:
                if not isinstance(updates['project_type'], ProjectType):
                    raise ValidationError(f"Invalid project type: {updates['project_type']}")

            # Validate skill level if present
            if 'skill_level' in updates:
                if not isinstance(updates['skill_level'], SkillLevel):
                    raise ValidationError(f"Invalid skill level: {updates['skill_level']}")

            # Add updated timestamp
            updates['updated_at'] = datetime.utcnow()

            # Update project
            project = self._repository.update(project_id, updates)

            log_info(f"Updated project: {project_id}")
            return project

        except Exception as e:
            log_error(f"Failed to update project {project_id}: {str(e)}")
            raise ValidationError(f"Project update failed: {str(e)}")

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id (str): Unique project identifier

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If project is not found
        """
        try:
            success = self._repository.delete(project_id)
            if success:
                log_info(f"Deleted project: {project_id}")
            return success
        except Exception as e:
            log_error(f"Failed to delete project {project_id}: {str(e)}")
            raise

    def add_component_to_project(self, project_id: str, component_data: Dict[str, Any]) -> Project:
        """
        Add a component to a project.

        Args:
            project_id (str): Project identifier
            component_data (Dict[str, Any]): Component details

        Returns:
            Project: Updated project with new component

        Raises:
            NotFoundError: If project is not found
            ValidationError: If component data is invalid
        """
        try:
            # Validate component data
            if not component_data.get('name'):
                raise ValidationError("Component name is required")

            # Ensure project exists
            project = self.get_project(project_id)

            # Add project_id to component data
            component_data['project_id'] = project_id
            component_data['created_at'] = datetime.utcnow()

            # Create component (assuming repository method or direct model creation)
            component = ProjectComponent(**component_data)

            # Add to project's components
            project.components.append(component)

            # Save changes
            self._repository.save(project)

            log_info(f"Added component to project {project_id}")
            return project

        except Exception as e:
            log_error(f"Failed to add component to project {project_id}: {str(e)}")
            raise ValidationError(f"Component addition failed: {str(e)}")

    def remove_component_from_project(self, project_id: str, component_id: str) -> Project:
        """
        Remove a component from a project.

        Args:
            project_id (str): Project identifier
            component_id (str): Component identifier

        Returns:
            Project: Updated project after component removal

        Raises:
            NotFoundError: If project or component is not found
        """
        try:
            # Retrieve project
            project = self.get_project(project_id)

            # Find and remove the component
            component = next(
                (comp for comp in project.components if str(comp.id) == str(component_id)),
                None
            )

            if not component:
                raise NotFoundError(f"Component {component_id} not found in project {project_id}")

            # Remove component
            project.components.remove(component)

            # Save changes
            self._repository.save(project)

            log_info(f"Removed component {component_id} from project {project_id}")
            return project

        except Exception as e:
            log_error(f"Failed to remove component from project {project_id}: {str(e)}")
            raise

    def update_project_progress(self, project_id: str, progress: int) -> Project:
        """
        Update project progress and adjust status accordingly.

        Args:
            project_id (str): Project identifier
            progress (int): Progress percentage (0-100)

        Returns:
            Project: Updated project

        Raises:
            ValidationError: If progress is invalid
        """
        try:
            # Validate progress
            if progress < 0 or progress > 100:
                raise ValidationError("Progress must be between 0 and 100")

            # Determine status based on progress
            status = (
                ProjectStatus.PLANNING if progress == 0 else
                ProjectStatus.IN_PROGRESS if progress < 50 else
                ProjectStatus.REFINEMENT if progress < 100 else
                ProjectStatus.COMPLETED
            )

            # Prepare updates
            updates = {
                'progress': progress,
                'status': status,
                'updated_at': datetime.utcnow()
            }

            # Update project
            project = self._repository.update(project_id, updates)

            log_info(f"Updated project {project_id} progress to {progress}%")
            return project

        except Exception as e:
            log_error(f"Failed to update project progress {project_id}: {str(e)}")
            raise ValidationError(f"Progress update failed: {str(e)}")

    def list_projects(
            self,
            project_type: Optional[ProjectType] = None,
            skill_level: Optional[SkillLevel] = None,
            status: Optional[ProjectStatus] = None
    ) -> List[Project]:
        """
        List projects with optional filtering.

        Args:
            project_type: Optional filter by project type
            skill_level: Optional filter by skill level
            status: Optional filter by project status

        Returns:
            List[Project]: Filtered list of projects
        """
        try:
            # Prepare filters
            filters = {}
            if project_type:
                filters['project_type'] = project_type
            if skill_level:
                filters['skill_level'] = skill_level
            if status:
                filters['status'] = status

            # Use repository method to find projects
            projects = self._repository.find_projects_by_complex_criteria(filters)

            log_debug(f"Listed {len(projects)} projects with filters: {filters}")
            return projects

        except Exception as e:
            log_error(f"Failed to list projects: {str(e)}")
            raise


    def generate_project_complexity_report(self, project_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive project complexity report.

        Args:
            project_id (str): Project identifier

        Returns:
            Dict[str, Any]: Project complexity report

        Raises:
            NotFoundError: If project is not found
        """
        try:
            project = self.get_project(project_id)

            # Analyze project components and calculate complexity
            components = project.components
            num_components = len(components)

            # Calculate complexity score
            skill_level_value = project.skill_level.value
            material_types = set(
                component.material_type
                for component in components
                if component.material_type
            )
            material_diversity = len(material_types)

            # Complexity calculation
            complexity_score = (
                    (num_components * 0.5) +
                    (skill_level_value * 2) +
                    (material_diversity * 1.5)
            )

            # Complexity rating
            complexity_rating = (
                "Simple" if complexity_score < 5 else
                "Moderate" if complexity_score < 10 else
                "Complex" if complexity_score < 15 else
                "Very Complex"
            )

            # Estimated time calculation
            base_hours = num_components * 0.5
            skill_factors = {
                SkillLevel.BEGINNER: 1.5,
                SkillLevel.INTERMEDIATE: 1.2,
                SkillLevel.ADVANCED: 1.0,
                SkillLevel.EXPERT: 0.8
            }
            skill_factor = skill_factors.get(project.skill_level, 1.0)
            estimated_hours = base_hours * skill_factor

            report = {
                "project_id": project_id,
                "project_name": project.name,
                "complexity_score": complexity_score,
                "complexity_rating": complexity_rating,
                "number_of_components": num_components,
                "skill_level": project.skill_level.name,
                "material_diversity": material_diversity,
                "estimated_time": estimated_hours,
                "factors": {
                    "component_count": num_components * 0.5,
                    "skill_level": skill_level_value * 2,
                    "material_diversity": material_diversity * 1.5
                }
            }

            log_info(f"Generated complexity report for project {project_id}")
            return report

        except Exception as e:
            log_error(f"Failed to generate complexity report for project {project_id}: {str(e)}")
            raise

    def duplicate_project(self, project_id: str, new_name: Optional[str] = None) -> Project:
        """
        Duplicate an existing project.

        Args:
            project_id (str): Project identifier to duplicate
            new_name (Optional[str]): Name for the duplicated project

        Returns:
            Project: Newly created duplicated project

        Raises:
            NotFoundError: If original project is not found
        """
        try:
            # Retrieve original project
            original_project = self.get_project(project_id)

            # Prepare duplicate project data
            duplicate_data = {
                'name': new_name or f"Copy of {original_project.name}",
                'project_type': original_project.project_type,
                'description': original_project.description,
                'skill_level': original_project.skill_level,
                'status': ProjectStatus.PLANNING,
                'progress': 0,
                # Copy metadata if exists
                'metadata': original_project.metadata.copy() if original_project.metadata else {}
            }

            # Create new project
            duplicated_project = self.create_project(duplicate_data)

            # Copy components
            for component in original_project.components:
                component_data = {
                    'name': component.name,
                    'material_id': component.material_id,
                    'material_type': component.material_type,
                    'quantity': component.quantity,
                    'dimensions': component.dimensions,
                    'notes': component.notes
                }
                self.add_component_to_project(duplicated_project.id, component_data)

            log_info(f"Duplicated project {project_id} to new project {duplicated_project.id}")
            return duplicated_project

        except Exception as e:
            log_error(f"Failed to duplicate project {project_id}: {str(e)}")
            raise

    def calculate_project_material_requirements(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate material requirements for a project.

        Args:
            project_id (str): Project identifier

        Returns:
            Dict[str, Any]: Material requirements analysis

        Raises:
            NotFoundError: If project is not found
        """
        try:
            project = self.get_project(project_id)

            # Group materials by type and ID
            material_requirements = {}

            for component in project.components:
                if not component.material_type:
                    continue

                key = (
                    f"{component.material_type}:{component.material_id}"
                    if component.material_id
                    else str(component.material_type)
                )

                if key not in material_requirements:
                    material_requirements[key] = {
                        "material_type": component.material_type,
                        "material_id": component.material_id,
                        "quantity": 0
                    }

                material_requirements[key]["quantity"] += component.quantity

            analysis = {
                "project_id": project_id,
                "project_name": project.name,
                "materials": list(material_requirements.values())
            }

            log_info(f"Calculated material requirements for project {project_id}")
            return analysis

        except Exception as e:
            log_info(f"Calculated material requirements for project {project_id}")
            return analysis

        except Exception as e:
            log_error(f"Failed to calculate material requirements for project {project_id}: {str(e)}")
            raise

    def analyze_project_material_usage(self, project_id: str) -> Dict[str, Any]:
        """
        Analyze material usage and efficiency for a project.

        Args:
            project_id (str): Project identifier

        Returns:
            Dict[str, Any]: Material usage analysis

        Raises:
            NotFoundError: If project is not found
        """
        try:
            # Get material requirements
            requirements = self.calculate_project_material_requirements(project_id)
            project = self.get_project(project_id)

            # Calculate aggregate metrics
            materials = requirements["materials"]
            total_quantity = sum(material["quantity"] for material in materials)

            # Calculate material diversity
            material_diversity = len(materials)
            material_types = len(set(material["material_type"] for material in materials))

            # Estimated waste factor (adjustable based on project complexity)
            waste_factor = 0.15  # Default 15% waste
            complexity_report = self.generate_project_complexity_report(project_id)

            # Adjust waste factor based on project complexity
            if complexity_report["complexity_rating"] == "Very Complex":
                waste_factor = 0.25
            elif complexity_report["complexity_rating"] == "Complex":
                waste_factor = 0.20

            # Generate comprehensive analysis
            analysis = {
                "project_id": project_id,
                "project_name": project.name,
                "total_material_quantity": total_quantity,
                "material_diversity": material_diversity,
                "material_breakdown": materials,
                "material_types": material_types,
                "estimated_waste_factor": waste_factor,
                "estimated_total_with_waste": total_quantity * (1 + waste_factor),
                "complexity": {
                    "rating": complexity_report["complexity_rating"],
                    "score": complexity_report["complexity_score"]
                }
            }

            log_info(f"Analyzed material usage for project {project_id}")
            return analysis

        except Exception as e:
            log_error(f"Failed to analyze material usage for project {project_id}: {str(e)}")
            raise

    def get_projects_by_deadline(
            self,
            before_date: Optional[datetime] = None,
            after_date: Optional[datetime] = None
    ) -> List[Project]:
        """
        Retrieve projects within a specific deadline range.

        Args:
            before_date (Optional[datetime]): Maximum deadline date
            after_date (Optional[datetime]): Minimum deadline date

        Returns:
            List[Project]: Projects matching the deadline criteria
        """
        try:
            # Prepare filtering conditions
            filters = {}

            if before_date:
                filters['deadline__lte'] = before_date

            if after_date:
                filters['deadline__gte'] = after_date

            # Use repository method to find projects
            projects = self._repository.find_projects_by_complex_criteria(filters)

            log_debug(f"Retrieved {len(projects)} projects by deadline")
            return projects

        except Exception as e:
            log_error(f"Failed to retrieve projects by deadline: {str(e)}")
            raise

    def get_complex_projects(self, min_components: int = 5) -> List[Project]:
        """
        Retrieve projects with a high number of components.

        Args:
            min_components (int): Minimum number of components to consider a project complex

        Returns:
            List[Project]: Complex projects
        """
        try:
            # Find projects with at least min_components
            complex_projects = [
                project for project in self._repository.find_projects_by_complex_criteria({})
                if len(project.components) >= min_components
            ]

            log_debug(f"Retrieved {len(complex_projects)} complex projects")
            return complex_projects

        except Exception as e:
            log_error(f"Failed to retrieve complex projects: {str(e)}")
            raise

    def get_projects_by_status(self, status: ProjectStatus) -> List[Project]:
        """
        Retrieve projects with a specific status.

        Args:
            status (ProjectStatus): Project status to filter by

        Returns:
            List[Project]: Projects with the specified status
        """
        try:
            projects = self._repository.find_projects_by_complex_criteria({'status': status})

            log_debug(f"Retrieved {len(projects)} projects with status {status}")
            return projects

        except Exception as e:
            log_error(f"Failed to retrieve projects by status {status}: {str(e)}")
            raise

    def search_projects(self, query: str) -> List[Project]:
        """
        Search for projects by name or description.

        Args:
            query (str): Search term

        Returns:
            List[Project]: Projects matching the search query
        """
        try:
            # Use repository to perform search
            projects = self._repository.search_projects(query)

            log_debug(f"Found {len(projects)} projects matching query '{query}'")
            return projects

        except Exception as e:
            log_error(f"Failed to search projects with query '{query}': {str(e)}")
            raise